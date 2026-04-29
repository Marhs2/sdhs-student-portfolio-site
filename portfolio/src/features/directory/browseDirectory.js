import { extractGithubUsername } from "../../services/githubCommitService.js";

export const DEFAULT_BROWSE_SORT = "githubCommits";
export const BROWSE_PAGE_SIZE = 10;

export const browseSortLabels = {
  featured: "추천순",
  latest: "최신순",
  name: "이름순",
  department: "학과순",
  githubCommits: "GitHub 활동순",
};

const toText = (value) => String(value ?? "").trim();
const toSearchText = (value) => toText(value).toLowerCase();

const uniqueSorted = (values) =>
  [...new Set(values.map(toText).filter(Boolean))].sort((left, right) =>
    left.localeCompare(right, "ko"),
  );

const readFeaturedRank = (profile) => Number(profile.featuredRank || 9999);
const readCreatedTime = (profile) => Date.parse(profile.createdAt || "") || 0;
const compareName = (left, right) =>
  toText(left.name).localeCompare(toText(right.name), "ko");

export const prepareBrowseProfiles = (profiles = [], commitCounts = {}) =>
  profiles.map((profile) => {
    const githubUsername = extractGithubUsername(profile.github).toLowerCase();
    const tags = Array.isArray(profile.tags) ? profile.tags : [];

    return {
      ...profile,
      githubUsername,
      githubCommitCount: commitCounts[githubUsername],
      searchText: [
        profile.name,
        profile.description,
        profile.job,
        profile.department,
        ...tags,
      ]
        .map(toSearchText)
        .filter(Boolean)
        .join(" "),
    };
  });

export const buildBrowseOptions = (profiles = []) => ({
  departments: uniqueSorted(profiles.map((profile) => profile.department)),
});

export const filterBrowseProfiles = (profiles = [], filters = {}) => {
  const normalizedSearch = toSearchText(filters.search);
  const selectedJobs = Array.isArray(filters.jobs) ? filters.jobs : [];

  return profiles.filter(
    (profile) =>
      (!normalizedSearch || profile.searchText.includes(normalizedSearch)) &&
      (!selectedJobs.length || selectedJobs.includes(profile.job)) &&
      (!filters.department || profile.department === filters.department),
  );
};

export const sortBrowseProfiles = (profiles = [], sort = DEFAULT_BROWSE_SORT) =>
  [...profiles].sort((left, right) => {
    const leftRank = readFeaturedRank(left);
    const rightRank = readFeaturedRank(right);
    const leftDate = readCreatedTime(left);
    const rightDate = readCreatedTime(right);

    if (sort === "latest") {
      return rightDate - leftDate || leftRank - rightRank;
    }
    if (sort === "name") {
      return compareName(left, right) || leftRank - rightRank;
    }
    if (sort === "department") {
      return (
        toText(left.department).localeCompare(toText(right.department), "ko") ||
        leftRank - rightRank
      );
    }
    if (sort === "githubCommits") {
      const leftCommits = Number(left.githubCommitCount || 0);
      const rightCommits = Number(right.githubCommitCount || 0);
      return rightCommits - leftCommits || leftRank - rightRank || compareName(left, right);
    }

    return leftRank - rightRank || rightDate - leftDate;
  });

export const paginateBrowseProfiles = (
  profiles = [],
  currentPage = 1,
  pageSize = BROWSE_PAGE_SIZE,
) => {
  const safePage = Math.max(1, Number(currentPage) || 1);
  const startIndex = (safePage - 1) * pageSize;
  return profiles.slice(startIndex, startIndex + pageSize);
};

export const buildBrowseState = ({
  profiles = [],
  filters = {},
  commitCounts = {},
  currentPage = 1,
  pageSize = BROWSE_PAGE_SIZE,
} = {}) => {
  const preparedProfiles = prepareBrowseProfiles(profiles, commitCounts);
  const filteredProfiles = sortBrowseProfiles(
    filterBrowseProfiles(preparedProfiles, filters),
    filters.sort || DEFAULT_BROWSE_SORT,
  );
  const filteredCount = filteredProfiles.length;
  const totalPages = Math.max(1, Math.ceil(filteredCount / pageSize));
  const safePage = Math.min(Math.max(1, Number(currentPage) || 1), totalPages);

  return {
    filteredProfiles,
    filteredCount,
    options: buildBrowseOptions(profiles),
    paginatedProfiles: paginateBrowseProfiles(filteredProfiles, safePage, pageSize),
    totalPages,
    safePage,
    pageStart: filteredCount === 0 ? 0 : (safePage - 1) * pageSize + 1,
    pageEnd: Math.min(safePage * pageSize, filteredCount),
  };
};

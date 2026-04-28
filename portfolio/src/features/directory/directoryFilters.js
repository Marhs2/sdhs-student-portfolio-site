export const ALL_FILTER = "all";

const toText = (value) => String(value ?? "").trim();

const normalizeSearch = (value) => toText(value).toLowerCase();

const uniqueSorted = (values) =>
  [...new Set(values.map(toText).filter(Boolean))].sort((left, right) =>
    left.localeCompare(right),
  );

export const buildDirectoryOptions = (profiles = []) => ({
  schools: uniqueSorted(profiles.map((profile) => profile.school)),
  departments: uniqueSorted(profiles.map((profile) => profile.department)),
  tracks: uniqueSorted(profiles.map((profile) => profile.track)),
  tags: uniqueSorted(profiles.flatMap((profile) => profile.tags || [])),
});

export const getInitialDirectoryFilters = () => ({
  search: "",
  job: ALL_FILTER,
  school: ALL_FILTER,
  department: ALL_FILTER,
  track: ALL_FILTER,
  tag: ALL_FILTER,
  sort: "featured",
});

export const filterDirectoryProfiles = (profiles = [], filters = {}) => {
  const search = normalizeSearch(filters.search);

  return profiles.filter((profile) => {
    const tags = Array.isArray(profile.tags) ? profile.tags : [];
    const haystack = [
      profile.name,
      profile.description,
      profile.github,
      profile.job,
      profile.school,
      profile.department,
      profile.track,
      ...tags,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return (
      (!search || haystack.includes(search)) &&
      (!filters.job || filters.job === ALL_FILTER || profile.job === filters.job) &&
      (!filters.school || filters.school === ALL_FILTER || profile.school === filters.school) &&
      (!filters.department ||
        filters.department === ALL_FILTER ||
        profile.department === filters.department) &&
      (!filters.track || filters.track === ALL_FILTER || profile.track === filters.track) &&
      (!filters.tag || filters.tag === ALL_FILTER || tags.includes(filters.tag))
    );
  });
};

export const sortDirectoryProfiles = (profiles = [], sort = "featured") =>
  [...profiles].sort((left, right) => {
    if (sort === "latest") {
      return String(right.createdAt || "").localeCompare(String(left.createdAt || ""));
    }
    if (sort === "name") {
      return toText(left.name).localeCompare(toText(right.name));
    }
    if (sort === "department") {
      return [toText(left.department), toText(left.name)]
        .join(" ")
        .localeCompare([toText(right.department), toText(right.name)].join(" "));
    }
    if (sort === "githubCommits") {
      return (Number(right.githubCommitCount) || 0) - (Number(left.githubCommitCount) || 0);
    }

    return (Number(left.featuredRank) || 9999) - (Number(right.featuredRank) || 9999);
  });

export const buildDirectoryState = (profiles = [], filters = {}) => {
  const normalizedFilters = {
    ...getInitialDirectoryFilters(),
    ...filters,
  };
  const filtered = filterDirectoryProfiles(profiles, normalizedFilters);

  return {
    rows: sortDirectoryProfiles(filtered, normalizedFilters.sort),
    options: buildDirectoryOptions(profiles),
    activeFilterCount: [
      normalizedFilters.job,
      normalizedFilters.school,
      normalizedFilters.department,
      normalizedFilters.track,
      normalizedFilters.tag,
    ].filter((value) => value && value !== ALL_FILTER).length + (normalizedFilters.search ? 1 : 0),
  };
};

import { getProfileCompleteness } from "../../shared/catalog/profileCompleteness.js";

const toText = (value) => String(value ?? "").trim();
const toSearchTokens = (value) => toText(value).toLowerCase().split(/\s+/).filter(Boolean);
const hasGithubProfile = (profile = {}) => /^https:\/\/github\.com\/[^/\s]+\/?$/i.test(toText(profile.github));

const ISSUE_LABELS = {
  name: "이름",
  job: "직무",
  description: "소개",
  school: "학교",
  department: "학과",
  github: "GitHub",
  image: "이미지",
};

const REVIEW_STATUS_LABELS = {
  draft: "초안",
  review: "검토",
  approved: "승인",
};

export const createAdminDraft = (profile = {}) => ({
  reviewStatus: profile.reviewStatus || "draft",
  isVisible: profile.isVisible !== false,
  isAdmin: Boolean(profile.isAdmin),
  featuredRank: Number(profile.featuredRank || 9999),
  school: profile.school || "",
  department: profile.department || "",
  track: profile.track || "",
});

export const syncAdminDrafts = (drafts, profiles = []) => {
  const activeIds = new Set(profiles.map((profile) => String(profile.id)));

  Object.keys(drafts).forEach((id) => {
    if (!activeIds.has(String(id))) {
      delete drafts[id];
    }
  });

  profiles.forEach((profile) => {
    drafts[profile.id] = createAdminDraft(profile);
  });
};

export const isAdminDraftDirty = (profile = {}, draft = {}) => {
  const baseline = createAdminDraft(profile);

  return (
    baseline.reviewStatus !== draft.reviewStatus ||
    baseline.isVisible !== draft.isVisible ||
    baseline.isAdmin !== Boolean(draft.isAdmin) ||
    baseline.featuredRank !== Number(draft.featuredRank || 9999) ||
    baseline.school !== toText(draft.school) ||
    baseline.department !== toText(draft.department) ||
    baseline.track !== toText(draft.track)
  );
};

export const getAdminProfileIssues = (profile = {}) => {
  const completeness = getProfileCompleteness(profile);
  const issues = completeness.missing.map((item) => `${ISSUE_LABELS[item] || item} 누락`);

  if (!profile.isVisible) {
    issues.push("비공개");
  }

  if (profile.reviewStatus !== "approved") {
    issues.push(profile.reviewStatus === "review" ? "검토 대기" : "초안");
  }

  return issues;
};

export const buildAdminSummary = (profiles = []) => {
  const completenessScores = profiles.map((profile) => getProfileCompleteness(profile).percent);
  const averageCompleteness =
    completenessScores.length > 0
      ? Math.round(
          completenessScores.reduce((total, score) => total + score, 0) /
            completenessScores.length,
        )
      : 0;

  return {
    total: profiles.length,
    visible: profiles.filter((profile) => profile.isVisible).length,
    approved: profiles.filter((profile) => profile.reviewStatus === "approved").length,
    review: profiles.filter((profile) => profile.reviewStatus === "review").length,
    draft: profiles.filter((profile) => profile.reviewStatus === "draft").length,
    hidden: profiles.filter((profile) => !profile.isVisible).length,
    admins: profiles.filter((profile) => profile.isAdmin).length,
    needsWork: profiles.filter((profile) => getProfileCompleteness(profile).percent < 70).length,
    exposedDrafts: profiles.filter(
      (profile) => profile.isVisible && profile.reviewStatus !== "approved",
    ).length,
    averageCompleteness,
  };
};

export const buildDirtyAdminRows = (profiles = [], drafts = {}) =>
  profiles.filter((profile) => isAdminDraftDirty(profile, drafts[profile.id] || createAdminDraft(profile)));

export const applyAdminDraftPatch = (drafts, rows = [], patch = {}) => {
  rows.forEach((row) => {
    drafts[row.id] = {
      ...(drafts[row.id] || createAdminDraft(row)),
      ...patch,
    };
  });
};

export const buildAdminRows = (profiles = [], filters = {}) => {
  const searchTokens = toSearchTokens(filters.search);
  const quickView = filters.quickView || "all";

  return profiles
    .filter((profile) => {
      const completeness = getProfileCompleteness(profile);
      const searchableText = [
        profile.id,
        profile.name,
        profile.email,
        profile.description,
        profile.job,
        profile.school,
        profile.department,
        profile.track,
        profile.github,
        profile.reviewStatus,
        profile.isVisible ? "visible 공개" : "hidden 비공개",
        ...(profile.tags || []),
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = searchTokens.every((token) => searchableText.includes(token));
      if (!matchesSearch) {
        return false;
      }

      if (quickView === "needsWork") {
        return completeness.percent < 70;
      }
      if (quickView === "exposedDrafts") {
        return profile.isVisible && profile.reviewStatus !== "approved";
      }
      if (quickView === "hidden") {
        return !profile.isVisible;
      }
      if (quickView === "missingGithub") {
        return !hasGithubProfile(profile);
      }
      if (quickView === "admins") {
        return Boolean(profile.isAdmin);
      }

      return true;
    })
    .map((profile) => ({
      ...profile,
      completeness: getProfileCompleteness(profile),
      issues: getAdminProfileIssues(profile),
      reviewStatusLabel: REVIEW_STATUS_LABELS[profile.reviewStatus] || "초안",
    }));
};

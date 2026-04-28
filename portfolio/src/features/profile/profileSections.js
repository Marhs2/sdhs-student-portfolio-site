const toText = (value) => String(value ?? "").trim();

const stripHtml = (value) => toText(value).replace(/<[^>]*>/g, "").trim();

const isGithubUrl = (value) => /^https:\/\/(www\.)?github\.com\/.+/i.test(toText(value));

const STATUS_LABELS = {
  draft: "초안",
  review: "검토 중",
  approved: "승인",
};

export const buildProfileSections = (profile = {}, projects = [], htmlContent = "") => {
  const safeProjects = Array.isArray(projects) ? projects : [];
  const representativeProject =
    safeProjects.find((item) => item.isFeatured) || safeProjects[0] || null;
  const remainingProjects = representativeProject
    ? safeProjects.filter((item) => item.id !== representativeProject.id)
    : safeProjects;

  const taxonomyLine = [profile.school, profile.department]
    .map(toText)
    .filter(Boolean)
    .join(" · ");
  const metaItems = [
    profile.school ? { label: "학교", value: profile.school } : null,
    profile.department ? { label: "학과", value: profile.department } : null,
  ].filter(Boolean);

  return {
    cleanDescription: stripHtml(profile.description) || "소개를 준비 중입니다.",
    taxonomyLine,
    metaItems,
    statusLabel: STATUS_LABELS[profile.reviewStatus] || STATUS_LABELS.draft,
    visibilityLabel: profile.isVisible === false ? "비공개" : "공개",
    isPrivate: profile.isVisible === false,
    projectCount: safeProjects.length,
    hasValidGithub: isGithubUrl(profile.github),
    representativeProject,
    remainingProjects,
    displayProjects: representativeProject ? remainingProjects : safeProjects,
    extraHtml: toText(htmlContent),
  };
};

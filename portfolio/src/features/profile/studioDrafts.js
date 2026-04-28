export { parseTags } from "../../shared/catalog/tags.js";

export const createEmptyProjectDraft = () => ({
  title: "",
  description: "",
  contribution: "",
  tagsText: "",
  githubUrl: "",
  websiteUrl: "",
  videoUrl: "",
  imageUrl: "",
  isFeatured: false,
});

export const hydrateProjectDraft = (item) => ({
  title: item?.title || "",
  description: item?.description || "",
  contribution: item?.contribution || "",
  tagsText: Array.isArray(item?.tags) ? item.tags.join(", ") : "",
  githubUrl: item?.githubUrl || "",
  websiteUrl: item?.websiteUrl || item?.customLinkUrl || "",
  videoUrl: item?.videoUrl || "",
  imageUrl: item?.imageUrl || "",
  isFeatured: Boolean(item?.isFeatured),
});

const isHttpUrl = (value) => /^https?:\/\/.+/i.test(String(value || "").trim());

export const buildProjectValidationState = (project = {}) => {
  const title = String(project.title || "").trim();
  const websiteUrl = String(project.websiteUrl || project.customLinkUrl || "").trim();

  if (!title) {
    return {
      canSubmit: false,
      message: "프로젝트 이름을 입력해 주세요.",
    };
  }

  if (websiteUrl && !isHttpUrl(websiteUrl)) {
    return {
      canSubmit: false,
      message: "웹 사이트 링크는 https:// 또는 http://로 시작해야 합니다.",
    };
  }

  return {
    canSubmit: true,
    message: "",
  };
};

export const removeProjectById = (projects = [], projectId) =>
  projects.filter((project) => String(project?.id) !== String(projectId));

export const buildProfileFormDraft = (profile) => ({
  name: profile?.name || "",
  description: profile?.description || "",
  job: profile?.job || "",
  tagsText: Array.isArray(profile?.tags) ? profile.tags.join(", ") : "",
  github: profile?.github || "",
  imageUrl: profile?.imageUrl || "",
  isVisible: profile?.isVisible !== false,
});

export const buildStudioSections = ({ completenessPercent, projectCount, noteFieldCount }) => [
  { label: "기본 정보", value: `${Number(completenessPercent) || 0}%` },
  { label: "프로젝트", value: `${Number(projectCount) || 0}개` },
  { label: "추가 정보", value: noteFieldCount > 0 ? `${noteFieldCount}칸` : "없음" },
];

export const buildVisibilityToggleCopy = (isVisible) =>
  isVisible
    ? {
        statusLabel: "공개",
        actionLabel: "비공개로 전환",
        nextVisible: false,
      }
    : {
        statusLabel: "비공개",
        actionLabel: "공개로 전환",
        nextVisible: true,
      };

export const shouldLoadPrivateProfileAssets = ({ profile, authState, targetProfileId }) => {
  if (!profile?.id || !authState?.user) {
    return false;
  }

  if (authState.isAdmin) {
    return true;
  }

  if (authState.profileId && Number(authState.profileId) === Number(profile.id)) {
    return true;
  }

  return !targetProfileId;
};

export const shouldRequestAuthenticatedProfileBundle = ({ profileId, authState }) => {
  if (!profileId || !authState?.user) {
    return false;
  }

  if (authState.isAdmin) {
    return true;
  }

  return Number(authState.profileId) === Number(profileId);
};

export const shouldRetryAuthenticatedProfileLoad = ({
  error,
  wasAuthenticated,
  authState,
}) =>
  error?.status === 404 &&
  !wasAuthenticated &&
  Boolean(authState?.user);

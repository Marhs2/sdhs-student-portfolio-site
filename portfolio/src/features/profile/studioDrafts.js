import { parseTags } from "../../shared/catalog/tags.js";

export { parseTags };

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
      message: "프로젝트 제목을 먼저 입력하세요.",
    };
  }

  if (websiteUrl && !isHttpUrl(websiteUrl)) {
    return {
      canSubmit: false,
      message: "웹사이트 링크는 https:// 또는 http://로 시작해야 합니다.",
    };
  }

  return {
    canSubmit: true,
    message: "",
  };
};

export const buildProjectCompletionState = (project = {}) => {
  const hasTitle = Boolean(String(project.title || "").trim());
  const hasDescription = String(project.description || "").trim().length >= 40;
  const hasContribution = Boolean(String(project.contribution || "").trim());
  const hasTags = parseTags(project.tagsText || "").length > 0;
  const hasProofLink = [
    project.githubUrl,
    project.websiteUrl || project.customLinkUrl,
    project.videoUrl,
    project.imageUrl,
  ].some((value) => Boolean(String(value || "").trim()));

  const items = [
    { key: "title", label: "프로젝트 제목", done: hasTitle },
    { key: "description", label: "40자 이상 설명", done: hasDescription },
    { key: "contribution", label: "내 역할", done: hasContribution },
    { key: "proof", label: "증빙 링크 또는 미디어", done: hasProofLink },
    { key: "tags", label: "태그", done: hasTags },
  ];
  const doneCount = items.filter((item) => item.done).length;

  return {
    items,
    doneCount,
    percent: Math.round((doneCount / items.length) * 100),
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
  { label: "상세 정보", value: noteFieldCount > 0 ? `${noteFieldCount}개 항목` : "없음" },
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

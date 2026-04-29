<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { useRoute, useRouter } from "vue-router";

import PortfolioItemForm from "../features/profile/PortfolioItemForm.vue";
import TagInput from "../shared/ui/TagInput.vue";
import {
  buildProfileFormDraft,
  buildStudioSections,
  buildVisibilityToggleCopy,
  createEmptyProjectDraft,
  hydrateProjectDraft,
  parseTags,
  removeProjectById,
  shouldLoadPrivateProfileAssets,
} from "../features/profile/studioDrafts.js";
import { cropDefaults, getCropPreviewStyle, getSquareCrop } from "../features/profile/imageCrop.js";
import SurfaceSection from "../shared/layout/SurfaceSection.vue";
import StatusView from "../shared/ui/StatusView.vue";
import { showSuccess, showError } from "../shared/ui/toast.js";
import {
  buildAdvancedNotesHtml,
  getAdvancedNoteFields,
  parseAdvancedNotesHtml,
} from "../shared/catalog/advancedNotes.js";
import { TAG_OPTIONS } from "../shared/catalog/tags.js";
import { getProfileCompleteness } from "../shared/catalog/profileCompleteness.js";
import { getAuthState, getMyProfile } from "../services/authService";
import {
    createProfile,
    deleteProfile,
    getProfileById,
  getProfileHtml,
  saveProfileHtml,
  updateProfile,
  uploadProfileImage,
} from "../services/profileService";
import {
  createPortfolioItem,
  deletePortfolioItem,
  listPortfolioItemsByProfile,
  updatePortfolioItem,
} from "../services/portfolioItemService";
import { JOB_OPTIONS } from "../services/jobs.js";

const noteFields = getAdvancedNoteFields();
const route = useRoute();
const router = useRouter();
const MIN_DESCRIPTION_LENGTH = 80;
const isLoading = ref(true);
const pageError = ref("");
const saveMessage = ref("");
const saveState = ref("info");
const notesMessage = ref("");
const notesState = ref("info");
const isSavingProfile = ref(false);
const isSavingNotes = ref(false);
const isSavingNewItem = ref(false);
const isSavingExistingItem = ref(false);
const isSavingVisibility = ref(false);
const isDeletingProfile = ref(false);
const deletingItemId = ref(null);
const authState = ref({
  user: null,
  isAdmin: false,
  profileId: null,
  hasProfile: false,
  loading: false,
});
const currentProfile = ref(null);
const portfolioItems = ref([]);
const selectedImage = ref(null);
const previewImage = ref("");
let previewObjectUrl = "";
const imageNaturalSize = reactive({
  width: 0,
  height: 0,
});
const imageCrop = reactive({
  x: cropDefaults.x,
  y: cropDefaults.y,
  zoom: cropDefaults.zoom,
});
const editingItemId = ref(null);
const editingItemDraft = ref(null);
const projectSort = ref("featured");

const profileForm = reactive({
  name: "",
  description: "",
  job: "",
  tagsText: "",
  github: "",
  imageUrl: "",
  isVisible: true,
});

const advancedSections = reactive({
  extraIntroduction: "",
  exhibitionNote: "",
  processNote: "",
});
const customAdvancedHtml = ref("");

const newItemDraft = ref(createEmptyProjectDraft());

const pageTitle = computed(() =>
  currentProfile.value
    ? authState.value.isAdmin && targetProfileId.value && authState.value.profileId !== currentProfile.value.id
      ? `${currentProfile.value.name || "프로필"} 수정`
      : "내 포트폴리오 수정"
    : "포트폴리오 작성",
);
const showAccessGate = computed(() => !isLoading.value && !authState.value.user);
const targetProfileId = computed(() => {
  const raw = Number(route.params.id);
  return Number.isFinite(raw) ? raw : null;
});
const profileDraftCompleteness = computed(() =>
  getProfileCompleteness({
    name: profileForm.name,
    job: profileForm.job,
    description: profileForm.description,
    github: profileForm.github,
    imageUrl: previewImage.value || profileForm.imageUrl,
    tags: parseTags(profileForm.tagsText),
  }),
);
const studioSections = computed(() =>
  buildStudioSections({
    completenessPercent: profileDraftCompleteness.value.percent,
    projectCount: portfolioItems.value.length,
    noteFieldCount: noteFields.length,
  }),
);
const visibilityToggle = computed(() =>
  buildVisibilityToggleCopy(profileForm.isVisible),
);
const qualityTasks = computed(() => [
  {
    label: "공개 이름",
    done: Boolean(profileForm.name.trim()),
  },
  {
    label: "직무 선택",
    done: Boolean(profileForm.job.trim()),
  },
  {
    label: `소개 ${MIN_DESCRIPTION_LENGTH}자 이상`,
    done: profileForm.description.trim().length >= MIN_DESCRIPTION_LENGTH,
  },
  {
    label: "GitHub URL",
    done: /^https:\/\/github\.com\//i.test(profileForm.github.trim()),
  },
  {
    label: "프로젝트 1개 이상",
    done: portfolioItems.value.length > 0,
  },
]);
const descriptionLength = computed(() => profileForm.description.trim().length);
const descriptionRemaining = computed(() =>
  Math.max(0, MIN_DESCRIPTION_LENGTH - descriptionLength.value),
);
const qualityDoneCount = computed(() => qualityTasks.value.filter((task) => task.done).length);
const sortedPortfolioItems = computed(() =>
  [...portfolioItems.value].sort((left, right) => {
    if (projectSort.value === "latest") {
      return (Date.parse(right.createdAt || "") || 0) - (Date.parse(left.createdAt || "") || 0);
    }
    if (projectSort.value === "title") {
      return String(left.title || "").localeCompare(String(right.title || ""), "ko");
    }
    return Number(right.isFeatured) - Number(left.isFeatured)
      || (Date.parse(right.createdAt || "") || 0) - (Date.parse(left.createdAt || "") || 0);
  }),
);
const imageCropStyle = computed(() => {
  if (!imageNaturalSize.width || !imageNaturalSize.height) {
    return {};
  }

  return getCropPreviewStyle({
    width: imageNaturalSize.width,
    height: imageNaturalSize.height,
    crop: imageCrop,
  });
});
const noteLabelMap = {
  extraIntroduction: "추가 소개",
  exhibitionNote: "전시 메모",
  processNote: "과정 메모",
};
const isHttpUrl = (value) => /^https?:\/\/.+/i.test(String(value || "").trim());

const applyAdvancedNotes = (html) => {
  const parsed = parseAdvancedNotesHtml(html);
  advancedSections.extraIntroduction = parsed.sections.extraIntroduction;
  advancedSections.exhibitionNote = parsed.sections.exhibitionNote;
  advancedSections.processNote = parsed.sections.processNote;
  customAdvancedHtml.value = parsed.customHtml;
};

const applyProfile = async (profile) => {
  currentProfile.value = profile;
  Object.assign(profileForm, buildProfileFormDraft(profile));
  previewImage.value = profile?.imageUrl || "";

  if (profile?.id) {
    const needsAuth = shouldLoadPrivateProfileAssets({
      profile,
      authState: authState.value,
      targetProfileId: targetProfileId.value,
    });
    const [htmlResponse, items] = await Promise.all([
      getProfileHtml(profile.id, { authenticated: needsAuth }),
      listPortfolioItemsByProfile(profile.id, { authenticated: needsAuth }),
    ]);
    applyAdvancedNotes(htmlResponse.html || "");
    portfolioItems.value = items;
  } else {
    applyAdvancedNotes("");
    portfolioItems.value = [];
  }

  editingItemId.value = null;
  editingItemDraft.value = null;
};

const loadPage = async () => {
  isLoading.value = true;
  pageError.value = "";

  try {
    authState.value = await getAuthState({ force: true });
    if (!authState.value.user) {
      pageError.value = "로그인 후 포트폴리오를 작성할 수 있습니다.";
      return;
    }

    if (targetProfileId.value && authState.value.isAdmin) {
      const targetProfile = await getProfileById(targetProfileId.value, { authenticated: true });
      await applyProfile(targetProfile);
      return;
    }

    if (targetProfileId.value && !authState.value.isAdmin) {
      pageError.value = "다른 유저의 프로필을 수정할 권한이 없습니다.";
      return;
    }

    if (authState.value.profileId) {
      const myProfile = await getMyProfile();
      await applyProfile(myProfile);
      return;
    }

    await applyProfile(null);
  } catch (error) {
    if (error.status === 404) {
      await applyProfile(null);
    } else {
      pageError.value = error.message || "편집 화면을 불러오지 못했습니다.";
    }
  } finally {
    isLoading.value = false;
  }
};

const handleImageChange = (event) => {
  const file = event.target.files?.[0] || null;
  selectedImage.value = file;
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = "";
  }
  previewObjectUrl = file ? URL.createObjectURL(file) : "";
  previewImage.value = previewObjectUrl || profileForm.imageUrl;
  imageNaturalSize.width = 0;
  imageNaturalSize.height = 0;
  imageCrop.x = cropDefaults.x;
  imageCrop.y = cropDefaults.y;
  imageCrop.zoom = cropDefaults.zoom;
};

const handleCropImageLoad = (event) => {
  imageNaturalSize.width = event.target.naturalWidth || 0;
  imageNaturalSize.height = event.target.naturalHeight || 0;
};

const scrollToSection = (sectionId) => {
  document.getElementById(sectionId)?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
};

const loadImage = (src) =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });

const buildCroppedImageFile = async () => {
  if (!selectedImage.value || !previewObjectUrl) {
    return selectedImage.value;
  }

  const image = await loadImage(previewObjectUrl);
  const canvas = document.createElement("canvas");
  const outputSize = 640;
  canvas.width = outputSize;
  canvas.height = outputSize;
  const context = canvas.getContext("2d");
  if (!context) {
    return selectedImage.value;
  }

  const { x: sourceX, y: sourceY, size: baseSize } = getSquareCrop({
    width: image.naturalWidth,
    height: image.naturalHeight,
    crop: imageCrop,
  });

  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(image, sourceX, sourceY, baseSize, baseSize, 0, 0, outputSize, outputSize);

  return new Promise((resolve) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          resolve(selectedImage.value);
          return;
        }
        resolve(new File([blob], selectedImage.value.name.replace(/\.[^.]+$/, ".webp"), {
          type: "image/webp",
        }));
      },
      "image/webp",
      0.82,
    );
  });
};

const handleSaveProfile = async () => {
  if (!authState.value.user) {
    return;
  }

  const isCreatingProfile = !currentProfile.value?.id;

  isSavingProfile.value = true;
  saveMessage.value = "";

  try {
    let imageUrl = profileForm.imageUrl || "";
    if (selectedImage.value) {
      const uploadFile = await buildCroppedImageFile();
      const upload = await uploadProfileImage(uploadFile);
      imageUrl = upload.imageUrl;
    }

    const payload = {
      name: profileForm.name.trim(),
      description: profileForm.description.trim(),
      job: profileForm.job.trim(),
      tags: parseTags(profileForm.tagsText),
      github: profileForm.github.trim(),
      imageUrl,
      isVisible: Boolean(profileForm.isVisible),
    };
    if (isCreatingProfile) {
      payload.createProfileConsent = true;
    }

    const nextProfile = currentProfile.value?.id
      ? await updateProfile(currentProfile.value.id, payload)
      : await createProfile(payload);

    showSuccess(currentProfile.value?.id
      ? "프로필 기본 정보를 저장했습니다."
      : "프로필을 생성했습니다. 프로젝트를 추가해 보세요.");
    saveState.value = "success";
    selectedImage.value = null;
    if (previewObjectUrl) {
      URL.revokeObjectURL(previewObjectUrl);
      previewObjectUrl = "";
    }
    await applyProfile(nextProfile);
    authState.value = await getAuthState({ force: true });
  } catch (error) {
    saveMessage.value = error.message || "프로필을 저장하지 못했습니다.";
    showError(saveMessage.value);
    saveState.value = "error";
  } finally {
    isSavingProfile.value = false;
  }
};

const handleToggleVisibility = async () => {
  if (!currentProfile.value?.id || isSavingVisibility.value) {
    return;
  }

  const previousVisible = Boolean(profileForm.isVisible);
  const nextVisible = !previousVisible;
  isSavingVisibility.value = true;
  profileForm.isVisible = nextVisible;

  try {
    const updated = await updateProfile(currentProfile.value.id, { isVisible: nextVisible });
    currentProfile.value = updated;
    profileForm.isVisible = updated.isVisible !== false;
    saveMessage.value = profileForm.isVisible
      ? "프로필을 공개로 전환했습니다."
      : "프로필을 비공개로 전환했습니다.";
    saveState.value = "success";
    showSuccess(saveMessage.value);
    authState.value = await getAuthState({ force: true });
  } catch (error) {
    profileForm.isVisible = previousVisible;
    saveMessage.value = error.message || "프로필 공개 상태를 변경하지 못했습니다.";
    saveState.value = "error";
    showError(saveMessage.value);
  } finally {
    isSavingVisibility.value = false;
  }
};

const handleDeleteProfile = async () => {
  if (!currentProfile.value?.id || isDeletingProfile.value) {
    return;
  }

  const shouldDelete = window.confirm(
    "프로필과 등록된 프로젝트를 모두 삭제할까요? 삭제 후 되돌릴 수 없습니다.",
  );
  if (!shouldDelete) {
    return;
  }

  isDeletingProfile.value = true;
  try {
    await deleteProfile(currentProfile.value.id);
    showSuccess("프로필을 삭제했습니다.");
    authState.value = await getAuthState({ force: true });
    await router.replace("/");
  } catch (error) {
    saveMessage.value = error.message || "프로필을 삭제하지 못했습니다.";
    saveState.value = "error";
    showError(saveMessage.value);
  } finally {
    isDeletingProfile.value = false;
  }
};

const handleSaveNotes = async () => {
  if (!currentProfile.value?.id) {
    notesMessage.value = "기본 프로필을 먼저 저장해 주세요.";
    notesState.value = "error";
    showError("기본 프로필을 먼저 저장해 주세요.");
    return;
  }

  isSavingNotes.value = true;
  notesMessage.value = "";

  try {
    const html = buildAdvancedNotesHtml({
      sections: advancedSections,
      customHtml: customAdvancedHtml.value,
    });
    const saved = await saveProfileHtml(currentProfile.value.id, html);
    applyAdvancedNotes(saved.html || "");
    notesMessage.value = "추가 정보를 저장했습니다.";
    notesState.value = "success";
    showSuccess("추가 정보를 저장했습니다.");
  } catch (error) {
    notesMessage.value = error.message || "추가 정보를 저장하지 못했습니다.";
    notesState.value = "error";
  } finally {
    isSavingNotes.value = false;
  }
};

const handleCreatePortfolioItem = async (payload) => {
  if (!currentProfile.value?.id) {
    saveMessage.value = "기본 프로필을 먼저 저장해 주세요.";
    saveState.value = "error";
    return;
  }

  isSavingNewItem.value = true;

  try {
    const created = await createPortfolioItem(payload);
    portfolioItems.value = [created, ...portfolioItems.value];
    newItemDraft.value = createEmptyProjectDraft();
    saveMessage.value = "프로젝트를 추가했습니다.";
    saveState.value = "success";
    showSuccess("프로젝트를 추가했습니다.");
  } catch (error) {
    saveMessage.value = error.message || "프로젝트를 추가하지 못했습니다.";
    saveState.value = "error";
  } finally {
    isSavingNewItem.value = false;
  }
};

const startEditingItem = (item) => {
  editingItemId.value = item.id;
  editingItemDraft.value = hydrateProjectDraft(item);
};

const cancelEditingItem = () => {
  editingItemId.value = null;
  editingItemDraft.value = null;
};

const handleDeletePortfolioItem = async (item) => {
  if (!item?.id || deletingItemId.value) {
    return;
  }

  const shouldDelete = window.confirm(
    `"${item.title || "프로젝트"}" 프로젝트를 삭제할까요? 삭제 후 되돌릴 수 없습니다.`,
  );
  if (!shouldDelete) {
    return;
  }

  deletingItemId.value = item.id;

  try {
    await deletePortfolioItem(item.id);
    portfolioItems.value = removeProjectById(portfolioItems.value, item.id);
    if (editingItemId.value === item.id) {
      cancelEditingItem();
    }
    saveMessage.value = "프로젝트를 삭제했습니다.";
    saveState.value = "success";
    showSuccess("프로젝트를 삭제했습니다.");
  } catch (error) {
    saveMessage.value = error.message || "프로젝트를 삭제하지 못했습니다.";
    saveState.value = "error";
    showError(saveMessage.value);
  } finally {
    deletingItemId.value = null;
  }
};

const handleUpdateExistingItem = async (payload) => {
  if (!editingItemId.value) {
    return;
  }

  isSavingExistingItem.value = true;

  try {
    const updated = await updatePortfolioItem(editingItemId.value, payload);
    portfolioItems.value = portfolioItems.value.map((item) =>
      item.id === updated.id ? updated : item,
    );
    saveMessage.value = "프로젝트를 수정했습니다.";
    saveState.value = "success";
    showSuccess("프로젝트를 수정했습니다.");
    cancelEditingItem();
  } catch (error) {
    saveMessage.value = error.message || "프로젝트를 수정하지 못했습니다.";
    saveState.value = "error";
  } finally {
    isSavingExistingItem.value = false;
  }
};

watch(
  () => route.params.id,
  async () => {
    await loadPage();
  },
);

onMounted(loadPage);

onUnmounted(() => {
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
  }
});
</script>

<template>
  <StatusView
    v-if="isLoading"
    title="편집 화면을 준비하는 중입니다."
    body="프로필과 프로젝트를 불러오고 있습니다."
  />
  <SurfaceSection
    v-else-if="showAccessGate"
    eyebrow="로그인 필요"
    title="로그인 후 포트폴리오를 작성할 수 있습니다."
    summary="프로필 생성과 프로젝트 편집은 로그인한 사용자만 사용할 수 있습니다."
  >
    <div class="studio-page__gate">
      <RouterLink to="/" class="studio-page__ghost-button">포트폴리오로 이동</RouterLink>
    </div>
  </SurfaceSection>
  <StatusView
    v-else-if="pageError"
    state="error"
    title="편집 화면을 열 수 없습니다."
    :body="pageError"
  />

  <div v-else class="studio-page">
    <div class="studio-page__workspace">
      <section class="studio-page__command-strip" aria-label="프로필 편집 상태">
        <div class="studio-page__command-heading">
          <span>편집 상태</span>
          <strong>{{ pageTitle }}</strong>
        </div>

        <div class="studio-page__compact-progress">
          <strong>{{ profileDraftCompleteness.percent }}%</strong>
          <span>완성도</span>
        </div>

        <div class="studio-page__summary-pills" aria-label="작성 현황">
          <button
            v-for="section in studioSections"
            :key="section.label"
            type="button"
            @click="scrollToSection(section.label === '프로젝트' ? 'studio-projects' : section.label === '추가 정보' ? 'studio-details' : 'studio-profile')"
          >
            {{ section.label }} <strong>{{ section.value }}</strong>
          </button>
        </div>

        <details class="studio-page__quality-menu">
          <summary>점검 {{ qualityDoneCount }}/{{ qualityTasks.length }}</summary>
          <ul>
            <li
              v-for="task in qualityTasks"
              :key="task.label"
              :data-done="task.done"
            >
              <span aria-hidden="true">{{ task.done ? "✓" : "!" }}</span>
              {{ task.label }}
            </li>
          </ul>
        </details>

        <div v-if="previewImage" class="studio-page__thumb">
          <img :src="previewImage" alt="Profile preview" loading="lazy" decoding="async" />
        </div>
      </section>

      <div class="studio-page__content">
        <SurfaceSection
          id="studio-profile"
          eyebrow="기본 정보"
          title="프로필 정보"
          summary="방문자가 가장 먼저 보는 이름, 직무, 소개를 정리합니다."
        >
          <div class="studio-page__form-grid">
            <label>
              <span>이름</span>
              <input v-model="profileForm.name" name="profile-name" type="text" placeholder="이름" />
            </label>

            <label>
              <span>희망 직무</span>
              <select v-model="profileForm.job" name="profile-job">
                <option value="">선택</option>
                <option v-for="job in JOB_OPTIONS" :key="job" :value="job">{{ job }}</option>
              </select>
            </label>

            <label>
              <span>태그</span>
              <TagInput
                v-model="profileForm.tagsText"
                input-id="profile-tags"
                name="profile-tags"
                :suggestions="TAG_OPTIONS"
                placeholder="frontend, unity, design"
              />
            </label>

            <label class="studio-page__wide">
              <span>소개</span>
              <textarea
                v-model="profileForm.description"
                name="profile-description"
                rows="4"
                placeholder="간단한 소개"
              />
              <small>
                {{ descriptionLength }}자 작성됨 ·
                <template v-if="descriptionRemaining > 0">{{ descriptionRemaining }}자 더 작성하면 점검을 통과합니다.</template>
                <template v-else>소개 점검 기준을 통과했습니다.</template>
              </small>
            </label>

            <label>
              <span>GitHub URL</span>
              <input v-model="profileForm.github" name="profile-github" type="url" inputmode="url" placeholder="https://github.com/..." />
            </label>

            <label>
              <span>프로필 이미지</span>
              <input name="profile-image" type="file" accept="image/png,image/jpeg,image/webp" @change="handleImageChange" />
            </label>
          </div>

          <div v-if="previewImage" class="studio-page__image-cropper" :data-cropping="Boolean(selectedImage)">
            <div class="studio-page__image-cropper-preview">
              <img
                :src="previewImage"
                :alt="selectedImage ? '프로필 이미지 자르기 미리보기' : '현재 프로필 이미지'"
                :style="selectedImage ? imageCropStyle : null"
                @load="selectedImage && handleCropImageLoad($event)"
              />
            </div>
            <div v-if="selectedImage" class="studio-page__crop-controls">
              <label>
                <span>가로 위치</span>
                <input v-model.number="imageCrop.x" type="range" min="0" max="100" />
              </label>
              <label>
                <span>세로 위치</span>
                <input v-model.number="imageCrop.y" type="range" min="0" max="100" />
              </label>
              <label>
                <span>확대</span>
                <input v-model.number="imageCrop.zoom" type="range" min="1" max="2.4" step="0.05" />
              </label>
            </div>
            <p v-else class="studio-page__crop-note">새 이미지를 선택하면 위치와 확대를 조정할 수 있습니다.</p>
          </div>

          <p v-if="saveMessage" class="studio-page__message" :data-state="saveState">{{ saveMessage }}</p>

          <div v-if="currentProfile?.id" class="studio-page__visibility-panel">
            <div>
              <span>공개 상태</span>
              <strong :data-visible="profileForm.isVisible">
                {{ visibilityToggle.statusLabel }}
              </strong>
            </div>
            <button
              type="button"
              class="studio-page__ghost-button"
              :disabled="isSavingVisibility"
              @click="handleToggleVisibility"
            >
              {{ isSavingVisibility ? "변경 중..." : visibilityToggle.actionLabel }}
            </button>
            <button
              type="button"
              class="studio-page__danger-button"
              :disabled="isDeletingProfile"
              @click="handleDeleteProfile"
            >
              {{ isDeletingProfile ? "삭제 중..." : "프로필 삭제" }}
            </button>
          </div>

          <label v-else class="studio-page__consent">
            <input v-model="profileForm.isVisible" type="checkbox" name="profile-visible" />
            <span>내 프로필을 공개합니다.</span>
          </label>

          <div class="studio-page__actions">
            <button
              type="button"
              class="studio-page__primary-button"
              :disabled="isSavingProfile"
              @click="handleSaveProfile"
            >
              {{ isSavingProfile ? "저장 중..." : "기본 정보 저장" }}
            </button>
          </div>
        </SurfaceSection>

        <SurfaceSection
          id="studio-projects"
          eyebrow="프로젝트"
          title="프로젝트 목록"
          summary="추가, 수정, 대표 지정까지 여기서 진행합니다."
          tone="muted"
        >
          <template #actions>
            <label class="studio-page__sort-control">
              <span>정렬</span>
              <select v-model="projectSort">
                <option value="featured">대표 먼저</option>
                <option value="latest">최신순</option>
                <option value="title">제목순</option>
              </select>
            </label>
          </template>

          <PortfolioItemForm
            v-model="newItemDraft"
            :busy="isSavingNewItem"
            :disabled="!currentProfile?.id"
            disabled-reason="기본 정보를 먼저 저장하면 프로젝트를 추가할 수 있습니다."
            submit-label="프로젝트 추가"
            @submit="handleCreatePortfolioItem"
          />

          <div v-if="!portfolioItems.length" class="studio-page__project-empty">
            <strong>아직 등록된 프로젝트가 없습니다.</strong>
            <p>대표로 보여줄 작업 1개부터 추가해 보세요. 제목만 저장한 뒤 설명과 링크를 천천히 보강해도 됩니다.</p>
          </div>

          <div v-if="portfolioItems.length" class="studio-page__project-list">
            <article v-for="item in sortedPortfolioItems" :key="item.id" class="studio-page__project-card">
              <div class="studio-page__project-copy">
                <div>
                  <p class="studio-page__project-eyebrow">
                    {{ item.isFeatured ? "대표 프로젝트" : "프로젝트" }}
                  </p>
                  <h3>{{ item.title || "제목 없음" }}</h3>
                </div>
                <p>{{ item.description || "설명 없음" }}</p>
                <p v-if="item.contribution"><strong>기여도</strong> {{ item.contribution }}</p>
                <ul v-if="item.tags.length" class="studio-page__project-tags">
                  <li v-for="tag in item.tags" :key="tag">{{ tag }}</li>
                </ul>
                <a
                  v-if="isHttpUrl(item.websiteUrl)"
                  class="studio-page__project-link"
                  :href="item.websiteUrl"
                  target="_blank"
                  rel="noreferrer"
                >
                  웹 사이트
                </a>
              </div>

              <div class="studio-page__project-actions">
                <button type="button" class="studio-page__ghost-button" @click="startEditingItem(item)">
                  수정
                </button>
                <button
                  type="button"
                  class="studio-page__danger-button"
                  :disabled="deletingItemId === item.id"
                  @click="handleDeletePortfolioItem(item)"
                >
                  {{ deletingItemId === item.id ? "삭제 중..." : "삭제" }}
                </button>
              </div>

              <div v-if="editingItemId === item.id" class="studio-page__project-editor">
                <PortfolioItemForm
                  v-model="editingItemDraft"
                  :busy="isSavingExistingItem"
                  submit-label="프로젝트 수정"
                  @submit="handleUpdateExistingItem"
                />

                <button type="button" class="studio-page__ghost-button" @click="cancelEditingItem">
                  취소
                </button>
              </div>
            </article>
          </div>
        </SurfaceSection>

        <SurfaceSection
          id="studio-details"
          eyebrow="상세 콘텐츠"
          title="상세 내용"
          summary="프로필 본문 아래에 이어지는 소개와 HTML 콘텐츠를 관리합니다."
        >
          <div class="studio-page__detail-editor">
            <section class="studio-page__detail-column" aria-label="텍스트 상세 내용">
              <div class="studio-page__detail-heading">
                <span>텍스트</span>
                <strong>상세 소개</strong>
              </div>

              <div class="studio-page__notes-grid">
                <label v-for="field in noteFields" :key="field.key">
                  <span>{{ noteLabelMap[field.key] || field.label }}</span>
                  <textarea
                    v-model="advancedSections[field.key]"
                    :name="`advanced-${field.key}`"
                    rows="4"
                    :placeholder="`${noteLabelMap[field.key] || field.label} 입력`"
                  />
                </label>
              </div>
            </section>

            <section class="studio-page__html-column" aria-label="HTML 상세 내용">
              <div class="studio-page__detail-heading">
                <span>HTML</span>
                <strong>상세 본문</strong>
              </div>

              <label class="studio-page__html-field">
                <span>HTML 코드</span>
                <textarea
                  v-model="customAdvancedHtml"
                  name="advanced-html"
                  rows="14"
                  placeholder="<section><p>추가 내용</p></section>"
                />
              </label>
            </section>
          </div>

          <p v-if="notesMessage" class="studio-page__message" :data-state="notesState">{{ notesMessage }}</p>

          <div class="studio-page__actions">
            <button
              type="button"
              class="studio-page__primary-button"
              :disabled="isSavingNotes"
              @click="handleSaveNotes"
            >
              {{ isSavingNotes ? "저장 중..." : "추가 정보 저장" }}
            </button>
          </div>
        </SurfaceSection>
      </div>
    </div>
  </div>
</template>

<style scoped>
.studio-page {
  display: grid;
  gap: 24px;
}

.studio-page__workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.studio-page__command-strip {
  position: sticky;
  top: 72px;
  z-index: 20;
  display: grid;
  grid-template-columns: minmax(160px, 0.9fr) auto minmax(260px, 1.6fr) auto auto;
  align-items: center;
  gap: 12px;
  min-height: 64px;
  padding: 10px 12px;
  border: 1px solid rgba(210, 210, 215, 0.9);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
}

.studio-page__command-heading {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.studio-page__command-heading span,
.studio-page__compact-progress span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 800;
}

.studio-page__command-heading strong {
  overflow: hidden;
  color: var(--text-strong);
  font-size: 0.96rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.studio-page__compact-progress {
  display: grid;
  justify-items: center;
  min-width: 76px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  background: var(--brand-soft);
}

.studio-page__compact-progress strong {
  color: var(--text-strong);
  font-size: 1.18rem;
  line-height: 1;
}

.studio-page__summary-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.studio-page__summary-pills button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: var(--bg-surface-muted);
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 700;
}

.studio-page__summary-pills button:hover {
  border-color: var(--brand-main);
  color: var(--brand-main);
}

.studio-page__summary-pills strong {
  color: var(--text-strong);
}

.studio-page__quality-menu {
  position: relative;
  justify-self: end;
}

.studio-page__quality-menu summary {
  min-height: 38px;
  padding: 8px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: var(--text-strong);
  cursor: pointer;
  font-weight: 800;
  list-style: none;
}

.studio-page__quality-menu summary::-webkit-details-marker {
  display: none;
}

.studio-page__quality-menu ul {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 10;
  width: 220px;
  display: grid;
  gap: 8px;
  padding: 12px;
  margin: 0;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-lg);
  list-style: none;
}

.studio-page__quality-menu li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-sub);
  font-size: 0.86rem;
  font-weight: 700;
}

.studio-page__quality-menu li[data-done="true"] {
  color: var(--success-text);
}

.studio-page__quality-menu li span {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: rgba(29, 29, 31, 0.08);
  color: var(--text-main);
  font-size: 0.72rem;
  font-weight: 800;
}

.studio-page__quality-menu li[data-done="true"] span {
  background: var(--success-soft);
  color: var(--success-text);
}

.studio-page__thumb {
  overflow: hidden;
  justify-self: end;
  width: 46px;
  height: 46px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--bg-surface-muted);
}

.studio-page__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.studio-page__content {
  display: grid;
  gap: 24px;
}

.studio-page__gate {
  display: flex;
  justify-content: flex-start;
}

.studio-page__form-grid,
.studio-page__notes-grid {
  display: grid;
  gap: 16px;
}

.studio-page__form-grid,
.studio-page__notes-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.studio-page__form-grid label,
.studio-page__notes-grid label {
  display: grid;
  gap: 8px;
}

.studio-page__form-grid span,
.studio-page__notes-grid span {
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 700;
}

.studio-page__form-grid small {
  color: var(--text-sub);
  font-size: 0.78rem;
  line-height: 1.5;
}

.studio-page__image-cropper {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
}

.studio-page__image-cropper-preview {
  position: relative;
  overflow: hidden;
  width: 132px;
  height: 132px;
  border-radius: 50%;
  background: var(--bg-surface-solid);
}

.studio-page__image-cropper-preview img {
  position: absolute;
  top: 0;
  left: 0;
  max-width: none;
  transform-origin: top left;
}

.studio-page__image-cropper[data-cropping="false"] .studio-page__image-cropper-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.studio-page__crop-controls {
  display: grid;
  gap: 10px;
}

.studio-page__crop-note {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.84rem;
  line-height: 1.5;
}

.studio-page__crop-controls label {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.studio-page__crop-controls span,
.studio-page__sort-control span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 800;
}

.studio-page__detail-editor {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(360px, 1.1fr);
  gap: 18px;
  align-items: start;
}

.studio-page__detail-column,
.studio-page__html-column {
  display: grid;
  gap: 14px;
  min-width: 0;
  padding: 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-surface-muted);
}

.studio-page__html-column {
  background: var(--bg-surface-solid);
}

.studio-page__detail-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.studio-page__detail-heading span {
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 800;
}

.studio-page__detail-heading strong {
  color: var(--text-strong);
  font-size: 1rem;
}

.studio-page__detail-column .studio-page__notes-grid {
  grid-template-columns: 1fr;
}

.studio-page__html-field {
  display: grid;
  gap: 8px;
}

.studio-page__html-field span {
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 700;
}

.studio-page__html-field textarea {
  min-height: 344px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  line-height: 1.6;
  resize: vertical;
}

.studio-page__wide {
  grid-column: 1 / -1;
}

.studio-page__actions {
  display: flex;
  justify-content: flex-end;
}

.studio-page__sort-control {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.studio-page__sort-control select {
  min-width: 120px;
  height: 38px;
  padding: 0 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
}

.studio-page__primary-button,
.studio-page__ghost-button {
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 700;
}

.studio-page__primary-button {
  border: none;
  background: var(--brand-main);
  color: #fff;
}

.studio-page__primary-button:hover {
  background: var(--brand-strong);
}

.studio-page__ghost-button {
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.82);
  color: var(--text-strong);
}

.studio-page__message {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
}

.studio-page__message[data-state="success"] {
  background: var(--success-soft);
  color: var(--success-text);
}

.studio-page__message[data-state="error"] {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.studio-page__consent {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
  color: var(--text-main);
  font-weight: 700;
}

.studio-page__consent input {
  width: 18px;
  height: 18px;
  accent-color: var(--brand-main);
}

.studio-page__visibility-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
}

.studio-page__visibility-panel div {
  display: grid;
  gap: 4px;
}

.studio-page__visibility-panel span {
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 700;
}

.studio-page__visibility-panel strong {
  color: var(--danger-text);
  font-size: 1rem;
}

.studio-page__visibility-panel strong[data-visible="true"] {
  color: var(--success-text);
}

.studio-page__project-list {
  display: grid;
  gap: 16px;
}

.studio-page__project-empty {
  display: grid;
  gap: 6px;
  padding: 16px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--bg-surface-solid);
}

.studio-page__project-empty strong,
.studio-page__project-empty p {
  margin: 0;
}

.studio-page__project-empty strong {
  color: var(--text-strong);
}

.studio-page__project-empty p {
  max-width: 62ch;
  color: var(--text-sub);
  line-height: 1.6;
}

.studio-page__project-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
}

.studio-page__project-copy {
  display: grid;
  gap: 8px;
}

.studio-page__project-copy h3,
.studio-page__project-copy p {
  margin: 0;
}

.studio-page__project-copy p {
  color: var(--text-main);
  line-height: 1.7;
}

.studio-page__project-eyebrow {
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.studio-page__project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.studio-page__project-tags li {
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--text-main);
  font-size: 0.84rem;
}

.studio-page__project-link {
  justify-self: start;
  min-height: 38px;
  padding: 8px 13px;
  border-radius: 999px;
  background: var(--brand-main);
  color: #fff;
  font-weight: 700;
}

.studio-page__project-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.studio-page__danger-button {
  min-height: 44px;
  padding: 0 18px;
  border: 1px solid var(--danger-text);
  border-radius: 999px;
  background: var(--danger-soft);
  color: var(--danger-text);
  font-weight: 700;
}

.studio-page__danger-button:hover:not(:disabled) {
  background: var(--danger-text);
  color: #fff;
}

.studio-page__danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.studio-page__project-editor {
  display: grid;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line-soft);
}

@media (max-width: 900px) {
  .studio-page__form-grid,
  .studio-page__notes-grid,
  .studio-page__image-cropper,
  .studio-page__detail-editor {
    grid-template-columns: 1fr;
  }

  .studio-page__command-strip {
    grid-template-columns: 1fr auto;
    align-items: start;
  }

  .studio-page__summary-pills,
  .studio-page__quality-menu {
    grid-column: 1 / -1;
    justify-self: stretch;
  }

  .studio-page__quality-menu summary {
    width: 100%;
    text-align: center;
  }

  .studio-page__quality-menu ul {
    position: static;
    width: auto;
    margin-top: 10px;
    box-shadow: none;
  }

  .studio-page__thumb {
    grid-row: 1 / span 2;
    grid-column: 2;
  }

  .studio-page__wide {
    grid-column: auto;
  }
}
</style>

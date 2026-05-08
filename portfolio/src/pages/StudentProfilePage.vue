<script setup>
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import PortfolioItemGrid from "../features/profile/PortfolioItemGrid.vue";
import ProfileHtmlSurface from "../features/profile/ProfileHtmlSurface.vue";
import { buildProfileSections } from "../features/profile/profileSections.js";
import {
  shouldRequestAuthenticatedProfileBundle,
  shouldRetryAuthenticatedProfileLoad,
} from "../features/profile/studioDrafts.js";
import SurfaceSection from "../shared/layout/SurfaceSection.vue";
import StatusView from "../shared/ui/StatusView.vue";
import { getAuthState } from "../services/authService";
import { getProfileBundle } from "../services/profileService";
import { buildDisplayImageSrcset, toDisplayImageUrl } from "../shared/media/imageUrls.js";

const route = useRoute();
const router = useRouter();

const isLoading = ref(true);
const errorMessage = ref("");
const profile = ref(null);
const authState = ref({
  user: null,
  isAdmin: false,
  profileId: null,
  loading: false,
});
const portfolioItems = ref([]);
const htmlContent = ref("");

const canEdit = computed(() => {
  if (!profile.value) {
    return false;
  }

  return authState.value.isAdmin || authState.value.profileId === profile.value.id;
});

const profileSections = computed(() =>
  buildProfileSections(profile.value || {}, portfolioItems.value, htmlContent.value),
);
const editRoute = computed(() => {
  if (!profile.value) {
    return "/me/edit";
  }

  if (authState.value.isAdmin && authState.value.profileId !== profile.value.id) {
    return `/profiles/${profile.value.id}/edit`;
  }

  return "/me/edit";
});
const profileEvidence = computed(() => {
  const items = [];
  if (profileSections.value.hasValidGithub) items.push("GitHub 연결");
  if (profileSections.value.projectCount > 0) {
    items.push(`프로젝트 ${profileSections.value.projectCount}개`);
  }
  if (profile.value?.imageUrl) items.push("프로필 사진");
  items.push(profileSections.value.visibilityLabel);
  return items;
});

const goBack = () => {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push("/");
  }
};

const refreshPage = () => {
  window.location.reload();
};

const unavailableMessage =
  "이 프로필은 비공개이거나 삭제되었거나 일시적으로 열 수 없습니다. 새로고침 후 다시 시도하세요.";

const loadPage = async (profileId) => {
  if (!profileId) {
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";

  try {
    const nextAuthState = await getAuthState();
    const shouldAuthenticate = shouldRequestAuthenticatedProfileBundle({
      profileId,
      authState: nextAuthState,
    });
    let bundle;
    let resolvedAuthState = nextAuthState;

    try {
      bundle = await getProfileBundle(profileId, {
        authenticated: shouldAuthenticate,
      });
    } catch (error) {
      if (
        !shouldRetryAuthenticatedProfileLoad({
          error,
          wasAuthenticated: shouldAuthenticate,
          authState: nextAuthState,
        })
      ) {
        throw error;
      }

      const refreshedAuthState = await getAuthState({ force: true });
      if (
        !shouldRequestAuthenticatedProfileBundle({
          profileId,
          authState: refreshedAuthState,
        })
      ) {
        throw error;
      }

      bundle = await getProfileBundle(profileId, { authenticated: true });
      resolvedAuthState = refreshedAuthState;
    }

    profile.value = bundle.profile;
    authState.value = resolvedAuthState;
    htmlContent.value = bundle.html;
    portfolioItems.value = bundle.portfolioItems;
  } catch (error) {
    errorMessage.value =
      error.status === 404
        ? unavailableMessage
        : `${error.message || "프로필을 불러오지 못했습니다."} 새로고침 후 다시 시도하세요.`;
    profile.value = null;
    portfolioItems.value = [];
    htmlContent.value = "";
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => route.params.id,
  async (profileId) => {
    await loadPage(profileId);
  },
  { immediate: true },
);
</script>

<template>
  <StatusView
    v-if="isLoading"
    title="프로필 불러오는 중"
    body="학생 정보와 프로젝트 증빙을 준비하고 있습니다."
  />
  <StatusView
    v-else-if="errorMessage"
    state="error"
    title="이 프로필을 열 수 없습니다."
    :body="errorMessage"
  >
    <template #actions>
      <button type="button" class="profile-page__status-button" @click="refreshPage">
        새로고침
      </button>
    </template>
  </StatusView>

  <div v-else-if="profile" class="profile-page">
    <nav class="profile-back">
      <button type="button" class="profile-back__btn" @click="goBack">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        뒤로
      </button>
    </nav>

    <section class="profile-header">
      <div class="profile-header__intro">
        <div class="profile-header__portrait">
          <img
            v-if="profile.imageUrl"
            :src="toDisplayImageUrl(profile.imageUrl, { width: 640 })"
            :srcset="buildDisplayImageSrcset(profile.imageUrl, [240, 480, 640])"
            sizes="(max-width: 720px) 160px, 240px"
            :alt="`${profile.name} 프로필 사진`"
            loading="lazy"
            decoding="async"
          />
          <span v-else>{{ profile.name?.slice(0, 1) || "S" }}</span>
        </div>

        <div class="profile-header__copy">
          <span v-if="profile.job" class="profile-header__role">{{ profile.job }}</span>
          <span
            v-if="canEdit && profileSections.isPrivate"
            class="profile-header__visibility"
          >
            비공개
          </span>
          <h1>{{ profile.name }}</h1>
          <p class="profile-header__desc">{{ profileSections.cleanDescription }}</p>
          <p v-if="profileSections.taxonomyLine" class="profile-header__taxonomy">
            {{ profileSections.taxonomyLine }}
          </p>
          <ul class="profile-header__evidence" aria-label="프로필 증빙">
            <li v-for="item in profileEvidence" :key="item">{{ item }}</li>
          </ul>
          <ul v-if="profile.badges?.length" class="profile-header__badges" aria-label="관리자 인증 배지">
            <li v-for="badge in profile.badges" :key="badge">{{ badge }}</li>
          </ul>
        </div>
      </div>

      <div class="profile-header__actions">
        <a
          v-if="profileSections.hasValidGithub"
          :href="profile.github"
          target="_blank"
          rel="noreferrer"
          class="profile-header__link"
        >
          GitHub
        </a>
        <RouterLink v-if="canEdit" :to="editRoute" class="profile-header__link">
          수정
        </RouterLink>
      </div>
    </section>

    <section v-if="profileSections.metaItems.length" class="profile-meta">
      <div v-for="item in profileSections.metaItems" :key="item.label" class="profile-meta__item">
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value }}</dd>
      </div>
      <div class="profile-meta__item">
        <dt>프로젝트</dt>
        <dd>{{ profileSections.projectCount }}</dd>
      </div>
      <div v-if="canEdit" class="profile-meta__item">
        <dt>공개 상태</dt>
        <dd>{{ profileSections.visibilityLabel }}</dd>
      </div>
      <div v-if="canEdit" class="profile-meta__item">
        <dt>검토 상태</dt>
        <dd>{{ profileSections.statusLabel }}</dd>
      </div>
    </section>

    <ul v-if="profile.tags?.length" class="profile-tags">
      <li v-for="tag in profile.tags" :key="tag">{{ tag }}</li>
    </ul>

    <SurfaceSection
      v-if="profileSections.representativeProject"
      eyebrow="대표"
      :title="profileSections.representativeProject.title || '대표 프로젝트'"
      summary="가장 보여주고 싶은 프로젝트를 먼저 배치해 작업 수준을 빠르게 확인할 수 있습니다."
    >
      <PortfolioItemGrid :items="[profileSections.representativeProject]" :editable="canEdit" />
    </SurfaceSection>

    <SurfaceSection
      eyebrow="프로젝트"
      title="프로젝트 증빙"
      summary="이 학생의 작업, 링크, 미디어, 기여 내용을 확인하세요."
    >
      <PortfolioItemGrid :items="profileSections.displayProjects" :editable="canEdit" />
    </SurfaceSection>

    <SurfaceSection
      v-if="profileSections.extraHtml"
      eyebrow="상세 정보"
      title="추가 기록"
      tone="muted"
    >
      <ProfileHtmlSurface :html-content="profileSections.extraHtml" />
    </SurfaceSection>
  </div>

  <StatusView
    v-else
    state="empty"
    title="프로필을 사용할 수 없습니다."
    :body="unavailableMessage"
  >
    <template #actions>
      <button type="button" class="profile-page__status-button" @click="refreshPage">
        새로고침
      </button>
    </template>
  </StatusView>
</template>

<style scoped>
.profile-page {
  display: grid;
  gap: 24px;
}

.profile-back {
  padding-top: 8px;
}

.profile-back__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px 6px 8px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--brand-main);
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
}

.profile-back__btn:hover {
  background: var(--brand-soft);
}

.profile-page__status-button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  font-weight: 700;
}

.profile-page__status-button:hover {
  background: var(--brand-soft);
  border-color: var(--brand-main);
}

.profile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 32px 0 24px;
  border-bottom: 1px solid var(--line-soft);
}

.profile-header__intro {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.profile-header__portrait {
  width: 112px;
  height: 112px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: var(--muted);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: var(--text-sub);
  font-size: 2rem;
  font-weight: 700;
}

.profile-header__portrait img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-header__copy {
  display: grid;
  gap: 6px;
}

.profile-header__role {
  color: var(--brand-main);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.profile-header__visibility {
  justify-self: start;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger-text);
  font-size: 0.78rem;
  font-weight: 700;
}

.profile-header__copy h1 {
  margin: 0;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  letter-spacing: 0;
  line-height: 1.1;
}

.profile-header__desc {
  margin: 4px 0 0;
  color: var(--text-main);
  line-height: 1.6;
  max-width: 58ch;
}

.profile-header__taxonomy {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.86rem;
}

.profile-header__evidence,
.profile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0;
  margin: 8px 0 0;
  list-style: none;
}

.profile-header__evidence li {
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background: var(--success-soft);
  color: var(--success-text);
  font-size: 0.78rem;
  font-weight: 750;
}

.profile-header__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0;
  margin: 2px 0 0;
  list-style: none;
}

.profile-header__badges li {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: var(--brand-soft);
  color: var(--brand-main);
  font-size: 0.8rem;
  font-weight: 850;
}

.profile-header__actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.profile-header__link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  font-size: 0.86rem;
  font-weight: 600;
}

.profile-header__link:hover {
  background: rgba(0, 0, 0, 0.03);
  border-color: var(--line-strong);
}

.profile-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.profile-meta__item {
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
}

.profile-meta__item dt {
  margin-bottom: 4px;
  color: var(--text-sub);
  font-size: 0.74rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.profile-meta__item dd {
  margin: 0;
  color: var(--text-strong);
  font-weight: 500;
}

.profile-tags {
  margin: 0;
}

.profile-tags li {
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
  }

  .profile-header__intro {
    flex-direction: column;
  }

  .profile-meta {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

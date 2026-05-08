<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";
import { buildDisplayImageSrcset, toDisplayImageUrl } from "../../shared/media/imageUrls.js";

const props = defineProps({
  profile: {
    type: Object,
    required: true,
  },
  adminMode: {
    type: Boolean,
    default: false,
  },
});

const initial = computed(() => props.profile.name?.slice(0, 1) || "P");
const githubUrl = computed(() => {
  const value = String(props.profile.github || "").trim();
  return /^https:\/\/(www\.)?github\.com\/.+/i.test(value) ? value : "";
});
</script>

<template>
  <article class="profile-card-v2">
    <div class="profile-card-v2__identity">
      <div class="profile-card-v2__avatar">
        <img
          v-if="profile.imageUrl"
          :src="toDisplayImageUrl(profile.imageUrl, { width: 192 })"
          :srcset="buildDisplayImageSrcset(profile.imageUrl, [96, 192, 288])"
          sizes="96px"
          :alt="`${profile.name} 프로필 이미지`"
          loading="lazy"
          decoding="async"
        />
        <span v-else>{{ initial }}</span>
      </div>

      <div class="profile-card-v2__copy">
        <p class="profile-card-v2__job">{{ profile.job || "직무 미지정" }}</p>
        <h2>{{ profile.name }}</h2>
        <p>{{ profile.description || "아직 소개 문구가 등록되지 않았습니다." }}</p>
      </div>
    </div>

    <dl class="profile-card-v2__meta">
      <div>
        <dt>이메일</dt>
        <dd>{{ profile.email || "미등록" }}</dd>
      </div>
      <div>
        <dt>GitHub</dt>
        <dd>
          <a
            v-if="githubUrl"
            :href="githubUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub 열기
          </a>
          <span v-else>미등록</span>
        </dd>
      </div>
    </dl>

    <ul v-if="profile.badges?.length" class="profile-card-v2__badges" aria-label="관리자 인증 배지">
      <li v-for="badge in profile.badges" :key="badge">{{ badge }}</li>
    </ul>

    <div class="profile-card-v2__actions">
      <RouterLink :to="`/profiles/${profile.id}`" class="shell-action shell-action--primary">
        상세 보기
      </RouterLink>
      <RouterLink
        v-if="adminMode"
        :to="`/profiles/${profile.id}`"
        class="shell-action shell-action--ghost"
      >
        관리자 검토
      </RouterLink>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";

import PortfolioVideoPreview from "./PortfolioVideoPreview.vue";
import { toWatchUrl } from "../../services/portfolioItemService";
import { buildDisplayImageSrcset, toDisplayImageUrl } from "../../shared/media/imageUrls.js";

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  editable: {
    type: Boolean,
    default: false,
  },
});

const hasItems = computed(() => props.items.length > 0);

const isGithubUrl = (value) =>
  /^https:\/\/(www\.)?github\.com\/.+/i.test(String(value || "").trim());

const isHttpUrl = (value) => /^https?:\/\/.+/i.test(String(value || "").trim());
</script>

<template>
  <section class="portfolio-grid">
    <div v-if="hasItems" class="portfolio-grid__items">
      <article
        v-for="item in items"
        :key="item.id"
        class="portfolio-grid__card"
        :class="{ 'portfolio-grid__card--with-media': item.imageUrl || item.videoUrl }"
      >
        <div v-if="item.imageUrl || item.videoUrl" class="portfolio-grid__media">
          <img
            v-if="item.imageUrl"
            :src="toDisplayImageUrl(item.imageUrl, { width: 720 })"
            :srcset="buildDisplayImageSrcset(item.imageUrl, [360, 720, 1080])"
            sizes="(max-width: 820px) calc(100vw - 76px), 360px"
            :alt="`${item.title || '프로젝트'} 이미지`"
            class="portfolio-grid__image"
            loading="lazy"
            decoding="async"
          />

          <PortfolioVideoPreview
            v-if="item.videoUrl"
            :video-url="item.videoUrl"
            :title="item.title || '프로젝트'"
            compact
          />
        </div>

        <div class="portfolio-grid__body">
          <div class="portfolio-grid__header">
            <p class="portfolio-grid__eyebrow">
              {{ item.isFeatured ? "대표 프로젝트" : "프로젝트" }}
            </p>
            <h3>{{ item.title || "제목 없는 프로젝트" }}</h3>
            <p class="portfolio-grid__description">
              {{ item.description || "아직 설명이 없습니다." }}
            </p>
          </div>

          <p v-if="item.contribution" class="portfolio-grid__contribution">
            <strong>내 역할</strong> {{ item.contribution }}
          </p>

          <ul v-if="item.tags.length" class="portfolio-grid__tags">
            <li v-for="tag in item.tags" :key="tag">{{ tag }}</li>
          </ul>

          <div class="portfolio-grid__actions">
            <a
              v-if="isHttpUrl(item.websiteUrl)"
              :href="item.websiteUrl"
              target="_blank"
              rel="noreferrer"
              class="portfolio-grid__link portfolio-grid__link--primary"
            >
              결과물 보기
            </a>
            <a
              v-if="isGithubUrl(item.githubUrl)"
              :href="item.githubUrl"
              target="_blank"
              rel="noreferrer"
              class="portfolio-grid__link"
            >
              GitHub
            </a>
            <a
              v-if="toWatchUrl(item.videoUrl)"
              :href="toWatchUrl(item.videoUrl)"
              target="_blank"
              rel="noreferrer"
              class="portfolio-grid__link"
            >
              영상 보기
            </a>
            <span v-if="editable" class="portfolio-grid__editable-pill">스튜디오에서 수정 가능</span>
          </div>
        </div>
      </article>
    </div>

    <div v-else class="portfolio-grid__empty">
      <strong>아직 프로젝트가 없습니다.</strong>
      <p>프로필을 제대로 보여주려면 스튜디오에서 프로젝트를 하나 이상 추가하세요.</p>
    </div>
  </section>
</template>

<style scoped>
.portfolio-grid {
  display: grid;
}

.portfolio-grid__items {
  display: grid;
  gap: 18px;
}

.portfolio-grid__card {
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-sm);
  display: grid;
}

.portfolio-grid__card--with-media {
  grid-template-columns: minmax(260px, 360px) minmax(0, 1fr);
  align-items: start;
}

.portfolio-grid__media {
  display: grid;
  gap: 12px;
  padding: 18px 0 18px 18px;
  align-content: start;
}

.portfolio-grid__image {
  width: 100%;
  aspect-ratio: 16 / 10;
  max-height: 260px;
  object-fit: cover;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: var(--bg-surface-muted);
}

.portfolio-grid__body {
  display: grid;
  gap: 14px;
  padding: 20px;
  min-width: 0;
}

.portfolio-grid__header {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.portfolio-grid__eyebrow {
  margin: 0;
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.portfolio-grid__header h3,
.portfolio-grid__description,
.portfolio-grid__contribution {
  margin: 0;
  min-width: 0;
}

.portfolio-grid__description,
.portfolio-grid__contribution {
  color: var(--text-main);
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.portfolio-grid__contribution strong {
  margin-right: 8px;
  color: var(--text-strong);
}

.portfolio-grid__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.portfolio-grid__tags li,
.portfolio-grid__editable-pill {
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--text-main);
  font-size: 0.84rem;
}

.portfolio-grid__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.portfolio-grid__link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-strong);
  font-weight: 600;
}

.portfolio-grid__link--primary {
  border-color: var(--brand-main);
  background: var(--brand-main);
  color: #fff;
}

.portfolio-grid__empty {
  padding: 24px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-xl);
  background: rgba(255, 252, 247, 0.7);
}

.portfolio-grid__empty strong,
.portfolio-grid__empty p {
  margin: 0;
}

.portfolio-grid__empty p {
  margin-top: 8px;
  color: var(--text-sub);
}

@media (max-width: 820px) {
  .portfolio-grid__card--with-media {
    grid-template-columns: 1fr;
  }

  .portfolio-grid__media {
    padding: 18px 18px 0;
  }
}
</style>

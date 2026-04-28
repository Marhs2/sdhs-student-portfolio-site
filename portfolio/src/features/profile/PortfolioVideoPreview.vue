<script setup>
import { computed } from "vue";

import { toEmbedUrl, toThumbnailUrl, toWatchUrl } from "../../services/portfolioItemService";

const props = defineProps({
  videoUrl: {
    type: String,
    default: "",
  },
  title: {
    type: String,
    default: "프로젝트 영상",
  },
  compact: {
    type: Boolean,
    default: false,
  },
});

const embedUrl = computed(() => toEmbedUrl(props.videoUrl));
const watchUrl = computed(() => toWatchUrl(props.videoUrl));
const thumbnailUrl = computed(() => toThumbnailUrl(props.videoUrl));
</script>

<template>
  <section
    v-if="embedUrl"
    class="portfolio-video-preview"
    :data-compact="compact"
  >
    <a
      v-if="compact && watchUrl"
      :href="watchUrl"
      class="portfolio-video-preview__thumbnail"
      target="_blank"
      rel="noreferrer"
    >
      <img
        v-if="thumbnailUrl"
        :src="thumbnailUrl"
        :alt="`${title} 썸네일`"
        class="portfolio-video-preview__thumbnail-image"
      />
      <span v-else class="portfolio-video-preview__thumbnail-fallback">{{ title }}</span>
      <span class="portfolio-video-preview__play-badge">영상</span>
    </a>

    <div v-else class="portfolio-video-preview__frame">
      <iframe
        :src="embedUrl"
        :title="`${title} 영상 미리보기`"
        loading="lazy"
        referrerpolicy="strict-origin-when-cross-origin"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowfullscreen
      />
    </div>

    <a
      v-if="watchUrl && !compact"
      :href="watchUrl"
      class="portfolio-video-preview__link"
      target="_blank"
      rel="noreferrer"
    >
      YouTube에서 보기
    </a>
  </section>
</template>

<style scoped>
.portfolio-video-preview {
  display: grid;
  gap: 10px;
}

.portfolio-video-preview__frame,
.portfolio-video-preview__thumbnail {
  position: relative;
  overflow: hidden;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: var(--bg-surface-muted);
}

.portfolio-video-preview__frame iframe,
.portfolio-video-preview__thumbnail-image {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
  object-fit: cover;
}

.portfolio-video-preview__thumbnail {
  display: block;
}

.portfolio-video-preview__thumbnail-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 20px;
  color: var(--text-sub);
  text-align: center;
}

.portfolio-video-preview__play-badge {
  position: absolute;
  right: 12px;
  bottom: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.72);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 600;
}

.portfolio-video-preview__link {
  width: fit-content;
  color: var(--brand-main);
  font-size: 0.9rem;
  font-weight: 600;
}
</style>

<script setup>
import { computed, reactive, ref, watch } from "vue";

import PortfolioVideoPreview from "./PortfolioVideoPreview.vue";
import TagInput from "../../shared/ui/TagInput.vue";
import { parseTags, TAG_OPTIONS } from "../../shared/catalog/tags.js";
import { buildProjectValidationState } from "./studioDrafts.js";

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      title: "",
      description: "",
      contribution: "",
      tagsText: "",
      githubUrl: "",
      websiteUrl: "",
      videoUrl: "",
      imageUrl: "",
      isFeatured: false,
    }),
  },
  submitLabel: {
    type: String,
    default: "프로젝트 저장",
  },
  busy: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["submit", "update:modelValue"]);
const fieldId = `project-form-${Math.random().toString(36).slice(2, 9)}`;
const validationMessage = ref("");

const form = reactive({
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

watch(
  () => props.modelValue,
  (nextValue) => {
    form.title = nextValue?.title || "";
    form.description = nextValue?.description || "";
    form.contribution = nextValue?.contribution || "";
    form.tagsText = nextValue?.tagsText || "";
    form.githubUrl = nextValue?.githubUrl || "";
    form.websiteUrl = nextValue?.websiteUrl || nextValue?.customLinkUrl || "";
    form.videoUrl = nextValue?.videoUrl || "";
    form.imageUrl = nextValue?.imageUrl || "";
    form.isFeatured = Boolean(nextValue?.isFeatured);
  },
  { immediate: true, deep: true },
);

watch(
  form,
  () => {
    emit("update:modelValue", { ...form });
    if (validationMessage.value && buildProjectValidationState(form).canSubmit) {
      validationMessage.value = "";
    }
  },
  { deep: true },
);

const validationState = computed(() => buildProjectValidationState(form));

const handleSubmit = () => {
  validationMessage.value = validationState.value.message;
  if (!validationState.value.canSubmit) {
    return;
  }

  emit("submit", {
    title: form.title.trim(),
    description: form.description.trim(),
    contribution: form.contribution.trim(),
    tags: parseTags(form.tagsText),
    githubUrl: form.githubUrl.trim(),
    websiteUrl: form.websiteUrl.trim(),
    videoUrl: form.videoUrl.trim(),
    imageUrl: form.imageUrl.trim(),
    isFeatured: form.isFeatured,
  });
};
</script>

<template>
  <section class="portfolio-item-form">
    <div class="portfolio-item-form__grid">
      <label>
        <span :id="`${fieldId}-title-label`">프로젝트 이름</span>
        <input
          v-model="form.title"
          :aria-labelledby="`${fieldId}-title-label`"
          name="project-title"
          type="text"
          placeholder="졸업 작품, 브랜드 시스템, 게임 프로젝트..."
          required
        />
      </label>

      <label>
        <span :id="`${fieldId}-contribution-label`">기여도</span>
        <input
          v-model="form.contribution"
          :aria-labelledby="`${fieldId}-contribution-label`"
          name="project-contribution"
          type="text"
          placeholder="UI / Motion, 프론트엔드, 비주얼 디자인..."
        />
      </label>

      <label class="portfolio-item-form__wide">
        <span :id="`${fieldId}-description-label`">설명</span>
        <textarea
          v-model="form.description"
          :aria-labelledby="`${fieldId}-description-label`"
          name="project-description"
          rows="4"
          placeholder="프로젝트가 하는 일, 담당한 역할, 중요한 이유를 적어주세요."
        />
      </label>

      <label>
        <span :id="`${fieldId}-tags-label`">태그</span>
        <TagInput
          v-model="form.tagsText"
          :input-id="`${fieldId}-tags`"
          name="project-tags"
          :suggestions="TAG_OPTIONS"
          placeholder="vue, figma, branding, motion"
        />
      </label>

      <label>
        <span :id="`${fieldId}-github-label`">GitHub URL</span>
        <input
          v-model="form.githubUrl"
          :aria-labelledby="`${fieldId}-github-label`"
          name="project-github-url"
          type="url"
          inputmode="url"
          placeholder="https://github.com/..."
        />
      </label>

      <label class="portfolio-item-form__wide">
        <span :id="`${fieldId}-website-label`">웹 사이트 링크</span>
        <input
          v-model="form.websiteUrl"
          :aria-labelledby="`${fieldId}-website-label`"
          name="project-website-url"
          type="url"
          inputmode="url"
          placeholder="https://example.com"
        />
      </label>

      <label>
        <span :id="`${fieldId}-video-label`">영상 URL</span>
        <input
          v-model="form.videoUrl"
          :aria-labelledby="`${fieldId}-video-label`"
          name="project-video-url"
          type="url"
          inputmode="url"
          placeholder="https://www.youtube.com/watch?v=..."
        />
      </label>

      <label>
        <span :id="`${fieldId}-image-label`">이미지 URL</span>
        <input
          v-model="form.imageUrl"
          :aria-labelledby="`${fieldId}-image-label`"
          name="project-image-url"
          type="url"
          inputmode="url"
          placeholder="https://..."
        />
      </label>

      <label class="portfolio-item-form__checkbox">
        <input v-model="form.isFeatured" name="project-featured" type="checkbox" />
        <span>대표 프로젝트</span>
      </label>
    </div>

    <div v-if="form.imageUrl" class="portfolio-item-form__image-preview">
      <img :src="form.imageUrl" :alt="`${form.title || 'Project'} preview`" />
    </div>

    <PortfolioVideoPreview
      v-if="form.videoUrl"
      :video-url="form.videoUrl"
      :title="form.title || 'Project'"
    />

    <div class="portfolio-item-form__actions">
      <p v-if="validationMessage" class="portfolio-item-form__message">
        {{ validationMessage }}
      </p>
      <button
        type="button"
        class="portfolio-item-form__submit"
        :disabled="busy"
        @click="handleSubmit"
      >
        {{ busy ? "저장 중..." : submitLabel }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.portfolio-item-form {
  display: grid;
  gap: 18px;
}

.portfolio-item-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.portfolio-item-form__grid label {
  display: grid;
  gap: 8px;
  color: var(--text-main);
}

.portfolio-item-form__grid span {
  color: var(--text-sub);
  font-size: 0.86rem;
  font-weight: 600;
}

.portfolio-item-form__wide {
  grid-column: 1 / -1;
}

.portfolio-item-form__grid .portfolio-item-form__checkbox {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  align-self: end;
  min-height: 44px;
}

.portfolio-item-form__checkbox input {
  width: 18px;
  height: 18px;
  margin: 0;
}

.portfolio-item-form__checkbox span {
  color: var(--text-main);
  font-size: 0.94rem;
}

.portfolio-item-form__image-preview {
  overflow: hidden;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
}

.portfolio-item-form__image-preview img {
  width: 100%;
  max-height: 240px;
  object-fit: cover;
}

.portfolio-item-form__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
}

.portfolio-item-form__message {
  margin: 0;
  color: var(--danger-text);
  font-size: 0.86rem;
  font-weight: 700;
}

.portfolio-item-form__submit {
  min-height: 44px;
  padding: 0 20px;
  border: none;
  border-radius: 999px;
  background: var(--brand-main);
  color: #fff;
  font-weight: 600;
}

.portfolio-item-form__submit:hover {
  background: var(--brand-strong);
}

@media (max-width: 720px) {
  .portfolio-item-form__grid {
    grid-template-columns: 1fr;
  }
}
</style>

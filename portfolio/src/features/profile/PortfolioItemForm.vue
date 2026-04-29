<script setup>
import { computed, reactive, ref, watch } from "vue";

import PortfolioVideoPreview from "./PortfolioVideoPreview.vue";
import TagInput from "../../shared/ui/TagInput.vue";
import { parseTags, TAG_OPTIONS } from "../../shared/catalog/tags.js";
import {
  buildProjectCompletionState,
  buildProjectValidationState,
} from "./studioDrafts.js";

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
  disabled: {
    type: Boolean,
    default: false,
  },
  disabledReason: {
    type: String,
    default: "",
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
const completionState = computed(() => buildProjectCompletionState(form));
const hasSupportingContent = computed(() =>
  [
    form.githubUrl,
    form.websiteUrl,
    form.videoUrl,
    form.imageUrl,
    form.tagsText,
  ].some((value) => Boolean(String(value || "").trim())),
);
const actionHint = computed(() => {
  if (props.disabled && props.disabledReason) {
    return props.disabledReason;
  }

  if (validationState.value.canSubmit) {
    return "저장할 수 있습니다. 링크와 미디어는 나중에 보강해도 됩니다.";
  }

  return validationState.value.message || "필수 정보를 먼저 입력해 주세요.";
});

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
  <section class="portfolio-item-form" :data-ready="validationState.canSubmit" :data-disabled="disabled">
    <header class="portfolio-item-form__header">
      <div class="portfolio-item-form__intro">
        <span>{{ submitLabel.includes("수정") ? "프로젝트 편집" : "새 프로젝트" }}</span>
        <h3>{{ submitLabel }}</h3>
        <p>이름과 한 줄 역할부터 적으면 저장할 수 있습니다. 링크, 이미지, 영상은 선택 사항입니다.</p>
      </div>

      <div class="portfolio-item-form__score" aria-label="프로젝트 작성 상태">
        <strong>{{ completionState.percent }}%</strong>
        <span>{{ completionState.doneCount }}/{{ completionState.items.length }} 완료</span>
      </div>
    </header>

    <ul class="portfolio-item-form__checklist" aria-label="프로젝트 작성 점검">
      <li
        v-for="item in completionState.items"
        :key="item.key"
        :data-done="item.done"
      >
        <span aria-hidden="true">{{ item.done ? "✓" : "" }}</span>
        {{ item.label }}
      </li>
    </ul>

    <fieldset class="portfolio-item-form__section" :disabled="disabled">
      <div class="portfolio-item-form__section-head">
        <strong>핵심 정보</strong>
        <span>목록 카드에 바로 보이는 내용입니다.</span>
      </div>

      <div class="portfolio-item-form__grid">
        <label>
          <span :id="`${fieldId}-title-label`">프로젝트 이름</span>
          <input
            v-model="form.title"
            :aria-labelledby="`${fieldId}-title-label`"
            :aria-invalid="validationMessage && !form.title.trim() ? 'true' : 'false'"
            name="project-title"
            type="text"
            placeholder="예: 졸업 작품 전시 웹사이트"
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
            placeholder="예: UI 설계, 프론트엔드 구현"
          />
        </label>

        <label class="portfolio-item-form__wide">
          <span :id="`${fieldId}-description-label`">설명</span>
          <textarea
            v-model="form.description"
            :aria-labelledby="`${fieldId}-description-label`"
            name="project-description"
            rows="4"
            placeholder="무엇을 만들었고, 내가 맡은 결정과 결과가 무엇인지 적어주세요."
          />
          <small>{{ form.description.trim().length }}자 작성됨</small>
        </label>
      </div>
    </fieldset>

    <details class="portfolio-item-form__details" :open="hasSupportingContent">
      <summary>
        <span>링크와 미디어</span>
        <strong>선택 입력</strong>
      </summary>

      <fieldset class="portfolio-item-form__grid" :disabled="disabled">
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
          <span>대표 프로젝트로 표시</span>
        </label>
      </fieldset>
    </details>

    <div v-if="form.imageUrl || form.videoUrl" class="portfolio-item-form__preview-grid">
      <div v-if="form.imageUrl" class="portfolio-item-form__image-preview">
        <img :src="form.imageUrl" :alt="`${form.title || 'Project'} preview`" />
      </div>

      <PortfolioVideoPreview
        v-if="form.videoUrl"
        :video-url="form.videoUrl"
        :title="form.title || 'Project'"
      />
    </div>

    <div class="portfolio-item-form__actions">
      <p
        class="portfolio-item-form__message"
        :data-state="validationMessage ? 'error' : 'hint'"
        aria-live="polite"
      >
        {{ validationMessage || actionHint }}
      </p>
      <button
        type="button"
        class="portfolio-item-form__submit"
        :disabled="busy || disabled"
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
  gap: 16px;
  padding: 18px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
}

.portfolio-item-form__header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
}

.portfolio-item-form__intro {
  display: grid;
  gap: 4px;
}

.portfolio-item-form__intro span {
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 800;
}

.portfolio-item-form__intro h3,
.portfolio-item-form__intro p {
  margin: 0;
}

.portfolio-item-form__intro h3 {
  font-size: 1.18rem;
}

.portfolio-item-form__intro p {
  max-width: 62ch;
  color: var(--text-sub);
  line-height: 1.6;
}

.portfolio-item-form__score {
  display: grid;
  justify-items: end;
  min-width: 112px;
  padding: 10px 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--brand-soft);
}

.portfolio-item-form__score strong {
  color: var(--text-strong);
  font-size: 1.24rem;
  line-height: 1;
}

.portfolio-item-form__score span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 700;
}

.portfolio-item-form__checklist {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.portfolio-item-form__checklist li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-muted);
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 700;
}

.portfolio-item-form__checklist li[data-done="true"] {
  border-color: rgba(4, 120, 87, 0.22);
  background: var(--success-soft);
  color: var(--success-text);
}

.portfolio-item-form__checklist li span {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-size: 0.66rem;
  line-height: 1;
}

.portfolio-item-form__section,
.portfolio-item-form__details {
  display: grid;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
}

.portfolio-item-form__section,
.portfolio-item-form__grid {
  min-width: 0;
  margin: 0;
}

.portfolio-item-form__details {
  background: var(--bg-surface-solid);
}

.portfolio-item-form__section-head,
.portfolio-item-form__details summary {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.portfolio-item-form__section-head strong,
.portfolio-item-form__details summary span {
  color: var(--text-strong);
  font-size: 0.98rem;
}

.portfolio-item-form__section-head span,
.portfolio-item-form__details summary strong {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 700;
}

.portfolio-item-form__details summary {
  cursor: pointer;
  list-style: none;
}

.portfolio-item-form__details summary::-webkit-details-marker {
  display: none;
}

.portfolio-item-form__details[open] summary {
  padding-bottom: 2px;
}

.portfolio-item-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding: 0;
  border: 0;
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

.portfolio-item-form__grid small {
  color: var(--text-sub);
  font-size: 0.78rem;
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

.portfolio-item-form__preview-grid {
  display: grid;
  gap: 12px;
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
  flex: 1;
  margin: 0;
  color: var(--text-sub);
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.5;
}

.portfolio-item-form__message[data-state="error"] {
  color: var(--danger-text);
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

.portfolio-item-form__submit:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

@media (max-width: 720px) {
  .portfolio-item-form {
    padding: 14px;
  }

  .portfolio-item-form__header {
    grid-template-columns: 1fr;
  }

  .portfolio-item-form__score {
    justify-items: start;
    width: 100%;
  }

  .portfolio-item-form__grid {
    grid-template-columns: 1fr;
  }

  .portfolio-item-form__actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

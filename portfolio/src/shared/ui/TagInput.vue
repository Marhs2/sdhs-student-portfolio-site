<script setup>
import { computed, ref } from "vue";

import {
  MAX_TAG_COUNT,
  TAG_OPTIONS,
  formatTagsText,
  normalizeTag,
  parseTags,
  suggestTags,
} from "../catalog/tags.js";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  inputId: {
    type: String,
    default: "",
  },
  name: {
    type: String,
    default: "tags",
  },
  placeholder: {
    type: String,
    default: "태그 입력 후 Enter",
  },
  suggestions: {
    type: Array,
    default: () => TAG_OPTIONS,
  },
  maxTags: {
    type: Number,
    default: MAX_TAG_COUNT,
  },
});

const emit = defineEmits(["update:modelValue"]);

const draft = ref("");
const isFocused = ref(false);

const tags = computed(() => parseTags(props.modelValue, { maxTags: props.maxTags }));
const remainingCount = computed(() => Math.max(0, props.maxTags - tags.value.length));
const tagText = computed(() => formatTagsText(tags.value));
const filteredSuggestions = computed(() =>
  suggestTags({
    input: draft.value,
    selectedTags: tags.value,
    options: props.suggestions,
    limit: 10,
  }),
);
const canAddMore = computed(() => tags.value.length < props.maxTags);
const inputPlaceholder = computed(() =>
  tags.value.length ? "태그 추가" : props.placeholder,
);

const syncTags = (nextTags) => {
  emit("update:modelValue", formatTagsText(nextTags.slice(0, props.maxTags)));
};

const addTag = (value) => {
  if (!canAddMore.value) {
    draft.value = "";
    return;
  }

  const [tag] = parseTags(value, { maxTags: 1 });
  if (!tag) {
    return;
  }

  syncTags([...tags.value, tag]);
  draft.value = "";
};

const removeTag = (tagToRemove) => {
  const key = String(tagToRemove).toLowerCase();
  syncTags(tags.value.filter((tag) => tag.toLowerCase() !== key));
};

const addDraftTags = () => {
  const nextTags = [...tags.value, ...parseTags(draft.value, { maxTags: props.maxTags })];
  syncTags(nextTags);
  draft.value = "";
};

const handleInput = () => {
  if (draft.value.includes(",") || draft.value.includes("，")) {
    addDraftTags();
  }
};

const handleKeydown = (event) => {
  if (event.key === "Enter" || event.key === "Tab") {
    if (draft.value.trim()) {
      event.preventDefault();
      addDraftTags();
    }
    return;
  }

  if (event.key === "Backspace" && !draft.value && tags.value.length) {
    removeTag(tags.value.at(-1));
  }
};
</script>

<template>
  <div class="tag-input" :class="{ 'tag-input--focused': isFocused }">
    <div class="tag-input__control">
      <button
        v-for="tag in tags"
        :key="tag"
        type="button"
        class="tag-input__chip"
        :aria-label="`${tag} 태그 삭제`"
        @click="removeTag(tag)"
      >
        <span>{{ tag }}</span>
        <span aria-hidden="true">×</span>
      </button>
      <input
        :id="inputId"
        v-model="draft"
        :name="name"
        type="text"
        :placeholder="inputPlaceholder"
        :disabled="!canAddMore"
        autocomplete="off"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @input="handleInput"
        @keydown="handleKeydown"
      />
    </div>

    <input type="hidden" :name="`${name}-value`" :value="tagText" />

    <div class="tag-input__meta">
      <span>{{ tags.length }} / {{ maxTags }}</span>
      <span v-if="remainingCount">쉼표나 Enter로 추가</span>
      <span v-else>태그 개수 제한에 도달했습니다.</span>
    </div>

    <div v-if="filteredSuggestions.length" class="tag-input__suggestions" aria-label="추천 태그">
      <button
        v-for="tag in filteredSuggestions"
        :key="tag"
        type="button"
        @mousedown.prevent
        @click="addTag(tag)"
      >
        {{ normalizeTag(tag) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.tag-input {
  display: grid;
  gap: 8px;
}

.tag-input__control {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 48px;
  padding: 8px 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface-main);
}

.tag-input--focused .tag-input__control {
  border-color: var(--brand-main);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-main) 14%, transparent);
}

.tag-input__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid color-mix(in srgb, var(--brand-main) 22%, var(--line-soft));
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-main) 9%, #fff);
  color: var(--brand-strong);
  font-size: 0.86rem;
  font-weight: 700;
}

.tag-input__chip:hover {
  background: color-mix(in srgb, var(--brand-main) 14%, #fff);
}

.tag-input__control input {
  flex: 1 1 160px;
  min-width: 120px;
  min-height: 32px;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text-main);
}

.tag-input__control input:disabled {
  opacity: 0.45;
}

.tag-input__meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.tag-input__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-input__suggestions button {
  min-height: 32px;
  padding: 0 11px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: var(--surface-raised);
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 700;
}

.tag-input__suggestions button:hover {
  border-color: color-mix(in srgb, var(--brand-main) 28%, var(--line-soft));
  color: var(--brand-strong);
}
</style>

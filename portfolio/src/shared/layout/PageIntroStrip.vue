<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: "",
  },
  metaLine: {
    type: String,
    default: "",
  },
  summary: {
    type: String,
    default: "",
  },
  title: {
    type: String,
    required: true,
  },
});
</script>

<template>
  <section class="page-intro">
    <div class="page-intro__copy">
      <p v-if="eyebrow" class="page-intro__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-intro__title">{{ title }}</h1>
      <p v-if="summary" class="page-intro__summary">{{ summary }}</p>
      <p v-if="metaLine" class="page-intro__meta">{{ metaLine }}</p>
    </div>

    <div v-if="$slots.actions" class="page-intro__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
.page-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 0;
  border-bottom: 1px solid var(--line-soft);
}

.page-intro__copy {
  display: grid;
  gap: 6px;
}

.page-intro__eyebrow {
  margin: 0;
  color: var(--brand-main);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.page-intro__title {
  margin: 0;
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.05;
}

.page-intro__summary {
  margin: 0;
  color: var(--text-sub);
  line-height: 1.6;
  max-width: 48ch;
}

.page-intro__meta {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.86rem;
}

.page-intro__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .page-intro {
    flex-direction: column;
  }
}
</style>

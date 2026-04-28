<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: "",
  },
  summary: {
    type: String,
    default: "",
  },
  tone: {
    type: String,
    default: "default",
  },
  title: {
    type: String,
    default: "",
  },
});
</script>

<template>
  <section :class="['surface', `surface--${tone}`]">
    <header v-if="eyebrow || title || summary || $slots.actions" class="surface__head">
      <div class="surface__copy">
        <p v-if="eyebrow" class="surface__eyebrow">{{ eyebrow }}</p>
        <h2 v-if="title" class="surface__title">{{ title }}</h2>
        <p v-if="summary" class="surface__summary">{{ summary }}</p>
      </div>

      <div v-if="$slots.actions" class="surface__actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="surface__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.surface {
  display: grid;
  gap: 20px;
  padding: 28px;
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-panel);
}

.surface--muted {
  background: var(--bg-surface-muted);
  box-shadow: none;
}

.surface__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.surface__copy {
  display: grid;
  gap: 4px;
}

.surface__eyebrow {
  margin: 0;
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.surface__title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.surface__summary {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.9rem;
  line-height: 1.6;
}

.surface__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.surface__body {
  display: grid;
  gap: 14px;
}

@media (max-width: 768px) {
  .surface {
    padding: 20px;
  }

  .surface__head {
    flex-direction: column;
  }
}
</style>

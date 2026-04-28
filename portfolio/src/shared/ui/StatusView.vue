<script setup>
defineProps({
  state: {
    type: String,
    default: "info",
  },
  title: {
    type: String,
    required: true,
  },
  body: {
    type: String,
    default: "",
  },
});
</script>

<template>
  <section class="status-view" :data-state="state">
    <div class="status-view__icon" v-if="state === 'error'">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    </div>
    <div class="status-view__icon" v-else-if="state === 'empty'">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="8" y1="12" x2="16" y2="12"/>
      </svg>
    </div>
    <div class="status-view__icon" v-else>
      <div class="status-view__spinner" />
    </div>
    <div class="status-view__copy">
      <h2>{{ title }}</h2>
      <p v-if="body">{{ body }}</p>
      <div v-if="$slots.actions" class="status-view__actions">
        <slot name="actions" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.status-view {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 28px;
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-panel);
}

.status-view__icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.03);
  color: var(--text-sub);
}

.status-view__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--line-strong);
  border-top-color: var(--brand-main);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-view__copy {
  display: grid;
  gap: 4px;
}

.status-view h2,
.status-view p {
  margin: 0;
}

.status-view h2 {
  color: var(--text-strong);
  font-size: 0.98rem;
  font-weight: 700;
}

.status-view p {
  color: var(--text-sub);
  font-size: 0.88rem;
  line-height: 1.5;
}

.status-view__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.status-view[data-state="error"] {
  border-color: rgba(220, 53, 69, 0.15);
}

.status-view[data-state="error"] .status-view__icon {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.status-view[data-state="empty"] .status-view__icon {
  background: rgba(0, 0, 0, 0.03);
}
</style>

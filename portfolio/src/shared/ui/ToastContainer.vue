<script setup>
import { toasts } from "./toast.js";
</script>

<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container" aria-live="polite">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast--${toast.type}`]"
        role="alert"
      >
        <svg v-if="toast.type === 'success'" class="toast__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <svg v-else-if="toast.type === 'error'" class="toast__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <svg v-else class="toast__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span>{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 999px;
  background: rgba(29, 29, 31, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: #fff;
  font-size: 0.88rem;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  pointer-events: auto;
}

.toast__icon {
  flex-shrink: 0;
}

.toast--success .toast__icon {
  color: #34c759;
}

.toast--error .toast__icon {
  color: #ff3b30;
}

.toast--info .toast__icon {
  color: #5ac8fa;
}

/* Transitions */
.toast-enter-active {
  transition:
    opacity 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>

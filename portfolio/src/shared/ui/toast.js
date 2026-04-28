import { reactive } from "vue";

let _id = 0;

export const toasts = reactive([]);

export function showToast(message, type = "info", duration = 3500) {
  const id = ++_id;
  toasts.push({ id, message, type });

  setTimeout(() => {
    const idx = toasts.findIndex((t) => t.id === id);
    if (idx !== -1) {
      toasts.splice(idx, 1);
    }
  }, duration);
}

export function showSuccess(message) {
  showToast(message, "success");
}

export function showError(message) {
  showToast(message, "error", 5000);
}

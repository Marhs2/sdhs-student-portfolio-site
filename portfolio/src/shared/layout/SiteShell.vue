<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { showError, showSuccess } from "../../shared/ui/toast.js";

const route = useRoute();

const authState = ref({
  loading: true,
  user: null,
  isAdmin: false,
  profileId: null,
  hasProfile: false,
});

const currentSectionKey = computed(() => String(route.meta.section || "browse"));

const navItems = computed(() => [{ key: "browse", label: "작품 탐색", to: "/" }]);

let stopWatchingAuth = null;
let authServicePromise = null;
const showScrollTop = ref(false);

const loadAuthService = () => {
  authServicePromise ||= import("../../services/authService");
  return authServicePromise;
};

const handleScroll = () => {
  showScrollTop.value = window.scrollY > 300;
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const refreshAuth = async () => {
  try {
    const { getAuthState } = await loadAuthService();
    authState.value = await getAuthState();
  } catch (error) {
    authState.value = {
      loading: false,
      user: null,
      isAdmin: false,
      profileId: null,
      hasProfile: false,
    };
    if (error.status === 403) {
      showError(error.message);
    }
  }
};

const handleAuthAction = async () => {
  const { signInWithGoogle, signOutUser } = await loadAuthService();

  if (authState.value.user) {
    await signOutUser();
    await refreshAuth();
    showSuccess("로그아웃되었습니다.");
    return;
  }

  await signInWithGoogle();
};

onMounted(async () => {
  await refreshAuth();
  const { watchAuthState } = await loadAuthService();
  stopWatchingAuth = watchAuthState(refreshAuth);
  window.addEventListener("scroll", handleScroll, { passive: true });
});

onBeforeUnmount(() => {
  stopWatchingAuth?.();
  window.removeEventListener("scroll", handleScroll);
});
</script>

<template>
  <div class="site-shell">
    <header class="site-shell__header">
      <div class="site-shell__container site-shell__header-inner">
        <RouterLink to="/" class="site-shell__brand">
          <svg class="site-shell__logo" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <rect x="2" y="2" width="9" height="9" rx="2"/>
            <rect x="13" y="2" width="9" height="9" rx="2"/>
            <rect x="2" y="13" width="9" height="9" rx="2"/>
            <rect x="13" y="13" width="9" height="9" rx="2"/>
          </svg>
          <span class="site-shell__brand-text">SDHS</span>
        </RouterLink>

        <nav class="site-shell__nav" aria-label="Primary">
          <RouterLink
            v-for="item in navItems"
            :key="item.key"
            :to="item.to"
            class="site-shell__nav-link"
            :data-active="item.key === currentSectionKey || (item.key === 'browse' && currentSectionKey === 'profile')"
          >
            {{ item.label }}
          </RouterLink>
        </nav>

        <div class="site-shell__actions">
          <template v-if="authState.user">
            <RouterLink
              class="site-shell__action"
              to="/me/edit"
            >
              내 프로필
            </RouterLink>
            <RouterLink
              v-if="authState.isAdmin"
              class="site-shell__action"
              to="/admin"
            >
              관리자
            </RouterLink>
            <RouterLink
              v-if="authState.isConfigAdmin"
              class="site-shell__action"
              to="/server-admin"
            >
              서버 관리자
            </RouterLink>
            <button type="button" class="site-shell__action site-shell__action--primary" @click="handleAuthAction">
              로그아웃
            </button>
          </template>
          <template v-else>
            <button type="button" class="site-shell__action site-shell__action--primary" @click="handleAuthAction">
              로그인
            </button>
          </template>
        </div>
      </div>
    </header>

    <main class="site-shell__container site-shell__main">
      <slot />
    </main>

    <footer class="site-shell__footer">
      <div class="site-shell__container site-shell__footer-inner">
        <p>서울디지텍고등학교 포트폴리오</p>
        <div class="site-shell__footer-links">
          <span>학생 작품 아카이브</span>
          <span>저작권은 각 제작자에게 있습니다.</span>
        </div>
      </div>
    </footer>

    <!-- Scroll-to-top -->
    <Transition name="scrolltop">
      <button
        v-if="showScrollTop"
        type="button"
        class="site-shell__scroll-top"
        aria-label="맨 위로 이동"
        @click="scrollToTop"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="18 15 12 9 6 15"/>
        </svg>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
.site-shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.site-shell__container {
  width: min(100%, var(--page-width));
  margin: 0 auto;
  padding-left: 20px;
  padding-right: 20px;
}

/* ── Header ── */
.site-shell__header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-page);
  border-bottom: 1px solid var(--line-soft);
}

.site-shell__header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 64px;
}

.site-shell__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-strong);
  min-width: 0;
  font-weight: 800;
}

.site-shell__logo {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  padding: 5px;
  border-radius: var(--radius-sm);
  background: var(--brand-main);
  color: #fff;
  opacity: 1;
}

.site-shell__brand-text {
  font-size: 0.95rem;
  letter-spacing: 0;
  white-space: nowrap;
}

.site-shell__nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.site-shell__nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  padding: 0 14px;
  border-radius: var(--radius-sm);
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 600;
}

.site-shell__nav-link:hover {
  color: var(--text-strong);
}

.site-shell__nav-link[data-active="true"] {
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  border: 1px solid var(--line-soft);
}

.site-shell__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.site-shell__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--card);
  color: var(--text-strong);
  font-size: 0.84rem;
  font-weight: 600;
  white-space: nowrap;
}

.site-shell__action:hover {
  background: var(--muted);
  border-color: var(--line-strong);
  color: var(--text-strong);
}

.site-shell__action--primary {
  background: var(--brand-main);
  color: #fff;
  font-weight: 600;
  border-color: var(--brand-main);
}

.site-shell__action--primary:hover {
  background: var(--brand-strong);
  color: #fff;
}

/* ── Main ── */
.site-shell__main {
  padding-top: 32px;
  padding-bottom: 80px;
}

/* ── Footer ── */
.site-shell__footer {
  border-top: 1px solid var(--line-soft);
  background: transparent;
}

.site-shell__footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
  padding-top: 16px;
  padding-bottom: 16px;
}

.site-shell__footer-inner p,
.site-shell__footer-links span {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.78rem;
}

.site-shell__footer-inner p {
  font-weight: 600;
  color: var(--text-main);
}

.site-shell__footer-links {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.site-shell__footer-links span + span {
  position: relative;
}

.site-shell__footer-links span + span::before {
  content: "";
  position: absolute;
  left: -8px;
  top: 50%;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--line-strong);
  transform: translateY(-50%);
}

.site-shell__scroll-top {
  position: fixed;
  left: 50%;
  bottom: 24px;
  z-index: 120;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  padding: 0;
  border: 1px solid var(--brand-strong);
  border-radius: var(--radius-md);
  background: var(--brand-main);
  color: #fff;
  box-shadow: var(--shadow-soft);
  cursor: pointer;
  transform: translateX(-50%);
}

.site-shell__scroll-top:hover {
  background: var(--brand-strong);
  color: #fff;
  border-color: var(--brand-strong);
}

.site-shell__scroll-top svg {
  width: 20px;
  height: 20px;
  stroke-width: 3;
}

.scrolltop-enter-active,
.scrolltop-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out), transform var(--duration-normal) var(--ease-out);
}

.scrolltop-enter-from,
.scrolltop-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .site-shell__header-inner {
    height: auto;
    padding-top: 12px;
    padding-bottom: 12px;
    flex-wrap: wrap;
  }

  .site-shell__nav {
    order: 3;
    width: 100%;
    overflow-x: auto;
  }

  .site-shell__footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .site-shell__footer-links {
    justify-content: flex-start;
  }

  .site-shell__scroll-top {
    bottom: 18px;
  }
}
</style>

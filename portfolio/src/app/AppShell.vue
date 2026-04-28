<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const authState = ref({
  loading: true,
  user: null,
  isAdmin: false,
  profileId: null,
});

let unsubscribe = null;
let authServicePromise = null;
let isMounted = false;

const routeTitle = computed(() => route.meta?.title || "포트폴리오 디렉토리");

const loadAuthService = () => {
  authServicePromise ||= import("../services/authService");
  return authServicePromise;
};

const refreshAuthState = async () => {
  const { getAuthState } = await loadAuthService();
  if (!isMounted) {
    return;
  }
  authState.value = await getAuthState();
};

const handleSignIn = async () => {
  const { signInWithGoogle } = await loadAuthService();
  await signInWithGoogle();
};

const handleSignOut = async () => {
  const { signOutUser } = await loadAuthService();
  await signOutUser();
  await refreshAuthState();
  router.push("/");
};

onMounted(async () => {
  isMounted = true;
  await new Promise((resolve) => requestAnimationFrame(resolve));
  await refreshAuthState();
  const { watchAuthState } = await loadAuthService();
  unsubscribe = watchAuthState(async () => {
    await refreshAuthState();
  });
});

onUnmounted(() => {
  isMounted = false;
  unsubscribe?.();
});
</script>

<template>
  <div class="app-shell">
    <header class="shell-header">
      <div class="shell-header__inner">
        <div class="shell-brand">
          <RouterLink to="/" class="shell-brand__home">Portfolio Directory</RouterLink>
          <p class="shell-brand__summary">
            한국어 우선 포트폴리오 디렉토리. 역할별 탐색과 프로필 편집을 한 화면 시스템으로 정리했습니다.
          </p>
        </div>

        <div class="shell-actions">
          <RouterLink to="/" class="shell-action shell-action--ghost">디렉토리</RouterLink>
          <RouterLink
            v-if="authState.user"
            to="/me/edit"
            class="shell-action shell-action--ghost"
          >
            내 프로필 편집
          </RouterLink>
          <RouterLink
            v-if="authState.isAdmin"
            to="/admin"
            class="shell-action shell-action--ghost"
          >
            관리자 보기
          </RouterLink>
          <button
            v-if="authState.user"
            type="button"
            class="shell-action shell-action--primary"
            @click="handleSignOut"
          >
            로그아웃
          </button>
          <button
            v-else
            type="button"
            class="shell-action shell-action--primary"
            @click="handleSignIn"
          >
            Google로 로그인
          </button>
        </div>
      </div>
    </header>

    <main class="shell-main">
      <section class="shell-page-head">
        <div>
          <p class="shell-page-head__eyebrow">PORTFOLIO DIRECTORY</p>
          <h1>{{ routeTitle }}</h1>
        </div>
      </section>

      <RouterView :auth-state="authState" />
    </main>
  </div>
</template>

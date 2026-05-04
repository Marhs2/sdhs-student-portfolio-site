import { createRouter, createWebHistory } from "vue-router";

const AdminCurationPage = () => import("../pages/AdminCurationPage.vue");
const AuthCallbackPage = () => import("../pages/AuthCallbackPage.vue");
const BrowsePage = () => import("../pages/BrowsePage.vue");
const StudioPage = () => import("../pages/StudioPage.vue");
const StudentProfilePage = () => import("../pages/StudentProfilePage.vue");

let authServicePromise = null;

const loadAuthService = () => {
  authServicePromise ||= import("../services/authService");
  return authServicePromise;
};

const routes = [
  {
    path: "/",
    component: BrowsePage,
    meta: {
      section: "browse",
      title: "SDHS 학생 포트폴리오",
      summary: "서울디지텍고등학교 학생 포트폴리오 목록",
    },
  },
  {
    path: "/profiles/:id",
    component: StudentProfilePage,
    meta: {
      section: "profile",
      title: "학생 프로필",
      summary: "학생 포트폴리오 프로필",
    },
  },
  {
    path: "/me/edit",
    component: StudioPage,
    meta: {
      section: "studio",
      title: "포트폴리오 스튜디오",
      summary: "프로필 편집",
    },
  },
  {
    path: "/profiles/:id/edit",
    component: StudioPage,
    meta: {
      section: "studio",
      title: "프로필 수정",
      summary: "프로필 편집",
    },
  },
  {
    path: "/admin",
    component: AdminCurationPage,
    meta: {
      requiresAdmin: true,
      section: "admin",
      title: "관리자",
      summary: "포트폴리오 관리",
    },
  },
  {
    path: "/server-admin",
    component: AdminCurationPage,
    props: {
      serverMode: true,
    },
    meta: {
      requiresServerAdmin: true,
      section: "server-admin",
      title: "서버 관리자",
      summary: "권한과 공개 설정 관리",
    },
  },
  {
    path: "/auth/callback",
    component: AuthCallbackPage,
    meta: {
      shell: false,
      title: "로그인",
    },
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0, behavior: "smooth" };
  },
});

router.beforeEach(async (to) => {
  if (!to.meta.requiresAdmin && !to.meta.requiresServerAdmin) {
    return true;
  }

  try {
    const { getAuthState } = await loadAuthService();
    const authState = await getAuthState();
    const hasAccess = to.meta.requiresServerAdmin
      ? authState.isConfigAdmin
      : authState.isAdmin;

    return hasAccess ? true : "/";
  } catch {
    return "/";
  }
});

router.afterEach((to) => {
  const title = to.meta.title ? `${to.meta.title} - SDHS` : "SDHS 학생 포트폴리오";
  document.title = title;
});

export default router;

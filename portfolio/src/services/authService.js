import { fetchJson } from "./apiClient";
import { allowedSchoolEmailDomain, isAllowedSchoolEmail } from "./authDomain.js";
import { waitForSupabaseSession } from "./authSession.js";
import { supabase } from "./supabaseClient";

let cachedAuthState = null;
let cachedAuthStateAt = 0;
let inFlightAuthState = null;
const authStateCacheTtlMs = 3000;
const authOperationTimeoutMs = 10000;

const createAuthTimeoutError = () => {
  const error = new Error(
    "로그인 상태 확인이 지연되고 있습니다. 새로고침하거나 잠시 후 다시 시도해 주세요.",
  );
  error.name = "TimeoutError";
  error.status = 408;
  return error;
};

const withAuthTimeout = async (operation) => {
  let timeoutId;
  try {
    return await Promise.race([
      operation,
      new Promise((_, reject) => {
        timeoutId = setTimeout(
          () => reject(createAuthTimeoutError()),
          authOperationTimeoutMs,
        );
      }),
    ]);
  } finally {
    clearTimeout(timeoutId);
  }
};

export const clearAuthStateCache = () => {
  cachedAuthState = null;
  cachedAuthStateAt = 0;
  inFlightAuthState = null;
};

const waitForSessionTimeoutMs = 5000;

export const waitForAuthSession = async (timeoutMs = waitForSessionTimeoutMs) =>
  waitForSupabaseSession(supabase.auth, { timeoutMs });

export const getSessionUser = async () => {
  const {
    data: { session },
    error,
  } = await withAuthTimeout(supabase.auth.getSession());

  if (error || !session?.user) {
    return null;
  }

  if (!isAllowedSchoolEmail(session.user.email)) {
    await supabase.auth.signOut();
    const authError = new Error(
      "서울디지텍고등학교 sdh.hs.kr 계정으로만 로그인할 수 있습니다.",
    );
    authError.status = 403;
    throw authError;
  }

  return session.user;
};

export const getAccessToken = async () => {
  const {
    data: { session },
    error,
  } = await withAuthTimeout(supabase.auth.getSession());

  if (error || !session?.access_token) {
    const authError = new Error("로그인이 필요합니다.");
    authError.status = 401;
    throw authError;
  }

  return session.access_token;
};

export const getAuthHeaders = async (headers = {}) => {
  const accessToken = await getAccessToken();

  return {
    ...headers,
    Authorization: `Bearer ${accessToken}`,
  };
};

const loadAuthState = async () => {
  const user = await getSessionUser();
  if (!user) {
    return {
      loading: false,
      user: null,
      isAdmin: false,
      profileId: null,
      hasProfile: false,
    };
  }

  try {
    const headers = await getAuthHeaders();
    const context = await fetchJson("/api/me/context", { headers });
    return {
      loading: false,
      user,
      isAdmin: Boolean(context.isAdmin),
      isConfigAdmin: Boolean(context.isConfigAdmin),
      profileId: context.profileId || null,
      hasProfile: Boolean(context.hasProfile),
    };
  } catch (error) {
    if (error.status === 404) {
      return {
        loading: false,
        user,
        isAdmin: false,
        profileId: null,
        hasProfile: false,
      };
    }

    throw error;
  }
};

export const getAuthState = async ({ force = false } = {}) => {
  if (
    !force &&
    cachedAuthState &&
    Date.now() - cachedAuthStateAt < authStateCacheTtlMs
  ) {
    return cachedAuthState;
  }

  if (!force && inFlightAuthState) {
    return inFlightAuthState;
  }

  inFlightAuthState = loadAuthState()
    .then((state) => {
      cachedAuthState = state;
      cachedAuthStateAt = Date.now();
      return state;
    })
    .finally(() => {
      inFlightAuthState = null;
    });

  return inFlightAuthState;
};

export const getMyProfile = async () => {
  const headers = await getAuthHeaders();
  return fetchJson("/api/me/profile", { headers });
};

export const signInWithGoogle = async () => {
  clearAuthStateCache();
  await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
      queryParams: {
        hd: allowedSchoolEmailDomain,
      },
    },
  });
};

export const signOutUser = async () => {
  await supabase.auth.signOut();
  clearAuthStateCache();
};

export const watchAuthState = (callback) => {
  let refreshTimer = null;
  const { data } = supabase.auth.onAuthStateChange(() => {
    clearAuthStateCache();
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => {
      callback();
    }, 0);
  });

  return () => {
    clearTimeout(refreshTimer);
    data.subscription?.unsubscribe();
  };
};

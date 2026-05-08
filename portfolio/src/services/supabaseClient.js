import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const localOnlySupabaseProjectRefs = new Set(["lbayyiylxjvqhcqejvkr"]);

const isLoopbackHost = (hostname) =>
  hostname === "localhost" ||
  hostname === "127.0.0.1" ||
  hostname === "::1";

const getSupabaseProjectRef = (url) => {
  try {
    return new URL(url).hostname.split(".")[0] || "";
  } catch {
    return "";
  }
};

const assertLocalOnlySupabaseProject = () => {
  const projectRef = getSupabaseProjectRef(supabaseUrl);
  const currentHost = typeof window !== "undefined" ? window.location.hostname : "";

  if (
    localOnlySupabaseProjectRefs.has(projectRef) &&
    currentHost &&
    !isLoopbackHost(currentHost)
  ) {
    throw new Error("Local-only Supabase project cannot be used outside localhost.");
  }
};

assertLocalOnlySupabaseProject();

const sessionScopedStorage =
  typeof window !== "undefined" ? window.sessionStorage : undefined;

export const supabaseAuthOptions = {
  persistSession: false,
  storage: sessionScopedStorage,
  detectSessionInUrl: true,
  flowType: "pkce",
};

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: supabaseAuthOptions,
});

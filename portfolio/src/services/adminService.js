import { fetchJson } from "./apiClient";
import { normalizeProfile } from "./profileService";

let authServicePromise = null;

const loadAuthService = () => {
  authServicePromise ||= import("./authService");
  return authServicePromise;
};

const getAuthHeaders = async (...args) => {
  const authService = await loadAuthService();
  return authService.getAuthHeaders(...args);
};

const privateGetCache = new Map();
const inFlightPrivateGets = new Map();
const privateGetCacheTtlMs = 10000;

const clearPrivateGetCache = () => {
  privateGetCache.clear();
  inFlightPrivateGets.clear();
};

const fetchPrivateJson = async (path) => {
  const cached = privateGetCache.get(path);
  if (cached && Date.now() - cached.createdAt < privateGetCacheTtlMs) {
    return cached.payload;
  }

  if (inFlightPrivateGets.has(path)) {
    return inFlightPrivateGets.get(path);
  }

  const request = getAuthHeaders()
    .then((headers) => fetchJson(path, { headers }))
    .then((payload) => {
      privateGetCache.set(path, {
        createdAt: Date.now(),
        payload,
      });
      return payload;
    })
    .finally(() => {
      inFlightPrivateGets.delete(path);
    });

  inFlightPrivateGets.set(path, request);
  return request;
};

const buildQueryString = (params = {}) => {
  const searchParams = new URLSearchParams();
  const keyMap = {
    reviewStatus: "review_status",
  };

  Object.entries(params).forEach(([key, value]) => {
    if (value == null || value === "" || value === "all") {
      return;
    }

    searchParams.set(keyMap[key] || key, String(value));
  });

  const query = searchParams.toString();
  return query ? `?${query}` : "";
};

export const listAdminProfiles = async (params = {}) => {
  const query = buildQueryString(params);
  const profiles = await fetchPrivateJson(`/api/admin/profiles${query}`);
  return profiles.map(normalizeProfile);
};

export const updateAdminProfile = async (profileId, payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });
  const {
    isAdmin: _isAdmin,
    school: _school,
    department: _department,
    track: _track,
    ...curationPayload
  } = payload;

  const profile = await fetchJson(`/api/admin/profiles/${profileId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(curationPayload),
  });
  clearPrivateGetCache();

  return normalizeProfile(profile);
};

export const getAdminSettings = async () => {
  return fetchPrivateJson("/api/admin/settings");
};

export const listServerAdminProfiles = async (params = {}) => {
  const query = buildQueryString(params);
  const profiles = await fetchPrivateJson(`/api/server-admin/profiles${query}`);
  return profiles.map(normalizeProfile);
};

export const updateServerAdminProfile = async (profileId, payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const profile = await fetchJson(`/api/server-admin/profiles/${profileId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });
  clearPrivateGetCache();

  return normalizeProfile(profile);
};

export const deleteServerAdminProfile = async (profileId) => {
  const headers = await getAuthHeaders();

  await fetchJson(`/api/server-admin/profiles/${profileId}`, {
    method: "DELETE",
    headers,
  });
  clearPrivateGetCache();
};

export const getServerAdminSettings = async () => {
  return fetchPrivateJson("/api/server-admin/settings");
};

export const addServerAdminDepartment = async (name) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const result = await fetchJson("/api/server-admin/settings/departments", {
    method: "POST",
    headers,
    body: JSON.stringify({ name }),
  });
  clearPrivateGetCache();
  return result;
};

export const deleteServerAdminDepartment = async (name) => {
  const headers = await getAuthHeaders();

  const result = await fetchJson(`/api/server-admin/settings/departments/${encodeURIComponent(name)}`, {
    method: "DELETE",
    headers,
  });
  clearPrivateGetCache();
  return result;
};

export const checkGithubCommitStatus = async (username = "torvalds") => {
  const headers = await getAuthHeaders();
  const query = new URLSearchParams({ username }).toString();
  return fetchJson(`/api/github/commit-status?${query}`, { headers });
};

import { fetchJson } from "./apiClient";
import { getAuthHeaders } from "./authService";
import { normalizeProfile } from "./profileService";

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
  const headers = await getAuthHeaders();
  const query = buildQueryString(params);
  const profiles = await fetchJson(`/api/admin/profiles${query}`, { headers });
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

  return normalizeProfile(profile);
};

export const getAdminSettings = async () => {
  const headers = await getAuthHeaders();
  return fetchJson("/api/admin/settings", { headers });
};

export const listServerAdminProfiles = async (params = {}) => {
  const headers = await getAuthHeaders();
  const query = buildQueryString(params);
  const profiles = await fetchJson(`/api/server-admin/profiles${query}`, { headers });
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

  return normalizeProfile(profile);
};

export const getServerAdminSettings = async () => {
  const headers = await getAuthHeaders();
  return fetchJson("/api/server-admin/settings", { headers });
};

export const addServerAdminDepartment = async (name) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  return fetchJson("/api/server-admin/settings/departments", {
    method: "POST",
    headers,
    body: JSON.stringify({ name }),
  });
};

export const deleteServerAdminDepartment = async (name) => {
  const headers = await getAuthHeaders();

  return fetchJson(`/api/server-admin/settings/departments/${encodeURIComponent(name)}`, {
    method: "DELETE",
    headers,
  });
};

export const checkGithubCommitStatus = async (username = "torvalds") => {
  const headers = await getAuthHeaders();
  const query = new URLSearchParams({ username }).toString();
  return fetchJson(`/api/github/commit-status?${query}`, { headers });
};

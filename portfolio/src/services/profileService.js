import { fetchJson } from "./apiClient";
import { normalizePortfolioItem } from "./portfolioItemService";

let authServicePromise = null;

const loadAuthService = () => {
  authServicePromise ||= import("./authService");
  return authServicePromise;
};

const getAuthHeaders = async (...args) => {
  const authService = await loadAuthService();
  return authService.getAuthHeaders(...args);
};

const normalizeTags = (tags) =>
  Array.isArray(tags) ? tags.map((tag) => String(tag).trim()).filter(Boolean) : [];

export const normalizeProfile = (profile = {}) => ({
  id: profile.id,
  name: profile.name || "",
  description: profile.description || "",
  job: profile.job || "",
  school: profile.school || "",
  department: profile.department || "",
  track: profile.track || "",
  tags: normalizeTags(profile.tags),
  badges: normalizeTags(profile.badges),
  featuredRank: Number.isFinite(Number(profile.featuredRank))
    ? Number(profile.featuredRank)
    : 9999,
  reviewStatus: profile.reviewStatus || "draft",
  isBanned: profile.reviewStatus === "banned",
  isVisible: profile.isVisible !== false,
  github: profile.github || "",
  email: profile.email || "",
  imageUrl: profile.imageUrl || "",
  createdAt: profile.createdAt || null,
  isAdmin: Boolean(profile.isAdmin),
});

export const normalizePublicProfile = (profile = {}) => {
  const {
    email: _email,
    isAdmin: _isAdmin,
    isBanned: _isBanned,
    isVisible: _isVisible,
    reviewStatus: _reviewStatus,
    ...publicProfile
  } = normalizeProfile(profile);

  return publicProfile;
};

const buildQueryString = (filters = {}) => {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value == null || value === "") {
      return;
    }

    params.set(key, String(value));
  });

  const query = params.toString();
  return query ? `?${query}` : "";
};

export const listProfiles = async (filters = {}) => {
  const profiles = await fetchJson(`/api/profiles${buildQueryString(filters)}`);
  return profiles.map(normalizePublicProfile);
};

export const getProfileById = async (profileId, options = {}) => {
  const requestOptions = {};
  if (options.authenticated) {
    requestOptions.headers = await getAuthHeaders();
  }

  const profile = await fetchJson(`/api/profiles/${profileId}`, requestOptions);
  return options.authenticated ? normalizeProfile(profile) : normalizePublicProfile(profile);
};

export const getProfileBundle = async (profileId, options = {}) => {
  const requestOptions = {};
  if (options.authenticated) {
    requestOptions.headers = await getAuthHeaders();
  }

  const bundle = await fetchJson(`/api/profiles/${profileId}/bundle`, requestOptions);
  return {
    profile: options.authenticated
      ? normalizeProfile(bundle.profile)
      : normalizePublicProfile(bundle.profile),
    html: bundle.html || "",
    portfolioItems: Array.isArray(bundle.portfolioItems)
      ? bundle.portfolioItems.map(normalizePortfolioItem)
      : [],
  };
};

export const createProfile = async (payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const profile = await fetchJson("/api/profiles", {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  return normalizeProfile(profile);
};

export const updateProfile = async (profileId, payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const profile = await fetchJson(`/api/profiles/${profileId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });

  return normalizeProfile(profile);
};

export const deleteProfile = async (profileId) => {
  const headers = await getAuthHeaders();

  await fetchJson(`/api/profiles/${profileId}`, {
    method: "DELETE",
    headers,
  });
};

export const getProfileHtml = async (profileId, options = {}) => {
  const requestOptions = {};
  if (options.authenticated) {
    requestOptions.headers = await getAuthHeaders();
  }

  return fetchJson(`/api/profiles/${profileId}/html`, requestOptions);
};

export const saveProfileHtml = async (profileId, html) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  return fetchJson(`/api/profiles/${profileId}/html`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ html }),
  });
};

export const uploadProfileImage = async (file) => {
  const headers = await getAuthHeaders();
  const formData = new FormData();
  formData.append("file", file);

  return fetchJson("/api/uploads/profile-image", {
    method: "POST",
    headers,
    body: formData,
  });
};

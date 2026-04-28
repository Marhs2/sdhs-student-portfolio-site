import { fetchJson } from "./apiClient";
import { getAuthHeaders } from "./authService";

const normalizeTags = (tags) =>
  Array.isArray(tags) ? tags.map((tag) => String(tag).trim()).filter(Boolean) : [];

export const normalizePortfolioItem = (item = {}) => ({
  id: item.id,
  title: item.title || "",
  description: item.description || "",
  contribution: item.contribution || "",
  tags: normalizeTags(item.tags),
  githubUrl: item.githubUrl || "",
  websiteUrl: item.websiteUrl || item.customLinkUrl || "",
  videoUrl: item.videoUrl || "",
  ownerEmail: item.ownerEmail || "",
  imageUrl: item.imageUrl || "",
  isFeatured: Boolean(item.isFeatured),
  createdAt: item.createdAt || null,
});

export const toEmbedUrl = (rawUrl) => {
  if (!rawUrl) {
    return "";
  }

  try {
    const url = new URL(rawUrl.trim());
    const host = url.hostname.replace("www.", "");

    if (host === "youtube.com" || host === "m.youtube.com") {
      if (url.pathname === "/watch") {
        const videoId = url.searchParams.get("v");
        return videoId ? `https://www.youtube.com/embed/${videoId}` : "";
      }

      if (url.pathname.startsWith("/embed/")) {
        return rawUrl;
      }

      if (url.pathname.startsWith("/shorts/")) {
        const videoId = url.pathname.split("/shorts/")[1];
        return videoId ? `https://www.youtube.com/embed/${videoId}` : "";
      }
    }

    if (host === "youtu.be") {
      const videoId = url.pathname.replace("/", "");
      return videoId ? `https://www.youtube.com/embed/${videoId}` : "";
    }

    return "";
  } catch {
    return "";
  }
};

export const toWatchUrl = (rawUrl) => {
  const embedUrl = toEmbedUrl(rawUrl);
  if (!embedUrl) {
    return "";
  }

  const videoId = embedUrl.split("/embed/")[1]?.split("?")[0];
  return videoId ? `https://www.youtube.com/watch?v=${videoId}` : "";
};

export const toThumbnailUrl = (rawUrl) => {
  const embedUrl = toEmbedUrl(rawUrl);
  if (!embedUrl) {
    return "";
  }

  const videoId = embedUrl.split("/embed/")[1]?.split("?")[0];
  return videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : "";
};

export const listPortfolioItemsByProfile = async (profileId, options = {}) => {
  const requestOptions = {};
  if (options.authenticated) {
    requestOptions.headers = await getAuthHeaders();
  }

  const items = await fetchJson(`/api/profiles/${profileId}/portfolio-items`, requestOptions);
  return items.map(normalizePortfolioItem);
};

export const getPortfolioItemById = async (itemId) => {
  const item = await fetchJson(`/api/portfolio-items/${itemId}`);
  return normalizePortfolioItem(item);
};

export const createPortfolioItem = async (payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const item = await fetchJson("/api/portfolio-items", {
    method: "POST",
    headers,
    body: JSON.stringify({
      ...payload,
      videoUrl: toEmbedUrl(payload.videoUrl),
    }),
  });

  return normalizePortfolioItem(item);
};

export const updatePortfolioItem = async (itemId, payload) => {
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });

  const item = await fetchJson(`/api/portfolio-items/${itemId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify({
      ...payload,
      videoUrl: toEmbedUrl(payload.videoUrl),
    }),
  });

  return normalizePortfolioItem(item);
};

export const deletePortfolioItem = async (itemId) => {
  const headers = await getAuthHeaders();

  await fetchJson(`/api/portfolio-items/${itemId}`, {
    method: "DELETE",
    headers,
  });
};

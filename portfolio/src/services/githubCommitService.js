import { fetchJson } from "./apiClient.js";

const GITHUB_PROFILE_PATTERN = /^https:\/\/(?:www\.)?github\.com\/([^/?#]+)\/?$/i;
const GITHUB_COMMIT_BATCH_SIZE = 20;
const GITHUB_COMMIT_BATCH_CONCURRENCY = 2;
const commitCountCache = new Map();
const commitCountCacheTtlMs = 5 * 60 * 1000;

export const clearGithubCommitCache = () => {
  commitCountCache.clear();
};

export const extractGithubUsername = (githubUrl = "") => {
  const normalized = String(githubUrl || "").trim();
  if (!normalized) return "";

  const direct = normalized.replace(/^@/, "");
  if (/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/.test(direct)) {
    return direct;
  }

  const match = normalized.match(GITHUB_PROFILE_PATTERN);
  return match?.[1] || "";
};

export const getGithubCommitCounts = async (usernames = []) => {
  const uniqueUsernames = [...new Set(usernames.map(extractGithubUsername).filter(Boolean))];
  if (!uniqueUsernames.length) {
    return {};
  }

  const now = Date.now();
  const counts = {};
  const missingUsernames = [];
  uniqueUsernames.forEach((username) => {
    const cacheKey = username.toLowerCase();
    const cached = commitCountCache.get(cacheKey);
    if (cached && now - cached.createdAt < commitCountCacheTtlMs) {
      counts[cacheKey] = cached.totalCommits;
      return;
    }
    missingUsernames.push(username);
  });

  const batches = [];
  for (let index = 0; index < missingUsernames.length; index += GITHUB_COMMIT_BATCH_SIZE) {
    batches.push(missingUsernames.slice(index, index + GITHUB_COMMIT_BATCH_SIZE));
  }

  const fetchBatch = (batch) =>
    fetchJson("/api/github/commits", {
      method: "POST",
      preservePublicCache: true,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ usernames: batch }),
    });

  const payloads = [];
  let nextBatchIndex = 0;
  const workerCount = Math.min(GITHUB_COMMIT_BATCH_CONCURRENCY, batches.length);

  await Promise.all(
    Array.from({ length: workerCount }, async () => {
      while (nextBatchIndex < batches.length) {
        const batch = batches[nextBatchIndex];
        nextBatchIndex += 1;
        payloads.push(await fetchBatch(batch));
      }
    }),
  );

  const errors = [];
  for (const payload of payloads) {
    errors.push(...(payload.errors || []));
  }

  const results = payloads.flatMap((payload) => payload.results || []);
  if (!results.length && errors.length) {
    throw new Error(errors[0].message || "GitHub 활동 수를 불러오지 못했습니다.");
  }

  results.forEach((item) => {
    const cacheKey = String(item.username || "").toLowerCase();
    const totalCommits = Number(item.totalCommits) || 0;
    if (!cacheKey) {
      return;
    }
    counts[cacheKey] = totalCommits;
    commitCountCache.set(cacheKey, {
      createdAt: Date.now(),
      totalCommits,
    });
  });

  return counts;
};

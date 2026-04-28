import { fetchJson } from "./apiClient.js";

const GITHUB_PROFILE_PATTERN = /^https:\/\/(?:www\.)?github\.com\/([^/?#]+)\/?$/i;
const GITHUB_COMMIT_BATCH_SIZE = 50;

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

  const payloads = [];
  const errors = [];
  for (let index = 0; index < uniqueUsernames.length; index += GITHUB_COMMIT_BATCH_SIZE) {
    const batch = uniqueUsernames.slice(index, index + GITHUB_COMMIT_BATCH_SIZE);
    const payload = await fetchJson("/api/github/commits", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ usernames: batch }),
    });
    payloads.push(payload);
    errors.push(...(payload.errors || []));
  }

  const results = payloads.flatMap((payload) => payload.results || []);
  if (!results.length && errors.length) {
    throw new Error(errors[0].message || "GitHub 활동 수를 불러오지 못했습니다.");
  }

  return Object.fromEntries(
    results.map((item) => [
      String(item.username || "").toLowerCase(),
      Number(item.totalCommits) || 0,
    ]),
  );
};

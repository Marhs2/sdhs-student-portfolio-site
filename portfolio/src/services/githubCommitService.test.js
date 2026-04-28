import assert from "node:assert/strict";
import test from "node:test";

import { extractGithubUsername, getGithubCommitCounts } from "./githubCommitService.js";

test("extractGithubUsername accepts handles and GitHub profile URLs", () => {
  assert.equal(extractGithubUsername("@Marhs2"), "Marhs2");
  assert.equal(extractGithubUsername("https://github.com/torvalds"), "torvalds");
  assert.equal(extractGithubUsername("https://www.github.com/gaearon/"), "gaearon");
  assert.equal(extractGithubUsername("https://github.com/org/repo"), "");
  assert.equal(extractGithubUsername("not a user"), "");
});

test("getGithubCommitCounts posts unique usernames to the backend", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/github/commits");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      usernames: ["torvalds", "gaearon"],
    });
    return {
      ok: true,
      json: async () => ({
        results: [
          { username: "torvalds", totalCommits: 10 },
          { username: "gaearon", totalCommits: 7 },
        ],
      }),
    };
  };

  try {
    assert.deepEqual(
      await getGithubCommitCounts([
        "https://github.com/torvalds",
        "torvalds",
        "https://github.com/gaearon",
      ]),
      {
        torvalds: 10,
        gaearon: 7,
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("getGithubCommitCounts splits large user batches", async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    const usernames = JSON.parse(options.body).usernames;
    calls.push(usernames);
    return {
      ok: true,
      json: async () => ({
        results: usernames.map((username, index) => ({
          username,
          totalCommits: index + 1,
        })),
      }),
    };
  };

  try {
    const usernames = Array.from({ length: 51 }, (_, index) => `user-${index + 1}`);
    const result = await getGithubCommitCounts(usernames);

    assert.equal(calls.length, 2);
    assert.equal(calls[0].length, 50);
    assert.equal(calls[1].length, 1);
    assert.equal(result["user-51"], 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("getGithubCommitCounts reports backend item errors when every lookup fails", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      results: [],
      errors: [{ username: "marhs2", message: "GitHub API 조회에 실패했습니다." }],
    }),
  });

  try {
    await assert.rejects(
      () => getGithubCommitCounts(["marhs2"]),
      /GitHub API 조회에 실패했습니다/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

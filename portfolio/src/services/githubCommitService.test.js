import assert from "node:assert/strict";
import test from "node:test";

import {
  clearGithubCommitCache,
  extractGithubUsername,
  getGithubCommitCounts,
} from "./githubCommitService.js";

const waitForMicrotasks = () => new Promise((resolve) => setTimeout(resolve, 0));

test("extractGithubUsername accepts handles and GitHub profile URLs", () => {
  assert.equal(extractGithubUsername("@Marhs2"), "Marhs2");
  assert.equal(extractGithubUsername("https://github.com/torvalds"), "torvalds");
  assert.equal(extractGithubUsername("https://www.github.com/gaearon/"), "gaearon");
  assert.equal(extractGithubUsername("https://github.com/org/repo"), "");
  assert.equal(extractGithubUsername("not a user"), "");
});

test("getGithubCommitCounts posts unique usernames to the backend", async () => {
  clearGithubCommitCache();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/github/commits");
    assert.equal(options.method, "POST");
    assert.equal(options.preservePublicCache, undefined);
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
    clearGithubCommitCache();
  }
});

test("getGithubCommitCounts splits large user batches", async () => {
  clearGithubCommitCache();
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

    assert.equal(calls.length, 3);
    assert.equal(calls[0].length, 20);
    assert.equal(calls[1].length, 20);
    assert.equal(calls[2].length, 11);
    assert.equal(result["user-51"], 11);
  } finally {
    globalThis.fetch = originalFetch;
    clearGithubCommitCache();
  }
});

test("getGithubCommitCounts overlaps large batches with bounded concurrency", async () => {
  clearGithubCommitCache();
  const originalFetch = globalThis.fetch;
  const requests = [];
  let pending;

  globalThis.fetch = async (_url, options) => {
    const usernames = JSON.parse(options.body).usernames;
    let resolveResponse;
    const response = new Promise((resolve) => {
      resolveResponse = resolve;
    });
    requests.push({
      usernames,
      resolve: () =>
        resolveResponse({
          ok: true,
          json: async () => ({
            results: usernames.map((username) => ({
              username,
              totalCommits: 1,
            })),
          }),
        }),
    });
    return response;
  };

  try {
    const usernames = Array.from({ length: 45 }, (_, index) => `parallel-${index + 1}`);
    pending = getGithubCommitCounts(usernames);

    await waitForMicrotasks();
    assert.equal(requests.length, 2);

    requests[0].resolve();
    for (let attempt = 0; attempt < 5 && requests.length < 3; attempt += 1) {
      await waitForMicrotasks();
    }
    assert.equal(requests.length, 3);

    requests[1].resolve();
    requests[2].resolve();
    const result = await pending;
    assert.equal(result["parallel-45"], 1);
  } finally {
    requests.forEach((request) => request.resolve());
    if (pending) {
      await pending.catch(() => {});
    }
    globalThis.fetch = originalFetch;
    clearGithubCommitCache();
  }
});

test("getGithubCommitCounts reports backend item errors when every lookup fails", async () => {
  clearGithubCommitCache();
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
    clearGithubCommitCache();
  }
});

test("getGithubCommitCounts reuses cached user counts", async () => {
  clearGithubCommitCache();
  const originalFetch = globalThis.fetch;
  let requestCount = 0;
  globalThis.fetch = async () => {
    requestCount += 1;
    return {
      ok: true,
      json: async () => ({
        results: [{ username: "torvalds", totalCommits: 10 }],
      }),
    };
  };

  try {
    assert.deepEqual(await getGithubCommitCounts(["torvalds"]), {
      torvalds: 10,
    });
    assert.deepEqual(await getGithubCommitCounts(["https://github.com/torvalds"]), {
      torvalds: 10,
    });
    assert.equal(requestCount, 1);
  } finally {
    globalThis.fetch = originalFetch;
    clearGithubCommitCache();
  }
});

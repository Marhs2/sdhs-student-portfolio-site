import assert from "node:assert/strict";
import test from "node:test";

import { clearApiCache, fetchJson } from "./apiClient.js";

test("fetchJson aborts stalled requests with a timeout error", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (_url, options = {}) =>
    new Promise((_resolve, reject) => {
      options.signal?.addEventListener("abort", () => {
        reject(options.signal.reason);
      });
    });

  try {
    await assert.rejects(
      () => fetchJson("/api/slow", { timeoutMs: 5 }),
      (error) => {
        assert.equal(error.status, 408);
        assert.equal(error.name, "TimeoutError");
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson clears stalled public GET requests from the in-flight cache", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;
  let requestCount = 0;

  globalThis.fetch = (_url, options = {}) => {
    requestCount += 1;
    return new Promise((_resolve, reject) => {
      options.signal?.addEventListener("abort", () => {
        reject(options.signal.reason);
      });
    });
  };

  try {
    await assert.rejects(() =>
      fetchJson("/api/stale-cache", { timeoutMs: 5, retryOnTimeout: false }),
    );
    await assert.rejects(() =>
      fetchJson("/api/stale-cache", { timeoutMs: 5, retryOnTimeout: false }),
    );
    assert.equal(requestCount, 2);
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson retries timed out GET requests once before failing", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;
  let requestCount = 0;

  globalThis.fetch = async (_url, options = {}) => {
    requestCount += 1;

    if (requestCount === 1) {
      return new Promise((_resolve, reject) => {
        options.signal?.addEventListener("abort", () => {
          reject(options.signal.reason);
        });
      });
    }

    return {
      ok: true,
      json: async () => ({ ok: true }),
    };
  };

  try {
    const payload = await fetchJson("/api/retry-on-timeout", { timeoutMs: 5 });
    assert.deepEqual(payload, { ok: true });
    assert.equal(requestCount, 2);
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson sends API requests with browser cache disabled", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async (_url, options = {}) => {
    assert.equal(options.cache, "no-store");
    return {
      ok: true,
      json: async () => ({ ok: true }),
    };
  };

  try {
    assert.deepEqual(await fetchJson("/api/profiles"), { ok: true });
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson invalidates public GET cache around mutations", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;
  let getCount = 0;

  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes("/api/profiles") && !options.method) {
      getCount += 1;
      return {
        ok: true,
        json: async () => ({ version: getCount }),
      };
    }

    return {
      ok: true,
      json: async () => ({ saved: true }),
    };
  };

  try {
    assert.deepEqual(await fetchJson("/api/profiles"), { version: 1 });
    assert.deepEqual(await fetchJson("/api/profiles"), { version: 1 });
    await fetchJson("/api/profiles/1", { method: "PUT", body: "{}" });
    assert.deepEqual(await fetchJson("/api/profiles"), { version: 2 });
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson can preserve public GET cache for read-only POST requests", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;
  let getCount = 0;

  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes("/api/profiles") && !options.method) {
      getCount += 1;
      return {
        ok: true,
        json: async () => ({ version: getCount }),
      };
    }

    assert.equal(options.preservePublicCache, undefined);
    return {
      ok: true,
      json: async () => ({ total: 1 }),
    };
  };

  try {
    assert.deepEqual(await fetchJson("/api/profiles"), { version: 1 });
    await fetchJson("/api/github/commits", {
      method: "POST",
      preservePublicCache: true,
      body: "{}",
    });
    assert.deepEqual(await fetchJson("/api/profiles"), { version: 1 });
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson formats FastAPI validation errors into readable messages", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async () => ({
    ok: false,
    status: 422,
    json: async () => ({
      detail: [
        {
          loc: ["body", "title"],
          msg: "String should have at least 1 character",
        },
      ],
    }),
  });

  try {
    await assert.rejects(
      () => fetchJson("/api/portfolio-items", { method: "POST", body: "{}" }),
      (error) => {
        assert.equal(error.status, 422);
        assert.match(error.message, /title/);
        assert.match(error.message, /String should have at least 1 character/);
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

test("fetchJson stringifies object detail errors instead of showing object Object", async () => {
  clearApiCache();
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async () => ({
    ok: false,
    status: 400,
    json: async () => ({
      detail: {
        error: "Storage upload failed",
        statusCode: 403,
      },
    }),
  });

  try {
    await assert.rejects(
      () => fetchJson("/api/uploads/profile-image", { method: "POST" }),
      (error) => {
        assert.equal(error.status, 400);
        assert.match(error.message, /Storage upload failed/);
        assert.doesNotMatch(error.message, /\[object Object\]/);
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
    clearApiCache();
  }
});

const productionApiBaseUrl = "https://sdhs-student-portfolio-site.onrender.com";
const rawApiBaseUrl = (import.meta.env?.VITE_API_BASE_URL || "").replace(/\/$/, "");
const publicGetCache = new Map();
const inFlightPublicGets = new Map();
const publicGetCacheTtlMs = 15000;
const defaultRequestTimeoutMs = 15000;

const isLoopbackHost = (hostname) =>
  hostname === "localhost" ||
  hostname === "127.0.0.1" ||
  hostname === "::1";

export const resolveApiBaseUrl = () => {
  if (!rawApiBaseUrl) {
    const currentHost =
      typeof window !== "undefined" ? window.location.hostname : "";
    return currentHost && !isLoopbackHost(currentHost) ? productionApiBaseUrl : "";
  }

  try {
    const url = new URL(rawApiBaseUrl);
    const currentHost =
      typeof window !== "undefined" ? window.location.hostname : "";

    if (url.hostname && isLoopbackHost(url.hostname) && !isLoopbackHost(currentHost)) {
      console.warn(
        `Ignoring loopback API base URL in a non-local environment: ${rawApiBaseUrl}`,
      );
      return productionApiBaseUrl;
    }
  } catch {
    return rawApiBaseUrl;
  }

  if (!rawApiBaseUrl && typeof window !== "undefined" && !isLoopbackHost(window.location.hostname)) {
    return productionApiBaseUrl;
  }

  return rawApiBaseUrl;
};

export const buildApiUrl = (path) => `${resolveApiBaseUrl()}${path}`;

const parseJson = async (response) => response.json().catch(() => ({}));

const stringifyErrorValue = (value) => {
  if (!value) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map(stringifyErrorValue).filter(Boolean).join("\n");
  }

  if (typeof value === "object") {
    if (typeof value.message === "string") {
      return value.message;
    }
    if (typeof value.error === "string") {
      return value.error;
    }

    return Object.entries(value)
      .map(([key, entry]) => `${key}: ${stringifyErrorValue(entry) || String(entry)}`)
      .join("\n");
  }

  return String(value);
};

const formatApiErrorMessage = (payload) => {
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => {
        const path = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        const message = item.msg || item.message || "요청 값이 올바르지 않습니다.";
        return path ? `${path}: ${message}` : message;
      })
      .join("\n");
  }

  return (
    stringifyErrorValue(payload.detail) ||
    stringifyErrorValue(payload.message) ||
    "요청에 실패했습니다."
  );
};

const isPublicGetRequest = (options = {}) =>
  !options.method &&
  !options.body &&
  !options.headers;

const isTimeoutError = (error) =>
  Boolean(error) && (error.name === "TimeoutError" || error.status === 408);

export const clearApiCache = () => {
  publicGetCache.clear();
  inFlightPublicGets.clear();
};

const createTimeoutError = (timeoutMs) => {
  const error = new Error(
    `${Math.round(timeoutMs / 1000)}초 안에 응답이 없어 요청을 중단했습니다. 잠시 후 다시 시도해 주세요.`,
  );
  error.name = "TimeoutError";
  error.status = 408;
  return error;
};

const shouldUseBrowserDefaultCache = (options = {}) => isPublicGetRequest(options);

const requestJson = async (path, options = {}) => {
  const timeoutMs = Number(options.timeoutMs || defaultRequestTimeoutMs);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort(createTimeoutError(timeoutMs));
  }, timeoutMs);
  const {
    timeoutMs: _timeoutMs,
    preservePublicCache: _preservePublicCache,
    ...fetchOptions
  } = options;

  let response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...fetchOptions,
      cache: fetchOptions.cache || (shouldUseBrowserDefaultCache(options) ? "default" : "no-store"),
      signal: fetchOptions.signal || controller.signal,
    });
  } catch (error) {
    if (controller.signal.aborted) {
      throw controller.signal.reason || createTimeoutError(timeoutMs);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }

  const payload = await parseJson(response);

  if (!response.ok) {
    const error = new Error(formatApiErrorMessage(payload));
    error.status = response.status;
    throw error;
  }

  return payload;
};

export const fetchJson = async (path, options = {}) => {
  const method = (options.method || "GET").toUpperCase();
  const shouldPreservePublicCache = options.preservePublicCache === true;

  if (method !== "GET") {
    if (!shouldPreservePublicCache) {
      clearApiCache();
    }
    try {
      return await requestJson(path, options);
    } finally {
      if (!shouldPreservePublicCache) {
        clearApiCache();
      }
    }
  }

  const runGetRequest = async () => {
    try {
      return await requestJson(path, options);
    } catch (error) {
      if (options.retryOnTimeout === false || !isTimeoutError(error)) {
        throw error;
      }

      return requestJson(path, options);
    }
  };

  if (!isPublicGetRequest(options)) {
    return runGetRequest();
  }

  const cached = publicGetCache.get(path);
  if (cached && Date.now() - cached.createdAt < publicGetCacheTtlMs) {
    return cached.payload;
  }

  if (inFlightPublicGets.has(path)) {
    return inFlightPublicGets.get(path);
  }

  const request = runGetRequest()
    .then((payload) => {
      publicGetCache.set(path, {
        createdAt: Date.now(),
        payload,
      });
      return payload;
    })
    .finally(() => {
      inFlightPublicGets.delete(path);
    });

  inFlightPublicGets.set(path, request);
  return request;
};

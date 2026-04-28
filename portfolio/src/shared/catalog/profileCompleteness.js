const PROFILE_CHECKS = [
  ["name", (profile) => profile.name],
  ["job", (profile) => profile.job],
  ["description", (profile) => String(profile.description || "").trim().length >= 80],
  ["github", (profile) => profile.github],
  ["image", (profile) => profile.imageUrl],
  ["tags", (profile) => Array.isArray(profile.tags) && profile.tags.length > 0],
];

const toBoolean = (value) =>
  typeof value === "boolean"
    ? value
    : Array.isArray(value)
      ? value.length > 0
      : Boolean(String(value ?? "").trim());

export const getProfileCompleteness = (profile = {}) => {
  const completed = [];
  const missing = [];

  PROFILE_CHECKS.forEach(([key, predicate]) => {
    if (toBoolean(predicate(profile))) {
      completed.push(key);
    } else {
      missing.push(key);
    }
  });

  const total = PROFILE_CHECKS.length;
  const percent = Math.round((completed.length / total) * 100);

  return {
    percent,
    completed,
    missing,
    total,
  };
};

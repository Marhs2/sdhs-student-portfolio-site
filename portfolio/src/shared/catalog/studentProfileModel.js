const toText = (value) => (value == null ? "" : String(value).trim());

const stripHtml = (value) => toText(value).replace(/<[^>]*>/g, "").trim();

const firstText = (...values) => values.map(toText).find(Boolean) || "";

const distinctText = (values) => [...new Set(values.map(toText).filter(Boolean))];

const ROLE_ALIASES = {
  프론트엔드: "프론트엔드",
  "프론트 엔드 개발자": "프론트엔드",
  "프론트엔드 개발자": "프론트엔드",
  frontend: "프론트엔드",
  frontenddeveloper: "프론트엔드",
  백엔드: "백엔드",
  "백 엔드 개발자": "백엔드",
  "백엔드 개발자": "백엔드",
  backend: "백엔드",
  backenddeveloper: "백엔드",
  풀스택: "풀스택",
  "풀 스택 개발자": "풀스택",
  "풀스택 개발자": "풀스택",
  fullstack: "풀스택",
  fullstackdeveloper: "풀스택",
  그래픽: "그래픽",
  graphicdesigner: "그래픽",
  graphicsdesigner: "그래픽",
  "게임 개발": "게임 개발",
  "게임 개발자": "게임 개발",
  gamedeveloper: "게임 개발",
};

const normalizeRole = (value) => {
  const raw = toText(value);
  if (!raw) {
    return "";
  }

  const aliasKey = raw.replace(/[\s_-]+/g, "").toLowerCase();
  return ROLE_ALIASES[raw] || ROLE_ALIASES[aliasKey] || raw;
};

const formatGithubHandle = (github) => {
  const raw = toText(github);

  if (!raw) {
    return "";
  }

  if (/^https?:\/\//i.test(raw)) {
    try {
      const url = new URL(raw);
      const handle = url.pathname.split("/").filter(Boolean)[0] || "";
      return handle ? `@${handle.replace(/^@/, "")}` : raw;
    } catch {
      return raw;
    }
  }

  return raw.startsWith("@") ? raw : `@${raw.replace(/^github\.com\//i, "").replace(/^\/+/, "")}`;
};

export const buildStudentCardModel = (profile = {}) => {
  const id = profile.id ?? "";
  const summary = stripHtml(firstText(profile.description, profile.summary, profile.bio));
  const title = firstText(
    profile.name,
    profile.displayName,
    profile.fullName,
    id !== "" ? `학생 ${id}` : "",
    "포트폴리오",
  );
  const role = normalizeRole(firstText(profile.job, profile.major, profile.cohort, profile.department));
  const taxonomy = distinctText([profile.school, profile.department]);
  const email = toText(profile.email);
  const github = formatGithubHandle(profile.github);
  const subtitle = role;
  const metaLine = taxonomy.join(" · ") || (role ? role : "프로필");
  const tags = distinctText(Array.isArray(profile.tags) ? profile.tags : [])
    .filter((tag) => normalizeRole(tag) !== role)
    .slice(0, 5);
  const imageUrl = firstText(profile.imageUrl, profile.avatarUrl);
  const featuredRank = Number.isFinite(Number(profile.featuredRank))
    ? Number(profile.featuredRank)
    : null;
  const githubCommitCount = Number.isFinite(Number(profile.githubCommitCount))
    ? Number(profile.githubCommitCount)
    : null;
  const accentTone = featuredRank != null && featuredRank <= 3 ? "featured" : taxonomy[0] ? "taxonomy" : "default";

  return {
    id,
    title,
    subtitle,
    metaLine: metaLine || "프로필",
    summary,
    tags,
    imageUrl,
    featuredRank,
    githubCommitCount,
    role,
    taxonomy,
    accentTone,
    isVisible: profile.isVisible !== false,
    reviewStatus: firstText(profile.reviewStatus, "draft"),
  };
};

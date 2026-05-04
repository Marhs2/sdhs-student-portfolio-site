import assert from "node:assert/strict";
import test from "node:test";

import {
  buildProfileFormDraft,
  buildProjectCompletionState,
  buildProjectValidationState,
  buildStudioSections,
  buildVisibilityToggleCopy,
  createEmptyProjectDraft,
  hydrateProjectDraft,
  parseTags,
  removeProjectById,
  shouldLoadPrivateProfileAssets,
  shouldRequestAuthenticatedProfileBundle,
  shouldRetryAuthenticatedProfileLoad,
} from "./studioDrafts.js";

test("buildProfileFormDraft converts profile data into form-safe text", () => {
  assert.deepEqual(
    buildProfileFormDraft({
      name: "Kim",
      description: "Portfolio",
      job: "프론트엔드",
      school: "Gondr High School",
      department: "Web Contents",
      track: "프론트엔드",
      tags: ["Vue", "Design"],
      github: "https://github.com/kim",
      imageUrl: "https://cdn.example.com/kim.jpg",
      isVisible: false,
    }),
    {
      name: "Kim",
      description: "Portfolio",
      job: "프론트엔드",
      tagsText: "Vue, Design",
      github: "https://github.com/kim",
      imageUrl: "https://cdn.example.com/kim.jpg",
      isVisible: false,
    },
  );
});

test("project draft helpers provide stable create and edit state", () => {
  assert.deepEqual(createEmptyProjectDraft(), {
    title: "",
    description: "",
    contribution: "",
    tagsText: "",
    githubUrl: "",
    websiteUrl: "",
    videoUrl: "",
    imageUrl: "",
    isFeatured: false,
  });

  assert.deepEqual(
    hydrateProjectDraft({
      title: "Main",
      description: "Demo",
      contribution: "UI",
      tags: ["Vue", "Motion"],
      githubUrl: "https://github.com/demo",
      websiteUrl: "https://demo.example.com",
      videoUrl: "https://youtu.be/demo",
      imageUrl: "https://cdn.example.com/demo.jpg",
      isFeatured: true,
    }),
    {
      title: "Main",
      description: "Demo",
      contribution: "UI",
      tagsText: "Vue, Motion",
      githubUrl: "https://github.com/demo",
      websiteUrl: "https://demo.example.com",
      videoUrl: "https://youtu.be/demo",
      imageUrl: "https://cdn.example.com/demo.jpg",
      isFeatured: true,
    },
  );
});

test("hydrateProjectDraft reads legacy custom link URLs as website links", () => {
  assert.equal(
    hydrateProjectDraft({
      customLinkUrl: "https://legacy.example.com",
    }).websiteUrl,
    "https://legacy.example.com",
  );
});

test("buildProjectValidationState requires a project title", () => {
  assert.deepEqual(buildProjectValidationState({ title: "  " }), {
    canSubmit: false,
    message: "프로젝트 제목을 먼저 입력하세요.",
  });

  assert.deepEqual(buildProjectValidationState({ title: "Demo" }), {
    canSubmit: true,
    message: "",
  });
});

test("buildProjectValidationState validates website link URLs", () => {
  assert.deepEqual(
    buildProjectValidationState({
      title: "Demo",
      websiteUrl: "example.com",
    }),
    {
      canSubmit: false,
      message: "웹사이트 링크는 https:// 또는 http://로 시작해야 합니다.",
    },
  );

  assert.deepEqual(
    buildProjectValidationState({
      title: "Demo",
      websiteUrl: "https://example.com",
    }),
    {
      canSubmit: true,
      message: "",
    },
  );
});

test("buildProjectCompletionState summarizes project draft quality", () => {
  assert.deepEqual(buildProjectCompletionState({}).percent, 0);

  const complete = buildProjectCompletionState({
    title: "Demo",
    description: "This project explains the problem, role, result, and why the work matters.",
    contribution: "프론트엔드",
    tagsText: "vue, portfolio",
    githubUrl: "https://github.com/demo",
  });

  assert.equal(complete.percent, 100);
  assert.equal(complete.doneCount, 5);
  assert.deepEqual(
    complete.items.map((item) => item.done),
    [true, true, true, true, true],
  );
});

test("parseTags and buildStudioSections normalize display state", () => {
  assert.deepEqual(parseTags(" vue, , design "), ["vue", "design"]);
  assert.deepEqual(
    buildStudioSections({
      completenessPercent: 63,
      projectCount: 2,
      noteFieldCount: 3,
    }),
    [
      { label: "기본 정보", value: "63%" },
      { label: "프로젝트", value: "2개" },
      { label: "상세 정보", value: "3개 항목" },
    ],
  );
});

test("buildVisibilityToggleCopy describes the current visibility action", () => {
  assert.deepEqual(buildVisibilityToggleCopy(true), {
    statusLabel: "공개",
    actionLabel: "비공개로 전환",
    nextVisible: false,
  });

  assert.deepEqual(buildVisibilityToggleCopy(false), {
    statusLabel: "비공개",
    actionLabel: "공개로 전환",
    nextVisible: true,
  });
});

test("removeProjectById removes only the matching project", () => {
  const projects = [
    { id: 1, title: "Keep" },
    { id: 2, title: "Remove" },
    { id: "3", title: "Also keep" },
  ];

  assert.deepEqual(removeProjectById(projects, 2), [
    { id: 1, title: "Keep" },
    { id: "3", title: "Also keep" },
  ]);
});

test("shouldLoadPrivateProfileAssets authenticates studio-owned drafts", () => {
  assert.equal(
    shouldLoadPrivateProfileAssets({
      profile: { id: 18 },
      authState: { user: { email: "student@sdh.hs.kr" }, profileId: null, isAdmin: false },
      targetProfileId: null,
    }),
    true,
  );

  assert.equal(
    shouldLoadPrivateProfileAssets({
      profile: { id: 18 },
      authState: { user: { email: "student@sdh.hs.kr" }, profileId: 18, isAdmin: false },
      targetProfileId: null,
    }),
    true,
  );

  assert.equal(
    shouldLoadPrivateProfileAssets({
      profile: { id: 18 },
      authState: { user: null, profileId: null, isAdmin: false },
      targetProfileId: null,
    }),
    false,
  );
});

test("shouldRequestAuthenticatedProfileBundle authenticates owner and admin detail loads", () => {
  assert.equal(
    shouldRequestAuthenticatedProfileBundle({
      profileId: 18,
      authState: { user: { email: "student@sdh.hs.kr" }, profileId: 18, isAdmin: false },
    }),
    true,
  );

  assert.equal(
    shouldRequestAuthenticatedProfileBundle({
      profileId: 18,
      authState: { user: { email: "admin@sdh.hs.kr" }, profileId: 3, isAdmin: true },
    }),
    true,
  );

  assert.equal(
    shouldRequestAuthenticatedProfileBundle({
      profileId: 18,
      authState: { user: { email: "other@sdh.hs.kr" }, profileId: 5, isAdmin: false },
    }),
    false,
  );
});

test("shouldRetryAuthenticatedProfileLoad retries stale public 404s for signed-in users", () => {
  assert.equal(
    shouldRetryAuthenticatedProfileLoad({
      error: { status: 404 },
      wasAuthenticated: false,
      authState: { user: { email: "student@sdh.hs.kr" } },
    }),
    true,
  );

  assert.equal(
    shouldRetryAuthenticatedProfileLoad({
      error: { status: 404 },
      wasAuthenticated: true,
      authState: { user: { email: "student@sdh.hs.kr" } },
    }),
    false,
  );

  assert.equal(
    shouldRetryAuthenticatedProfileLoad({
      error: { status: 500 },
      wasAuthenticated: false,
      authState: { user: { email: "student@sdh.hs.kr" } },
    }),
    false,
  );
});

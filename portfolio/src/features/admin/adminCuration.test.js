import assert from "node:assert/strict";
import test from "node:test";

import {
  applyAdminDraftPatch,
  buildAdminRows,
  buildAdminSummary,
  buildDirtyAdminRows,
  createAdminDraft,
  isAdminDraftDirty,
  syncAdminDrafts,
} from "./adminCuration.js";

const profiles = [
  {
    id: 1,
    name: "Kim",
    description: "Vue portfolio",
    job: "프론트엔드",
    school: "Gondr High School",
    department: "Web Contents",
    track: "Frontend",
    github: "https://github.com/kim",
    imageUrl: "https://cdn.example.com/kim.jpg",
    tags: ["Vue"],
    reviewStatus: "approved",
    isVisible: true,
    featuredRank: 1,
  },
  {
    id: 2,
    name: "Park",
    description: "",
    job: "",
    school: "",
    department: "",
    tags: [],
    reviewStatus: "review",
    isVisible: false,
    featuredRank: 9999,
  },
];

test("buildAdminSummary counts operational curation states", () => {
  assert.deepEqual(buildAdminSummary(profiles), {
    total: 2,
    visible: 1,
    approved: 1,
    review: 1,
    draft: 0,
    banned: 0,
    hidden: 1,
    admins: 0,
    needsWork: 1,
    exposedDrafts: 0,
    averageCompleteness: 50,
  });
});

test("buildAdminRows searches taxonomy and attaches completeness", () => {
  const rows = buildAdminRows(profiles, { search: "frontend" });

  assert.equal(rows.length, 1);
  assert.equal(rows[0].id, 1);
  assert.equal(rows[0].completeness.percent, 83);
  assert.deepEqual(rows[0].issues, ["소개 누락"]);
});

test("buildAdminRows searches operational fields beyond visible copy", () => {
  const rows = buildAdminRows(
    [
      {
        id: 3,
        name: "Lee",
        email: "lee@sdh.hs.kr",
        github: "https://github.com/school-lee",
        department: "AI Software",
        tags: ["security"],
        reviewStatus: "draft",
        isVisible: true,
      },
      {
        id: 4,
        name: "Banned",
        description: "Removed from public access",
        reviewStatus: "banned",
        isVisible: false,
        featuredRank: 4,
      },
    ],
    { search: "school-lee security" },
  );

  assert.equal(rows.length, 1);
  assert.equal(rows[0].id, 3);
});

test("buildAdminRows applies quick operational filters", () => {
  const rows = buildAdminRows(
    [
      {
        id: 1,
        name: "Ready",
        description: "Complete student profile",
        job: "Frontend",
        school: "Gondr High School",
        department: "Web Contents",
        github: "https://github.com/ready",
        imageUrl: "https://cdn.example.com/ready.jpg",
        reviewStatus: "approved",
        isVisible: true,
        featuredRank: 1,
      },
      {
        id: 2,
        name: "Draft",
        description: "",
        reviewStatus: "draft",
        isVisible: true,
        featuredRank: 3,
      },
      {
        id: 3,
        name: "Missing Github",
        description: "Needs repository",
        job: "Backend",
        school: "Gondr High School",
        department: "Web Contents",
        imageUrl: "https://cdn.example.com/missing.jpg",
        reviewStatus: "review",
        isVisible: false,
        featuredRank: 2,
      },
    ],
    { quickView: "exposedDrafts" },
  );

  assert.deepEqual(rows.map((row) => row.id), [2]);
  assert.deepEqual(
    buildAdminRows(profiles, { quickView: "needsWork" }).map((row) => row.id),
    [2],
  );
  assert.deepEqual(
    buildAdminRows(profiles, { quickView: "hidden" }).map((row) => row.id),
    [2],
  );
  assert.deepEqual(
    buildAdminRows(
      [
        ...profiles,
        { id: 4, name: "Banned", reviewStatus: "banned", isVisible: false },
      ],
      { quickView: "banned" },
    ).map((row) => row.id),
    [4],
  );
});

test("admin draft helpers sync and detect unsaved changes", () => {
  const drafts = { stale: createAdminDraft({ id: "stale" }) };
  syncAdminDrafts(drafts, profiles);

  assert.deepEqual(Object.keys(drafts).sort(), ["1", "2"]);
  assert.equal(isAdminDraftDirty(profiles[0], drafts[1]), false);

  drafts[1].featuredRank = 3;
  assert.equal(isAdminDraftDirty(profiles[0], drafts[1]), true);

  drafts[1] = createAdminDraft(profiles[0]);
  drafts[1].isAdmin = true;
  assert.equal(isAdminDraftDirty(profiles[0], drafts[1]), true);

  drafts[1] = createAdminDraft(profiles[0]);
  drafts[1].department = "Server";
  assert.equal(isAdminDraftDirty(profiles[0], drafts[1]), true);
});

test("admin bulk helpers apply draft patches and return changed rows", () => {
  const drafts = {};
  syncAdminDrafts(drafts, profiles);

  applyAdminDraftPatch(drafts, profiles, {
    reviewStatus: "approved",
    isVisible: true,
  });

  const dirtyRows = buildDirtyAdminRows(profiles, drafts);
  assert.deepEqual(dirtyRows.map((row) => row.id), [2]);
  assert.equal(drafts[2].reviewStatus, "approved");
  assert.equal(drafts[2].isVisible, true);
});

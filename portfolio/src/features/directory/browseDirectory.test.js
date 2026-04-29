import assert from "node:assert/strict";
import test from "node:test";

import {
  buildBrowseState,
  filterBrowseProfiles,
  prepareBrowseProfiles,
  sortBrowseProfiles,
} from "./browseDirectory.js";

const profiles = [
  {
    id: 1,
    name: "Kim Mina",
    description: "Vue UI portfolio",
    job: "프론트엔드",
    department: "Web Contents",
    tags: ["Vue", "UI"],
    featuredRank: 2,
    github: "https://github.com/mina",
    createdAt: "2026-04-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Park Jun",
    description: "FastAPI service",
    job: "백엔드",
    department: "Game Contents",
    tags: ["FastAPI"],
    featuredRank: 1,
    github: "@jun",
    createdAt: "2026-04-03T00:00:00Z",
  },
  {
    id: 3,
    name: "Lee Sora",
    description: "Design system",
    job: "디자인",
    department: "Web Contents",
    tags: ["Branding"],
    featuredRank: 3,
    github: "",
    createdAt: "2026-04-02T00:00:00Z",
  },
];

test("prepareBrowseProfiles caches search text and GitHub usernames", () => {
  const prepared = prepareBrowseProfiles(profiles, { mina: 14 });

  assert.equal(prepared[0].githubUsername, "mina");
  assert.equal(prepared[0].githubCommitCount, 14);
  assert.match(prepared[0].searchText, /vue ui portfolio/);
});

test("filterBrowseProfiles uses prepared search text and selected filters", () => {
  const prepared = prepareBrowseProfiles(profiles);

  assert.deepEqual(
    filterBrowseProfiles(prepared, {
      search: "fastapi",
      jobs: ["백엔드"],
      department: "Game Contents",
    }).map((profile) => profile.id),
    [2],
  );
});

test("sortBrowseProfiles keeps GitHub ordering secondary-safe before counts load", () => {
  const prepared = prepareBrowseProfiles(profiles);

  assert.deepEqual(
    sortBrowseProfiles(prepared, "githubCommits").map((profile) => profile.id),
    [2, 1, 3],
  );
});

test("sortBrowseProfiles promotes profiles when GitHub counts arrive", () => {
  const prepared = prepareBrowseProfiles(profiles, {
    mina: 25,
    jun: 4,
  });

  assert.deepEqual(
    sortBrowseProfiles(prepared, "githubCommits").map((profile) => profile.id),
    [1, 2, 3],
  );
});

test("buildBrowseState clamps pagination and exposes display bounds", () => {
  const state = buildBrowseState({
    profiles,
    filters: { sort: "featured" },
    currentPage: 99,
    pageSize: 2,
  });

  assert.equal(state.totalPages, 2);
  assert.equal(state.safePage, 2);
  assert.deepEqual(state.paginatedProfiles.map((profile) => profile.id), [3]);
  assert.equal(state.pageStart, 3);
  assert.equal(state.pageEnd, 3);
});

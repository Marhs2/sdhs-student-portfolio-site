import assert from "node:assert/strict";
import test from "node:test";

import {
  ALL_FILTER,
  buildDirectoryOptions,
  buildDirectoryState,
  filterDirectoryProfiles,
} from "./directoryFilters.js";

const profiles = [
  {
    id: 1,
    name: "Kim Mina",
    job: "프론트엔드",
    school: "Gondr High School",
    department: "Web Contents",
    track: "Frontend",
    tags: ["Vue", "UI"],
    featuredRank: 2,
    createdAt: "2026-04-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Park Jun",
    job: "백엔드",
    school: "Gondr High School",
    department: "Game Contents",
    track: "Server",
    tags: ["FastAPI", "Supabase"],
    featuredRank: 1,
    createdAt: "2026-04-03T00:00:00Z",
  },
];

test("filterDirectoryProfiles searches taxonomy and tags", () => {
  assert.deepEqual(
    filterDirectoryProfiles(profiles, {
      search: "supabase",
      job: ALL_FILTER,
      school: ALL_FILTER,
      department: ALL_FILTER,
      track: ALL_FILTER,
      tag: ALL_FILTER,
    }).map((profile) => profile.id),
    [2],
  );

  assert.deepEqual(
    filterDirectoryProfiles(profiles, {
      search: "web contents",
      job: ALL_FILTER,
      school: ALL_FILTER,
      department: ALL_FILTER,
      track: ALL_FILTER,
      tag: ALL_FILTER,
    }).map((profile) => profile.id),
    [1],
  );
});

test("buildDirectoryOptions derives stable taxonomy filters", () => {
  assert.deepEqual(buildDirectoryOptions(profiles), {
    schools: ["Gondr High School"],
    departments: ["Game Contents", "Web Contents"],
    tracks: ["Frontend", "Server"],
    tags: ["FastAPI", "Supabase", "UI", "Vue"],
  });
});

test("buildDirectoryState filters and sorts by featured rank", () => {
  const state = buildDirectoryState(profiles, {
    department: "Game Contents",
    sort: "featured",
  });

  assert.deepEqual(state.rows.map((profile) => profile.id), [2]);
  assert.equal(state.activeFilterCount, 1);
});

test("buildDirectoryState sorts by GitHub commit counts", () => {
  const state = buildDirectoryState(
    profiles.map((profile) => ({
      ...profile,
      githubCommitCount: profile.id === 1 ? 30 : 12,
    })),
    {
      sort: "githubCommits",
    },
  );

  assert.deepEqual(state.rows.map((profile) => profile.id), [1, 2]);
});

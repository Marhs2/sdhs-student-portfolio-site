import assert from "node:assert/strict";
import test from "node:test";

import { getProfileCompleteness } from "./profileCompleteness.js";

test("getProfileCompleteness reports completion percentage and missing fields", () => {
  const result = getProfileCompleteness({
    name: "Minji",
    job: "Frontend Developer",
    description: "Builds exhibition-ready UI with reliable interaction flows, accessible layouts, and polished project storytelling.",
    github: "",
    imageUrl: "https://cdn.example.com/avatar.jpg",
    tags: ["vue", "motion"],
  });

  assert.equal(result.percent, 83);
  assert.deepEqual(result.missing, ["github"]);
});

test("getProfileCompleteness treats failed boolean predicates as missing", () => {
  const result = getProfileCompleteness({
    name: "Minji",
    job: "Frontend Developer",
    description: "Too short",
    github: "https://github.com/minji",
    imageUrl: "https://cdn.example.com/avatar.jpg",
    tags: ["vue"],
  });

  assert.equal(result.percent, 83);
  assert.deepEqual(result.missing, ["description"]);
});

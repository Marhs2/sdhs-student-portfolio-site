import assert from "node:assert/strict";
import test from "node:test";

import { TAG_OPTIONS, formatTagsText, parseTags, suggestTags } from "./tags.js";

test("parseTags normalizes separators, duplicates, hashtags, and limits", () => {
  assert.deepEqual(
    parseTags(" #Vue, vue， FastAPI\nAI ", { maxTags: 3 }),
    ["Vue", "FastAPI", "AI"],
  );
});

test("formatTagsText returns stable comma text", () => {
  assert.equal(formatTagsText(["Vue", "vue", " FastAPI "]), "Vue, FastAPI");
});

test("suggestTags filters by query and selected tags", () => {
  assert.deepEqual(
    suggestTags({
      input: "y",
      selectedTags: ["TypeScript"],
      options: ["TypeScript", "Python", "Unity"],
    }),
    ["Python", "Unity"],
  );
});

test("TAG_OPTIONS includes broad language and library suggestions", () => {
  const options = new Set(TAG_OPTIONS);

  assert.ok(options.has("TypeScript"));
  assert.ok(options.has("C++"));
  assert.ok(options.has("Spring Boot"));
  assert.ok(options.has("Hugging Face Transformers"));
  assert.ok(TAG_OPTIONS.length > 250);
});

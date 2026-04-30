import assert from "node:assert/strict";
import test from "node:test";

import { buildDisplayImageSrcset, toDisplayImageUrl } from "./imageUrls.js";

test("toDisplayImageUrl requests Supabase rendered public images", () => {
  const optimized = toDisplayImageUrl(
    "https://example.supabase.co/storage/v1/object/public/user-img/profiles/avatar.jpg?v=123",
    { width: 128, quality: 70, enableTransforms: true },
  );

  assert.equal(
    optimized,
    "https://example.supabase.co/storage/v1/render/image/public/user-img/profiles/avatar.jpg?v=123&width=128&quality=70&resize=cover",
  );
});

test("toDisplayImageUrl leaves non-Supabase URLs unchanged", () => {
  assert.equal(
    toDisplayImageUrl("https://cdn.example.com/avatar.jpg", { width: 128 }),
    "https://cdn.example.com/avatar.jpg",
  );
});

test("toDisplayImageUrl leaves Supabase URLs unchanged when transforms are disabled", () => {
  const source =
    "https://example.supabase.co/storage/v1/object/public/user-img/profiles/avatar.jpg?v=123";

  assert.equal(toDisplayImageUrl(source, { width: 128 }), source);
});

test("buildDisplayImageSrcset emits width descriptors", () => {
  assert.equal(
    buildDisplayImageSrcset("https://cdn.example.com/avatar.jpg", [80, 160]),
    "https://cdn.example.com/avatar.jpg 80w, https://cdn.example.com/avatar.jpg 160w",
  );
});

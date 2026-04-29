import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const siteShellSource = readFileSync(
  new URL("./SiteShell.vue", import.meta.url),
  "utf8",
);

test("SiteShell does not render the portfolio exploration nav", () => {
  assert.equal(siteShellSource.includes("site-shell__nav"), false);
  assert.equal(siteShellSource.includes("작품 탐색"), false);
});

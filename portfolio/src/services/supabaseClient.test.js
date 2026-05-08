import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const currentDir = dirname(fileURLToPath(import.meta.url));

test("Supabase auth session is not persisted across browser restarts", async () => {
  const source = await readFile(join(currentDir, "supabaseClient.js"), "utf8");

  assert.match(source, /persistSession:\s*false/);
  assert.doesNotMatch(source, /persistSession:\s*true/);
});

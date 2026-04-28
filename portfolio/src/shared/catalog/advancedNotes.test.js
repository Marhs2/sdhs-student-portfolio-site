import assert from "node:assert/strict";
import test from "node:test";

import {
  buildAdvancedNotesHtml,
  parseAdvancedNotesHtml,
} from "./advancedNotes.js";

test("advanced notes roundtrip keeps managed sections and custom html", () => {
  const html = buildAdvancedNotesHtml({
    sections: {
      extraIntroduction: "Warm introduction",
      exhibitionNote: "Installed in the lobby",
      processNote: "Prototype, critique, and motion pass",
    },
    customHtml: "<section><h2>Legacy HTML</h2><p>Preserve me.</p></section>",
  });

  const parsed = parseAdvancedNotesHtml(html);

  assert.deepEqual(parsed.sections, {
    extraIntroduction: "Warm introduction",
    exhibitionNote: "Installed in the lobby",
    processNote: "Prototype, critique, and motion pass",
  });
  assert.equal(parsed.customHtml, "<section><h2>Legacy HTML</h2><p>Preserve me.</p></section>");
});

test("advanced notes parser falls back safely when no metadata exists", () => {
  const parsed = parseAdvancedNotesHtml("<section><p>Only custom content</p></section>");

  assert.deepEqual(parsed.sections, {
    extraIntroduction: "",
    exhibitionNote: "",
    processNote: "",
  });
  assert.equal(parsed.customHtml, "<section><p>Only custom content</p></section>");
});

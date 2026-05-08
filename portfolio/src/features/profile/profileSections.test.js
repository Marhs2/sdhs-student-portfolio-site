import assert from "node:assert/strict";
import test from "node:test";

import { buildProfileSections } from "./profileSections.js";

test("buildProfileSections separates representative project and keeps summary fields", () => {
  const sections = buildProfileSections(
    {
      description: "<p>Interaction designer</p>",
      school: "Gondr High School",
      department: "Web Contents",
      track: "프론트엔드",
      reviewStatus: "approved",
      isVisible: false,
      github: "https://github.com/student",
    },
    [
      { id: 1, title: "Archive", isFeatured: false },
      { id: 2, title: "Main", isFeatured: true },
    ],
    "<section>extra</section>",
  );

  assert.equal(sections.cleanDescription, "Interaction designer");
  assert.equal(sections.taxonomyLine, "Gondr High School / Web Contents");
  assert.deepEqual(sections.metaItems, [
    { label: "학교", value: "Gondr High School" },
    { label: "학과", value: "Web Contents" },
  ]);
  assert.equal(sections.statusLabel, "승인됨");
  assert.equal(sections.visibilityLabel, "비공개");
  assert.equal(sections.isPrivate, true);
  assert.equal(sections.projectCount, 2);
  assert.equal(sections.hasValidGithub, true);
  assert.equal(sections.representativeProject.id, 2);
  assert.deepEqual(sections.remainingProjects.map((item) => item.id), [1]);
  assert.equal(sections.extraHtml, "<section>extra</section>");
});

test("buildProfileSections falls back safely for empty projects and unsafe text", () => {
  const sections = buildProfileSections({ github: "github.com/student" }, [], "");

  assert.equal(sections.cleanDescription, "아직 자기소개를 작성하지 않았습니다.");
  assert.equal(sections.taxonomyLine, "");
  assert.deepEqual(sections.metaItems, []);
  assert.equal(sections.statusLabel, "초안");
  assert.equal(sections.visibilityLabel, "공개");
  assert.equal(sections.isPrivate, false);
  assert.equal(sections.projectCount, 0);
  assert.equal(sections.hasValidGithub, false);
  assert.equal(sections.representativeProject, null);
  assert.deepEqual(sections.displayProjects, []);
});

test("buildProfileSections removes tag delimiters from summary text", () => {
  const sections = buildProfileSections({
    description: "<scrip<script>is removed</script>t>alert(123)</script>",
  });

  assert.equal(sections.cleanDescription.includes("<script"), false);
  assert.equal(sections.cleanDescription.includes(">"), false);
});

test("buildProfileSections only exposes real GitHub profile links as GitHub", () => {
  assert.equal(
    buildProfileSections({ github: "https://github.com/student" }).hasValidGithub,
    true,
  );
  assert.equal(
    buildProfileSections({ github: "https://www.gmarket.co.kr/search" }).hasValidGithub,
    false,
  );
});

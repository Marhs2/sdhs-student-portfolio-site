import assert from "node:assert/strict";
import test from "node:test";

import { buildStudentCardModel } from "./studentProfileModel.js";

test("buildStudentCardModel keeps identity metadata first", () => {
  const card = buildStudentCardModel({
    id: 42,
    name: "Ava Kim",
    job: "Frontend Developer",
    school: "Seoul Digitech High School",
    department: "Visual Communication",
    github: "https://github.com/ava-kim",
    description: "Builds student-facing products with clear information hierarchy.",
    imageUrl: "https://cdn.example.com/ava.jpg",
    featuredRank: "3",
    tags: ["vue", "branding"],
  });

  assert.deepEqual(Object.keys(card), [
    "id",
    "title",
    "subtitle",
    "metaLine",
    "summary",
    "tags",
    "imageUrl",
    "featuredRank",
    "githubCommitCount",
    "role",
    "taxonomy",
    "accentTone",
    "email",
    "github",
    "isVisible",
    "reviewStatus",
  ]);
  assert.deepEqual(card, {
    id: 42,
    title: "Ava Kim",
    subtitle: "프론트엔드",
    metaLine: "Seoul Digitech High School / Visual Communication",
    summary: "Builds student-facing products with clear information hierarchy.",
    tags: ["vue", "branding"],
    imageUrl: "https://cdn.example.com/ava.jpg",
    featuredRank: 3,
    githubCommitCount: null,
    role: "프론트엔드",
    taxonomy: ["Seoul Digitech High School", "Visual Communication"],
    accentTone: "featured",
    email: "",
    github: "@ava-kim",
    isVisible: true,
    reviewStatus: "draft",
  });
});

test("buildStudentCardModel does not repeat the role in tags", () => {
  const card = buildStudentCardModel({
    id: 7,
    name: "Jung Dongil",
    job: "fullstack",
    tags: ["java", "vue.js", "fullstack"],
  });

  assert.equal(card.role, "풀스택");
  assert.deepEqual(card.tags, ["java", "vue.js"]);
});

test("buildStudentCardModel falls back to stable defaults", () => {
  const card = buildStudentCardModel({});

  assert.deepEqual(card, {
    id: "",
    title: "포트폴리오",
    subtitle: "",
    metaLine: "프로필",
    summary: "",
    tags: [],
    imageUrl: "",
    featuredRank: null,
    githubCommitCount: null,
    role: "",
    taxonomy: [],
    accentTone: "default",
    email: "",
    github: "",
    isVisible: true,
    reviewStatus: "draft",
  });
});

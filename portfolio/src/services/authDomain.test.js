import assert from "node:assert/strict";
import test from "node:test";

import { isAllowedSchoolEmail } from "./authDomain.js";

test("allows only Seoul Digitech school email domain", () => {
  assert.equal(isAllowedSchoolEmail("student@sdh.hs.kr"), true);
  assert.equal(isAllowedSchoolEmail(" Student@SDH.HS.KR "), true);
  assert.equal(isAllowedSchoolEmail("student@gmail.com"), false);
  assert.equal(isAllowedSchoolEmail("student@evil-sdh.hs.kr"), false);
  assert.equal(isAllowedSchoolEmail(""), false);
});

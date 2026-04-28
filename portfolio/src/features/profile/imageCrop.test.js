import assert from "node:assert/strict";
import test from "node:test";

import { getCropPreviewStyle, getSquareCrop, normalizeCrop } from "./imageCrop.js";

test("getSquareCrop uses the same percent crop coordinates for saving", () => {
  assert.deepEqual(getSquareCrop({
    width: 1600,
    height: 900,
    crop: { x: 50, y: 50, zoom: 1 },
  }), {
    x: 350,
    y: 0,
    size: 900,
  });

  assert.deepEqual(getSquareCrop({
    width: 1600,
    height: 900,
    crop: { x: 100, y: 100, zoom: 2 },
  }), {
    x: 1150,
    y: 450,
    size: 450,
  });
});

test("getCropPreviewStyle maps the saved crop rectangle into the preview", () => {
  assert.deepEqual(getCropPreviewStyle({
    width: 1600,
    height: 900,
    crop: { x: 50, y: 50, zoom: 1 },
  }), {
    width: "177.77777777777777%",
    height: "100%",
    transform: "translate(-21.875%, 0%)",
  });
});

test("normalizeCrop clamps unsafe slider values", () => {
  assert.deepEqual(normalizeCrop({ x: -20, y: 140, zoom: 9 }), {
    x: 0,
    y: 100,
    zoom: 2.4,
  });
});

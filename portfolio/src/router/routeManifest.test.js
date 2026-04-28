import assert from "node:assert/strict";
import test from "node:test";

import { routeManifest } from "./routeManifest.js";

test("routeManifest documents the public, studio, admin, and auth route owners", () => {
  assert.deepEqual(routeManifest, {
    home: { path: "/", owner: "browse" },
    profile: { path: "/profiles/:id", owner: "profile" },
    studio: { path: "/me/edit", owner: "studio" },
    admin: { path: "/admin", owner: "admin" },
    serverAdmin: { path: "/server-admin", owner: "server-admin" },
    authCallback: { path: "/auth/callback", owner: "auth" },
  });
});

export const routeManifest = {
  home: { path: "/", owner: "browse" },
  profile: { path: "/profiles/:id", owner: "profile" },
  studio: { path: "/me/edit", owner: "studio" },
  admin: { path: "/admin", owner: "admin" },
  serverAdmin: { path: "/server-admin", owner: "server-admin" },
  authCallback: { path: "/auth/callback", owner: "auth" },
};

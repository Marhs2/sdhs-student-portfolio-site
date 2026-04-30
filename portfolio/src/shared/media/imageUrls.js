const SUPABASE_PUBLIC_OBJECT_MARKER = "/storage/v1/object/public/";
const supabaseImageTransformsEnabled =
  import.meta.env?.VITE_ENABLE_SUPABASE_IMAGE_TRANSFORMS === "true";

const clampWidth = (width) => {
  const numericWidth = Number(width);
  if (!Number.isFinite(numericWidth)) {
    return 640;
  }
  return Math.min(1600, Math.max(64, Math.round(numericWidth)));
};

export const toDisplayImageUrl = (
  url,
  {
    width = 640,
    quality = 75,
    enableTransforms = supabaseImageTransformsEnabled,
  } = {},
) => {
  const source = String(url || "").trim();
  if (!enableTransforms || !source || !source.includes(SUPABASE_PUBLIC_OBJECT_MARKER)) {
    return source;
  }

  try {
    const parsedUrl = new URL(source);
    parsedUrl.pathname = parsedUrl.pathname.replace(
      SUPABASE_PUBLIC_OBJECT_MARKER,
      "/storage/v1/render/image/public/",
    );
    parsedUrl.searchParams.set("width", String(clampWidth(width)));
    parsedUrl.searchParams.set(
      "quality",
      String(Math.min(90, Math.max(40, Number(quality) || 75))),
    );
    parsedUrl.searchParams.set("resize", "cover");
    return parsedUrl.toString();
  } catch {
    return source;
  }
};

export const buildDisplayImageSrcset = (url, widths = [160, 320, 640], options = {}) =>
  widths
    .map((width) => `${toDisplayImageUrl(url, { ...options, width })} ${clampWidth(width)}w`)
    .join(", ");

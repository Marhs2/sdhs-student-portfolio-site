const MANAGED_BLOCK_ATTRIBUTE = 'data-studio-managed="notes"';
const COMMENT_PREFIX = "<!--studio-notes:";
const COMMENT_PATTERN = /<!--studio-notes:(.*?)-->/;
const MANAGED_BLOCK_PATTERN =
  /<div data-studio-managed="notes">[\s\S]*?<\/div>/g;

const NOTE_FIELDS = [
  {
    key: "extraIntroduction",
    label: "Extra introduction",
  },
  {
    key: "exhibitionNote",
    label: "Exhibition note",
  },
  {
    key: "processNote",
    label: "Process note",
  },
];

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const normalizeNotes = (sections = {}) =>
  NOTE_FIELDS.reduce((accumulator, field) => {
    accumulator[field.key] = String(sections[field.key] ?? "").trim();
    return accumulator;
  }, {});

const textToParagraphs = (value) => {
  const content = String(value ?? "").trim();
  if (!content) {
    return "";
  }

  return content
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, "<br />")}</p>`)
    .join("");
};

const decodeNotes = (encoded) => {
  if (!encoded) {
    return normalizeNotes();
  }

  try {
    return normalizeNotes(JSON.parse(decodeURIComponent(encoded)));
  } catch {
    return normalizeNotes();
  }
};

export const getAdvancedNoteFields = () => NOTE_FIELDS.map((field) => ({ ...field }));

export const buildAdvancedNotesHtml = ({ sections = {}, customHtml = "" } = {}) => {
  const normalizedSections = normalizeNotes(sections);
  const renderedSections = NOTE_FIELDS.filter(({ key }) => normalizedSections[key]).map(
    ({ key, label }) =>
      `<section class="studio-note" data-note-key="${key}"><h2>${label}</h2>${textToParagraphs(normalizedSections[key])}</section>`,
  );
  const trimmedCustomHtml = String(customHtml ?? "").trim();

  if (!renderedSections.length && !trimmedCustomHtml) {
    return "";
  }

  const serialized = encodeURIComponent(JSON.stringify(normalizedSections));
  const parts = [];

  if (renderedSections.length) {
    parts.push(`${COMMENT_PREFIX}${serialized}-->`);
    parts.push(`<div ${MANAGED_BLOCK_ATTRIBUTE}>${renderedSections.join("")}</div>`);
  }

  if (trimmedCustomHtml) {
    parts.push(trimmedCustomHtml);
  }

  return parts.join("\n");
};

export const parseAdvancedNotesHtml = (html = "") => {
  const source = String(html ?? "");
  const encodedNotes = source.match(COMMENT_PATTERN)?.[1] || "";
  const sections = decodeNotes(encodedNotes);

  const customHtml = source
    .replace(COMMENT_PATTERN, "")
    .replace(MANAGED_BLOCK_PATTERN, "")
    .trim();

  return {
    sections,
    customHtml,
  };
};

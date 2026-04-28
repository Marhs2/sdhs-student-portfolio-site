<script setup>
import { computed } from "vue";

const props = defineProps({
  htmlContent: {
    type: String,
    default: "",
  },
});

const srcDoc = computed(() => {
  if (!props.htmlContent) {
    return "";
  }

  return `
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; media-src 'none'; frame-src 'none'; connect-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'"
    />
    <style>
      :root {
        color-scheme: light;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #424245;
      }
      body {
        margin: 0;
        padding: 28px;
        background: #fff;
        line-height: 1.7;
        font-size: 15px;
      }
      h1, h2, h3, h4 {
        font-family: "Inter", -apple-system, sans-serif;
        line-height: 1.15;
        letter-spacing: -0.03em;
        color: #1d1d1f;
        margin: 0 0 0.75em;
      }
      p, ul, ol, blockquote, pre, table { margin: 0 0 1em; }
      img { max-width: 100%; height: auto; border-radius: 12px; }
      a { color: rgb(0, 114, 206); }
      blockquote {
        margin: 0 0 1em;
        padding: 16px 18px;
        border-left: 3px solid rgb(0, 114, 206);
        background: #f5f5f7;
        border-radius: 0 8px 8px 0;
      }
      pre {
        padding: 16px;
        border-radius: 10px;
        background: #1d1d1f;
        color: #f5f5f7;
        overflow: auto;
        font-size: 14px;
      }
      code {
        font-family: "SF Mono", "Menlo", monospace;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      td, th {
        padding: 10px 12px;
        border: 1px solid rgba(0,0,0,0.08);
      }
    </style>
  </head>
  <body>${props.htmlContent}</body>
</html>`;
});
</script>

<template>
  <section class="html-surface">
    <div v-if="htmlContent" class="html-surface__frame-wrap">
      <iframe
        class="html-surface__frame"
        :srcdoc="srcDoc"
        title="프로필 HTML 본문"
        sandbox
        referrerpolicy="no-referrer"
      />
    </div>

    <div v-else class="html-surface__empty">
      <p>아직 등록된 추가 내용이 없습니다.</p>
    </div>
  </section>
</template>

<style scoped>
.html-surface {
  display: grid;
}

.html-surface__frame-wrap {
  min-height: 400px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--line-soft);
  background: #fff;
}

.html-surface__frame {
  width: 100%;
  height: 100%;
  min-height: 400px;
  border: 0;
}

.html-surface__empty p {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.9rem;
}
</style>

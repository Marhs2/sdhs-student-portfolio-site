<script setup>
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import { RouterView, useRoute } from "vue-router";

import SiteShell from "./shared/layout/SiteShell.vue";
import ToastContainer from "./shared/ui/ToastContainer.vue";

const SpeedInsights = defineAsyncComponent(() =>
  import("@vercel/speed-insights/vue").then((module) => module.SpeedInsights),
);

const route = useRoute();
const showShell = computed(() => route.meta.shell !== false);
const showSpeedInsights = ref(false);

onMounted(() => {
  const scheduleIdle =
    window.requestIdleCallback ||
    ((callback) => window.setTimeout(callback, 1200));

  scheduleIdle(() => {
    showSpeedInsights.value = true;
  });
});
</script>

<template>
  <SiteShell v-if="showShell">
    <RouterView />
  </SiteShell>

  <RouterView v-else />

  <ToastContainer />
  <SpeedInsights v-if="showSpeedInsights" />
</template>

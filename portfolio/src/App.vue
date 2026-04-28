<script setup>
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";

import SiteShell from "./shared/layout/SiteShell.vue";
import ToastContainer from "./shared/ui/ToastContainer.vue";

const route = useRoute();
const showShell = computed(() => route.meta.shell !== false);
</script>

<template>
  <SiteShell v-if="showShell">
    <RouterView />
  </SiteShell>

  <RouterView v-else />

  <ToastContainer />
</template>

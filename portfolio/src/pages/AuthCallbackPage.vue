<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import StatusView from "../shared/ui/StatusView.vue";
import { clearAuthStateCache, getAuthState, waitForAuthSession } from "../services/authService";

const router = useRouter();
const message = ref("로그인 정보를 확인하는 중입니다.");

onMounted(async () => {
  try {
    await waitForAuthSession();
    clearAuthStateCache();
    const authState = await getAuthState({ force: true });
    if (authState.user) {
      router.replace("/me/edit");
      return;
    }

    message.value = "로그인을 확인하지 못했습니다. 다시 시도해 주세요.";
  } catch (error) {
    message.value =
      error.message || "로그인 처리 중 오류가 발생했습니다.";
  }
});
</script>

<template>
  <StatusView title="로그인 콜백 처리 중" :body="message" />
</template>

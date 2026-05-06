<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";

import PageIntroStrip from "../shared/layout/PageIntroStrip.vue";
import SurfaceSection from "../shared/layout/SurfaceSection.vue";
import StatusView from "../shared/ui/StatusView.vue";
import { showSuccess, showError } from "../shared/ui/toast.js";
import {
  applyAdminDraftPatch,
  buildAdminPagination,
  buildDirtyAdminRows,
  buildAdminRows,
  buildAdminSummary,
  createAdminDraft,
  isAdminDraftDirty,
  syncAdminDrafts,
} from "../features/admin/adminCuration.js";
import {
  addServerAdminDepartment,
  checkGithubCommitStatus,
  deleteServerAdminProfile,
  deleteServerAdminDepartment,
  getAdminSettings,
  getServerAdminSettings,
  listAdminProfiles,
  listServerAdminProfiles,
  updateAdminProfile,
  updateServerAdminProfile,
} from "../services/adminService";
import { getAuthState } from "../services/authService";

const props = defineProps({
  serverMode: {
    type: Boolean,
    default: false,
  },
});

const isLoading = ref(true);
const errorMessage = ref("");
const adminProfiles = ref([]);
const adminSettings = ref(null);
const authState = ref({
  user: null,
  isAdmin: false,
  isConfigAdmin: false,
  profileId: null,
  loading: false,
});
const saveStates = reactive({});
const selectedIds = reactive({});
const bulkSaveState = ref("");
const currentPage = ref(1);
const departmentDraft = ref("");
const departmentState = ref("");
const githubStatus = ref(null);
const githubStatusState = ref("");
const filters = reactive({
  search: "",
  quickView: "all",
  reviewStatus: "all",
  visibility: "all",
  sort: "featured",
});
const drafts = reactive({});
let filterReloadTimer = null;
let loadRequestId = 0;

const buildRemoteFilters = () => ({
  reviewStatus: filters.reviewStatus,
  visibility: filters.visibility,
  sort: filters.sort,
});

const loadProfiles = async () => {
  const requestId = ++loadRequestId;
  isLoading.value = true;
  errorMessage.value = "";

  try {
    authState.value = await getAuthState();
    const hasAccess = props.serverMode ? authState.value.isConfigAdmin : authState.value.isAdmin;
    if (!hasAccess) {
      errorMessage.value = props.serverMode
        ? "Server admin access is required to use the control desk."
        : "Admin access is required to use the curation desk.";
      adminProfiles.value = [];
      return;
    }

    const listProfiles = props.serverMode ? listServerAdminProfiles : listAdminProfiles;
    const getSettings = props.serverMode ? getServerAdminSettings : getAdminSettings;
    const [nextProfiles, nextSettings] = await Promise.all([
      listProfiles(buildRemoteFilters()),
      getSettings(),
    ]);
    if (requestId !== loadRequestId) {
      return;
    }

    adminProfiles.value = nextProfiles;
    adminSettings.value = nextSettings;
    syncAdminDrafts(drafts, adminProfiles.value);
  } catch (error) {
    if (requestId !== loadRequestId) {
      return;
    }

    errorMessage.value = error.message || "관리 데이터를 불러오지 못했습니다.";
    adminProfiles.value = [];
  } finally {
    if (requestId === loadRequestId) {
      isLoading.value = false;
    }
  }
};

const summary = computed(() => buildAdminSummary(adminProfiles.value));

const rows = computed(() => buildAdminRows(adminProfiles.value, filters));
const pageState = computed(() => buildAdminPagination({ rows: rows.value, currentPage: currentPage.value }));
const paginatedRows = computed(() => pageState.value.paginatedRows);
const quickFilters = computed(() => [
  { key: "all", label: "전체", count: adminProfiles.value.length },
  { key: "needsWork", label: "보완 필요", count: summary.value.needsWork },
  { key: "exposedDrafts", label: "공개 초안", count: summary.value.exposedDrafts },
  { key: "hidden", label: "비공개", count: summary.value.hidden },
  { key: "banned", label: "밴", count: summary.value.banned },
  {
    key: "missingGithub",
    label: "GitHub 없음",
    count: buildAdminRows(adminProfiles.value, { quickView: "missingGithub" }).length,
  },
  { key: "admins", label: "관리자", count: summary.value.admins },
]);
const selectedRows = computed(() => rows.value.filter((row) => selectedIds[row.id]));
const selectedCount = computed(() => selectedRows.value.length);
const dirtyRows = computed(() => buildDirtyAdminRows(adminProfiles.value, drafts));
const dirtyCount = computed(() => dirtyRows.value.length);
const selectedDirtyCount = computed(() => selectedRows.value.filter(rowDirty).length);
const activeFilterCount = computed(() =>
  [
    filters.search,
    filters.quickView !== "all",
    filters.reviewStatus !== "all",
    filters.visibility !== "all",
    filters.sort !== "featured",
  ].filter(Boolean).length,
);
const activeFilterText = computed(() =>
  activeFilterCount.value ? `${activeFilterCount.value}개 조건 적용` : "전체 목록",
);
const allRowsSelected = computed(
  () => paginatedRows.value.length > 0 && paginatedRows.value.every((row) => selectedIds[row.id]),
);

const showAccessGate = computed(() =>
  !isLoading.value && (props.serverMode ? !authState.value.isConfigAdmin : !authState.value.isAdmin),
);
const reviewedCount = computed(() => summary.value.review);
const hiddenCount = computed(() => summary.value.hidden);
const bannedCount = computed(() => summary.value.banned);
const exposedDraftCount = computed(() => summary.value.exposedDrafts);
const configAdminText = computed(() => {
  if (!props.serverMode) {
    return "서버 관리자 화면에서 확인";
  }

  return adminSettings.value?.controlsAdminGrants
    ? "환경변수로 관리"
    : "프로필 권한으로 관리";
});
const managedDepartments = computed(() => adminSettings.value?.departments || []);
const githubStatusLabel = computed(() => {
  if (githubStatusState.value === "checking") {
    return "확인 중";
  }
  if (!githubStatus.value) {
    return "미확인";
  }
  return githubStatus.value.ok ? "정상" : "문제 있음";
});
const rowDirty = (row) => isAdminDraftDirty(row, drafts[row.id] || createAdminDraft(row));

const clearSelection = () => {
  Object.keys(selectedIds).forEach((id) => {
    delete selectedIds[id];
  });
};

const toggleAllRows = () => {
  if (allRowsSelected.value) {
    paginatedRows.value.forEach((row) => {
      delete selectedIds[row.id];
    });
    return;
  }

  paginatedRows.value.forEach((row) => {
    selectedIds[row.id] = true;
  });
};

const goToPage = (page) => {
  currentPage.value = Math.min(Math.max(1, Number(page) || 1), pageState.value.totalPages);
};

const resetFilters = () => {
  filters.search = "";
  filters.quickView = "all";
  filters.reviewStatus = "all";
  filters.visibility = "all";
  filters.sort = "featured";
};

const applyBulkPatch = (patch, message) => {
  if (selectedRows.value.length === 0) {
    showError("먼저 프로필을 선택해 주세요.");
    return;
  }

  applyAdminDraftPatch(drafts, selectedRows.value, patch);
  showSuccess(message);
};

const handleSave = async (profileId) => {
  saveStates[profileId] = {
    state: "saving",
    message: "저장 중...",
  };

  try {
    const updateProfile = props.serverMode ? updateServerAdminProfile : updateAdminProfile;
    const updated = await updateProfile(profileId, drafts[profileId]);
    adminProfiles.value = adminProfiles.value.map((profile) =>
      profile.id === updated.id ? updated : profile,
    );
    drafts[profileId] = createAdminDraft(updated);
    saveStates[profileId] = {
      state: "success",
      message: "저장됨",
    };
    showSuccess(`${updated.name || '프로필'} 저장 완료`);
  } catch (error) {
    saveStates[profileId] = {
      state: "error",
      message: error.message || "저장 실패",
    };
    showError(error.message || "저장에 실패했습니다.");
  }
};

const saveAdminRows = async (rowsToSave, successMessage) => {
  bulkSaveState.value = "saving";

  try {
    const updatedProfiles = [];
    for (const row of rowsToSave) {
      saveStates[row.id] = {
        state: "saving",
        message: "저장 중...",
      };
      const updateProfile = props.serverMode ? updateServerAdminProfile : updateAdminProfile;
      const updated = await updateProfile(row.id, drafts[row.id]);
      updatedProfiles.push(updated);
      drafts[row.id] = createAdminDraft(updated);
      saveStates[row.id] = {
        state: "success",
        message: "저장됨",
      };
    }

    adminProfiles.value = adminProfiles.value.map((profile) => {
      const updated = updatedProfiles.find((item) => item.id === profile.id);
      return updated || profile;
    });
    bulkSaveState.value = "success";
    showSuccess(successMessage(updatedProfiles.length));
  } catch (error) {
    bulkSaveState.value = "error";
    showError(error.message || "일괄 저장에 실패했습니다.");
  }
};

const handleSaveAll = async () => {
  if (dirtyRows.value.length === 0) {
    showError("저장할 변경사항이 없습니다.");
    return;
  }

  await saveAdminRows(dirtyRows.value, (count) => `${count}개 프로필을 저장했습니다.`);
};

const handleSaveSelected = async () => {
  const rowsToSave = selectedRows.value.filter(rowDirty);
  if (rowsToSave.length === 0) {
    showError("선택한 프로필에 저장할 변경사항이 없습니다.");
    return;
  }

  await saveAdminRows(rowsToSave, (count) => `선택한 변경사항 ${count}개를 저장했습니다.`);
};

const handleBanSelected = () => {
  applyBulkPatch(
    { reviewStatus: "banned", isVisible: false },
    "선택 항목을 밴 상태로 변경했습니다. 저장해야 적용됩니다.",
  );
};

const handleDeleteProfile = async (row) => {
  if (!props.serverMode || !row?.id) {
    showError("삭제는 서버 관리자 화면에서만 가능합니다.");
    return;
  }

  const confirmation = window.prompt(
    `${row.name || row.email || "프로필"} 프로필과 프로젝트를 모두 삭제합니다. 계속하려면 DELETE를 입력하세요.`,
  );
  if (confirmation !== "DELETE") {
    return;
  }

  saveStates[row.id] = {
    state: "saving",
    message: "삭제 중...",
  };
  try {
    await deleteServerAdminProfile(row.id);
    adminProfiles.value = adminProfiles.value.filter((profile) => profile.id !== row.id);
    delete drafts[row.id];
    delete selectedIds[row.id];
    delete saveStates[row.id];
    showSuccess("프로필을 삭제했습니다.");
  } catch (error) {
    saveStates[row.id] = {
      state: "error",
      message: error.message || "삭제 실패",
    };
    showError(error.message || "프로필을 삭제하지 못했습니다.");
  }
};

const handleDeleteSelected = async () => {
  if (!props.serverMode) {
    showError("삭제는 서버 관리자 화면에서만 가능합니다.");
    return;
  }
  if (selectedRows.value.length === 0) {
    showError("삭제할 프로필을 선택해 주세요.");
    return;
  }

  const confirmation = window.prompt(
    `선택한 ${selectedRows.value.length}개 프로필과 프로젝트를 모두 삭제합니다. 계속하려면 DELETE를 입력하세요.`,
  );
  if (confirmation !== "DELETE") {
    return;
  }

  bulkSaveState.value = "saving";
  try {
    const ids = selectedRows.value.map((row) => row.id);
    for (const id of ids) {
      saveStates[id] = {
        state: "saving",
        message: "삭제 중...",
      };
      await deleteServerAdminProfile(id);
      delete drafts[id];
      delete selectedIds[id];
      delete saveStates[id];
    }
    adminProfiles.value = adminProfiles.value.filter((profile) => !ids.includes(profile.id));
    bulkSaveState.value = "success";
    showSuccess(`${ids.length}개 프로필을 삭제했습니다.`);
  } catch (error) {
    bulkSaveState.value = "error";
    showError(error.message || "선택 프로필을 삭제하지 못했습니다.");
  }
};

const handleAddDepartment = async () => {
  const name = departmentDraft.value.trim();
  if (!name) {
    showError("추가할 학과명을 입력해 주세요.");
    return;
  }

  departmentState.value = "saving";
  try {
    const result = await addServerAdminDepartment(name);
    adminSettings.value = {
      ...(adminSettings.value || {}),
      departments: result.departments || [],
    };
    departmentDraft.value = "";
    departmentState.value = "success";
    showSuccess("학과를 추가했습니다.");
  } catch (error) {
    departmentState.value = "error";
    showError(error.message || "학과를 추가하지 못했습니다.");
  }
};

const handleDeleteDepartment = async (name) => {
  const shouldDelete = window.confirm(
    `"${name}" 학과를 목록에서 삭제할까요? 기존 프로필의 학과 값은 자동으로 지우지 않습니다.`,
  );
  if (!shouldDelete) {
    return;
  }

  departmentState.value = "saving";
  try {
    const result = await deleteServerAdminDepartment(name);
    adminSettings.value = {
      ...(adminSettings.value || {}),
      departments: result.departments || [],
    };
    departmentState.value = "success";
    showSuccess("학과를 삭제했습니다.");
  } catch (error) {
    departmentState.value = "error";
    showError(error.message || "학과를 삭제하지 못했습니다.");
  }
};

const handleCheckGithubCommits = async () => {
  githubStatusState.value = "checking";
  try {
    githubStatus.value = await checkGithubCommitStatus("torvalds");
    githubStatusState.value = githubStatus.value.ok ? "success" : "error";
    if (githubStatus.value.ok) {
      showSuccess("GitHub 활동 수 조회가 정상 작동합니다.");
    } else {
      showError(githubStatus.value.message || "GitHub 활동 수 조회에 문제가 있습니다.");
    }
  } catch (error) {
    githubStatus.value = {
      ok: false,
      configured: false,
      checkedUsername: "torvalds",
      totalCommits: null,
      message: error.message || "GitHub 활동 수 조회 상태를 확인하지 못했습니다.",
    };
    githubStatusState.value = "error";
    showError(githubStatus.value.message);
  }
};

watch(
  () => [filters.reviewStatus, filters.visibility, filters.sort],
  () => {
    clearTimeout(filterReloadTimer);
    filterReloadTimer = setTimeout(loadProfiles, 250);
  },
);

watch(
  () => [filters.search, filters.quickView, filters.reviewStatus, filters.visibility, filters.sort],
  () => {
    currentPage.value = 1;
  },
);

watch(rows, () => {
  if (currentPage.value !== pageState.value.safePage) {
    currentPage.value = pageState.value.safePage;
  }

  const visibleIds = new Set(rows.value.map((row) => String(row.id)));
  Object.keys(selectedIds).forEach((id) => {
    if (!visibleIds.has(String(id))) {
      delete selectedIds[id];
    }
  });
});

onMounted(loadProfiles);

onUnmounted(() => {
  clearTimeout(filterReloadTimer);
});
</script>

<template>
  <div class="admin-page">
    <PageIntroStrip
      eyebrow="관리자"
      title="포트폴리오 관리"
      summary="공개 상태와 추천 순서를 관리합니다."
      :meta-line="`전체 ${summary.total}개 · 공개 ${summary.visible}개 · 승인 ${summary.approved}개 · 평균 완성도 ${summary.averageCompleteness}%`"
    />

    <SurfaceSection
      v-if="props.serverMode"
      eyebrow="SERVER ADMIN"
      title="서버 관리자 제어판"
      summary="PORTFOLIO_ADMIN_EMAILS에 등록된 서버 관리자만 관리자 권한 부여와 운영 정책을 통제할 수 있습니다."
      tone="muted"
    />

    <SurfaceSection
      v-if="showAccessGate"
      eyebrow="권한 필요"
      title="관리자만 접근할 수 있습니다."
      summary="관리 화면은 로그인 후 관리자 권한이 있는 계정에서만 사용할 수 있습니다."
    >
      <div class="admin-page__gate">
        <button type="button" class="admin-page__save-button" @click="$router.push('/')">
          포트폴리오로 이동
        </button>
      </div>
    </SurfaceSection>

    <div v-else class="admin-page__workspace">
      <section class="admin-page__command-deck" aria-label="관리 현황과 설정">
        <div class="admin-page__metrics" aria-label="관리 현황">
          <article class="admin-page__metric admin-page__metric--primary">
            <span>전체 프로필</span>
            <strong>{{ summary.total }}</strong>
            <small>결과 {{ rows.length }}명</small>
          </article>
          <article class="admin-page__metric">
            <span>공개</span>
            <strong>{{ summary.visible }}</strong>
          </article>
          <article class="admin-page__metric">
            <span>검토 중</span>
            <strong>{{ reviewedCount }}</strong>
          </article>
          <article class="admin-page__metric">
            <span>초안</span>
            <strong>{{ summary.draft }}</strong>
          </article>
          <article class="admin-page__metric">
            <span>비공개</span>
            <strong>{{ hiddenCount }}</strong>
          </article>
          <article class="admin-page__metric admin-page__metric--danger">
            <span>밴</span>
            <strong>{{ bannedCount }}</strong>
          </article>
          <article class="admin-page__metric">
            <span>보완 필요</span>
            <strong>{{ summary.needsWork }}</strong>
          </article>
          <article class="admin-page__metric">
            <span>완성도</span>
            <strong>{{ summary.averageCompleteness }}%</strong>
          </article>
        </div>

        <details class="admin-page__settings-drawer">
          <summary>
            <span>관리자 설정</span>
            <strong>{{ adminSettings?.currentAdminSource === "environment" ? "환경변수 관리자" : "프로필 관리자" }}</strong>
          </summary>
          <dl class="admin-page__settings">
            <div>
              <dt>허용 이메일</dt>
              <dd>@{{ adminSettings?.allowedEmailDomain || "sdh.hs.kr" }}</dd>
            </div>
            <div>
              <dt>현재 권한</dt>
              <dd>{{ adminSettings?.currentAdminSource === "environment" ? "환경변수 관리자" : "프로필 관리자" }}</dd>
            </div>
            <div>
              <dt>환경변수 관리자</dt>
              <dd>{{ configAdminText }}</dd>
            </div>
            <div>
              <dt>업로드 제한</dt>
              <dd>{{ Math.round((adminSettings?.maxUploadBytes || 0) / 1024 / 1024) || 5 }}MB</dd>
            </div>
            <div v-if="props.serverMode">
              <dt>GitHub 활동 조회</dt>
              <dd>{{ githubStatusLabel }}</dd>
            </div>
          </dl>

          <section v-if="props.serverMode" class="admin-page__github-status">
            <div>
              <span>GitHub 활동 API</span>
              <strong>
                <template v-if="githubStatus?.ok">
                  {{ githubStatus.checkedUsername }} · {{ Number(githubStatus.totalCommits || 0).toLocaleString() }}개
                </template>
                <template v-else>
                  {{ githubStatus?.message || "GitHub GraphQL 연결 상태를 확인합니다." }}
                </template>
              </strong>
            </div>
            <button
              type="button"
              class="admin-page__save-button"
              :disabled="githubStatusState === 'checking'"
              @click="handleCheckGithubCommits"
            >
              {{ githubStatusState === "checking" ? "확인 중..." : "작동 확인" }}
            </button>
          </section>

          <section v-if="props.serverMode" class="admin-page__department-manager">
            <div class="admin-page__department-manager-head">
              <span>학과 관리</span>
              <strong>{{ managedDepartments.length }}개</strong>
            </div>
            <div class="admin-page__department-add">
              <input
                v-model.trim="departmentDraft"
                name="department-create"
                type="text"
                placeholder="새 학과명"
                @keyup.enter="handleAddDepartment"
              />
              <button
                type="button"
                class="admin-page__save-button"
                :disabled="departmentState === 'saving'"
                @click="handleAddDepartment"
              >
                추가
              </button>
            </div>
            <div class="admin-page__department-list">
              <span v-for="department in managedDepartments" :key="department">
                {{ department }}
                <button
                  type="button"
                  :aria-label="`${department} 삭제`"
                  @click="handleDeleteDepartment(department)"
                >
                  삭제
                </button>
              </span>
            </div>
          </section>
        </details>
      </section>

      <div class="admin-page__sticky-tools">
        <div class="admin-page__tool-strip">
          <div class="admin-page__tool-status" aria-live="polite">
            <strong>{{ rows.length }}명</strong>
            <span>
              {{ activeFilterText }} · {{ pageState.pageStart }}-{{ pageState.pageEnd }} 표시 ·
              {{ selectedCount }}개 선택 · {{ dirtyCount }}개 저장 대기
            </span>
          </div>

          <label class="admin-page__quick-search">
            <span>검색</span>
            <input
              v-model="filters.search"
              name="admin-search"
              type="search"
              placeholder="이름, 이메일, GitHub, 학과, 태그"
            />
            <button
              v-if="filters.search"
              type="button"
              aria-label="검색어 지우기"
              @click="filters.search = ''"
            >
              ×
            </button>
          </label>

          <details class="admin-page__filter-menu">
            <summary>상세 필터</summary>
            <div class="admin-page__filters">
              <label>
                <span>검토 상태</span>
                <select v-model="filters.reviewStatus" name="admin-review-status">
                  <option value="all">전체</option>
                  <option value="draft">초안</option>
                  <option value="review">검토</option>
                  <option value="approved">승인</option>
                  <option value="banned">밴</option>
                </select>
              </label>

              <label>
                <span>공개 여부</span>
                <select v-model="filters.visibility" name="admin-visibility">
                  <option value="all">전체</option>
                  <option value="visible">공개만</option>
                  <option value="hidden">비공개만</option>
                </select>
              </label>

              <label>
                <span>정렬</span>
                <select v-model="filters.sort" name="admin-sort">
                  <option value="featured">추천 순서</option>
                  <option value="latest">최신순</option>
                  <option value="name">이름순</option>
                  <option value="department">학과순</option>
                </select>
              </label>

              <button type="button" class="admin-page__ghost-button" @click="resetFilters">
                필터 초기화
              </button>
            </div>
          </details>

          <div class="admin-page__bulk-actions" aria-label="일괄 작업">
            <button type="button" class="admin-page__ghost-button" @click="toggleAllRows">
              {{ allRowsSelected ? "현재 페이지 해제" : "현재 페이지 선택" }}
            </button>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="selectedCount === 0"
              @click="applyBulkPatch({ reviewStatus: 'approved', isVisible: true }, '선택 항목을 승인/공개 상태로 변경했습니다.')"
            >
              승인 공개
            </button>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="selectedCount === 0"
              @click="applyBulkPatch({ reviewStatus: 'review' }, '선택 항목을 검토 상태로 변경했습니다.')"
            >
              검토
            </button>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="selectedCount === 0"
              @click="applyBulkPatch({ isVisible: false }, '선택 항목을 비공개로 변경했습니다. 저장해야 적용됩니다.')"
            >
              비공개
            </button>
            <button
              type="button"
              class="admin-page__danger-button"
              :disabled="selectedCount === 0"
              @click="handleBanSelected"
            >
              선택 밴
            </button>
            <button
              v-if="props.serverMode"
              type="button"
              class="admin-page__danger-button"
              :disabled="selectedCount === 0 || bulkSaveState === 'saving'"
              @click="handleDeleteSelected"
            >
              선택 삭제
            </button>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="selectedDirtyCount === 0 || bulkSaveState === 'saving'"
              @click="handleSaveSelected"
            >
              선택 저장 {{ selectedDirtyCount }}
            </button>
            <button
              type="button"
              class="admin-page__save-button"
              :disabled="dirtyCount === 0 || bulkSaveState === 'saving'"
              @click="handleSaveAll"
            >
              {{ bulkSaveState === "saving" ? "저장 중" : `전체 저장 ${dirtyCount}` }}
            </button>
          </div>
        </div>

        <div class="admin-page__quick-filters" aria-label="빠른 보기">
          <button
            v-for="filter in quickFilters"
            :key="filter.key"
            type="button"
            class="admin-page__quick-filter"
            :data-active="filters.quickView === filter.key"
            @click="filters.quickView = filter.key"
          >
            <span>{{ filter.label }}</span>
            <strong>{{ filter.count }}</strong>
          </button>
          <button
            v-if="activeFilterCount"
            type="button"
            class="admin-page__quick-filter admin-page__quick-filter--reset"
            @click="resetFilters"
          >
            <span>조건 초기화</span>
          </button>
        </div>
      </div>

      <div class="admin-page__content">
        <section v-if="exposedDraftCount" class="admin-page__quality-alert">
          <div>
            <p>공개 품질 경고</p>
            <h2>{{ exposedDraftCount }}개 초안 프로필이 공개 중입니다.</h2>
            <span>승인 전까지 비공개로 돌리거나, 검토 후 승인 공개 상태로 저장해 주세요.</span>
          </div>
        </section>

        <StatusView
          v-if="isLoading"
          title="관리 목록을 불러오는 중입니다."
          body="프로필 상태와 추천 순서를 준비하고 있습니다."
        />
        <StatusView
          v-else-if="errorMessage"
          state="error"
          title="관리 화면을 열 수 없습니다."
          :body="errorMessage"
        />
        <StatusView
          v-else-if="rows.length === 0"
          state="empty"
          title="조건에 맞는 프로필이 없습니다."
          body="필터를 다시 선택해 주세요."
        />

        <section v-else class="admin-page__table">
          <article
            v-for="row in paginatedRows"
            :key="row.id"
            class="admin-page__row"
            :data-selected="Boolean(selectedIds[row.id])"
            :data-banned="row.reviewStatus === 'banned'"
          >
            <label class="admin-page__row-select" :aria-label="`${row.name || '프로필'} 선택`">
              <input v-model="selectedIds[row.id]" :name="`admin-select-${row.id}`" type="checkbox" />
              <span aria-hidden="true"></span>
            </label>

            <div class="admin-page__row-main">
              <div class="admin-page__row-topline">
                <p class="admin-page__row-eyebrow">{{ row.job || "프로필" }}</p>
                <div class="admin-page__row-topline-meta">
                  <span v-if="rowDirty(row)" class="admin-page__dirty-pill">
                    변경됨
                  </span>
                  <span class="admin-page__status-pill" :data-status="row.reviewStatus || 'draft'">
                    {{ row.reviewStatusLabel }}
                  </span>
                  <span class="admin-page__visibility-pill" :data-visible="row.isVisible">
                    {{ row.isVisible ? "공개" : "비공개" }}
                  </span>
                </div>
              </div>

              <div class="admin-page__row-head">
                <div class="admin-page__row-identity">
                  <h2>{{ row.name || "이름 없음" }}</h2>
                  <p>{{ [row.school, row.department].filter(Boolean).join(" · ") || "학과 정보 없음" }}</p>
                  <p v-if="row.email" class="admin-page__row-email">{{ row.email }}</p>
                </div>

                <div class="admin-page__row-links">
                  <RouterLink :to="`/profiles/${row.id}`" class="admin-page__row-link">
                    보기
                  </RouterLink>
                  <RouterLink :to="`/profiles/${row.id}/edit`" class="admin-page__row-link">
                    편집
                  </RouterLink>
                </div>
              </div>

              <div class="admin-page__row-summary">
                <p>{{ row.description || "소개 없음" }}</p>
                <div class="admin-page__completeness">
                  <strong>{{ row.completeness.percent }}%</strong>
                  <span>완성도</span>
                </div>
              </div>

              <div class="admin-page__chips">
                <span v-for="item in row.tags" :key="item">{{ item }}</span>
                <span
                  v-for="issue in row.issues"
                  :key="issue"
                  class="admin-page__issue-chip"
                >
                  {{ issue }}
                </span>
              </div>
            </div>

            <div class="admin-page__row-controls">
              <div class="admin-page__controls">
                <label class="admin-page__control-field">
                  <span>상태</span>
                  <select v-model="drafts[row.id].reviewStatus" :name="`admin-review-${row.id}`">
                    <option value="draft">초안</option>
                    <option value="review">검토</option>
                    <option value="approved">승인</option>
                    <option value="banned">밴</option>
                  </select>
                </label>

                <label class="admin-page__control-field">
                  <span>추천 순서</span>
                  <input
                    v-model.number="drafts[row.id].featuredRank"
                    :name="`admin-featured-rank-${row.id}`"
                    type="number"
                    min="1"
                    step="1"
                  />
                </label>

                <template v-if="props.serverMode">
                  <label class="admin-page__control-field admin-page__control-field--wide">
                    <span>학교</span>
                    <input
                      v-model.trim="drafts[row.id].school"
                      :name="`admin-school-${row.id}`"
                      type="text"
                      placeholder="서울디지텍고등학교"
                    />
                  </label>

                  <label class="admin-page__control-field">
                    <span>학과</span>
                    <select
                      v-model="drafts[row.id].department"
                      :name="`admin-department-${row.id}`"
                    >
                      <option value="">선택 안 함</option>
                      <option
                        v-for="department in managedDepartments"
                        :key="department"
                        :value="department"
                      >
                        {{ department }}
                      </option>
                    </select>
                  </label>

                  <label class="admin-page__control-field">
                    <span>트랙</span>
                    <input
                      v-model.trim="drafts[row.id].track"
                      :name="`admin-track-${row.id}`"
                      type="text"
                      placeholder="전공 트랙"
                    />
                  </label>
                </template>

                <label class="admin-page__toggle">
                  <input v-model="drafts[row.id].isVisible" :name="`admin-visible-${row.id}`" type="checkbox" />
                  <span class="admin-page__toggle-track" aria-hidden="true"></span>
                  <span>공개</span>
                </label>

                <label v-if="props.serverMode" class="admin-page__toggle">
                  <input v-model="drafts[row.id].isAdmin" :name="`admin-is-admin-${row.id}`" type="checkbox" />
                  <span class="admin-page__toggle-track" aria-hidden="true"></span>
                  <span>관리자</span>
                </label>
              </div>

              <div class="admin-page__risk-actions">
                <button
                  type="button"
                  class="admin-page__ghost-button"
                  @click="applyAdminDraftPatch(drafts, [row], { reviewStatus: drafts[row.id].reviewStatus === 'banned' ? 'review' : 'banned', isVisible: false })"
                >
                  {{ drafts[row.id].reviewStatus === "banned" ? "밴 해제" : "밴 처리" }}
                </button>
                <button
                  v-if="props.serverMode"
                  type="button"
                  class="admin-page__danger-button"
                  :disabled="saveStates[row.id]?.state === 'saving'"
                  @click="handleDeleteProfile(row)"
                >
                  삭제
                </button>
              </div>

              <div class="admin-page__actions">
                <button
                  type="button"
                  class="admin-page__save-button"
                  :disabled="!rowDirty(row) || saveStates[row.id]?.state === 'saving'"
                  @click="handleSave(row.id)"
                >
                  {{ saveStates[row.id]?.state === "saving" ? "저장 중" : "저장" }}
                </button>
                <p v-if="saveStates[row.id]" :data-state="saveStates[row.id].state">
                  {{ saveStates[row.id].message }}
                </p>
              </div>
            </div>
          </article>
        </section>

        <nav
          v-if="rows.length > 0"
          class="admin-page__pagination"
          aria-label="관리자 프로필 페이지"
        >
          <p>
            {{ pageState.pageStart }}-{{ pageState.pageEnd }} / {{ pageState.totalCount }}명
          </p>
          <div>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="pageState.safePage === 1"
              @click="goToPage(pageState.safePage - 1)"
            >
              이전
            </button>
            <template v-for="(pageItem, index) in pageState.pageItems" :key="`${pageItem}-${index}`">
              <span v-if="pageItem === '...'" class="admin-page__page-gap" aria-hidden="true">
                ...
              </span>
              <button
                v-else
                type="button"
                class="admin-page__page-button"
                :data-active="pageState.safePage === pageItem"
                :aria-current="pageState.safePage === pageItem ? 'page' : undefined"
                @click="goToPage(pageItem)"
              >
                {{ pageItem }}
              </button>
            </template>
            <button
              type="button"
              class="admin-page__ghost-button"
              :disabled="pageState.safePage === pageState.totalPages"
              @click="goToPage(pageState.safePage + 1)"
            >
              다음
            </button>
          </div>
        </nav>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  display: grid;
  gap: 24px;
}

.admin-page__workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.admin-page__command-deck {
  display: grid;
  gap: 14px;
}

.admin-page__sticky-tools {
  position: sticky;
  top: calc(var(--shell-sticky-top) + var(--shell-sticky-gap));
  z-index: 8;
  display: grid;
  gap: 10px;
}

.admin-page__tool-strip {
  display: grid;
  grid-template-columns: minmax(150px, auto) minmax(260px, 1fr) auto minmax(0, 1.8fr);
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 8px 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-sm);
}

.admin-page__tool-status {
  display: grid;
  gap: 2px;
  min-width: 130px;
  padding: 0 8px;
}

.admin-page__tool-status strong {
  color: var(--text-strong);
  font-size: 0.98rem;
  line-height: 1.1;
}

.admin-page__tool-status span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 700;
}

.admin-page__quick-search {
  position: relative;
  display: grid;
  gap: 4px;
  min-width: 0;
}

.admin-page__quick-search span {
  color: var(--text-sub);
  font-size: 0.72rem;
  font-weight: 800;
}

.admin-page__quick-search input {
  min-height: 40px;
  padding-right: 36px;
}

.admin-page__quick-search button {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xs);
  background: var(--bg-surface-solid);
  color: var(--text-sub);
  font-weight: 800;
}

.admin-page__quick-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.admin-page__quick-filter {
  min-height: 34px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-main);
  font-weight: 700;
}

.admin-page__quick-filter[data-active="true"] {
  border-color: var(--brand-main);
  background: var(--brand-soft);
  color: var(--brand-main);
}

.admin-page__quick-filter strong {
  min-width: 22px;
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  background: var(--muted);
  color: var(--text-strong);
  font-size: 0.76rem;
  text-align: center;
}

.admin-page__quick-filter--reset {
  color: var(--text-sub);
}

.admin-page__content {
  display: grid;
  gap: 20px;
}

.admin-page__quality-alert {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  border: 1px solid rgba(138, 93, 30, 0.24);
  border-radius: var(--radius-xl);
  background: var(--warning-soft);
  color: var(--warning-text);
}

.admin-page__quality-alert p,
.admin-page__quality-alert h2,
.admin-page__quality-alert span {
  margin: 0;
}

.admin-page__quality-alert p {
  font-size: 0.78rem;
  font-weight: 800;
}

.admin-page__quality-alert h2 {
  color: var(--warning-text);
  font-size: 1.1rem;
}

.admin-page__quality-alert span {
  color: var(--text-main);
}

.admin-page__bulk-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.admin-page__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-sm);
}

.admin-page__pagination p {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 800;
}

.admin-page__pagination div {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.admin-page__page-button {
  min-width: 40px;
  min-height: 40px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  font-weight: 800;
}

.admin-page__page-button[data-active="true"] {
  border-color: var(--brand-main);
  background: var(--brand-main);
  color: #fff;
}

.admin-page__page-gap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  min-height: 40px;
  color: var(--text-sub);
  font-weight: 900;
}

.admin-page__gate {
  display: flex;
  justify-content: flex-start;
}

.admin-page__metrics,
.admin-page__filters,
.admin-page__table {
  display: grid;
  gap: 16px;
}

.admin-page__metrics {
  grid-template-columns: minmax(160px, 1.4fr) repeat(7, minmax(96px, 1fr));
  gap: 12px;
}

.admin-page__metric,
.admin-page__row {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-sm);
}

.admin-page__metric {
  min-height: 112px;
  padding: 18px;
  display: grid;
  align-content: space-between;
}

.admin-page__metric--primary {
  background:
    linear-gradient(135deg, rgba(0, 113, 227, 0.12), rgba(255, 255, 255, 0.92)),
    var(--bg-surface-solid);
}

.admin-page__metric--danger {
  background: var(--danger-soft);
}

.admin-page__metric--danger strong {
  color: var(--danger-text);
}

.admin-page__metric span {
  color: var(--text-sub);
  font-size: 0.76rem;
  font-weight: 700;
}

.admin-page__metric strong {
  color: var(--text-strong);
  font-size: 1.65rem;
  line-height: 1;
}

.admin-page__metric small {
  color: var(--brand-main);
  font-size: 0.82rem;
  font-weight: 800;
}

.admin-page__filters {
  grid-template-columns: repeat(3, minmax(150px, 1fr)) auto;
  align-items: end;
  gap: 12px;
}

.admin-page__filters label,
.admin-page__controls label {
  display: grid;
  gap: 8px;
}

.admin-page__search input {
  min-height: 48px;
}

.admin-page__filters span,
.admin-page__controls span {
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 700;
}

.admin-page__filter-menu {
  position: relative;
}

.admin-page__filter-menu summary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  font-weight: 800;
  cursor: pointer;
  list-style: none;
}

.admin-page__filter-menu summary::-webkit-details-marker {
  display: none;
}

.admin-page__filter-menu[open] summary {
  border-color: var(--brand-main);
  background: var(--brand-soft);
  color: var(--brand-main);
}

.admin-page__filter-menu .admin-page__filters {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  z-index: 12;
  width: min(860px, calc(100vw - 48px));
  padding: 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.16);
}

.admin-page__settings-drawer,
.admin-page__settings {
  display: grid;
}

.admin-page__settings-drawer {
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-solid);
  box-shadow: var(--shadow-sm);
}

.admin-page__settings-drawer summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 54px;
  padding: 0 18px;
  color: var(--text-main);
  cursor: pointer;
  list-style: none;
}

.admin-page__settings-drawer summary::-webkit-details-marker {
  display: none;
}

.admin-page__settings-drawer summary span {
  color: var(--text-sub);
  font-size: 0.82rem;
  font-weight: 800;
}

.admin-page__settings-drawer summary strong {
  color: var(--text-strong);
  font-size: 0.92rem;
}

.admin-page__settings {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
  padding: 0 18px 18px;
}

.admin-page__settings div {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
}

.admin-page__settings dt,
.admin-page__settings dd {
  margin: 0;
}

.admin-page__settings dt {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 700;
}

.admin-page__settings dd {
  color: var(--text-strong);
  font-size: 0.88rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.admin-page__github-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin: 0 18px 18px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-muted);
}

.admin-page__github-status div {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.admin-page__github-status span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 800;
}

.admin-page__github-status strong {
  color: var(--text-strong);
  font-size: 0.9rem;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.admin-page__department-manager {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 0.8fr);
  gap: 14px;
  padding: 0 18px 18px;
}

.admin-page__department-manager-head {
  display: grid;
  align-content: center;
  gap: 4px;
  min-width: 0;
}

.admin-page__department-manager-head span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 800;
}

.admin-page__department-manager-head strong {
  color: var(--text-strong);
  font-size: 1rem;
}

.admin-page__department-add {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.admin-page__department-list {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.admin-page__department-list span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 8px 0 12px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: var(--bg-surface-muted);
  color: var(--text-main);
  font-size: 0.84rem;
  font-weight: 700;
}

.admin-page__department-list button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  border: none;
  border-radius: 999px;
  background: rgba(138, 36, 36, 0.1);
  color: var(--danger-text);
  font-size: 0.72rem;
  font-weight: 900;
}

.admin-page__ghost-button {
  min-height: 40px;
  padding: 0 13px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--text-strong);
  font-weight: 600;
}

.admin-page__ghost-button:disabled {
  color: var(--text-sub);
  opacity: 0.55;
  cursor: not-allowed;
}

.admin-page__row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) minmax(258px, 0.36fr);
  gap: 18px;
  padding: 20px;
  scroll-margin-top: calc(var(--shell-sticky-top) + 76px);
  content-visibility: auto;
  contain-intrinsic-size: auto 320px;
}

.admin-page__row[data-selected="true"] {
  border-color: var(--brand-ring-strong);
  box-shadow: 0 0 0 3px var(--brand-ring), var(--shadow-sm);
}

.admin-page__row[data-banned="true"] {
  border-color: rgba(153, 27, 27, 0.28);
  background: linear-gradient(180deg, var(--danger-soft), var(--bg-surface-solid) 140px);
}

.admin-page__row-select {
  display: grid;
  align-content: start;
  justify-items: center;
  padding-top: 4px;
  cursor: pointer;
}

.admin-page__row-select input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.admin-page__row-select span {
  width: 22px;
  height: 22px;
  border: 1px solid var(--line-strong);
  border-radius: 7px;
  background: #fff;
}

.admin-page__row-select input:checked + span {
  border-color: var(--brand-main);
  background: var(--brand-main);
  box-shadow: inset 0 0 0 5px #fff;
}

.admin-page__row-select input:focus-visible + span {
  outline: 2px solid var(--brand-main);
  outline-offset: 2px;
}

.admin-page__row-main,
.admin-page__row-controls {
  display: grid;
  gap: 16px;
  align-content: start;
}

.admin-page__row-controls {
  padding: 14px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface-muted);
  border: 1px solid var(--line-soft);
  align-self: stretch;
}

.admin-page__row-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.admin-page__row-topline-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.admin-page__status-pill,
.admin-page__visibility-pill,
.admin-page__dirty-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
}

.admin-page__status-pill {
  background: var(--brand-soft);
  color: var(--brand-main);
}

.admin-page__dirty-pill {
  background: rgba(138, 93, 30, 0.12);
  color: var(--warning-text);
}

.admin-page__status-pill[data-status="approved"] {
  background: var(--success-soft);
  color: var(--success-text);
}

.admin-page__status-pill[data-status="review"] {
  background: var(--warning-soft);
  color: var(--warning-text);
}

.admin-page__status-pill[data-status="banned"] {
  background: var(--danger-soft);
  color: var(--danger-text);
}

.admin-page__visibility-pill {
  background: rgba(29, 29, 31, 0.06);
  color: var(--text-main);
}

.admin-page__visibility-pill[data-visible="false"] {
  background: rgba(138, 36, 36, 0.1);
  color: var(--danger-text);
}

.admin-page__row-head,
.admin-page__row-summary,
.admin-page__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.admin-page__row-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.admin-page__row-eyebrow,
.admin-page__row-head h2,
.admin-page__row-head p,
.admin-page__row-summary p {
  margin: 0;
}

.admin-page__row-eyebrow {
  color: var(--brand-main);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.admin-page__row-identity {
  display: grid;
  gap: 4px;
}

.admin-page__row-head p,
.admin-page__row-summary p {
  color: var(--text-main);
  line-height: 1.7;
  max-width: 52ch;
}

.admin-page__row-email {
  color: var(--text-sub) !important;
  font-size: 0.84rem;
}

.admin-page__row-link,
.admin-page__save-button,
.admin-page__danger-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  font-weight: 700;
}

.admin-page__row-link {
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.82);
  color: var(--text-strong);
}

.admin-page__completeness {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  background: var(--brand-soft);
  text-align: center;
}

.admin-page__completeness strong,
.admin-page__completeness span {
  display: block;
}

.admin-page__completeness strong {
  color: var(--text-strong);
  font-size: 1.4rem;
}

.admin-page__completeness span {
  color: var(--text-sub);
  font-size: 0.78rem;
  font-weight: 700;
}

.admin-page__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.admin-page__chips span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(231, 237, 247, 0.9);
  color: var(--text-main);
  font-size: 0.82rem;
}

.admin-page__chips .admin-page__issue-chip {
  background: var(--warning-soft);
  color: var(--warning-text);
  font-weight: 700;
}

.admin-page__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 104px;
  gap: 12px;
}

.admin-page__control-field {
  min-width: 0;
}

.admin-page__control-field--wide {
  grid-column: 1 / -1;
}

.admin-page__toggle {
  position: relative;
  grid-column: 1 / -1;
  display: flex !important;
  align-items: center;
  justify-content: space-between;
  min-height: 46px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--bg-surface-solid);
  color: var(--text-main);
  cursor: pointer;
}

.admin-page__toggle input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.admin-page__toggle-track {
  order: 2;
  position: relative;
  width: 42px;
  height: 24px;
  border-radius: 999px;
  background: rgba(29, 29, 31, 0.16);
  transition: background-color 0.16s ease;
}

.admin-page__toggle-track::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-sm);
  transition: transform 0.16s ease;
}

.admin-page__toggle input:checked + .admin-page__toggle-track {
  background: var(--brand-main);
}

.admin-page__toggle input:checked + .admin-page__toggle-track::after {
  transform: translateX(18px);
}

.admin-page__toggle input:focus-visible + .admin-page__toggle-track {
  outline: 2px solid var(--brand-main);
  outline-offset: 2px;
}

.admin-page__save-button {
  border: none;
  background: var(--brand-main);
  color: #fff;
  min-width: 96px;
}

.admin-page__danger-button {
  border: 1px solid rgba(153, 27, 27, 0.28);
  background: var(--danger-soft);
  color: var(--danger-text);
}

.admin-page__danger-button:hover:not(:disabled) {
  border-color: var(--danger-text);
  background: var(--danger-text);
  color: var(--danger-soft);
}

.admin-page__danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.admin-page__risk-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
  padding-top: 2px;
}

.admin-page__save-button:hover {
  background: var(--brand-strong);
}

.admin-page__save-button:disabled {
  background: rgba(29, 29, 31, 0.1);
  color: var(--text-sub);
  cursor: not-allowed;
}

.admin-page__save-button:disabled:hover {
  background: rgba(29, 29, 31, 0.1);
}

.admin-page__actions p {
  margin: 0;
  font-weight: 600;
}

.admin-page__actions p[data-state="success"] {
  color: var(--success-text);
}

.admin-page__actions p[data-state="error"] {
  color: var(--danger-text);
}

@media (max-width: 980px) {
  .admin-page__row {
    grid-template-columns: 32px minmax(0, 1fr);
  }

  .admin-page__row-controls {
    grid-column: 2;
  }

  .admin-page__metrics,
  .admin-page__controls {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-page__filters,
  .admin-page__settings {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-page__department-manager {
    grid-template-columns: 1fr;
  }

  .admin-page__github-status {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-page__sticky-tools {
    position: static;
  }

  .admin-page__tool-strip {
    grid-template-columns: 1fr;
  }

  .admin-page__bulk-actions {
    justify-content: flex-start;
  }

  .admin-page__pagination {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-page__pagination div {
    justify-content: flex-start;
  }

  .admin-page__filter-menu .admin-page__filters {
    position: static;
    width: auto;
    margin-top: 10px;
    box-shadow: none;
  }
}

@media (max-width: 720px) {
  .admin-page__metrics,
  .admin-page__controls,
  .admin-page__filters,
  .admin-page__settings,
  .admin-page__department-add {
    grid-template-columns: 1fr;
  }

  .admin-page__settings-drawer summary,
  .admin-page__row-topline,
  .admin-page__row-head,
  .admin-page__row-summary,
  .admin-page__actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

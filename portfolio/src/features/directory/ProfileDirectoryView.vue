<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import ProfileCard from "./ProfileCard.vue";
import StatusView from "../../shared/ui/StatusView.vue";
import { JOB_OPTIONS } from "../../services/jobs";
import { listProfiles } from "../../services/profileService";
import {
  ALL_FILTER,
  buildDirectoryState,
  getInitialDirectoryFilters,
} from "./directoryFilters";

const props = defineProps({
  mode: {
    type: String,
    default: "public",
  },
});

const isLoading = ref(true);
const errorMessage = ref("");
const profiles = ref([]);
const filters = reactive(getInitialDirectoryFilters());

const heading = computed(() =>
  props.mode === "admin"
    ? {
        title: "관리자 디렉토리",
        body: "전체 프로필을 같은 카드 시스템 안에서 검토하고 상세 보기로 이동할 수 있습니다.",
      }
    : {
        title: "탐색 가능한 인재 디렉토리",
        body: "학교, 학과, 직무, 태그 필터로 필요한 프로필을 빠르게 찾을 수 있습니다.",
      },
);

const directoryState = computed(() => buildDirectoryState(profiles.value, filters));
const filteredProfiles = computed(() => directoryState.value.rows);
const filterOptions = computed(() => directoryState.value.options);

const resetFilters = () => {
  Object.assign(filters, getInitialDirectoryFilters());
};

const loadProfiles = async () => {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    profiles.value = await listProfiles();
  } catch (error) {
    errorMessage.value = error.message || "프로필을 불러오지 못했습니다.";
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadProfiles);
</script>

<template>
  <section class="directory-page">
    <div class="directory-hero">
      <div>
        <p class="directory-hero__eyebrow">
          {{ props.mode === "admin" ? "ADMIN MODE" : "DISCOVER TALENT" }}
        </p>
        <h2>{{ heading.title }}</h2>
        <p>{{ heading.body }}</p>
      </div>

      <div class="directory-summary">
        <strong>{{ filteredProfiles.length }}</strong>
        <span>현재 조건에 맞는 프로필</span>
      </div>
    </div>

    <section class="directory-toolbar">
      <label class="toolbar-search">
        <span>이름, 소개, 학교, 학과, 태그 검색</span>
        <input
          v-model="filters.search"
          type="text"
          placeholder="예: Vue, Web Contents, 프론트엔드"
        />
      </label>

      <div class="toolbar-jobs">
        <button
          type="button"
          class="filter-chip"
          :aria-pressed="filters.job === ALL_FILTER"
          :data-active="filters.job === ALL_FILTER"
          @click="filters.job = ALL_FILTER"
        >
          전체
        </button>
        <button
          v-for="job in JOB_OPTIONS"
          :key="job"
          type="button"
          class="filter-chip"
          :aria-pressed="filters.job === job"
          :data-active="filters.job === job"
          @click="filters.job = job"
        >
          {{ job }}
        </button>
      </div>

      <div class="directory-taxonomy-filters">
        <label>
          <span>학교</span>
          <select v-model="filters.school">
            <option :value="ALL_FILTER">전체 학교</option>
            <option v-for="school in filterOptions.schools" :key="school" :value="school">
              {{ school }}
            </option>
          </select>
        </label>

        <label>
          <span>학과</span>
          <select v-model="filters.department">
            <option :value="ALL_FILTER">전체 학과</option>
            <option
              v-for="department in filterOptions.departments"
              :key="department"
              :value="department"
            >
              {{ department }}
            </option>
          </select>
        </label>

        <label>
          <span>트랙</span>
          <select v-model="filters.track">
            <option :value="ALL_FILTER">전체 트랙</option>
            <option v-for="track in filterOptions.tracks" :key="track" :value="track">
              {{ track }}
            </option>
          </select>
        </label>

        <label>
          <span>태그</span>
          <select v-model="filters.tag">
            <option :value="ALL_FILTER">전체 태그</option>
            <option v-for="tag in filterOptions.tags" :key="tag" :value="tag">
              {{ tag }}
            </option>
          </select>
        </label>

        <label>
          <span>정렬</span>
          <select v-model="filters.sort">
            <option value="featured">추천순</option>
            <option value="latest">최신순</option>
            <option value="name">이름순</option>
            <option value="department">학과순</option>
          </select>
        </label>
      </div>

      <div class="directory-active-filters">
        <span>활성 필터 {{ directoryState.activeFilterCount }}개</span>
        <button type="button" class="filter-chip" @click="resetFilters">
          필터 초기화
        </button>
      </div>
    </section>

    <StatusView
      v-if="isLoading"
      title="프로필을 불러오는 중입니다."
      body="디렉토리 데이터를 가져오고 있습니다."
    />
    <StatusView
      v-else-if="errorMessage"
      state="error"
      title="디렉토리를 불러오지 못했습니다."
      :body="errorMessage"
    />
    <StatusView
      v-else-if="filteredProfiles.length === 0"
      state="empty"
      title="조건에 맞는 프로필이 없습니다."
      body="검색어를 지우거나 다른 학교, 학과, 직무, 태그 필터를 선택해 보세요."
    />

    <div v-else class="directory-grid">
      <ProfileCard
        v-for="profile in filteredProfiles"
        :key="profile.id"
        :profile="profile"
        :admin-mode="props.mode === 'admin'"
      />
    </div>
  </section>
</template>

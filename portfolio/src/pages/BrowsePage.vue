<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";

import StatusView from "../shared/ui/StatusView.vue";
import { buildStudentCardModel } from "../shared/catalog/studentProfileModel.js";
import { extractGithubUsername, getGithubCommitCounts } from "../services/githubCommitService";
import { JOB_OPTIONS } from "../services/jobs.js";
import { listProfiles } from "../services/profileService";
import {
  BROWSE_PAGE_SIZE,
  DEFAULT_BROWSE_SORT,
  browseSortLabels,
  buildBrowseState,
} from "../features/directory/browseDirectory";
import { buildDisplayImageSrcset, toDisplayImageUrl } from "../shared/media/imageUrls.js";

const isLoading = ref(true);
const errorMessage = ref("");
const profiles = ref([]);
const searchInput = ref(null);
const commitCounts = ref({});
const isLoadingCommitCounts = ref(false);
const commitCountMessage = ref("");
const currentPage = ref(1);
let commitCountRequestId = 0;

const filters = reactive({
  search: "",
  jobs: [],
  department: "",
  sort: DEFAULT_BROWSE_SORT,
});

const browseState = computed(() =>
  buildBrowseState({
    profiles: profiles.value,
    filters,
    commitCounts: commitCounts.value,
    currentPage: currentPage.value,
    pageSize: BROWSE_PAGE_SIZE,
  }),
);
const options = computed(() => ({
  jobs: JOB_OPTIONS,
  departments: browseState.value.options.departments,
}));
const filteredProfiles = computed(() => browseState.value.filteredProfiles);
const filteredCount = computed(() => browseState.value.filteredCount);
const totalPages = computed(() => browseState.value.totalPages);
const paginatedCards = computed(() =>
  browseState.value.paginatedProfiles.map((profile) => buildStudentCardModel(profile)),
);
const pageStart = computed(() => browseState.value.pageStart);
const pageEnd = computed(() => browseState.value.pageEnd);

const hasActiveFilters = computed(() =>
  Boolean(filters.search || filters.jobs.length || filters.department || filters.sort !== DEFAULT_BROWSE_SORT),
);

const activeFilterChips = computed(() => {
  const chips = [];
  filters.jobs.forEach((job) => chips.push({ key: `job:${job}`, type: "job", value: job, label: job }));
  if (filters.department) chips.push({ key: "department", label: filters.department });
  if (filters.sort !== DEFAULT_BROWSE_SORT) {
    chips.push({ key: "sort", label: browseSortLabels[filters.sort] || "Sort" });
  }
  return chips;
});

const buildEvidenceBadges = (card) => {
  const badges = [];
  if (card.github) badges.push("GitHub 연결");
  if (card.imageUrl) badges.push("사진 있음");
  if (card.reviewStatus === "approved") badges.push("승인됨");
  if (card.isVisible) badges.push("공개");
  return badges.slice(0, 4);
};

const loadCommitCounts = async () => {
  if (filters.sort !== "githubCommits" || isLoadingCommitCounts.value) {
    return;
  }

  const requestId = ++commitCountRequestId;
  const usernames = profiles.value.map((profile) => extractGithubUsername(profile.github)).filter(Boolean);
  if (!usernames.length) {
    commitCountMessage.value = "?? GitHub URL? ??? ???? ????.";
    commitCounts.value = {};
    return;
  }

  isLoadingCommitCounts.value = true;
  commitCountMessage.value = "";
  try {
    const nextCounts = await getGithubCommitCounts(usernames);
    if (requestId === commitCountRequestId) {
      commitCounts.value = nextCounts;
    }
  } catch (error) {
    if (requestId === commitCountRequestId) {
      commitCountMessage.value = error.message || "GitHub ??? ???? ?????.";
    }
  } finally {
    if (requestId === commitCountRequestId) {
      isLoadingCommitCounts.value = false;
    }
  }
};

const loadProfiles = async () => {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    profiles.value = await listProfiles();
    isLoading.value = false;
    void loadCommitCounts();
  } catch (error) {
    errorMessage.value = error.message || "?? ????? ??? ???? ?????.";
    isLoading.value = false;
  }
};

const resetFilters = () => {
  filters.search = "";
  filters.jobs = [];
  filters.department = "";
  filters.sort = DEFAULT_BROWSE_SORT;
  currentPage.value = 1;
};

const toggleJob = (job) => {
  filters.jobs = filters.jobs.includes(job)
    ? filters.jobs.filter((item) => item !== job)
    : [...filters.jobs, job];
};

const removeFilter = (chip) => {
  if (chip.type === "job") {
    filters.jobs = filters.jobs.filter((item) => item !== chip.value);
    return;
  }
  if (chip.key === "sort") {
    filters.sort = DEFAULT_BROWSE_SORT;
    return;
  }
  filters[chip.key] = "";
};

const clearSearch = () => {
  filters.search = "";
  searchInput.value?.focus();
};

const goToPage = (page) => {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value);
};

watch(() => filters.sort, loadCommitCounts);
watch(
  () => [filters.search, filters.jobs.join(","), filters.department, filters.sort],
  () => {
    currentPage.value = 1;
  },
);
watch(filteredCount, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
  if (currentPage.value !== browseState.value.safePage) {
    currentPage.value = browseState.value.safePage;
  }
});
onMounted(loadProfiles);
</script>

<template>
  <div class="browse-page">
    <section class="browse-hero">
      <div class="browse-hero__copy">
        <p class="browse-hero__eyebrow">서울디지텍고등학교</p>
        <h1>SDHS 학생 포트폴리오</h1>
        <p>이름, 희망 분야, 학과, 태그로 학생 작업을 찾고 공개된 프로필을 확인하세요.</p>
      </div>
      <div class="browse-hero__count">
        <strong>{{ filteredCount }}</strong>
        <span>개의 공개 프로필</span>
      </div>
    </section>

    <section class="browse-filters" aria-label="프로필 필터">
      <div class="browse-filters__search">
        <svg class="browse-filters__search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          ref="searchInput"
          v-model="filters.search"
          name="profile-search"
          type="text"
          placeholder="이름, 소개, 태그 검색"
        />
        <button
          v-if="filters.search"
          type="button"
          class="browse-filters__clear"
          aria-label="검색어 지우기"
          @click="clearSearch"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="browse-filters__selects">
        <select v-model="filters.department" name="department-filter" :class="{ active: filters.department }">
          <option value="">학과</option>
          <option v-for="department in options.departments" :key="department" :value="department">
            {{ department }}
          </option>
        </select>

        <select v-model="filters.sort" name="sort-filter" :class="{ active: filters.sort !== DEFAULT_BROWSE_SORT }">
          <option value="githubCommits">GitHub 활동순</option>
          <option value="featured">추천순</option>
          <option value="latest">최신순</option>
          <option value="name">이름순</option>
          <option value="department">학과순</option>
        </select>
      </div>
    </section>

    <section class="browse-job-filters" aria-label="희망 분야 필터">
      <button
        v-for="job in options.jobs"
        :key="job"
        type="button"
        class="browse-job-filter"
        :data-active="filters.jobs.includes(job)"
        :aria-pressed="filters.jobs.includes(job)"
        @click="toggleJob(job)"
      >
        {{ job }}
      </button>
    </section>

    <div class="browse-chips" v-if="activeFilterChips.length">
      <button
        v-for="chip in activeFilterChips"
        :key="chip.key"
        type="button"
        class="browse-chip"
        @click="removeFilter(chip)"
      >
        {{ chip.label }}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>

      <button
        v-if="hasActiveFilters"
        key="reset"
        type="button"
        class="browse-chip browse-chip--reset"
        @click="resetFilters"
      >
        모두 초기화
      </button>
    </div>

    <p v-if="!isLoading && !errorMessage && filteredProfiles.length > 0" class="browse-result-count">
      총 {{ filteredCount }}개 중 {{ pageStart }}-{{ pageEnd }}개 표시
      <template v-if="filters.sort === 'githubCommits'">
        / {{ isLoadingCommitCounts ? "GitHub 활동 불러오는 중" : "GitHub 활동 기준 정렬" }}
      </template>
    </p>
    <p v-if="commitCountMessage" class="browse-result-count browse-result-count--warning">
      {{ commitCountMessage }}
    </p>

    <section v-if="isLoading" class="browse-grid">
      <div v-for="n in 6" :key="n" class="browse-skeleton">
        <div class="browse-skeleton__image" />
        <div class="browse-skeleton__body">
          <div class="browse-skeleton__line browse-skeleton__line--title" />
          <div class="browse-skeleton__line browse-skeleton__line--meta" />
          <div class="browse-skeleton__line browse-skeleton__line--text" />
        </div>
      </div>
    </section>

    <StatusView
      v-else-if="errorMessage"
      state="error"
      title="???? ???? ?????."
      :body="errorMessage"
    />

    <section v-else-if="filteredProfiles.length === 0" class="browse-empty">
      <div class="browse-empty__icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </div>
      <h2>조건에 맞는 프로필이 없습니다.</h2>
      <p>검색어를 바꾸거나 필터를 초기화해 보세요.</p>
      <button
        v-if="hasActiveFilters"
        type="button"
        class="browse-empty__reset"
        @click="resetFilters"
      >
        필터 초기화
      </button>
    </section>

    <section v-else class="browse-grid">
      <RouterLink
        v-for="card in paginatedCards"
        :key="card.id"
        :to="`/profiles/${card.id}`"
        class="browse-card"
      >
        <div class="browse-card__image">
          <img
            v-if="card.imageUrl"
            :src="toDisplayImageUrl(card.imageUrl, { width: 164 })"
            :srcset="buildDisplayImageSrcset(card.imageUrl, [82, 164, 246])"
            sizes="82px"
            :alt="card.title"
            width="82"
            height="82"
            loading="lazy"
            decoding="async"
          />
          <span v-else class="browse-card__initial">{{ card.title.slice(0, 1) }}</span>
        </div>

        <div class="browse-card__body">
          <div class="browse-card__top">
            <h2>{{ card.title }}</h2>
            <span v-if="card.role" class="browse-card__role">{{ card.role }}</span>
          </div>
          <p v-if="card.metaLine" class="browse-card__meta">{{ card.metaLine }}</p>
          <p class="browse-card__summary">{{ card.summary || "?? ??? ????." }}</p>
          <ul v-if="card.tags.length" class="browse-card__tags">
            <li v-for="tag in card.tags" :key="tag">{{ tag }}</li>
          </ul>
          <ul class="browse-card__evidence" aria-label="Profile evidence">
            <li v-for="badge in buildEvidenceBadges(card)" :key="badge">{{ badge }}</li>
          </ul>
          <p v-if="filters.sort === 'githubCommits'" class="browse-card__commits">
            GitHub ?쒕룞 {{ Number(card.githubCommitCount || 0).toLocaleString() }}
          </p>
        </div>

        <div class="browse-card__footer">
          <span>??? ??</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </div>
      </RouterLink>
    </section>

    <nav v-if="!isLoading && !errorMessage && totalPages > 1" class="browse-pagination" aria-label="??? ???">
      <button type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
        ??
      </button>
      <span>{{ currentPage }} / {{ totalPages }}</span>
      <button type="button" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
        ?ㅼ쓬
      </button>
    </nav>
  </div>
</template>

<style scoped>
.browse-page {
  display: grid;
  gap: 18px;
}

.browse-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 0 8px;
  overflow: hidden;
}

.browse-hero__copy {
  display: grid;
  gap: 8px;
}

.browse-hero__eyebrow {
  margin: 0;
  color: var(--brand-main);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.browse-hero__copy h1 {
  max-width: 720px;
  margin: 0;
  font-size: clamp(2rem, 3.2vw, 2.8rem);
  font-weight: 750;
  letter-spacing: 0;
  line-height: 1;
}

.browse-hero__copy p {
  max-width: 62ch;
  margin: 0;
  color: var(--text-sub);
  font-size: 1.02rem;
}

.browse-hero__count {
  display: grid;
  text-align: right;
  gap: 4px;
  flex-shrink: 0;
  min-width: 170px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--card);
  box-shadow: var(--shadow-sm);
}

.browse-hero__count strong {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-strong);
  letter-spacing: 0;
  line-height: 1;
}

.browse-hero__count span {
  color: var(--text-sub);
  font-size: 0.82rem;
}

.browse-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: var(--radius-lg);
  background: var(--card);
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-sm);
}

.browse-filters__search {
  position: relative;
  flex: 1;
  min-width: 160px;
}

.browse-filters__search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-sub);
  pointer-events: none;
}

.browse-filters__search input {
  padding-left: 36px;
  padding-right: 36px;
  border: 1px solid var(--line-soft);
  background: var(--bg-surface-solid);
  border-radius: var(--radius-sm);
  height: 40px;
}

.browse-filters__search input:focus {
  background: var(--bg-surface-solid);
  box-shadow: 0 0 0 2px var(--brand-ring);
}

.browse-filters__clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-xs);
  background: var(--card);
  color: var(--text-sub);
  cursor: pointer;
}

.browse-filters__clear:hover {
  background: var(--muted);
  color: var(--text-strong);
}

.browse-filters__selects {
  display: flex;
  gap: 8px;
}

.browse-filters__selects select {
  width: auto;
  min-width: 80px;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  background: var(--bg-surface-solid);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-size: 0.88rem;
  cursor: pointer;
}

.browse-filters__selects select.active {
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-weight: 600;
  border-color: var(--brand-main);
}

.browse-filters__selects select:focus {
  background: var(--bg-surface-solid);
  box-shadow: 0 0 0 2px var(--brand-ring);
}

.browse-job-filters,
.browse-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.browse-job-filter {
  min-height: 34px;
  padding: 0 13px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-main);
  font-size: 0.82rem;
  font-weight: 700;
}

.browse-job-filter[data-active="true"] {
  border-color: var(--brand-main);
  background: var(--brand-main);
  color: #fff;
}

.browse-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.browse-chip:hover {
  background: var(--brand-main);
  color: #fff;
}

.browse-chip--reset {
  background: var(--card);
  border-color: var(--line-soft);
  color: var(--text-sub);
}

.browse-chip--reset:hover {
  background: var(--muted);
  color: var(--text-strong);
}

.browse-result-count {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.84rem;
  font-weight: 500;
}

.browse-result-count--warning {
  color: var(--warning-text);
  font-weight: 700;
}

.browse-skeleton {
  justify-self: center;
  width: 100%;
  max-width: 280px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
  overflow: hidden;
}

.browse-skeleton__image {
  width: 96px;
  height: 96px;
  margin: 20px auto 4px;
  border-radius: var(--radius-lg);
  background: var(--muted);
}

.browse-skeleton__body {
  padding: 16px 18px 20px;
  display: grid;
  gap: 10px;
}

.browse-skeleton__line {
  border-radius: 6px;
  background: #f0f0f2;
}

.browse-skeleton__line--title {
  width: 60%;
  height: 18px;
}

.browse-skeleton__line--meta {
  width: 40%;
  height: 14px;
}

.browse-skeleton__line--text {
  width: 90%;
  height: 14px;
}

.browse-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 24px;
  text-align: center;
}

.browse-empty__icon {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
  display: grid;
  place-items: center;
  color: var(--text-sub);
  margin-bottom: 8px;
}

.browse-empty h2 {
  margin: 0;
  font-size: 1.2rem;
  letter-spacing: 0;
}

.browse-empty p {
  margin: 0;
  color: var(--text-sub);
  font-size: 0.92rem;
}

.browse-empty__reset {
  margin-top: 4px;
  height: 36px;
  padding: 0 20px;
  border: 1px solid var(--brand-main);
  border-radius: var(--radius-sm);
  background: var(--brand-main);
  color: #fff;
  font-size: 0.86rem;
  font-weight: 600;
}

.browse-empty__reset:hover {
  background: var(--brand-strong);
}

.browse-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.browse-card {
  justify-self: center;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 340px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface-solid);
  border: 1px solid var(--line-soft);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
  content-visibility: auto;
  contain-intrinsic-size: auto 390px;
}

.browse-card:hover {
  border-color: var(--line-strong);
  box-shadow: var(--shadow-hover);
}

.browse-card:focus-visible {
  outline: 2px solid var(--brand-main);
  outline-offset: 2px;
}

.browse-card__image {
  width: 82px;
  height: 82px;
  margin: 18px auto 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--muted);
  border: 1px solid var(--line-soft);
  display: grid;
  place-items: center;
}

.browse-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.browse-card__initial {
  font-size: 2rem;
  font-weight: 700;
  color: var(--brand-strong);
  opacity: 0.9;
}

.browse-card__body {
  padding: 14px 18px 12px;
  display: grid;
  gap: 8px;
  flex: 1;
}

.browse-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.browse-card__top h2,
.browse-card__meta,
.browse-card__summary,
.browse-card__commits {
  margin: 0;
}

.browse-card__top h2 {
  font-size: 1.08rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
}

.browse-card__role {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: var(--radius-xs);
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 0.74rem;
  font-weight: 600;
}

.browse-card__meta {
  color: var(--text-sub);
  font-size: 0.84rem;
}

.browse-card__summary {
  color: var(--text-main);
  font-size: 0.9rem;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.browse-card__tags,
.browse-card__evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0;
  margin: 4px 0 0;
  list-style: none;
}

.browse-card__tags li {
  padding: 3px 8px;
  border-radius: var(--radius-xs);
  background: var(--muted);
  color: var(--text-main);
  font-size: 0.74rem;
  font-weight: 500;
}

.browse-card__evidence li {
  padding: 3px 8px;
  border-radius: var(--radius-xs);
  background: var(--success-soft);
  color: var(--success-text);
  font-size: 0.72rem;
  font-weight: 700;
}

.browse-card__commits {
  color: var(--brand-strong);
  font-size: 0.82rem;
  font-weight: 800;
}

.browse-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  border-top: 1px solid var(--line-soft);
  color: var(--brand-strong);
  font-size: 0.82rem;
  font-weight: 600;
  transition: background-color 0.15s ease;
}

.browse-card:hover .browse-card__footer {
  background: var(--muted);
}

.browse-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0 4px;
}

.browse-pagination button {
  min-height: 36px;
  padding: 0 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-surface-solid);
  color: var(--text-strong);
  font-weight: 700;
}

.browse-pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.browse-pagination span {
  color: var(--text-sub);
  font-size: 0.88rem;
  font-weight: 800;
}

@media (max-width: 1024px) {
  .browse-filters {
    flex-wrap: wrap;
  }

  .browse-filters__selects {
    flex-wrap: wrap;
  }

  .browse-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }
}

@media (max-width: 640px) {
  .browse-hero {
    flex-direction: column;
    align-items: flex-start;
    padding: 32px 0 4px;
  }

  .browse-hero__count {
    text-align: left;
  }

  .browse-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .browse-filters__selects {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .browse-grid {
    grid-template-columns: 1fr;
  }

  .browse-card,
  .browse-skeleton {
    max-width: none;
  }
}
</style>

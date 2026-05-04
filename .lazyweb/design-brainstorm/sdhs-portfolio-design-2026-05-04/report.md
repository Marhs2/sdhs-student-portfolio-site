# Design Brainstorm: SDHS Student Portfolio Site

## TL;DR

지금 가장 큰 디자인 개선점은 장식이 아니라 "학생을 탐색하는 사람"과 "포트폴리오를 작성하는 학생"의 흐름을 분리해 더 선명하게 만드는 것이다. 먼저 깨진 한국어 UI 문자열을 복구하고, 그 다음 디렉터리는 채용/파트너 매칭처럼 스캔 가능하게, 프로필은 음악 앱의 아티스트 페이지처럼 작품 중심으로, 작성 화면은 제품 온보딩 체크리스트처럼 진행형으로 바꾸는 것이 효율적이다.

## Current State From Code

현재 앱은 Vue/Vite 기반이며 주요 화면은 `BrowsePage.vue`, `StudentProfilePage.vue`, `StudioPage.vue`, `AdminCurationPage.vue`로 나뉜다. 구조 자체는 나쁘지 않다. 디렉터리에는 검색, 학과, 직무, 정렬, 페이지네이션이 있고, 프로필에는 대표 프로젝트와 전체 프로젝트가 있으며, 스튜디오에는 완성도 퍼센트와 작성 섹션 이동이 있다.

하지만 현재 화면 코드의 한국어 텍스트가 다수 깨져 있다. 예: 버튼, 안내문, 상태 메시지, 제목이 mojibake 상태라 사용자는 기능을 이해하기 전에 신뢰를 잃는다. 디자인 개선은 색상이나 카드 모양보다 이 텍스트 복구와 정보 구조 재정렬이 먼저다.

## Which Ideas to Prototype

| Idea | Novelty | Feasibility | Verdict |
|------|---------|-------------|---------|
| 디렉터리를 "학생 카드 갤러리"가 아니라 "매칭 가능한 인재 탐색 화면"으로 재구성 | Medium | High | Prototype |
| 프로필 페이지를 음악 앱 아티스트 페이지처럼 대표작, 활동, 기술, 링크가 한눈에 보이는 쇼케이스로 전환 | High | Medium | Prototype |
| 작성 스튜디오를 체크리스트형 진행 화면으로 정리하고, 저장 전 누락/품질 상태를 지속 표시 | Medium | High | Prototype |
| 프로젝트를 앨범/디스코그래피처럼 탭과 정렬이 있는 작품 목록으로 표현 | High | Medium | Explore |
| 학생이 공개 프로필 섹션 순서를 직접 조정하는 "프로필 레이아웃 커스터마이저" | High | Low | Wild Card |

## The Obvious Approach

교육/포트폴리오 사이트의 흔한 패턴은 큰 소개문, 카드 그리드, 필터 몇 개, 개별 상세 페이지다. 현재 사이트도 이 축에 가깝다. 이 방식은 구현이 쉽고 예측 가능하지만, 학생의 강점이나 프로젝트 맥락이 빠르게 드러나지 않는다.

![Codecademy projects reference](references/codecademy-projects.png)
*Codecademy Projects - 프로젝트 카드에 난이도, 주제, 언어, 시간 같은 판단 단서를 함께 붙이는 교육형 프로젝트 탐색 패턴 [Lazyweb]*

## Cross-Pollination Ideas

### From Business Directories: Asana Partner Directory

![Asana partner directory reference](references/asana-partner-directory.png)
*Asana Partner Directory - 검색, 다중 필터, 상태 배지, 카드형 전문가 목록을 결합한 매칭 디렉터리 [Lazyweb]*

**The Pattern:** 사람을 단순 목록으로 보여주지 않고, 선택에 필요한 판단 단서와 상태를 카드 표면에 올린다. 필터는 왼쪽이나 상단에 붙이고, 결과 카드는 "누가 어떤 상황에 맞는가"를 빠르게 비교하게 만든다.

**Applied Here:** `BrowsePage.vue`의 학생 카드는 이름, 직무, 학과, 태그만 보여주는 대신 "대표 프로젝트 있음", "GitHub 연결됨", "영상 포함", "관리자 승인됨", "최근 업데이트" 같은 신뢰 단서를 카드 하단에 배치한다. 필터는 직무 칩만 나열하지 말고 `개발`, `디자인`, `영상`, `하드웨어`, `팀 프로젝트`, `GitHub 있음` 같은 실제 탐색 의도 중심으로 묶는다.

**Why It's a Zag:** 학교 포트폴리오 사이트는 보통 작품 전시처럼 보인다. 이 패턴은 교사, 심사자, 외부 방문자가 학생을 목적에 맞게 찾는 "탐색 도구"로 바꾼다.

**Sketch:**

```text
+------------------------------------------------------+
| Search students, projects, tags          [Sort: fit] |
+----------------------+-------------------------------+
| Track                | [Kim Minseo]  Frontend         |
| [x] Web              | Dept: Software  GitHub linked  |
| [ ] Design           | Tags: Vue, API, UI             |
| [x] Has project      | Evidence: 3 projects, video    |
| [ ] GitHub only      | [Open profile]                 |
+----------------------+-------------------------------+
```

### From Music Apps: Artist Profile And Discography

![Deezer discography reference](references/deezer-discography.png)
*Deezer discography - 작품을 앨범, EP, 싱글처럼 탭으로 나누고 커버 이미지와 연도, 수량, 정렬을 붙이는 목록 패턴 [Lazyweb]*

**The Pattern:** 제작자의 정체성은 상단에서 짧게 잡고, 핵심은 작품 목록과 활동 증거로 이어진다. 탭은 단순 분류가 아니라 "어떤 작품을 볼 것인가"를 빠르게 바꾸는 탐색 장치다.

**Applied Here:** `StudentProfilePage.vue`의 대표 프로젝트와 전체 프로젝트를 유지하되, `Featured`, `Web`, `Video`, `GitHub`, `Team` 같은 탭을 추가한다. 프로젝트 카드에는 설명보다 먼저 결과물 이미지, 역할, 기여도, 링크 상태를 배치한다. 프로필 헤더는 사진, 이름, 목표 직무, 1문장 소개, 핵심 태그만 남겨 더 단단하게 만든다.

**Why It's a Zag:** 학생 포트폴리오는 보통 자기소개가 길고 프로젝트는 아래로 밀린다. 음악 앱 패턴은 "이 학생이 실제로 만든 것"을 더 빨리 보여준다.

**Sketch:**

```text
+------------------------------------------------------+
| [Photo] Kim Minseo                [GitHub] [Contact] |
| Frontend Developer | Vue, FastAPI, UI Polish          |
| Builds school tools with careful UX and auth flows.  |
+------------------------------------------------------+
| Featured | Web | Video | GitHub | Team               |
+------------------------------------------------------+
| [Project image]  Student Portfolio Platform          |
| Role: Frontend + API integration | 2026              |
| Evidence: live site, repo, 4 screenshots             |
+------------------------------------------------------+
```

### From Productivity Dashboards: Checklist Quality Strip

![Field/productivity dashboard reference](references/genie-profile-timeline.png)
*Genie/AppNation about page - 상단 핵심 지표와 타임라인을 함께 보여주는 진행/맥락 표현 [Lazyweb]*

**The Pattern:** 사용자가 지금 어떤 상태에 있고 무엇을 해야 하는지 상단에 고정한다. 긴 폼을 무작정 나열하지 않고, 현재 완성도, 누락 항목, 다음 작업을 지속적으로 보여준다.

**Applied Here:** `StudioPage.vue`에는 이미 완성도 퍼센트와 품질 메뉴가 있다. 이것을 더 강하게 밀어 "작성 커맨드 바"로 만든다. 상단에는 `72%`, `공개 가능`, `GitHub 필요`, `대표 프로젝트 없음`을 보여주고, 아래 섹션은 기본 정보, 이미지, 프로젝트, 상세 소개로 접을 수 있게 한다. 저장 버튼은 섹션별로 흩어두기보다 상단과 현재 섹션 하단에 일관되게 둔다.

**Why It's a Zag:** 포트폴리오 작성 화면을 CMS 폼처럼 만들지 않고, 제출 전 품질을 관리하는 작업대처럼 만든다.

**Sketch:**

```text
+------------------------------------------------------+
| 72% complete | Needs: GitHub, 1 featured project      |
| [Basic done] [Image done] [Projects 1/3] [Details]   |
|                                        [Save draft]  |
+------------------------------------------------------+
| Basic profile                                        |
| Name       [________________]                        |
| Role       [Frontend Developer v]                    |
| Intro      [____________________________________]     |
+------------------------------------------------------+
```

### From Collection Customizers: Section Order Control

![Vinyls layout customization reference](references/vinyls-layout-customization.png)
*Vinyls - 앨범 상세 화면의 섹션을 드래그로 재정렬하거나 숨기는 커스터마이징 패턴 [Lazyweb]*

**The Pattern:** 모든 사용자에게 같은 상세 페이지 순서를 강요하지 않는다. 사용자가 자신에게 중요한 섹션을 위로 올리고 불필요한 섹션은 숨긴다.

**Applied Here:** 학생이 공개 프로필의 섹션 순서를 `대표 프로젝트`, `전체 프로젝트`, `상세 소개`, `기술 태그`, `GitHub` 순으로 직접 고를 수 있게 한다. 단, 초기 버전에서는 실제 드래그 기능보다 "대표 프로젝트 먼저 / 소개 먼저" 같은 2-3개 프리셋이 더 안전하다.

**Why It's a Zag:** 학생마다 강점이 다르다. 디자인 학생은 이미지가 먼저, 개발 학생은 GitHub/프로젝트가 먼저, 영상 학생은 비디오가 먼저일 수 있다.

**Sketch:**

```text
+---------------- Profile layout ----------------------+
| [1] Featured project              [move] [hide]       |
| [2] Project gallery               [move] [hide]       |
| [3] About and process notes        [move] [hide]       |
| [4] Skills and tags                [move] [hide]       |
| [Preview public page]                         [Save]  |
+------------------------------------------------------+
```

## Immediate Design Fixes

1. **Fix all mojibake Korean text first.** Broken labels currently make the UI look unfinished even where layout is sound.
2. **Reduce card-on-card density.** The app already uses many surfaces and cards. Keep page sections flatter and reserve cards for repeated profile/project items.
3. **Make the browse page more comparative.** Add evidence badges and stronger filter grouping so users can decide without opening every profile.
4. **Give project media more visual priority.** Student work should feel like the primary artifact, not an attachment under the bio.
5. **Use one restrained secondary accent.** The current blue system is clean but one-note. Add a small green/amber status language for approval, completeness, and needs-work states.
6. **Make mobile filters collapsible.** On small screens, search first, then a compact "Filters" button, then active chips. Avoid showing every filter before results.

## Wild Cards

### Weekly Showcase Mode

Borrow from recap/playlist patterns: the home page could show "This week's featured work" with 3-5 curated projects, not just a directory. This makes the site feel alive and gives students a reason to keep profiles current. Risk: it needs curation rules or admin effort.

### Reviewer Mode

Borrow from hiring/recruiting tools: add a private admin/reviewer view that compares students by completeness, project count, GitHub presence, and review status. This is less public-facing but could make school operations much smoother.

## Sources

- Lazyweb: Codecademy Projects screenshot, Education category.
- Lazyweb: Asana Partner Directory screenshot, Business category.
- Lazyweb: Deezer discography screenshot, Music category.
- Lazyweb: Genie/AppNation profile timeline screenshot, Productivity category.
- Lazyweb: Vinyls layout customization screenshot, Music category.
- Web research: [Webflow student portfolio examples](https://webflow.com/blog/student-portfolio-examples), [Portfolial directory](https://www.portfolial.com/directory/), [Dashboard UX Checklist](https://biblueprint.com/resources/dashboard-checklist), [Creative Bloq portfolio examples](https://www.creativebloq.com/portfolios/examples-712368).

# Portfolio Frontend

Vue 3 + Vite 기반의 학생 포트폴리오 프론트엔드입니다. 루트 프로젝트의 `npm run dev`를 쓰면 백엔드와 함께 실행되고, 이 폴더에서는 프론트엔드만 독립 실행할 수 있습니다.

## Commands

```powershell
npm install
npm run dev
npm run test
npm run build
npm run preview
```

- Dev server: `http://127.0.0.1:5173`
- Build output: `dist/`
- Tests: Node test runner로 `src/**/*.test.js` 실행

## Environment

로컬 개발 환경변수는 `portfolio/.env.local`에 둡니다.

```text
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_BASE_URL=http://127.0.0.1:8000
```

`VITE_API_BASE_URL`은 FastAPI 백엔드 주소입니다. 배포 빌드에서는 Vercel 또는 Northflank의 build-time environment variable로 넣어야 합니다.

## Project Layout

```text
src/
  app/          앱 셸
  features/     directory, profile, admin 등 도메인 기능
  pages/        라우트 단위 페이지
  router/       Vue Router 설정과 route manifest
  services/     API, Supabase, auth, profile 서비스
  shared/       공용 UI, layout, catalog helper
  styles/       토큰과 도메인별 CSS
```

라우트는 `src/router/index.js`에서 관리합니다. route ownership을 바꾸거나 페이지 파일을 삭제하기 전에는 `src/router/routeManifest.js`와 테스트를 함께 확인합니다.

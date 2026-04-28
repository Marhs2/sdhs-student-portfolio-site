# Portfolio Directory

한국어 우선 포트폴리오 디렉토리입니다.  
프런트엔드는 Vue 3 + Vite, 백엔드는 FastAPI + Supabase로 구성되어 있습니다.

## Architecture

- Frontend: `portfolio/`
- Backend: `backend/`
- API surface: `/api/*`
- Frontend routes:
  - `/`
  - `/profiles/:id`
  - `/me/edit`
  - `/portfolio-items/:id/edit`
  - `/admin`
  - `/auth/callback`

## Required Environment Variables

### Frontend

```text
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
VITE_API_BASE_URL
```

로그인과 가입은 서울디지텍고등학교 Google 계정만 허용합니다. 앱 서버는
`@sdh.hs.kr` 이메일만 인증 사용자로 인정하며, Supabase 대시보드에서도 Google
provider의 허용 도메인을 `sdh.hs.kr`로 제한해야 OAuth 계정 생성 단계까지 막을
수 있습니다.

### Backend

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
PORTFOLIO_ALLOWED_ORIGINS
PORTFOLIO_ALLOWED_ORIGIN_REGEX
PORTFOLIO_ADMIN_EMAILS
PORTFOLIO_MAX_UPLOAD_BYTES
PORTFOLIO_PUBLIC_CACHE_TTL_SECONDS
PORTFOLIO_PUBLIC_CACHE_STALE_SECONDS
GITHUB_TOKEN
PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS
```

샘플 값은 [backend/.env.example](backend/.env.example) 에 있습니다.

`PORTFOLIO_ADMIN_EMAILS` 는 쉼표로 구분한 `@sdh.hs.kr` 관리자 이메일 목록입니다.
여기에 등록된 계정은 아직 프로필이 없거나 DB의 `isAdmin` 값이 꺼져 있어도
관리자 화면에 접근할 수 있습니다.

`PORTFOLIO_PUBLIC_CACHE_TTL_SECONDS` 는 공개 목록 API의 서버 내부 캐시 시간입니다.
기본값은 `30` 입니다. `PORTFOLIO_PUBLIC_CACHE_STALE_SECONDS` 는 Supabase가 잠깐
실패할 때 최근 공개 응답을 유지하는 시간이며 기본값은 `300` 입니다.

`GITHUB_TOKEN` 은 GitHub GraphQL 활동 수 조회에 쓰는 서버 전용 토큰입니다.
프론트에는 노출하지 않습니다. `PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS` 는
GitHub 사용자별 활동 수 캐시 시간이며 기본값은 `900` 입니다.

## Local Development

저장소 루트에서 실행:

```powershell
npm run dev
```

이 스크립트는 다음을 실행합니다.

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

### Local-only test Supabase

테스트 Supabase 프로젝트 `lbayyiylxjvqhcqejvkr`는 로컬에서만 쓰도록 코드에서 막아두었습니다.

- 프론트가 `https://lbayyiylxjvqhcqejvkr.supabase.co`를 쓰면서 `localhost`, `127.0.0.1`, `::1`이 아닌 곳에서 실행되면 즉시 중단됩니다.
- 백엔드가 같은 테스트 Supabase를 쓰면서 `PORTFOLIO_ALLOWED_ORIGINS`에 로컬이 아닌 origin이 들어 있으면 시작하지 않습니다.
- 테스트 키는 `portfolio/.env.local`, `backend/.env.local` 같은 로컬 파일에만 넣고 배포 환경변수에는 넣지 마세요.

로컬 프론트 예시:

```text
VITE_SUPABASE_URL=https://lbayyiylxjvqhcqejvkr.supabase.co
VITE_SUPABASE_ANON_KEY=<test anon key>
VITE_API_BASE_URL=http://127.0.0.1:8000
```

로컬 백엔드 예시:

```text
SUPABASE_URL=https://lbayyiylxjvqhcqejvkr.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<rotated test service role key>
PORTFOLIO_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
PORTFOLIO_ALLOWED_ORIGIN_REGEX=
PORTFOLIO_ADMIN_EMAILS=<local test admin email>
PORTFOLIO_MAX_UPLOAD_BYTES=5242880
GITHUB_TOKEN=<github token for commit count lookup>
PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS=900
```

권장 Python 설정:

```powershell
C:\Python313\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

다른 Python 경로를 쓸 경우:

```powershell
$env:PORTFOLIO_PYTHON = "C:\Python313\python.exe"
npm run dev
```

## Deploy

### Northflank

이 저장소는 루트에 실행 가능한 기본 웹 프로세스가 없습니다. Northflank에서
`failed to launch: determine start command: when there is no default process a command is required`
가 나오면 서비스가 repo root를 buildpack으로 빌드했지만 실행 명령을 찾지 못한
상태입니다.

권장 구성은 프론트엔드와 백엔드를 별도 서비스로 배포하는 방식입니다.

#### Frontend service

- Build option: Dockerfile
- Build context: `portfolio`
- Dockerfile path: `portfolio/Dockerfile`
- Public port: `8080`
- Health check path: `/health`
- Build arguments:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_API_BASE_URL`

`VITE_API_BASE_URL` 은 Northflank 백엔드 서비스의 공개 URL을 가리켜야 합니다.
Vite 환경변수는 정적 빌드 시점에 주입되므로 runtime variable만 넣으면 프론트
번들에 반영되지 않습니다.

#### Backend service

- Build option: Dockerfile
- Build context: `backend`
- Dockerfile path: `backend/Dockerfile`
- Public port: `8080`
- Runtime variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `PORTFOLIO_ALLOWED_ORIGINS`
  - `PORTFOLIO_ALLOWED_ORIGIN_REGEX`
  - `PORTFOLIO_ADMIN_EMAILS`
  - `PORTFOLIO_MAX_UPLOAD_BYTES`

`PORTFOLIO_ALLOWED_ORIGINS` 에는 Northflank 프론트엔드 공개 URL을 포함해야 합니다.

Buildpack을 계속 쓸 경우에는 command override를 직접 지정해야 합니다.

- Frontend root: `portfolio`
- Frontend build command: `npm ci && npm run build`
- Frontend start command: `sh -c 'npm run preview -- --host 0.0.0.0 --port ${PORT:-8080}'`
- Backend root: `backend`
- Backend build command: `pip install -r requirements.txt`
- Backend start command: `sh -c 'python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}'`

### Vercel

- Root Directory: repository root
- Install Command: `vercel.json` 사용
- Build Command: `vercel.json` 사용
- Output Directory: `vercel.json` 사용

`VITE_API_BASE_URL` 는 Render 백엔드 URL을 가리켜야 합니다.

### Render

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- `PORTFOLIO_ALLOWED_ORIGINS`:
  `https://portfoilo-s-ite-rsgx.vercel.app,https://portfoilo-site-fullstack.vercel.app,http://127.0.0.1:5173,http://localhost:5173`
- `PORTFOLIO_ALLOWED_ORIGIN_REGEX`:
  `https://portfoilo-s-ite-[a-z0-9-]+(?:-[a-z0-9-]+)*\.vercel\.app`

Render 대시보드에 기존 Start Command가 남아 있으면 `render.yaml`보다 그 값이
먼저 적용될 수 있습니다. `python uvicorn main:app --reload`가 보이면 위 명령으로
교체하고, 운영 배포에서는 `--reload`를 사용하지 않습니다.

# SDHS Student Portfolio Site

서울디지텍고 학생 포트폴리오를 검색, 열람, 작성, 관리하는 웹 서비스입니다.
프론트엔드는 Vue 3 + Vite, 백엔드는 FastAPI + Supabase로 구성되어 있습니다.

## 구성

- Frontend: `portfolio/`
- Backend: `backend/`
- API: FastAPI 서버의 `/api/*`
- Database/Auth/Storage: Supabase
- Deployment: Vercel(frontend), Render 또는 Northflank(backend)

주요 화면은 다음 라우트에서 확인합니다.

| Route | Purpose |
| --- | --- |
| `/` | 학생 포트폴리오 목록과 검색/필터 |
| `/profiles/:id` | 학생 공개 프로필 상세 |
| `/me/edit` | 로그인한 사용자의 프로필 작성/수정 |
| `/profiles/:id/edit` | 특정 프로필 수정 |
| `/admin` | 관리자 큐레이션 화면 |
| `/server-admin` | 서버 관리자 권한/정책 관리 |
| `/auth/callback` | Supabase OAuth 콜백 |

## 빠른 시작

### 1. 의존성 설치

```powershell
npm install
npm --prefix portfolio install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

Python 실행 파일이 여러 개라면 먼저 가상환경을 활성화하거나, 실행 전에 원하는 Python을 지정합니다.

```powershell
$env:PORTFOLIO_PYTHON = "C:\Python313\python.exe"
```

### 2. 환경변수 준비

백엔드는 `backend/.env`를 읽습니다. 예시는 `backend/.env.example`을 기준으로 복사해서 채웁니다.

```powershell
Copy-Item .\backend\.env.example .\backend\.env
```

프론트엔드는 `portfolio/.env.local`에 Vite 환경변수를 둡니다.

```text
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. 로컬 서버 실행

루트에서 한 번에 실행합니다.

```powershell
npm run dev
```

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

개별 실행도 가능합니다.

```powershell
npm run frontend:dev
npm run backend:dev
```

## 환경변수

### Frontend

| Name | Required | Description |
| --- | --- | --- |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Yes | Browser에서 사용하는 Supabase anon key |
| `VITE_API_BASE_URL` | Recommended | FastAPI 서버 URL. 로컬은 `http://127.0.0.1:8000` |
| `VITE_ENABLE_SUPABASE_IMAGE_TRANSFORMS` | No | Supabase image transform endpoint가 활성화된 프로젝트에서만 `true`로 설정 |

배포 환경에서 `VITE_API_BASE_URL`을 비워두면 프론트엔드는 기본 프로덕션 API URL을 사용합니다. 단, 새 백엔드 URL로 옮기면 Vercel 환경변수도 함께 갱신해야 합니다. Vite 환경변수는 빌드 시점에 번들에 포함되므로 runtime variable만 바꿔서는 기존 빌드에 반영되지 않습니다.

### Backend

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `SUPABASE_AUTH_URL` | Recommended | `SUPABASE_URL` | OAuth/Auth 토큰 검증용 Supabase project URL |
| `SUPABASE_AUTH_SERVICE_ROLE_KEY` | Recommended | `SUPABASE_SERVICE_ROLE_KEY` | Auth 토큰 검증용 service role key. 클라이언트에 노출 금지 |
| `SUPABASE_DB_URL` | Recommended | `SUPABASE_URL` | 프로필/포트폴리오/스토리지 접근용 Supabase project URL. 로컬 Supabase는 `http://127.0.0.1:54321` |
| `SUPABASE_DB_SERVICE_ROLE_KEY` | Recommended | `SUPABASE_SERVICE_ROLE_KEY` | DB/Storage 접근용 service role key. 클라이언트에 노출 금지 |
| `SUPABASE_URL` | Legacy | - | Auth와 DB가 같은 프로젝트일 때 쓰는 기존 공통 Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Legacy | - | Auth와 DB가 같은 프로젝트일 때 쓰는 기존 공통 service role key |
| `PORTFOLIO_ALLOWED_ORIGINS` | Recommended | `http://127.0.0.1:5173,http://localhost:5173` | CORS 허용 origin 목록 |
| `PORTFOLIO_ALLOWED_ORIGIN_REGEX` | No | empty | 추가 허용 origin 정규식. 공유 `vercel.app` 전체 wildcard는 차단됨 |
| `PORTFOLIO_ADMIN_EMAILS` | Recommended | empty | 서버 관리자 이메일 목록. 쉼표로 구분 |
| `PORTFOLIO_MAX_UPLOAD_BYTES` | No | `1048576` | 업로드 이미지 최대 크기 |
| `PORTFOLIO_UPLOAD_DIR` | No | `backend/uploads` | 로컬 이미지 업로드 저장 디렉터리. Docker 배포는 `/app/uploads` volume 사용 |
| `PORTFOLIO_PUBLIC_CACHE_TTL_SECONDS` | No | `30` | 공개 목록 서버 캐시 TTL |
| `PORTFOLIO_PUBLIC_CACHE_STALE_SECONDS` | No | `300` | Supabase 장애 시 stale 공개 응답 유지 시간 |
| `GITHUB_TOKEN` | Optional | empty | GitHub 커밋 수 조회용 서버 토큰 |
| `PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS` | No | `900` | GitHub 커밋 수 조회 캐시 TTL |
| `PORTFOLIO_KEEPALIVE_URL` | No | empty | 설정하면 백엔드가 이 URL을 주기적으로 GET 호출. Render Free sleep 완화용 `/health` URL |
| `PORTFOLIO_KEEPALIVE_INTERVAL_SECONDS` | No | `600` | keepalive 호출 간격. 최소 60초로 제한 |

`PORTFOLIO_ADMIN_EMAILS`에 등록된 `@sdh.hs.kr` 계정은 DB의 `isAdmin` 값과 별개로 서버 관리자 화면에 접근할 수 있습니다.

## 인증 정책

- Google OAuth를 사용합니다.
- 학교 계정만 허용하도록 `@sdh.hs.kr` 도메인을 검사합니다.
- Supabase Dashboard의 Google provider 설정에서도 허용 도메인을 `sdh.hs.kr`로 제한해야 불필요한 OAuth 계정 생성을 줄일 수 있습니다.
- 브라우저 세션은 `sessionStorage` 기반으로 유지됩니다.

## 로컬 전용 Supabase 보호

테스트용 Supabase project ref `lbayyiylxjvqhcqejvkr`는 로컬에서만 사용하도록 양쪽에서 막습니다.

- 프론트엔드: 해당 Supabase URL을 쓰면서 `localhost`, `127.0.0.1`, `::1`이 아닌 host에서 실행되면 즉시 오류를 냅니다.
- 백엔드: 같은 Supabase URL을 쓰면서 `PORTFOLIO_ALLOWED_ORIGINS`에 로컬이 아닌 origin이 있으면 시작하지 않습니다.
- 테스트 키와 service role key는 `portfolio/.env.local`, `backend/.env` 같은 로컬 파일에만 둡니다.

로컬 테스트 예시:

```text
# portfolio/.env.local
VITE_SUPABASE_URL=https://lbayyiylxjvqhcqejvkr.supabase.co
VITE_SUPABASE_ANON_KEY=<test anon key>
VITE_API_BASE_URL=http://127.0.0.1:8000
```

```text
# backend/.env
SUPABASE_AUTH_URL=https://lbayyiylxjvqhcqejvkr.supabase.co
SUPABASE_AUTH_SERVICE_ROLE_KEY=<rotated auth service role key>
SUPABASE_DB_URL=http://127.0.0.1:54321
SUPABASE_DB_SERVICE_ROLE_KEY=<local supabase service role key>
PORTFOLIO_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
PORTFOLIO_ALLOWED_ORIGIN_REGEX=
PORTFOLIO_ADMIN_EMAILS=<local test admin email>
PORTFOLIO_MAX_UPLOAD_BYTES=1048576
GITHUB_TOKEN=<github token for commit count lookup>
PORTFOLIO_GITHUB_COMMIT_CACHE_TTL_SECONDS=900
PORTFOLIO_KEEPALIVE_URL=
PORTFOLIO_KEEPALIVE_INTERVAL_SECONDS=600
```

## 테스트와 빌드

```powershell
npm run frontend:test
npm run backend:test
npm run frontend:build
```

루트 `npm run dev`는 프론트엔드와 백엔드를 함께 띄우는 개발용 명령입니다. 프로덕션 검증에는 `frontend:build`와 백엔드 테스트를 별도로 확인합니다.

## 배포

### Vercel frontend

- Root Directory: repository root
- Install Command: `vercel.json` 사용
- Build Command: `vercel.json` 사용
- Output Directory: `portfolio/dist`
- Required env vars:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_API_BASE_URL`

현재 루트 `vercel.json`은 `npm --prefix portfolio run build`로 프론트엔드를 빌드하고, SPA 라우트를 `index.html`로 rewrite합니다.

### Self-hosted Docker Compose

자체 VPS/호스팅 서버에서 프론트엔드와 백엔드를 함께 운영하려면 `deploy/docker-compose.self-hosted.yml`을 사용합니다.
Caddy가 80/443 포트를 열고 HTTPS 인증서를 자동 발급하며, `/api/*`와 `/health`는 FastAPI 백엔드로 프록시하고 나머지는 정적 프론트엔드를 제공합니다.

서버 준비:

```bash
git clone <repo-url> sdhs-student-portfolio-site
cd sdhs-student-portfolio-site
cp deploy/.env.example deploy/.env
```

`deploy/.env`에서 최소한 아래 값을 서버 도메인과 Supabase 키로 채웁니다.

```env
APP_DOMAIN=portfolio.example.com
VITE_SUPABASE_URL=https://your-auth-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_auth_project_anon_key
VITE_API_BASE_URL=__same_origin__
SUPABASE_AUTH_URL=https://your-auth-project.supabase.co
SUPABASE_AUTH_SERVICE_ROLE_KEY=your_auth_service_role_key
SUPABASE_DB_URL=https://your-db-project.supabase.co
SUPABASE_DB_SERVICE_ROLE_KEY=your_db_service_role_key
PORTFOLIO_ALLOWED_ORIGINS=https://portfolio.example.com
PORTFOLIO_UPLOAD_DIR=/app/uploads
```

이미지 URL은 하이브리드로 동작합니다. DB에 기존 Supabase Storage 절대 URL이 들어 있으면 그대로 Supabase에서 이미지를 가져오고, 새로 업로드한 이미지는 `/uploads/...` 상대 URL로 저장되어 자체 서버의 Docker volume에서 제공됩니다.

실행:

```bash
docker compose -f deploy/docker-compose.self-hosted.yml --env-file deploy/.env up -d --build
```

GitHub Actions CI/CD:

- `.github/workflows/ci.yml`: PR/push마다 프론트 테스트, 프론트 빌드, 백엔드 테스트 실행
- `.github/workflows/deploy-self-hosted.yml`: `main` 브랜치 CI 성공 후 서버에 SSH 접속해 `git reset --hard origin/main` 후 Docker Compose 재배포

GitHub repository secrets:

| Secret | Description |
| --- | --- |
| `SSH_HOST` | 서버 IP 또는 도메인 |
| `SSH_USER` | 배포에 사용할 서버 사용자 |
| `SSH_PRIVATE_KEY` | 해당 사용자의 private SSH key |
| `APP_DIR` | 서버 안의 repo 절대 경로. 예: `/home/deploy/sdhs-student-portfolio-site` |

서버에는 Docker Compose v2와 Git이 설치되어 있어야 하고, `APP_DOMAIN`의 DNS A/AAAA 레코드는 서버를 가리켜야 합니다. Caddy가 80/443 포트를 사용하므로 서버 방화벽에서도 두 포트를 열어야 합니다.

### Render backend

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`
- Backend keepalive: `PORTFOLIO_KEEPALIVE_URL` is set to the deployed `/health` URL in `render.yaml`, so the running backend periodically calls its own health endpoint.
- Keepalive fallback: `.github/workflows/render-keepalive.yml` also pings `/health` every 10 minutes as an external mitigation.
- Required env vars:
  - `SUPABASE_AUTH_URL`
  - `SUPABASE_AUTH_SERVICE_ROLE_KEY`
  - `SUPABASE_DB_URL`
  - `SUPABASE_DB_SERVICE_ROLE_KEY`
  - `PORTFOLIO_ALLOWED_ORIGINS`
  - `PORTFOLIO_ADMIN_EMAILS`
  - `PORTFOLIO_MAX_UPLOAD_BYTES`
  - `GITHUB_TOKEN`

Render Dashboard에 기존 Start Command가 남아 있으면 `render.yaml`보다 대시보드 값이 먼저 적용될 수 있습니다. `python uvicorn main:app --reload`처럼 개발용 명령이 보이면 위 Start Command로 교체합니다.

### Northflank

프론트엔드와 백엔드를 별도 서비스로 배포하는 구성이 가장 단순합니다.

Buildpack을 계속 쓴다면 명령을 명시합니다.

```text
Frontend root: portfolio
Frontend build command: npm ci && npm run build
Frontend start command: sh -c 'npm run preview -- --host 0.0.0.0 --port ${PORT:-8080}'

Backend root: backend
Backend build command: pip install -r requirements.txt
Backend start command: sh -c 'python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}'
```

`PORTFOLIO_ALLOWED_ORIGINS`에는 배포된 프론트엔드의 공개 URL을 포함해야 합니다.

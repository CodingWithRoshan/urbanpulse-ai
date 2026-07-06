# UrbanPulse AI — Production Build

Multi-agent civic intelligence platform for the Google AI Hackathon. This repo contains the
already-upgraded FastAPI/Google ADK backend and the new production Next.js + TypeScript frontend,
wired together end to end.

```
urbanpulse-ai-production/
  backend/    FastAPI + Google ADK multi-agent backend (unchanged in this pass)
  frontend/   Next.js 14 + TypeScript client (new — see frontend/README.md)
  docker-compose.yml
```

## Run everything locally

1. **Backend**
   ```bash
   cd backend
   cp .env.example .env        # fill in whichever API keys you have; everything
                                # degrades to a labelled mock if a key is missing
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8080
   ```

2. **Frontend**
   ```bash
   cd frontend
   cp .env.example .env.local
   # BACKEND_API_URL=http://localhost:8080
   # GOOGLE_CLIENT_ID must equal the backend's GOOGLE_OAUTH_CLIENT_ID
   npm install
   npm run dev
   ```

3. Open **http://localhost:3000**. The frontend calls the backend directly (CORS is already
   configured for `http://localhost:3000` in `backend/.env.example`).

### Or with Docker Compose

```bash
cp .env.example .env        # root-level file, feeds the frontend's build args
                             # (GOOGLE_OAUTH_CLIENT_ID, GOOGLE_MAPS_API_KEY) -
                             # separate from backend/.env, which docker-compose
                             # also loads automatically for the backend service
docker compose up --build
```

This builds and runs both containers, with the frontend pointed at
`http://localhost:8080` for the backend. Without the root `.env` filled in,
`docker compose` still runs, but the frontend image is built with an empty
Google Client ID / Maps key (Sign-In and the map will silently not work) -
Compose only warns about this, so it's easy to miss.

## Deploying to production

Three independent paths exist in this repo - pick one, you don't need all three:

| Path | Files | Best for |
|---|---|---|
| **Cloud Run via GitHub Actions** | `backend/.github/workflows/deploy-backend.yml`, `frontend/.github/workflows/deploy-frontend.yml` | Automatic deploy on every push to `main`; requires Workload Identity Federation set up once (see comments at the top of each workflow file for the exact repo secrets and `gcloud` prerequisites) |
| **Cloud Run via CLI** | `backend/README.md` / `frontend/README.md` "Deploying to Cloud Run" sections | A one-off manual deploy without setting up CI |
| **DigitalOcean App Platform** | `.do/app.yaml` | A single-click, non-GCP-specific option; edit the placeholder `repo:` field to your own GitHub repo first, then `doctl apps create --spec .do/app.yaml` |

Regardless of path, both services need matching config: the frontend's
`BACKEND_API_URL` must point at wherever the backend actually ends
up, and the backend's `ALLOWED_ORIGINS` must include the frontend's real URL
for CORS to allow it.

### Fixing an already-deployed pair of Cloud Run services

If you already ran `gcloud run deploy` once and the frontend shows "Couldn't load city
vitals: Failed to fetch", it's almost always because the frontend was built before this
runtime-config change and has an old/default backend URL frozen into its JS bundle.
Redeploy the frontend once to pick up the fix; after that, both services can be updated
with plain env vars and no rebuild:

```bash
# 1. Redeploy the frontend (one-time - picks up src/app/api/config/route.ts)
gcloud run deploy urbanpulse-frontend \
  --source frontend \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars BACKEND_API_URL=https://urbanpulse-backend-XXXXXXXXX.asia-south1.run.app,GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com,GOOGLE_MAPS_API_KEY=your-maps-key

# 2. Point the backend's CORS allowlist at the frontend's real URL
gcloud run services update urbanpulse-backend \
  --region asia-south1 \
  --update-env-vars ALLOWED_ORIGINS=https://urbanpulse-frontend-XXXXXXXXX.asia-south1.run.app
```

From now on, if the backend URL ever changes, this one command is enough - no rebuild:
```bash
gcloud run services update urbanpulse-frontend --region asia-south1 \
  --update-env-vars BACKEND_API_URL=https://new-backend-url
```

## How the two halves connect

- **Contract**: `frontend/src/types/api.ts` mirrors `backend/app/domain/schemas.py` field-for-field,
  and `frontend/src/lib/apiClient.ts` calls the exact routes mounted in
  `backend/app/api/v1/router.py` (`/api/v1/auth/google`, `/api/v1/auth/me`,
  `/api/v1/city-vitals`, `/api/v1/assistant/ask`, `/api/v1/reports`).
- **Auth**: the frontend gets a Google ID token via Google Identity Services, exchanges it for an
  app JWT at `POST /api/v1/auth/google`, and attaches it as `Authorization: Bearer <token>` on
  every subsequent request. Role (Citizen/Authority/Admin) comes back from the backend and drives
  which tabs the UI shows (`frontend/src/components/Header.tsx`,
  `frontend/src/components/AppShell.tsx`).
- **CORS**: the backend's `ALLOWED_ORIGINS` env var must include the frontend's origin
  (`http://localhost:3000` locally; your Cloud Run frontend URL in production).
- **Deployment**: both services deploy independently to Cloud Run via
  `backend/.github/workflows/deploy-backend.yml` and
  `frontend/.github/workflows/deploy-frontend.yml`. Point the frontend's
  `BACKEND_API_URL` runtime environment variable at the backend's Cloud Run URL -
  this is read at request time (`frontend/src/app/api/config/route.ts`), so changing
  it later only needs a service update/restart, not a rebuild.

## What this pass delivered

The backend was already refactored into a clean, modular, ADK-based architecture in a prior pass
(agents, services, repositories, domain schemas, JWT auth, Firestore/GCS, legacy route aliases for
backward compatibility). This pass replaced the static `urbanpulse-ai.html` prototype frontend
with a full production Next.js + TypeScript application that:

- Preserves the original UI, layout, and workflow (Dashboard → AI Assistant → Report Issue →
  Authority Console) pixel-for-pixel in spirit, including the color system, KPI cards, agent-trace
  panel, and upload flow.
- Replaces every piece of mock/simulated client-side logic with real calls into the backend's
  live data services and Gemini-powered agents.
- Adds real Google Sign-In, JWT-based sessions, and role-gated views (Citizen / Authority /
  Admin), instead of the prototype's no-auth, everyone-sees-everything model.
- Ships with Docker, a Cloud Run–ready standalone build, and a GitHub Actions pipeline matching
  the backend's.

See `frontend/README.md` for a detailed before/after table and project structure.

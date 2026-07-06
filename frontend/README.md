# UrbanPulse AI — Frontend

Production Next.js 14 (App Router) + TypeScript client for UrbanPulse AI, built to match the
original single-page prototype's UI and workflow one-for-one (Dashboard / AI Assistant / Report
Issue / Authority Console), but now talking to the real FastAPI + Google ADK backend instead of
mock, client-side data.

## What changed vs. the HTML prototype

| Prototype (`urbanpulse-ai.html`) | This app |
|---|---|
| Inline `<script>` with hand-rolled DOM updates | Next.js + TypeScript, componentized (`src/components`) |
| `Math.random()` mock weather/AQI/traffic/flood data | Live `GET /api/v1/city-vitals` polled every 60s |
| Simulated agent trace with `setTimeout` | Real `POST /api/v1/assistant/ask` response rendered as a staggered trace, driven by actual Planner/Traffic/Environment/Prediction/Risk/Recommendation agent output |
| Fake Gemini Vision classification (`pick(CATS)`) | Real multipart upload to `POST /api/v1/reports`, classified server-side by Gemini Vision |
| In-memory `reports` array | Persisted reports fetched from Firestore via the backend, refreshed after every submission/status change |
| No auth — everyone sees everything | Google Sign-In → backend JWT exchange; Citizen/Authority/Admin role-gated views |
| Global mutable `cityState` | Typed API client (`src/lib/apiClient.ts`) + React hooks (`useCityVitals`, `useReports`) |

Visual language (colors, type, layout, the pulse-strip header, KPI cards, chat/agent-trace split
panel, upload zone) is preserved from the original design tokens.

## Local development

```bash
cp .env.example .env.local
# edit .env.local: point BACKEND_API_URL at your running backend,
# and set GOOGLE_CLIENT_ID to the same OAuth client the backend trusts.

npm install
npm run dev
# open http://localhost:3000
```

The backend must be running separately (see `../backend/README.md`) with matching
`GOOGLE_OAUTH_CLIENT_ID` and `ALLOWED_ORIGINS=http://localhost:3000`.

## Project structure

```
src/
  app/                 # App Router pages (/, /login) + root layout + providers
  components/
    views/             # DashboardView, AssistantView, ReportView, AuthorityView
    Header.tsx          # nav tabs, live clock, theme toggle, auth controls
    KpiCard.tsx, Charts.tsx, MapPanel.tsx, AlertFeed.tsx
  hooks/               # useCityVitals (polling), useReports (CRUD + refresh)
  lib/
    apiClient.ts        # typed fetch wrapper for every backend endpoint
    AuthContext.tsx      # Google login, JWT storage, role helpers
    ThemeContext.tsx     # dark/light toggle (matches original data-theme approach)
  types/api.ts          # TypeScript mirror of the backend's Pydantic schemas
```

## Role-based access

- **Citizen** (default role after Google sign-in): Dashboard, AI Assistant, Report Issue, and
  "Your Submitted Reports".
- **Authority / Admin**: everything a Citizen sees, plus the Authority Console tab (priority
  ranking, status updates, AI recommendations, resolution-rate chart). Roles are assigned
  server-side (`backend/app/api/v1/auth.py`); there is nothing to configure on the frontend.

## Docker

```bash
docker build -t urbanpulse-web .
docker run -p 3000:3000 \
  -e BACKEND_API_URL=https://your-backend-url \
  -e GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com \
  -e GOOGLE_MAPS_API_KEY=your-maps-key \
  urbanpulse-web
```

These are runtime environment variables (read via `src/app/api/config/route.ts`), not build
args - the same image works against any backend URL; just change the `-e` values and restart
the container, no rebuild needed.

Or from the repo root: `docker compose up --build` runs both services together.

## Deployment

`.github/workflows/deploy-frontend.yml` type-checks, builds, and deploys to Cloud Run on every
push to `main` that touches `frontend/**` — mirroring the backend's existing pipeline.

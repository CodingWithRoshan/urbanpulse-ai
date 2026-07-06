# UrbanPulse AI — Backend (Production Architecture)

This is the upgraded backend for the UrbanPulse AI hackathon prototype. The
original two-file prototype (`main.py` + `agents.py`, ~330 lines, mock data,
`random`-based classification, in-memory-only state) has been refactored into
a modular, layered FastAPI application with real integrations, while
**every original endpoint path, response shape, and business rule is
preserved** — the existing frontend keeps working unmodified against
`/api/*` and `/healthz`.

## What changed and why

| Area | Prototype | Upgraded |
|---|---|---|
| Structure | 2 files, all logic mixed together | Layered: `domain` / `services` / `repositories` / `agents` / `api` |
| Weather/AQI/Traffic/Time | Hardcoded mock dicts | Real Google Weather API, Google Air Quality API, Google Maps Distance Matrix, and Google Time Zone API calls (OpenWeather as a weather fallback), each with a labelled mock fallback if a key is missing |
| Flood prediction | `random`-free but static mock | Gemini 2.5 Flash reasoning over live weather, with a deterministic rule-based fallback (never `random`) |
| Complaint classification | `random.choice` | Gemini Vision multimodal classification, with a deterministic (hash-based, not random) fallback |
| Orchestration | Hand-written Python call chain "shaped like" ADK | Real `google-adk` graph (`SequentialAgent` / `ParallelAgent` / `LoopAgent` / session memory / agent-as-tool) behind `ADK_ENABLED`, plus an equivalent dependency-free async orchestrator as the default runtime path |
| State | Module-level `dict` | Repository pattern: Firestore-backed when configured, in-memory fallback otherwise, same interface either way |
| Images | Never persisted | Cloud Storage upload, with inline data-URL fallback |
| Auth | None | Google Sign-In → JWT, role-based access (Citizen / Authority / Admin) |
| Deployment | Manual `gcloud run deploy` | Dockerfile + GitHub Actions build/test/deploy pipeline |

Nothing about the agent responsibilities or the risk/recommendation logic was
removed — `RiskScoreAgent`'s weighting (35% AQI / 35% traffic / 30% flood) and
`RecommendationAgent`'s three intents (`flood_risk`, `outdoor_safety`,
`commute_decision`) are the same rules, just now backed by live data and
optionally phrased by Gemini instead of hardcoded strings.

## Why the ADK graph is feature-flagged

`google-adk`'s `LlmAgent` graph expects a configured Gemini/Vertex runtime to
actually reason at each step. Shipping it as the **only** code path would mean
the submission fails to run for anyone without billing enabled. Instead:

- `ADK_ENABLED=false` (default): `FallbackOrchestrator` runs the exact same
  five-stage pipeline (Planner → Environment → Parallel[Traffic, Prediction]
  → RiskScore → Loop-refined Recommendation) with plain `asyncio.gather`,
  calling the identical service/agent classes.
- `ADK_ENABLED=true` + `GEMINI_API_KEY` set: `AdkOrchestrator`
  (`app/agents/adk_orchestrator.py`) builds and runs the real
  `SequentialAgent(planner, environment, ParallelAgent(traffic, prediction),
  risk_score, LoopAgent(recommendation, risk_score))` graph with ADK's
  session service. If it throws for any reason, `Orchestrator` (the facade in
  `app/agents/orchestrator.py`) automatically retries on the fallback path so
  a flaky demo network never 500s the API.

Both paths produce the same `DecisionResponse` schema, so the frontend and
judges can toggle `ADK_ENABLED` without noticing a difference beyond
"phrasing gets more natural and reasoning becomes visible in ADK traces."

## Project layout

```
backend/
  app/
    main.py                 # FastAPI app factory, routers, exception handlers
    core/
      config.py              # Settings (env-driven, every integration optional)
      security.py             # JWT issuance/verification, RBAC dependency
      logging_config.py
    domain/
      schemas.py              # Pydantic request/response models
      enums.py                # Role, ReportStatus, Intent, ComplaintCategory
      exceptions.py
    services/                 # One class per external integration
      gemini_service.py       # google-genai wrapper (text + vision)
      weather_service.py      # Google Weather API (OpenWeather fallback)
      aqi_service.py          # Google Air Quality API
      traffic_service.py      # Google Maps Distance Matrix API
      timezone_service.py     # Google Time Zone API
      flood_prediction_service.py  # Gemini-reasoned flood risk
      alerts_service.py
      storage_service.py      # Cloud Storage
      firestore_service.py
      google_auth_service.py  # Google ID token verification
    repositories/              # Firestore-backed, in-memory fallback, same interface
      report_repository.py
      session_repository.py
      base_repository.py
    agents/
      planner_agent.py
      data_agents.py          # Traffic / Environment / Prediction agents
      risk_score_agent.py
      recommendation_agent.py
      complaint_agent.py
      fallback_orchestrator.py # Default runtime graph (asyncio)
      adk_orchestrator.py      # Real Google ADK graph (feature-flagged)
      orchestrator.py          # Facade + composition root (DI)
    api/
      deps.py
      legacy_router.py        # Preserves original /api/* and /healthz paths
      v1/                     # Versioned /api/v1/* routes (same handlers)
  tests/                       # pytest suite (health, vitals, assistant, auth, RBAC)
  Dockerfile
  .github/workflows/deploy-backend.yml
  requirements.txt
  .env.example
```

## Running locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in whichever keys you have; all are optional
uvicorn app.main:app --reload --port 8080
```

With an empty `.env`, every integration degrades to its labelled mock and the
full pipeline still runs end-to-end — this is intentional so the app is
demoable and CI-testable without cloud credentials. Add keys incrementally to
light up real Weather / AQI / Traffic / Gemini / Firestore / GCS one at a
time; `/healthz` reports which are active.

Run the test suite:

```bash
pip install pytest
pytest -q
```

## API surface

Both of these are live simultaneously (identical behaviour):

- Legacy (matches the original prototype's frontend): `/api/city-vitals`,
  `/api/assistant/ask`, `/api/reports`, `/healthz`
- Versioned: `/api/v1/city-vitals`, `/api/v1/assistant/ask`,
  `/api/v1/reports`, `/api/v1/auth/google`, `/api/v1/auth/me`,
  `/api/v1/healthz`

Auth: `POST /api/v1/auth/google` with a Google ID token returns an app JWT.
Send it as `Authorization: Bearer <token>` on `/api/reports*`.
`GET /api/reports` returns every report to Authority/Admin, and only the
caller's own reports to a Citizen. `PATCH /api/reports/{id}/status` requires
Authority or Admin.

## Deploying to Cloud Run

```bash
gcloud run deploy urbanpulse-api \
  --source backend \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,FIRESTORE_ENABLED=true,GCS_ENABLED=true \
  --set-secrets GEMINI_API_KEY=urbanpulse-gemini-api-key:latest,GOOGLE_API_KEY=urbanpulse-google-api-key:latest,OPENWEATHER_API_KEY=urbanpulse-openweather-api-key:latest,JWT_SECRET_KEY=urbanpulse-jwt-secret:latest,GOOGLE_OAUTH_CLIENT_ID=urbanpulse-oauth-client-id:latest
```

`.github/workflows/deploy-backend.yml` automates the same thing via Workload
Identity Federation on every push to `main` that touches `backend/`; it runs
`compileall` + `pytest` first and only deploys on a green build.

## Next steps (not yet wired, by design)

- Frontend migration to Next.js + TypeScript (separate deliverable/zip).
- A Firestore `users` collection + Admin UI to replace the in-process
  `_AUTHORITY_EMAILS` / `_ADMIN_EMAILS` allowlist in `app/api/v1/auth.py`
  with persisted role assignment.

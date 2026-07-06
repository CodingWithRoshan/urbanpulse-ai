"""Regression tests for bugs found during the pre-submission audit.

Each test below is named after (and pins the fix for) a specific bug that
previously shipped silently:

1. POST /auth/google returned 422 "body.payload" because the router used
   `Depends(GoogleAuthService)` directly, and FastAPI mistook the
   service's `settings` constructor parameter for a second body field.
2. GoogleAuthService.verify() only caught ValueError, so a network
   failure fetching Google's certs (google.auth.exceptions.TransportError)
   surfaced as an unhandled 500 instead of a clean 401.
3. FirestoreService.__init__ checked `self.is_available` -- which itself
   checks `self._client is not None` -- to decide whether to create
   `self._client`. That client is always None at that point in __init__,
   so the guard was always False and the client was never created even
   when Firestore was fully configured.
4. The ADK orchestrator's `refinement_loop` reused the same
   `risk_score_agent` instance that was also used at the top level of the
   sequential pipeline. ADK enforces a strict single-parent tree, so the
   graph failed to build at all once ADK was enabled.
"""
from unittest.mock import patch

import pytest
from google.auth import exceptions as google_auth_exceptions

from app.core.config import get_settings
from app.services.firestore_service import FirestoreService
from app.services.google_auth_service import GoogleAuthService


# --- Bug 1 & 2: /auth/google -------------------------------------------------


def test_auth_google_does_not_require_a_settings_body_field(client):
    """A plain {"id_token": ...} body must not 422 on a missing `settings`
    or `payload` wrapper field. This is the DI bug: `Depends(GoogleAuthService)`
    used to make FastAPI treat the constructor's `settings` parameter as a
    second required body field."""
    with patch.object(GoogleAuthService, "verify", return_value={
        "sub": "abc123", "email": "citizen@test.com", "name": "Test Citizen",
    }):
        response = client.post("/api/v1/auth/google", json={"id_token": "fake-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "citizen@test.com"
    assert "access_token" in body


def test_auth_google_network_failure_returns_clean_401_not_500(client):
    """If fetching Google's certs fails (TransportError), the endpoint must
    return a clean 401, not an unhandled 500."""
    service = GoogleAuthService(get_settings())

    def _boom(*args, **kwargs):
        raise google_auth_exceptions.TransportError("Could not fetch certificates")

    with patch(
        "app.services.google_auth_service.google_id_token.verify_oauth2_token",
        side_effect=_boom,
    ):
        with patch(
            "app.api.v1.auth.get_google_auth_service",
            return_value=service,
        ):
            response = client.post("/api/v1/auth/google", json={"id_token": "fake-token"})

    assert response.status_code == 401
    assert response.status_code != 500


# --- Bug 3: FirestoreService.is_available self-reference --------------------


def test_firestore_client_is_created_when_configured():
    """Regression for the self-referential is_available bug: the client must
    actually be constructed (attempted) when Firestore is configured, instead
    of always staying None because is_available checked the not-yet-created
    client.

    Uses an explicit Settings override rather than the cached get_settings()
    singleton, so the outcome doesn't depend on whatever happens to be in the
    local .env when pytest runs (that environment-coupling was itself fragile).
    """
    settings = get_settings().model_copy(
        update={"firestore_enabled": True, "firestore_project_id": "test-project"}
    )
    assert settings.firestore_configured

    with patch(
        "app.services.firestore_service.firestore.AsyncClient",
        return_value="fake-client-instance",
    ) as mock_client:
        service = FirestoreService(settings)

    mock_client.assert_called_once()
    assert service.client == "fake-client-instance"
    assert service.is_available is True


def test_firestore_is_available_false_when_not_configured():
    settings = get_settings()
    unconfigured = settings.model_copy(update={"firestore_enabled": False})

    service = FirestoreService(unconfigured)

    assert service.is_available is False
    assert service.client is None


# --- Bug 4: ADK single-parent agent tree -------------------------------------


def test_adk_graph_builds_without_shared_agent_instance():
    """Regression for the ADK single-parent tree violation: risk_score_agent
    must not appear both at the top level of the pipeline and inside
    refinement_loop, since ADK agents can only have one parent."""
    google_adk = pytest.importorskip("google.adk.agents")

    from app.agents.adk_orchestrator import AdkOrchestrator
    from app.agents.planner_agent import PlannerAgent
    from app.agents.recommendation_agent import RecommendationAgent
    from app.agents.risk_score_agent import RiskScoreAgent
    from app.services.alerts_service import AlertsService
    from app.services.gemini_service import GeminiService
    from app.services.timezone_service import TimeZoneService

    class _FakeSessionRepo:
        async def append(self, *a, **k):
            return []

    class _FakeAgent:
        async def run(self, *a, **k):
            return {}

    settings = get_settings()
    orchestrator = AdkOrchestrator(
        settings=settings,
        planner=PlannerAgent(_FakeSessionRepo()),
        traffic_agent=_FakeAgent(),
        environment_agent=_FakeAgent(),
        prediction_agent=_FakeAgent(),
        risk_scorer=RiskScoreAgent(),
        recommender=RecommendationAgent(GeminiService(settings)),
        alerts_service=AlertsService(),
        timezone_service=TimeZoneService(settings),
    )

    root = orchestrator._build_graph()  # must not raise a pydantic ValidationError

    risk_agent_names_at_top_level = {sa.name for sa in root.sub_agents}
    refinement_loop = next(sa for sa in root.sub_agents if sa.name == "refinement_loop")
    risk_agent_names_in_loop = {sa.name for sa in refinement_loop.sub_agents}

    # The two risk-scoring agents used at different tree positions must be
    # distinctly-named (i.e. genuinely different instances), never the same
    # agent object reused in two places.
    shared_names = risk_agent_names_at_top_level & risk_agent_names_in_loop
    assert shared_names == set(), f"Agent instance(s) shared across tree positions: {shared_names}"

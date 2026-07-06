from fastapi import APIRouter, Depends

from app.agents.orchestrator import Orchestrator
from app.api.deps import get_orchestrator_dep
from app.core.security import get_optional_user
from app.domain.schemas import AuthenticatedUser, DecisionQuery, DecisionResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=DecisionResponse)
async def ask_assistant(
    query: DecisionQuery,
    orchestrator: Orchestrator = Depends(get_orchestrator_dep),
    user: AuthenticatedUser | None = Depends(get_optional_user),
):
    """
    Runs the full agent pipeline:
    Planner -> Environment -> [Traffic || Prediction] (parallel) -> Risk Score
    -> Recommendation (with one refinement loop pass on borderline scores).

    Session memory is keyed by session_id (falling back to the caller's
    account id when authenticated) so the Planner can reuse prior context.
    """
    session_id = query.session_id or (user.id if user else "anonymous")
    return await orchestrator.run_decision_pipeline(
        question=query.question, lat=query.lat, lng=query.lng, session_id=session_id
    )

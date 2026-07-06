from fastapi import APIRouter, Depends

from app.agents.orchestrator import Orchestrator
from app.api.deps import get_orchestrator_dep
from app.domain.schemas import CityVitals

router = APIRouter(tags=["city-vitals"])


@router.get("/city-vitals", response_model=CityVitals)
async def city_vitals(orchestrator: Orchestrator = Depends(get_orchestrator_dep)):
    """Aggregated KPI snapshot: weather, AQI, traffic, flood risk, alerts, health score."""
    return await orchestrator.get_city_vitals()

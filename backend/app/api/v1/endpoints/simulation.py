from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_store_access
from app.models.user import User
from app.schemas.simulation import SimulatePromoRequest, SimulatePromoResponse
from app.services.simulation_service import SimulationService

router = APIRouter()


@router.post(
    "/simulate",
    response_model=SimulatePromoResponse,
    summary="Simulate What-If Promotional Uplift Curve",
    description="Calculates estimated price elasticity, demand lift, and revenue impact across the promotion duration vs baseline.",
)
def simulate_promotion(
    req: SimulatePromoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.store_id:
        verify_store_access(req.store_id, current_user)

    service = SimulationService(db)
    return service.simulate(req)

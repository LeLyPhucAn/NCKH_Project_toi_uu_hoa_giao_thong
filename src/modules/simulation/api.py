from fastapi import APIRouter, Depends
from modules.simulation.schemas import SimulationLogResponse
from modules.simulation.service import SimulationService

router = APIRouter(prefix="/api/simulation-log", tags=["Simulation"])


def get_simulation_service() -> SimulationService:
    return SimulationService()


@router.get("", response_model=SimulationLogResponse)
def get_simulation_log(service: SimulationService = Depends(get_simulation_service)):
    log_content = service.get_simulation_log()
    return SimulationLogResponse(log=log_content)

from fastapi import APIRouter, Depends
from typing import List
from modules.routing.schemas import RouteDetailResponse, RoutingExecutionResponse
from modules.routing.service import RoutingService

router = APIRouter(prefix="/api/routing", tags=["Routing"])


def get_routing_service() -> RoutingService:
    return RoutingService()


@router.get("/routes", response_model=List[RouteDetailResponse])
def get_routes(service: RoutingService = Depends(get_routing_service)):
    return service.get_routing_results()


@router.post("/run", response_model=RoutingExecutionResponse)
def run_routing(service: RoutingService = Depends(get_routing_service)):
    df_res = service.execute_routing()
    return RoutingExecutionResponse(status="success", total_routes_computed=len(df_res))

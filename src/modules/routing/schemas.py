from pydantic import BaseModel
from typing import List


class RouteDetailResponse(BaseModel):
    order_id: int
    hub_id: int
    hub_strategy: str
    traffic_condition: str
    scenario: str
    time: float
    distance: float
    cost: float
    co2: float
    modes_used: str


class RoutingExecutionResponse(BaseModel):
    status: str
    total_routes_computed: int

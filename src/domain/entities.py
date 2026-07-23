from pydantic import BaseModel, Field
from typing import Optional, List


class Location(BaseModel):
    lat: float = Field(..., description="Vĩ độ (Latitude)")
    lon: float = Field(..., description="Kinh độ (Longitude)")


class Order(BaseModel):
    order_id: int
    lat: float
    lon: float
    weight: float = 5.0
    status: str = "pending"


class HubCandidate(BaseModel):
    hub_id: int
    name: str
    lat: float
    lon: float
    is_selected: bool = False


class TransitStation(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    mode_type: str  # metro or waterbus


class RouteMetric(BaseModel):
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


class KPIRecord(BaseModel):
    traffic_condition: str
    scenario: str
    avg_time_min: float
    total_distance_km: float
    avg_distance_km: Optional[float] = None
    total_cost_vnd: float
    avg_cost_vnd: Optional[float] = None
    total_co2_kg: float
    avg_co2_kg: Optional[float] = None
    delivery_count: Optional[int] = None

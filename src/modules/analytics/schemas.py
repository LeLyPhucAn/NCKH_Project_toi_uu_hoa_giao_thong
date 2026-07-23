from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class KPIRecordDTO(BaseModel):
    traffic_condition: str
    scenario: str
    avg_time_min: float
    total_distance_km: float
    total_cost_vnd: float
    total_co2_kg: float
    avg_cost_vnd: Optional[float] = None
    avg_distance_km: Optional[float] = None
    avg_co2_kg: Optional[float] = None


class ImprovementDTO(BaseModel):
    traffic_condition: str
    scenario: str
    time_improvement_pct: float
    co2_improvement_pct: float
    cost_improvement_pct: float


class KPISummaryResponse(BaseModel):
    summary: List[KPIRecordDTO]
    improvement: List[ImprovementDTO]

from pydantic import BaseModel
from typing import List, Optional


class HubResponse(BaseModel):
    hub_id: int
    name: str
    lat: float
    lon: float
    is_selected: bool = False


class HubSelectionRequest(BaseModel):
    num_hubs: int = 5

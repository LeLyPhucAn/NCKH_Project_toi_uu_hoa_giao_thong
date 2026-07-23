from fastapi import APIRouter, Depends, Query
from typing import List
from modules.hub.schemas import HubResponse, HubSelectionRequest
from modules.hub.service import HubService

router = APIRouter(prefix="/api/hubs", tags=["Hubs"])


def get_hub_service() -> HubService:
    return HubService()


@router.get("", response_model=List[HubResponse])
def get_hubs(service: HubService = Depends(get_hub_service)):
    return service.get_selected_or_candidate_hubs()


@router.post("/select", response_model=List[HubResponse])
def select_hubs(req: HubSelectionRequest, service: HubService = Depends(get_hub_service)):
    selected_df = service.select_optimal_hubs(num_hubs=req.num_hubs)
    selected_df['is_selected'] = True
    return selected_df.to_dict(orient="records")

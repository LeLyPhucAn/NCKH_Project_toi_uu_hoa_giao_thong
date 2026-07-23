import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from core.config.settings import settings
from modules.analytics.schemas import KPISummaryResponse
from modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/api", tags=["Analytics"])


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


@router.get("/kpis", response_model=KPISummaryResponse)
def get_kpis(service: AnalyticsService = Depends(get_analytics_service)):
    return service.get_kpi_summary()


@router.get("/download-excel")
def download_excel():
    excel_path = os.path.join(settings.RESULTS_DIR, "summary_results.xlsx")
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="File summary_results.xlsx chưa được tạo.")
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Report_Logistics_Multimodal.xlsx"
    )

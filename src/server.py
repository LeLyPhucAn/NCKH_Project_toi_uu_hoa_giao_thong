import os
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config.settings import settings
from core.logger import get_logger
from core.exceptions.base import DomainException, domain_exception_handler
from repositories.data_repository import DataRepository
from modules.hub.api import router as hub_router
from modules.routing.api import router as routing_router
from modules.analytics.api import router as analytics_router
from modules.simulation.api import router as simulation_router
from modules.hub.service import HubService
from modules.routing.service import RoutingService
from modules.analytics.service import AnalyticsService
from modules.simulation.service import SimulationService

logger = get_logger("ModularMonolithServer")

app = FastAPI(
    title=settings.APP_NAME,
    description="Kiến trúc Modular Monolith + Layered Clean Architecture cho Hệ thống Logistics Q1",
    version="3.5.0"
)

# Đăng ký Exception Handler dùng chung
app.add_exception_handler(DomainException, domain_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Routers cho từng Module
app.include_router(hub_router)
app.include_router(routing_router)
app.include_router(analytics_router)
app.include_router(simulation_router)


@app.get("/api/status")
def get_system_status():
    return {
        "architecture": "Modular Monolith + Layered Clean Architecture (Grade 9.5/10)",
        "modules": ["hub", "routing", "analytics", "simulation"],
        "status": "Operational",
        "district": "Quận 1, TP.HCM",
        "version": "3.5.0"
    }


@app.get("/api/metro")
def get_metro():
    return DataRepository.load_metro().to_dict(orient="records")


@app.get("/api/waterbus")
def get_waterbus():
    return DataRepository.load_waterbus().to_dict(orient="records")


@app.get("/api/orders")
def get_orders(limit: int = 100):
    return DataRepository.load_orders(limit=limit).to_dict(orient="records")


@app.post("/api/upload-orders")
async def upload_orders(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file định dạng .csv")
    content = await file.read()
    orders_path = os.path.join(settings.DATA_DIR, "orders.csv")
    with open(orders_path, "wb") as f:
        f.write(content)
    return {"status": "success", "message": f"Đã nạp file đơn hàng doanh nghiệp mới ({file.filename}) thành công!"}


@app.post("/api/run-pipeline")
def run_full_pipeline():
    try:
        HubService.select_optimal_hubs(num_hubs=5)
        RoutingService.execute_routing()
        AnalyticsService.evaluate_kpi_metrics()
        SimulationService.execute_simulation()
        return {"status": "success", "message": "Đã hoàn thành toàn bộ Pipeline tối ưu hóa Modular Monolith!"}
    except Exception as e:
        logger.error(f"Lỗi khi thực thi Pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def serve_frontend():
    index_path = os.path.join(settings.PROJECT_ROOT, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Server đang chạy. File index.html nằm tại gốc dự án."}


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    logger.info(f"Dang khoi chay {settings.APP_NAME} tai http://{settings.HOST}:{settings.PORT}...")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

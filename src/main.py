import os
import sys

# Thêm src vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.hub.service import HubService
from modules.routing.service import RoutingService
from modules.analytics.service import AnalyticsService
from modules.simulation.service import SimulationService
from core.logger import get_logger

logger = get_logger("MainPipeline")


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    logger.info("=== Bắt đầu Pipeline Tối ưu hóa Logistics (Modular Monolith Architecture) ===")
    
    # Bước 1 & 2 & 3: Chọn Hub
    HubService.select_optimal_hubs(num_hubs=5)
    
    # Bước 4: Routing Dijkstra
    RoutingService.execute_routing()
    
    # Bước 5: Đánh giá KPI & Phát thải CO2
    AnalyticsService.evaluate_kpi_metrics()
    
    # Bước 6: Mô phỏng Sự kiện ABM SimPy
    SimulationService.execute_simulation()
    
    logger.info("=== Pipeline Hoàn Thành 7/7 Bước Thành Công! ===")


if __name__ == "__main__":
    main()
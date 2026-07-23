import os

# Đường dẫn dự án
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
GRAPH_CACHE_PATH = os.path.join(RESULTS_DIR, "multimodal_graph.pkl")

# Tạo thư mục results nếu chưa tồn tại
os.makedirs(RESULTS_DIR, exist_ok=True)

# Thông số vận tải & Hệ số phát thải CO2 (kg/km)
CO2_EMISSION_FACTORS = {
    "road": 0.12,       # Xe máy / Ô tô nhỏ: 120g CO2/km
    "metro": 0.02,      # Metro chạy điện: 20g CO2/km
    "waterbus": 0.05,   # Tàu thủy: 50g CO2/km
    "transfer": 0.0     # Đi bộ / chuyển tải
}

# Vận tốc trung bình (km/h)
SPEED_KMH = {
    "road_offpeak": 25.0,
    "road_peak": 10.0,    # Kẹt xe giờ cao điểm
    "metro": 40.0,
    "waterbus": 20.0
}

# Hệ số chi phí (VNĐ/km hoặc VNĐ/chuyến)
COST_RATES = {
    "road_per_km": 3000.0,
    "transfer_per_handling": 7500.0
}

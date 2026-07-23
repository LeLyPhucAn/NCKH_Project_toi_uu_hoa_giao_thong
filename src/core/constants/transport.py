# Hằng số vận tải & hệ số phát thải CO2 (kg/km)
CO2_EMISSION_FACTORS = {
    "road": 0.12,       # Xe máy / Ô tô nhỏ: 120g CO2/km
    "metro": 0.02,      # Metro điện: 20g CO2/km
    "waterbus": 0.05,   # Tàu thủy: 50g CO2/km
    "transfer": 0.0     # Đi bộ / bốc dỡ
}

# Vận tốc trung bình (km/h)
SPEED_KMH = {
    "road_offpeak": 25.0,
    "road_peak": 10.0,
    "metro": 40.0,
    "waterbus": 20.0
}

# Hệ số thời gian giờ cao điểm
PEAK_TRAFFIC_MULTIPLIER = 2.5

# Thời gian bốc dỡ/chuyển tải (phút)
HANDLING_TIME_MINUTES = 10.0

# Bán kính chuyển tải tối đa (km)
MAX_TRANSFER_DISTANCE_KM = 0.5

# Giá cước tham chiếu (VNĐ)
COST_RATES = {
    "road_per_km": 3000.0,
    "metro_per_trip": 1000.0,
    "transfer_per_handling": 7500.0
}

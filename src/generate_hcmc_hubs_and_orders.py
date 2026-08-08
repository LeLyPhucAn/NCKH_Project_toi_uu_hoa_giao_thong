import pandas as pd
import numpy as np
import random
import os

# Set seed for exact reproducibility
random.seed(2026)
np.random.seed(2026)

# -------------------------------------------------------------
# 1. GENERATE 30 REALISTIC HUB CANDIDATES ACROSS HCMC DISTRICTS
# -------------------------------------------------------------
hubs_data = [
    # Quận 1 & Trung tâm
    (1,  "Hub_01_Ben_Thanh_Q1",            10.7721, 106.6983),
    (2,  "Hub_02_Nha_Hat_Q1",              10.7762, 106.7031),
    (3,  "Hub_03_Ba_Son_Q1",               10.7836, 106.7094),
    (4,  "Hub_04_Tan_Dinh_Q1",             10.7892, 106.6908),
    (5,  "Hub_05_Nguyen_Hue_Q1",           10.7741, 106.7038),

    # Quận 3
    (6,  "Hub_06_Dien_Bien_Phu_Q3",        10.7831, 106.6854),
    (7,  "Hub_07_Ky_Dong_Q3",              10.7811, 106.6782),
    (8,  "Hub_08_Ho_Con_Rua_Q3",           10.7827, 106.6961),

    # Quận 4 & Quận 7
    (9,  "Hub_09_Hoang_Dieu_Q4",           10.7601, 106.7015),
    (10, "Hub_10_Ben_Van_Don_Q4",          10.7632, 106.6942),
    (11, "Hub_11_Phu_My_Hung_Q7",          10.7294, 106.7118),
    (12, "Hub_12_Nguyen_Van_Linh_Q7",      10.7335, 106.7231),
    (13, "Hub_13_Huynh_Tan_Phat_Q7",       10.7451, 106.7312),

    # Quận 5 & Quận 6 & Quận 8
    (14, "Hub_14_An_Dong_Q5",              10.7554, 106.6712),
    (15, "Hub_15_Hung_Vuong_Q5",           10.7588, 106.6668),
    (16, "Hub_16_Cho_Lon_Q6",              10.7512, 106.6508),
    (17, "Hub_17_Pham_The_Hien_Q8",        10.7412, 106.6781),

    # Quận 10 & Quận 11
    (18, "Hub_18_Ba_Thang_Hai_Q10",        10.7702, 106.6685),
    (19, "Hub_19_Ly_Thai_To_Q10",          10.7672, 106.6751),
    (20, "Hub_20_To_Hien_Thanh_Q10",       10.7791, 106.6632),
    (21, "Hub_21_Dam_Sen_Q11",             10.7681, 106.6451),

    # Bình Thạnh & Phú Nhuận
    (22, "Hub_22_Van_Thanh_Binh_Thanh",    10.7974, 106.7165),
    (23, "Hub_23_Tan_Cang_Binh_Thanh",     10.8002, 106.7248),
    (24, "Hub_24_Dinh_Bo_Linh_Binh_Thanh", 10.8091, 106.7132),
    (25, "Hub_25_Phan_Xinh_Phu_Nhuan",     10.7961, 106.6892),

    # Tân Bình & Gò Vấp
    (26, "Hub_26_Cong_Hoa_Tan_Binh",       10.8012, 106.6521),
    (27, "Hub_27_Truong_Chinh_Tan_Binh",   10.8055, 106.6432),
    (28, "Hub_28_Quang_Trung_Go_Vap",      10.8351, 106.6651),

    # TP. Thủ Đức (Quận 2, Quận 9, Thủ Đức cũ)
    (29, "Hub_29_Thao_Dien_Thu_Duc",       10.8052, 106.7368),
    (30, "Hub_30_KCNC_Thu_Duc",            10.8590, 106.7881),
]

df_hubs = pd.DataFrame(hubs_data, columns=["hub_id", "name", "lat", "lon"])

# -------------------------------------------------------------
# 2. GENERATE 500 VALID ORDERS ACROSS URBAN DISTRICTS OF HCMC
# -------------------------------------------------------------
# Define street land centers for 15 major delivery zones in HCMC
district_street_centers = [
    # (Lat, Lon, Radius_lat, Radius_lon, weight_probability)
    (10.7750, 106.7000, 0.012, 0.012),  # Quận 1 - Trung tâm
    (10.7820, 106.6850, 0.010, 0.010),  # Quận 3 - Võ Thị Sáu / ĐBP
    (10.7600, 106.7020, 0.008, 0.008),  # Quận 4 - Hoàng Diệu
    (10.7550, 106.6700, 0.010, 0.010),  # Quận 5 - An Đông / Nguyễn Trãi
    (10.7500, 106.6500, 0.009, 0.009),  # Quận 6 - Hậu Giang / Chợ Lớn
    (10.7350, 106.7150, 0.012, 0.012),  # Quận 7 - Phú Mỹ Hưng / Nguyễn Thị Thập
    (10.7420, 106.6750, 0.008, 0.008),  # Quận 8 - Phạm Thế Hiển
    (10.7700, 106.6680, 0.010, 0.010),  # Quận 10 - 3 Tháng 2 / Tô Hiến Thành
    (10.7650, 106.6480, 0.008, 0.008),  # Quận 11 - Lê Đại Hành
    (10.8000, 106.7100, 0.012, 0.012),  # Bình Thạnh - Điện Biên Phủ / Đinh Bộ Lĩnh
    (10.7960, 106.6850, 0.008, 0.008),  # Phú Nhuận - Phan Xinh / Phan Đăng Lưu
    (10.8020, 106.6500, 0.011, 0.011),  # Tân Bình - Cộng Hòa / Trường Chinh
    (10.8350, 106.6650, 0.012, 0.012),  # Gò Vấp - Quang Trung / Nguyễn Oanh
    (10.8050, 106.7400, 0.012, 0.012),  # Thủ Đức - Thảo Điền / An Phú
    (10.8550, 106.7800, 0.015, 0.015),  # Thủ Đức - Khu Công Nghệ Cao / ĐHQG
]

orders = []
num_orders = 500
orders_per_zone = num_orders // len(district_street_centers) # ~33 orders per zone
remainder = num_orders % len(district_street_centers)

order_id = 1
for zone_idx, (c_lat, c_lon, r_lat, r_lon) in enumerate(district_street_centers):
    count = orders_per_zone + (1 if zone_idx < remainder else 0)
    for _ in range(count):
        # Generate coordinates within residential/street land offset
        # Use normal distribution to concentrate along streets
        lat_offset = np.random.normal(0, r_lat / 2.5)
        lon_offset = np.random.normal(0, r_lon / 2.5)
        
        # Clip to ensure bounds
        lat_offset = np.clip(lat_offset, -r_lat, r_lat)
        lon_offset = np.clip(lon_offset, -r_lon, r_lon)
        
        lat = round(c_lat + lat_offset, 7)
        lon = round(c_lon + lon_offset, 7)
        
        # Weight from 0.5kg to 15kg
        weight_kg = round(random.uniform(0.5, 12.5), 2)
        
        orders.append({
            "order_id": order_id,
            "lat": lat,
            "lon": lon,
            "weight_kg": weight_kg,
            "weight": 5.0,
            "status": "pending",
            "assigned_hub_id": 1
        })
        order_id += 1

df_orders = pd.DataFrame(orders)

# Save to data/
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

df_hubs.to_csv(os.path.join(data_dir, "hub_candidates.csv"), index=False)
df_orders.to_csv(os.path.join(data_dir, "orders.csv"), index=False)

print(f"SUCCESSfully generated:")
print(f" - {len(df_hubs)} Hub candidates in data/hub_candidates.csv")
print(f" - {len(df_orders)} Orders in data/orders.csv")

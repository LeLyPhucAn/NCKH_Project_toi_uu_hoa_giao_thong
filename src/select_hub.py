import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2


def haversine_matrix(orders_coords, hubs_coords):
    """
    Tính ma trận khoảng cách Haversine (km) giữa tất cả cặp (order, hub).
    Chính xác hơn Euclidean vì tính đến độ cong bề mặt Trái Đất.
    Vectorized bằng numpy để đủ nhanh với 300 × 15 = 4500 cặp.
    """
    R = 6371.0  # Bán kính Trái Đất (km)

    # Chuyển sang radian
    o_lat = np.radians(orders_coords[:, 0])[:, np.newaxis]   # (300, 1)
    o_lon = np.radians(orders_coords[:, 1])[:, np.newaxis]   # (300, 1)
    h_lat = np.radians(hubs_coords[:, 0])[np.newaxis, :]     # (1, 15)
    h_lon = np.radians(hubs_coords[:, 1])[np.newaxis, :]     # (1, 15)

    dlat = h_lat - o_lat
    dlon = h_lon - o_lon

    a = np.sin(dlat / 2) ** 2 + np.cos(o_lat) * np.cos(h_lat) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c  # ma trận (300, 15) km


def select_hub(hubs_df, orders_df, num_hubs=5):
    print("[3/7] Selecting Optimal Hubs (Greedy + Haversine)...")
    hubs_coords = hubs_df[['lat', 'lon']].values
    orders_coords = orders_df[['lat', 'lon']].values

    # FIX: Dùng khoảng cách Haversine thay vì Euclidean trên tọa độ lat/lon
    dist_matrix = haversine_matrix(orders_coords, hubs_coords)

    selected_indices = []
    for _ in range(num_hubs):
        best_hub = -1
        min_total_dist = float('inf')

        for i in range(len(hubs_df)):
            if i in selected_indices:
                continue
            temp_selected = selected_indices + [i]
            # Mỗi đơn được phục vụ bởi hub gần nhất trong tập đã chọn
            total_dist = np.sum(np.min(dist_matrix[:, temp_selected], axis=1))
            if total_dist < min_total_dist:
                min_total_dist, best_hub = total_dist, i

        selected_indices.append(best_hub)
        chosen_name = hubs_df.iloc[best_hub]['name']
        print(f"  -> Chọn Hub #{len(selected_indices)}: {chosen_name} (tổng khoảng cách giảm còn {min_total_dist:.2f} km)")

    selected_hubs = hubs_df.iloc[selected_indices].copy()
    selected_hubs.to_csv("results/selected_hubs.csv", index=False)
    print(f"  -> {num_hubs} Selected Hubs saved to results/selected_hubs.csv")
    return selected_hubs
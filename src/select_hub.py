import os
import pandas as pd
import numpy as np
import itertools

def haversine_matrix(orders_coords, hubs_coords):
    """
    Tính ma trận khoảng cách Haversine (km) giữa tất cả cặp (order, hub).
    Vectorized bằng numpy để chạy nhanh.
    """
    R = 6371.0  # Bán kính Trái Đất (km)

    # Chuyển sang radian
    o_lat = np.radians(orders_coords[:, 0])[:, np.newaxis]   # (300, 1)
    o_lon = np.radians(orders_coords[:, 1])[:, np.newaxis]   # (300, 1)
    h_lat = np.radians(hubs_coords[:, 0])[np.newaxis, :]     # (1, num_hubs)
    h_lon = np.radians(hubs_coords[:, 1])[np.newaxis, :]     # (1, num_hubs)

    dlat = h_lat - o_lat
    dlon = h_lon - o_lon

    a = np.sin(dlat / 2) ** 2 + np.cos(o_lat) * np.cos(h_lat) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c  # ma trận (num_orders, num_hubs) km


def select_hub(hubs_df, orders_df, num_hubs=3):
    """
    Thuật toán K-Medoids tối ưu hóa chọn Hub:
    Tìm tập hợp K Hubs trong số các ứng viên sao cho tổng khoảng cách từ mỗi đơn hàng
    đến Hub gần nhất được gán là NHỎ NHẤT.
    Vì số lượng Hub ứng viên nhỏ (6 Hub), chúng ta sử dụng phương pháp tìm kiếm vét cạn (Brute-force)
    để tìm ra nghiệm tối ưu toàn cục (Global Optimum), tránh bị kẹt ở nghiệm cục bộ như K-Means/K-Medoids thông thường.
    """
    print(f"[3/7] Selecting {num_hubs} Optimal Hubs using Global K-Medoids...")
    
    hubs_coords = hubs_df[['lat', 'lon']].values
    orders_coords = orders_df[['lat', 'lon']].values

    # 1. Tính ma trận khoảng cách Haversine giữa 300 orders và các Hubs
    dist_matrix = haversine_matrix(orders_coords, hubs_coords) # shape: (300, num_candidates)

    num_candidates = len(hubs_df)
    if num_hubs > num_candidates:
        num_hubs = num_candidates

    # 2. Tìm tất cả các tổ hợp chập K của các Hub ứng viên
    candidates_indices = list(range(num_candidates))
    combinations = list(itertools.combinations(candidates_indices, num_hubs))

    best_combination = None
    min_global_dist = float('inf')

    # 3. Duyệt qua từng tổ hợp để tìm tổ hợp có tổng khoảng cách nhỏ nhất
    for combo in combinations:
        # Với mỗi đơn hàng, tìm khoảng cách đến Hub gần nhất trong tổ hợp đang xét
        min_dists_for_combo = np.min(dist_matrix[:, combo], axis=1)
        total_dist = np.sum(min_dists_for_combo)

        if total_dist < min_global_dist:
            min_global_dist = total_dist
            best_combination = combo

    # 4. Gán nhãn cụm (cluster) cho từng đơn hàng dựa trên Hub gần nhất được chọn
    best_combo_dist_matrix = dist_matrix[:, best_combination]
    assigned_hub_indices_in_combo = np.argmin(best_combo_dist_matrix, axis=1)
    
    # Chuyển index trong combo thành index thực tế của hubs_df
    assigned_hub_ids = [hubs_df.iloc[best_combination[i]]['hub_id'] for i in assigned_hub_indices_in_combo]
    
    # 5. Lưu kết quả gán Hub vào orders_df
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    orders_df['assigned_hub_id'] = assigned_hub_ids
    orders_df.to_csv(os.path.join(data_dir, "orders.csv"), index=False)

    # 6. In và lưu kết quả danh sách Hub được chọn
    selected_hubs = hubs_df.iloc[list(best_combination)].copy()
    selected_hubs.to_csv(os.path.join(results_dir, "selected_hubs.csv"), index=False)
    
    print(f"  -> Global K-Medoids Optimization Finished!")
    print(f"  -> Total distance to nearest hubs: {min_global_dist:.2f} km")
    print(f"  -> Selected Hubs:")
    for idx, row in selected_hubs.iterrows():
        # Đếm số đơn hàng gán cho hub này
        assigned_count = sum(1 for h_id in assigned_hub_ids if h_id == row['hub_id'])
        print(f"     Hub {int(row['hub_id'])}: {row['name']} -> Phục vụ: {assigned_count} đơn hàng")
        
    return selected_hubs
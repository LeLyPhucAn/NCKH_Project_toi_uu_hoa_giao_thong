import numpy as np
import pandas as pd
from shared.utils.haversine import haversine_matrix


def run_greedy_pmedian(hubs_df: pd.DataFrame, orders_df: pd.DataFrame, num_hubs: int = 5) -> pd.DataFrame:
    """Thuật toán Greedy chọn p vị trí Micro Hubs tối ưu nhất dựa trên ma trận Haversine."""
    hubs_coords = hubs_df[['lat', 'lon']].values
    orders_coords = orders_df[['lat', 'lon']].values

    dist_matrix = haversine_matrix(orders_coords, hubs_coords)

    selected_indices = []
    for _ in range(min(num_hubs, len(hubs_df))):
        best_hub = -1
        min_total_dist = float('inf')

        for i in range(len(hubs_df)):
            if i in selected_indices:
                continue
            temp_selected = selected_indices + [i]
            total_dist = np.sum(np.min(dist_matrix[:, temp_selected], axis=1))
            if total_dist < min_total_dist:
                min_total_dist, best_hub = total_dist, i

        if best_hub != -1:
            selected_indices.append(best_hub)

    selected_hubs = hubs_df.iloc[selected_indices].copy()
    return selected_hubs

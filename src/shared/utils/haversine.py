import math
import numpy as np


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách Haversine (km) giữa 2 tọa độ lat/lon."""
    R = 6371.0  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def haversine_matrix(orders_coords: np.ndarray, hubs_coords: np.ndarray) -> np.ndarray:
    """Vectorized calculation ma trận khoảng cách Haversine (km) (orders × hubs)."""
    R = 6371.0
    o_lat = np.radians(orders_coords[:, 0])[:, np.newaxis]
    o_lon = np.radians(orders_coords[:, 1])[:, np.newaxis]
    h_lat = np.radians(hubs_coords[:, 0])[np.newaxis, :]
    h_lon = np.radians(hubs_coords[:, 1])[np.newaxis, :]

    dlat = h_lat - o_lat
    dlon = h_lon - o_lon

    a = np.sin(dlat / 2) ** 2 + np.cos(o_lat) * np.cos(h_lat) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

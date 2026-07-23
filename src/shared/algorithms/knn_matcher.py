import osmnx as ox
import pandas as pd
from typing import Dict, Any


def match_hubs_and_orders_to_nodes(G_road, hubs_df: pd.DataFrame, orders_df: pd.DataFrame) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    """Map-matching vị trí Lat/Lon của Hub và Order vào nút mạng lưới giao thông gần nhất bằng K-NN."""
    hub_nodes = {}
    for _, hub in hubs_df.iterrows():
        hub_nodes[hub["hub_id"]] = ox.distance.nearest_nodes(G_road, X=hub["lon"], Y=hub["lat"])

    order_nodes = {}
    for idx, order in orders_df.iterrows():
        order_nodes[order["order_id"]] = ox.distance.nearest_nodes(G_road, X=order["lon"], Y=order["lat"])

    return hub_nodes, order_nodes

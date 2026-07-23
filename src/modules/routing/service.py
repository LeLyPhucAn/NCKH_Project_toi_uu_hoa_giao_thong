import pandas as pd
import networkx as nx
import osmnx as ox
from repositories.data_repository import DataRepository
from repositories.graph_repository import GraphRepository
from repositories.result_repository import ResultRepository
from shared.algorithms.dijkstra import run_dijkstra_shortest_path
from shared.utils.haversine import haversine_distance
from core.logger import get_logger

logger = get_logger("RoutingService")


def get_nearest_hub(order_lat: float, order_lon: float, hubs_df: pd.DataFrame) -> pd.Series:
    best_idx = hubs_df.index[0]
    min_dist = float("inf")
    for idx, hub in hubs_df.iterrows():
        dist = haversine_distance(order_lat, order_lon, hub["lat"], hub["lon"])
        if dist < min_dist:
            min_dist = dist
            best_idx = idx
    return hubs_df.loc[best_idx]


class RoutingService:
    @staticmethod
    def execute_routing() -> pd.DataFrame:
        logger.info("Đang thực thi Routing Dijkstra trên các kịch bản...")
        G = GraphRepository.load_or_build_graph()
        orders_df = DataRepository.load_orders()
        hubs_df = ResultRepository.load_selected_hubs()

        if hubs_df is None or hubs_df.empty:
            hubs_df = DataRepository.load_hubs().head(5)

        results = []
        road_nodes = [n for n, d in G.nodes(data=True) if d.get("mode") not in ["metro_station", "waterbus_station"]]
        G_road = G.subgraph(road_nodes)

        traffic_conditions = ["Off-Peak", "Peak"]

        scenarios = {
            "Road Only":        ["road"],
            "Road + Metro":     ["road", "metro", "transfer"],
            "Road + Waterbus":  ["road", "waterbus", "transfer"],
            "Full Multimodal":  ["road", "metro", "waterbus", "transfer"],
        }

        # Cache subgraphs
        subgraph_cache = {}
        for scenario_name, allowed_modes in scenarios.items():
            valid_edges = []
            for u, v, k, d in G.edges(keys=True, data=True):
                mode = d.get("mode")
                if mode == "transfer":
                    ttype = d.get("transfer_type")
                    if "Metro" in scenario_name and ttype != "metro":
                        continue
                    if "Waterbus" in scenario_name and ttype != "waterbus":
                        continue
                if mode in allowed_modes:
                    valid_edges.append((u, v, k))
            subgraph_cache[scenario_name] = G.edge_subgraph(valid_edges)

        hub_nodes = {hub["hub_id"]: ox.distance.nearest_nodes(G_road, X=hub["lon"], Y=hub["lat"]) for _, hub in hubs_df.iterrows()}

        for order_idx, order in orders_df.iterrows():
            order_node = ox.distance.nearest_nodes(G_road, X=order["lon"], Y=order["lat"])
            nearest_hub = get_nearest_hub(order["lat"], order["lon"], hubs_df)
            hub_node = hub_nodes[nearest_hub["hub_id"]]

            if hub_node == order_node:
                continue

            for traffic in traffic_conditions:
                for scenario_name, G_sub in subgraph_cache.items():
                    try:
                        path, (dist_km, time_min, co2_emit, cost_vnd, modes) = run_dijkstra_shortest_path(
                            G_sub, source_node=hub_node, target_node=order_node, traffic_condition=traffic
                        )
                        results.append({
                            "order_id":          order["order_id"],
                            "hub_id":            nearest_hub["hub_id"],
                            "hub_strategy":      "nearest",
                            "traffic_condition": traffic,
                            "scenario":          scenario_name,
                            "time":              round(time_min, 4),
                            "distance":          round(dist_km, 4),
                            "cost":              round(cost_vnd, 2),
                            "co2":               round(co2_emit, 4),
                            "modes_used":        modes,
                        })
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        pass

        df_res = pd.DataFrame(results)
        if not df_res.empty:
            ResultRepository.save_routing_results(df_res)
            logger.info(f"Đã hoàn thành định tuyến cho {df_res['order_id'].nunique()} đơn hàng.")
        return df_res

    @staticmethod
    def get_routing_results():
        res = ResultRepository.load_routing_results()
        if res is not None and not res.empty:
            return res.to_dict(orient="records")
        return []

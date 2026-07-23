import os
import pickle
import pandas as pd
import networkx as nx
import osmnx as ox
from core.config.settings import settings
from core.constants.transport import (
    SPEED_KMH,
    CO2_EMISSION_FACTORS,
    HANDLING_TIME_MINUTES,
    MAX_TRANSFER_DISTANCE_KM,
    COST_RATES
)
from core.logger import get_logger
from repositories.data_repository import DataRepository
from shared.utils.haversine import haversine_distance

logger = get_logger("GraphRepository")


class GraphRepository:
    """Repository quản lý khởi tạo, xây dựng & Caching Đồ thị Mạng lưới Đa phương thức."""

    @staticmethod
    def load_or_build_graph(force_rebuild: bool = False) -> nx.MultiDiGraph:
        cache_path = settings.GRAPH_CACHE_PATH
        if not force_rebuild and os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    G = pickle.load(f)
                logger.info("Đã nạp đồ thị Multimodal Graph từ Cache pkl.")
                return G
            except Exception as e:
                logger.warning(f"Cache lỗi ({e}), tiến hành dựng lại Đồ thị...")
                if os.path.exists(cache_path):
                    os.remove(cache_path)

        return GraphRepository._build_graph()

    @staticmethod
    def _build_graph() -> nx.MultiDiGraph:
        logger.info("Đang tải mạng lưới đường bộ OpenStreetMap TP.HCM (OSMnx)...")
        places = ["District 1, Ho Chi Minh City, Vietnam"]
        G = ox.graph_from_place(places, network_type="drive")

        # Gán thuộc tính mặc định cho cạnh đường bộ
        for u, v, k, d in G.edges(keys=True, data=True):
            d["mode"] = "road"
            d["co2"] = CO2_EMISSION_FACTORS["road"]
            d["cost"] = COST_RATES["road_per_km"] * (d.get("length", 0) / 1000.0)
            length_km = d.get("length", 0) / 1000.0
            d["travel_time"] = (length_km / SPEED_KMH["road_offpeak"]) * 60.0

        metro_df = DataRepository.load_metro()
        metro_edges = DataRepository.load_metro_edges()
        waterbus_df = DataRepository.load_waterbus()

        GraphRepository._add_waterbus_layer(G, waterbus_df)
        GraphRepository._add_metro_layer(G, metro_df, metro_edges)
        GraphRepository._add_transfer_edges(G)

        with open(settings.GRAPH_CACHE_PATH, 'wb') as f:
            pickle.dump(G, f)
        logger.info("Đã lưu Đồ thị vào Cache pkl thành công.")
        return G

    @staticmethod
    def _add_waterbus_layer(G: nx.MultiDiGraph, df: pd.DataFrame):
        for idx, row in df.iterrows():
            node_id = f"waterbus_{idx}"
            G.add_node(node_id, y=row["lat"], x=row["lon"], mode="waterbus_station", station_name=row["name"].strip())
            if idx > 0:
                prev_node = f"waterbus_{idx - 1}"
                dist_km = haversine_distance(row["lat"], row["lon"], df.iloc[idx - 1]["lat"], df.iloc[idx - 1]["lon"])
                time_min = (dist_km / SPEED_KMH["waterbus"]) * 60.0
                G.add_edge(prev_node, node_id, length=dist_km * 1000, travel_time=time_min, mode="waterbus", co2=CO2_EMISSION_FACTORS["waterbus"], cost=0.0)
                G.add_edge(node_id, prev_node, length=dist_km * 1000, travel_time=time_min, mode="waterbus", co2=CO2_EMISSION_FACTORS["waterbus"], cost=0.0)

    @staticmethod
    def _add_metro_layer(G: nx.MultiDiGraph, metro_df: pd.DataFrame, edges_df: pd.DataFrame):
        for _, row in metro_df.iterrows():
            node_id = f"metro_{row['name'].strip()}"
            G.add_node(node_id, y=row["lat"], x=row["lon"], mode="metro_station", station_name=row["name"].strip())

        for _, row in edges_df.iterrows():
            u_node = f"metro_{row['source'].strip()}"
            v_node = f"metro_{row['target'].strip()}"
            if G.has_node(u_node) and G.has_node(v_node):
                u_data = G.nodes[u_node]
                v_data = G.nodes[v_node]
                dist_km = haversine_distance(u_data["y"], u_data["x"], v_data["y"], v_data["x"])
                time_min = (dist_km / SPEED_KMH["metro"]) * 60.0 + 0.5  # dwell 30s
                G.add_edge(u_node, v_node, length=dist_km * 1000, travel_time=time_min, mode="metro", co2=CO2_EMISSION_FACTORS["metro"], cost=COST_RATES["metro_per_trip"])
                G.add_edge(v_node, u_node, length=dist_km * 1000, travel_time=time_min, mode="metro", co2=CO2_EMISSION_FACTORS["metro"], cost=COST_RATES["metro_per_trip"])

    @staticmethod
    def _add_transfer_edges(G: nx.MultiDiGraph):
        road_nodes = [n for n, d in G.nodes(data=True) if d.get("mode") not in ["metro_station", "waterbus_station"]]
        transit_nodes = [n for n, d in G.nodes(data=True) if d.get("mode") in ["metro_station", "waterbus_station"]]

        for t_node in transit_nodes:
            t_data = G.nodes[t_node]
            t_lat, t_lon = t_data["y"], t_data["x"]
            ttype = "metro" if t_data.get("mode") == "metro_station" else "waterbus"

            nearest_road_node = ox.distance.nearest_nodes(G.subgraph(road_nodes), X=t_lon, Y=t_lat)
            r_data = G.nodes[nearest_road_node]
            dist_km = haversine_distance(t_lat, t_lon, r_data["y"], r_data["x"])

            if dist_km <= MAX_TRANSFER_DISTANCE_KM:
                time_min = HANDLING_TIME_MINUTES
                G.add_edge(nearest_road_node, t_node, length=dist_km * 1000, travel_time=time_min, mode="transfer", transfer_type=ttype, co2=CO2_EMISSION_FACTORS["transfer"], cost=COST_RATES["transfer_per_handling"])
                G.add_edge(t_node, nearest_road_node, length=dist_km * 1000, travel_time=time_min, mode="transfer", transfer_type=ttype, co2=CO2_EMISSION_FACTORS["transfer"], cost=COST_RATES["transfer_per_handling"])

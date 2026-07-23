import networkx as nx
from typing import Dict, Any, List, Tuple
from core.constants.transport import CO2_EMISSION_FACTORS, COST_RATES



def make_weight_fn(traffic_condition: str):
    """Tạo hàm trọng số cho Dijkstra hỗ trợ điều chỉnh giờ cao điểm/thấp điểm."""
    def get_weight(u, v, edge_dict):
        min_w = float("inf")
        for key, d in edge_dict.items():
            t = d.get("travel_time", 0)
            w = t * 2.5 if (traffic_condition == "Peak" and d.get("mode") == "road") else t
            if w < min_w:
                min_w = w
        return min_w
    return get_weight


def get_best_edge_data(G_sub: nx.MultiDiGraph, u: Any, v: Any, traffic_condition: str) -> Dict[str, Any]:
    edges = G_sub[u][v]
    best_key = list(edges.keys())[0]
    min_w = float("inf")
    for key, data in edges.items():
        t = data.get("travel_time", 0)
        w = t * 2.5 if (traffic_condition == "Peak" and data.get("mode") == "road") else t
        if w < min_w:
            min_w = w
            best_key = key
    return edges[best_key]


def compute_route_metrics(G_sub: nx.MultiDiGraph, path: List[Any], traffic_condition: str) -> Tuple[float, float, float, float, str]:
    """Tính toán quãng đường, thời gian, lượng phát thải CO2, chi phí và các phương thức sử dụng."""
    dist_km = time_min = co2_emit = cost_vnd = 0.0
    modes_used = set()

    for i in range(len(path) - 1):
        edge_data = get_best_edge_data(G_sub, path[i], path[i + 1], traffic_condition)
        l_km = edge_data.get("length", 0) / 1000.0
        mode = edge_data.get("mode", "road")
        modes_used.add(mode)
        dist_km += l_km

        t_edge = edge_data.get("travel_time", 0)
        if traffic_condition == "Peak" and mode == "road":
            t_edge *= 2.5
        time_min += t_edge

        co2_factor = edge_data.get("co2", CO2_EMISSION_FACTORS.get(mode, 0.12))
        co2_emit += l_km * co2_factor

        if mode == "road":
            cost_vnd += l_km * COST_RATES["road_per_km"]
        elif mode == "transfer":
            cost_vnd += edge_data.get("cost", COST_RATES["transfer_per_handling"])

    return dist_km, time_min, co2_emit, cost_vnd, "+".join(sorted(modes_used))


def run_dijkstra_shortest_path(G_sub: nx.MultiDiGraph, source_node: Any, target_node: Any, traffic_condition: str):
    """Thực thi thuật toán Dijkstra tìm đường ngắn nhất trên đồ thị phụ."""
    weight_fn = make_weight_fn(traffic_condition)
    path = nx.shortest_path(G_sub, source=source_node, target=target_node, weight=weight_fn)
    metrics = compute_route_metrics(G_sub, path, traffic_condition)
    return path, metrics

"""
ROUTING MODULE - So sánh hiệu quả giao hàng Đa phương thức vs Truyền thống
===========================================================================
Luồng giao hàng thực tế:
  Mega-Hub (Bến xe Miền Đông Mới, Thủ Đức) → [Metro/Waterbus/Xe máy] → Hub Q1 → [Xe máy] → Khách hàng

Các kịch bản so sánh:
  1. Road Only:       Mega-Hub → (xe máy chạy thẳng 16km) → Khách hàng
  2. Road + Metro:    Mega-Hub → (xe máy đến ga Metro) → (Metro) → (xe máy từ ga đến KH)
  3. Road + Waterbus: Mega-Hub → (xe máy đến bến tàu) → (Waterbus) → (xe máy từ bến đến KH)
  4. Full Multimodal: Mega-Hub → (Chọn đường tối ưu nhất kết hợp tất cả phương tiện)
"""
import os
import networkx as nx
import osmnx as ox
import pandas as pd
import numpy as np
import math


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_nearest_hub(order_lat, order_lon, hubs_df):
    best_idx = hubs_df.index[0]
    min_dist = float("inf")
    for idx, hub in hubs_df.iterrows():
        dist = haversine_km(order_lat, order_lon, hub["lat"], hub["lon"])
        if dist < min_dist:
            min_dist = dist
            best_idx = idx
    return hubs_df.loc[best_idx]


def make_weight_fn(traffic):
    """Hàm tính trọng số cạnh: Giờ cao điểm → đường bộ chậm gấp 2.5 lần."""
    def get_weight(u, v, edge_dict):
        min_w = float("inf")
        for key, d in edge_dict.items():
            t = d.get("travel_time", 0)
            w = t * 2.5 if (traffic == "Peak" and d.get("mode") == "road") else t
            if w < min_w:
                min_w = w
        return min_w
    return get_weight


def get_best_edge_data(G_sub, u, v, traffic_condition):
    """Lấy dữ liệu cạnh tốt nhất (nhẹ nhất) giữa 2 nút."""
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


def compute_route_metrics(G_sub, path, traffic):
    """Tính toán các chỉ số KPI từ một đường đi (path)."""
    dist_km = time_min = co2_emit = cost_vnd = 0.0
    modes_used = set()
    for i in range(len(path) - 1):
        edge_data = get_best_edge_data(G_sub, path[i], path[i + 1], traffic)
        l_km = edge_data.get("length", 0) / 1000
        mode = edge_data.get("mode", "road")
        modes_used.add(mode)
        dist_km += l_km
        t_edge = edge_data.get("travel_time", 0)
        if traffic == "Peak" and mode == "road":
            t_edge *= 2.5
        time_min += t_edge

        # Chi phí CO2 và tiền
        if mode == "road":
            co2_emit += l_km * 0.12       # Xe máy: 0.12 kg CO2 / km
            cost_vnd += l_km * 3000.0      # Xe máy: 3,000 VND / km
        elif mode == "metro":
            co2_emit += l_km * 0.02        # Metro điện: 0.02 kg CO2 / km (Rất thấp)
            cost_vnd += 0                  # Đã tính phí vé ở transfer edge
        elif mode == "waterbus":
            co2_emit += l_km * 0.05        # Waterbus: 0.05 kg CO2 / km
            cost_vnd += 0                  # Đã tính phí vé ở transfer edge
        elif mode == "transfer":
            co2_emit += 0                  # Không phát thải khi lên/xuống ga
            cost_vnd += edge_data.get("cost", 7000.0)  # Phí vé

    return dist_km, time_min, co2_emit, cost_vnd, "+".join(sorted(modes_used))


def build_subgraph(G, allowed_modes, scenario_name):
    """Lọc đồ thị chỉ giữ lại các cạnh thuộc loại phương tiện được phép."""
    valid_edges = []
    for u, v, k, d in G.edges(keys=True, data=True):
        mode = d.get("mode")

        # Lọc transfer edges: Chỉ giữ transfer phù hợp với kịch bản
        if mode == "transfer":
            ttype = d.get("transfer_type", "")
            if scenario_name in ["Road Only", "Central Road Only"]:
                continue  # Road Only không có transfer
            if "Metro" in scenario_name and "Waterbus" not in scenario_name and "Full" not in scenario_name and "Multimodal" not in scenario_name:
                if ttype != "metro":
                    continue
            if "Waterbus" in scenario_name and "Metro" not in scenario_name and "Full" not in scenario_name and "Multimodal" not in scenario_name:
                if ttype != "waterbus":
                    continue

        if mode in allowed_modes:
            valid_edges.append((u, v, k))

    return G.edge_subgraph(valid_edges)


def routing(G, orders_df, hubs_df):
    """
    Chạy so sánh hiệu quả giữa 4 kịch bản giao hàng:
    Xuất phát từ Mega-Hub (Bến xe Miền Đông Mới, Thủ Đức) → Khách hàng (Quận 1).
    """
    print("[4/7] Running Routing: Mega-Hub (Thu Duc) → District 1 Customers...")
    results = []
    skipped = 0

    # Lọc ra các node đường bộ thuần túy
    road_nodes = [n for n, d in G.nodes(data=True)
                  if isinstance(n, int) and d.get("mode") not in ["metro_station", "waterbus_station", "hub_candidate"]]
    G_road = G.subgraph(road_nodes)

    # ─── MEGA-HUB: Bến xe Miền Đông Mới (Ga 14 Metro Line 1 ─ Thủ Đức) ───
    MEGA_HUB_LAT = 10.880667
    MEGA_HUB_LON = 106.814886
    mega_hub_node = ox.distance.nearest_nodes(G_road, X=MEGA_HUB_LON, Y=MEGA_HUB_LAT)
    print(f"  -> Mega-Hub (Thu Duc): Node {mega_hub_node} ({MEGA_HUB_LAT}, {MEGA_HUB_LON})")

    # ─── Định nghĩa 4 kịch bản ───
    scenarios = {
        "Road Only":        ["road"],
        "Road + Metro":     ["road", "metro", "transfer"],
        "Road + Waterbus":  ["road", "waterbus", "transfer"],
        "Full Multimodal":  ["road", "metro", "waterbus", "transfer"],
    }

    traffic_conditions = ["Off-Peak", "Peak"]

    # ─── Pre-filter subgraphs ───
    print("  -> Pre-filtering subgraphs...")
    subgraph_cache = {}
    for name, modes in scenarios.items():
        subgraph_cache[name] = build_subgraph(G, modes, name)

    # Debug: Đếm số cạnh transfer liên kết
    metro_t = sum(1 for u, v, k, d in G.edges(keys=True, data=True)
                  if d.get("mode") == "transfer" and d.get("transfer_type") == "metro")
    water_t = sum(1 for u, v, k, d in G.edges(keys=True, data=True)
                  if d.get("mode") == "transfer" and d.get("transfer_type") == "waterbus")
    print(f"  -> Transfer edges: Metro={metro_t}, Waterbus={water_t}")

    # ─── NEAREST HUB STRATEGY: Mega-Hub → Hub gần nhất của KH → KH ───
    print("  -> Strategy: NEAREST HUB (Mega-Hub → nearest Q1 Hub → Customer)")
    
    # Tìm node đường bộ gần mỗi Hub nhất
    hub_nodes = {}
    for _, hub in hubs_df.iterrows():
        hub_nodes[hub["hub_id"]] = ox.distance.nearest_nodes(G_road, X=hub["lon"], Y=hub["lat"])

    for order_idx, order in orders_df.iterrows():
        order_node = ox.distance.nearest_nodes(G_road, X=order["lon"], Y=order["lat"])

        # Tìm Hub gần đơn hàng nhất
        nearest_hub = get_nearest_hub(order["lat"], order["lon"], hubs_df)
        hub_node = hub_nodes[nearest_hub["hub_id"]]

        if mega_hub_node == order_node:
            skipped += 1
            continue

        for traffic in traffic_conditions:
            get_weight = make_weight_fn(traffic)

            for scenario_name, G_sub in subgraph_cache.items():
                try:
                    # Tìm đường ngắn nhất từ MEGA-HUB → KHÁCH HÀNG
                    path = nx.shortest_path(G_sub, source=mega_hub_node, target=order_node, weight=get_weight)
                    dist_km, time_min, co2_emit, cost_vnd, modes = compute_route_metrics(G_sub, path, traffic)

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

    # ─── CENTRALIZED HUB STRATEGY: Mega-Hub → Hub trung tâm cố định → KH ───
    print("  -> Strategy: CENTRALIZED (Mega-Hub → Central Hub → Customer)")

    central_hub = hubs_df.loc[hubs_df.apply(
        lambda r: haversine_km(r["lat"], r["lon"], 10.7721, 106.6983), axis=1
    ).idxmin()]
    print(f"  -> Central Hub: {central_hub['name']} (hub_id={central_hub['hub_id']})")

    centralized_scenarios = {
        "Central Road Only":       ["road"],
        "Central Road + Metro":    ["road", "metro", "transfer"],
        "Central Road + Waterbus": ["road", "waterbus", "transfer"],
        "Central Full Multimodal": ["road", "metro", "waterbus", "transfer"],
    }

    central_cache = {}
    for name, modes in centralized_scenarios.items():
        central_cache[name] = build_subgraph(G, modes, name)

    for order_idx, order in orders_df.iterrows():
        order_node = ox.distance.nearest_nodes(G_road, X=order["lon"], Y=order["lat"])

        if mega_hub_node == order_node:
            continue

        for traffic in traffic_conditions:
            get_weight = make_weight_fn(traffic)

            for scenario_name, G_sub in central_cache.items():
                try:
                    path = nx.shortest_path(G_sub, source=mega_hub_node, target=order_node, weight=get_weight)
                    dist_km, time_min, co2_emit, cost_vnd, modes = compute_route_metrics(G_sub, path, traffic)

                    results.append({
                        "order_id":          order["order_id"],
                        "hub_id":            central_hub["hub_id"],
                        "hub_strategy":      "centralized",
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

    # ─── Tổng kết ───
    df_res = pd.DataFrame(results)
    print(f"  -> Skipped: {skipped} orders (same node as mega-hub)")
    if not df_res.empty:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        results_dir = os.path.join(base_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        df_res.to_csv(os.path.join(results_dir, "routing_results.csv"), index=False)
        nearest_cnt = df_res[df_res['hub_strategy'] == 'nearest']['order_id'].nunique()
        central_cnt = df_res[df_res['hub_strategy'] == 'centralized']['order_id'].nunique()
        print(f"  -> Routing done: {nearest_cnt} orders (nearest), {central_cnt} orders (centralized)")

        # In thống kê nhanh để xác nhận sự khác biệt giữa các kịch bản
        print("\n  -> QUICK STATS (Nearest Hub Strategy):")
        for traffic in traffic_conditions:
            df_t = df_res[(df_res['hub_strategy'] == 'nearest') & (df_res['traffic_condition'] == traffic)]
            if df_t.empty:
                continue
            print(f"     [{traffic}]")
            for sc in scenarios.keys():
                df_sc = df_t[df_t['scenario'] == sc]
                if df_sc.empty:
                    continue
                avg_time = df_sc['time'].mean()
                avg_co2 = df_sc['co2'].mean()
                avg_dist = df_sc['distance'].mean()
                mm_count = (df_sc['modes_used'] != 'road').sum()
                print(f"       {sc:<20s}: Time={avg_time:.2f}min | Dist={avg_dist:.2f}km | CO2={avg_co2:.4f}kg | Multimodal={mm_count}")

    return df_res
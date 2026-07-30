import networkx as nx
import osmnx as ox
import pandas as pd
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


def get_best_edge_data(G_sub, u, v, traffic_condition):
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


def make_weight_fn(traffic):
    def get_weight(u, v, edge_dict):
        min_w = float("inf")
        for key, d in edge_dict.items():
            t = d.get("travel_time", 0)
            w = t * 2.5 if (traffic == "Peak" and d.get("mode") == "road") else t
            if w < min_w:
                min_w = w
        return min_w
    return get_weight


def compute_route_metrics(G_sub, path, traffic):
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
        co2_emit += l_km * edge_data.get("co2", 0.12)
        if mode == "road":
            cost_vnd += l_km * 3000.0
        elif mode == "transfer":
            cost_vnd += edge_data.get("cost", 7500.0)
    return dist_km, time_min, co2_emit, cost_vnd, "+".join(sorted(modes_used))


def routing(G, orders_df, hubs_df):
    print("[4/7] Running Routing across Traffic Conditions & Scenarios...")
    results = []
    skipped_same_node = 0

    road_nodes = [n for n, d in G.nodes(data=True)
                  if isinstance(n, int) and d.get("mode") not in ["metro_station", "waterbus_station", "hub_candidate"]]
    G_road = G.subgraph(road_nodes)

    traffic_conditions = ["Off-Peak", "Peak"]

    scenarios = {
        "Road Only":        ["road"],
        "Road + Metro":     ["road", "metro", "transfer"],
        "Road + Waterbus":  ["road", "waterbus", "transfer"],
        "Full Multimodal":  ["road", "metro", "waterbus", "transfer"],
    }

    centralized_scenarios = {
        "Central Road Only":       ["road"],
        "Central Road + Metro":    ["road", "metro", "transfer"],
        "Central Road + Waterbus": ["road", "waterbus", "transfer"],
        "Central Full Multimodal": ["road", "metro", "waterbus", "transfer"],
    }

    def build_subgraph_cache(scenario_dict):
        cache = {}
        for scenario_name, allowed_modes in scenario_dict.items():
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
            cache[scenario_name] = G.edge_subgraph(valid_edges)
        return cache

    print("  -> Pre-filtering subgraphs...")
    subgraph_cache  = build_subgraph_cache(scenarios)
    central_cache   = build_subgraph_cache(centralized_scenarios)

    metro_t  = sum(1 for u,v,k,d in G.edges(keys=True,data=True) if d.get("mode")=="transfer" and d.get("transfer_type")=="metro")
    water_t  = sum(1 for u,v,k,d in G.edges(keys=True,data=True) if d.get("mode")=="transfer" and d.get("transfer_type")=="waterbus")
    print(f"  -> Transfer edges connected: Metro={metro_t}, Waterbus={water_t}")

    hub_nodes = {}
    for _, hub in hubs_df.iterrows():
        hub_nodes[hub["hub_id"]] = ox.distance.nearest_nodes(G_road, X=hub["lon"], Y=hub["lat"])

    central_hub = hubs_df.loc[hubs_df.apply(
        lambda r: haversine_km(r["lat"], r["lon"], 10.7721, 106.6983), axis=1
    ).idxmin()]
    central_hub_node = ox.distance.nearest_nodes(G_road, X=central_hub["lon"], Y=central_hub["lat"])
    print(f"  -> Central hub for Centralized scenarios: {central_hub['name']} (hub_id={central_hub['hub_id']})")

    for order_idx, order in orders_df.iterrows():
        order_node = ox.distance.nearest_nodes(G_road, X=order["lon"], Y=order["lat"])

        nearest_hub = get_nearest_hub(order["lat"], order["lon"], hubs_df)
        hub_node = hub_nodes[nearest_hub["hub_id"]]

        if hub_node == order_node:
            skipped_same_node += 1
        else:
            for traffic in traffic_conditions:
                get_weight = make_weight_fn(traffic)
                for scenario_name, G_sub in subgraph_cache.items():
                    try:
                        path = nx.shortest_path(G_sub, source=hub_node, target=order_node, weight=get_weight)
                        dist_km, time_min, co2_emit, cost_vnd, modes = compute_route_metrics(G_sub, path, traffic)
                        results.append({
                            "order_id":         order["order_id"],
                            "hub_id":           nearest_hub["hub_id"],
                            "hub_strategy":     "nearest",
                            "traffic_condition": traffic,
                            "scenario":         scenario_name,
                            "time":             round(time_min, 4),
                            "distance":         round(dist_km, 4),
                            "cost":             round(cost_vnd, 2),
                            "co2":              round(co2_emit, 4),
                            "modes_used":       modes,
                        })
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        pass

        if central_hub_node == order_node:
            continue
        for traffic in traffic_conditions:
            get_weight = make_weight_fn(traffic)
            for scenario_name, G_sub in central_cache.items():
                try:
                    path = nx.shortest_path(G_sub, source=central_hub_node, target=order_node, weight=get_weight)
                    dist_km, time_min, co2_emit, cost_vnd, modes = compute_route_metrics(G_sub, path, traffic)
                    results.append({
                        "order_id":         order["order_id"],
                        "hub_id":           central_hub["hub_id"],
                        "hub_strategy":     "centralized",
                        "traffic_condition": traffic,
                        "scenario":         scenario_name,
                        "time":             round(time_min, 4),
                        "distance":         round(dist_km, 4),
                        "cost":             round(cost_vnd, 2),
                        "co2":              round(co2_emit, 4),
                        "modes_used":       modes,
                    })
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

    df_res = pd.DataFrame(results)
    print(f"  -> Skipped: {skipped_same_node} orders (same node as hub)")
    if not df_res.empty:
        df_res.to_csv("results/routing_results.csv", index=False)
        nearest_cnt = df_res[df_res['hub_strategy']=='nearest']['order_id'].nunique()
        central_cnt = df_res[df_res['hub_strategy']=='centralized']['order_id'].nunique()
        print(f"  -> Routing done: {nearest_cnt} orders (nearest-hub), {central_cnt} orders (centralized)")
    return df_res
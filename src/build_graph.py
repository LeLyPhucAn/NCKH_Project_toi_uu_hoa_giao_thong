import os
import math
import pickle
import re
import unicodedata
import networkx as nx
import osmnx as ox
import pandas as pd

ox.settings.log_console = False


def calculate_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách Haversine giữa 2 tọa độ (km)."""
    R = 6371  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def add_waterbus_layer(G, df, speed_kmh=20, co2_factor=0.05):
    """Khởi tạo các bến sông (Waterbus) và tạo liên kết 2 chiều tuần tự."""
    for idx, row in df.iterrows():
        node_id = f"waterbus_{idx}"
        # Đánh dấu node bến Waterbus với thuộc tính tên trạm và vị trí tọa độ
        G.add_node(
            node_id,
            y=row["lat"],
            x=row["lon"],
            mode="waterbus_station",
            station_name=row["name"].strip(),
        )

        if idx > 0:
            prev_node = f"waterbus_{idx - 1}"
            dist_km = calculate_distance(
                row["lat"],
                row["lon"],
                df.iloc[idx - 1]["lat"],
                df.iloc[idx - 1]["lon"],
            )
            time_min = (dist_km / speed_kmh) * 60
            G.add_edge(
                prev_node,
                node_id,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="waterbus",
                co2=co2_factor,
                cost=0.0,
            )
            G.add_edge(
                node_id,
                prev_node,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="waterbus",
                co2=co2_factor,
                cost=0.0,
            )


def normalize_name(name):
    """Chuẩn hóa tên ga phục vụ đối chiếu dữ liệu."""
    name = str(name).strip().lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join([c for c in name if not unicodedata.combining(c)])
    name = name.replace("đ", "d")
    name = re.sub(r"[^a-z0-9]", "", name)
    name = name.replace("tp", "thanhpho")
    name = name.replace("kcncao", "khucongnghecao")
    name = name.replace("kcn", "khucongnghecao")
    name = name.replace("dhqg", "daihocquocgia")
    name = name.replace("bxmmoi", "benxemiendongmoi")
    name = name.replace("miendong", "benxemiendongmoi")
    name = name.replace("suoitien", "daihocquocgia")
    return name


def add_metro_layer_with_edges(
    G, metro_df, edges_df, speed_kmh=40, co2_factor=0.02
):
    """Khởi tạo tất cả ga Metro và nối các ga dựa trên file HCMC_Metro_Edges.csv."""
    station_coords = {}

    # Bước 1: Thêm toàn bộ ga Metro (Nodes) vào đồ thị
    for _, row in metro_df.iterrows():
        station_name = row["name"].strip()
        node_id = f"metro_{station_name}"
        G.add_node(
            node_id,
            y=row["lat"],
            x=row["lon"],
            mode="metro_station",
            station_name=station_name,
        )
        norm_name = normalize_name(station_name)
        station_coords[norm_name] = (row["lat"], row["lon"], station_name)

    # Bước 2: Duyệt qua file Edges để vẽ các đường ray nối giữa các ga
    for _, edge in edges_df.iterrows():
        from_st = str(edge["from_station"]).strip()
        to_st = str(edge["to_station"]).strip()
        line_name = edge["line"]
        norm_from = normalize_name(from_st)
        norm_to = normalize_name(to_st)

        if norm_from in station_coords and norm_to in station_coords:
            coord_u = station_coords[norm_from]
            coord_v = station_coords[norm_to]
            node_u = f"metro_{coord_u[2]}"
            node_v = f"metro_{coord_v[2]}"

            dist_km = calculate_distance(
                coord_u[0], coord_u[1], coord_v[0], coord_v[1]
            )
            time_min = (dist_km / speed_kmh) * 60

            G.add_edge(
                node_u,
                node_v,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="metro",
                line=line_name,
                co2=co2_factor,
                cost=0.0,
            )
            G.add_edge(
                node_v,
                node_u,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="metro",
                line=line_name,
                co2=co2_factor,
                cost=0.0,
            )

    # Bước 3: Nối tuần tự dự phòng cho Metro Line 1
    for i in range(len(metro_df) - 1):
        row_u = metro_df.iloc[i]
        row_v = metro_df.iloc[i + 1]
        node_u = f"metro_{row_u['name'].strip()}"
        node_v = f"metro_{row_v['name'].strip()}"

        if not G.has_edge(node_u, node_v):
            dist_km = calculate_distance(
                row_u["lat"], row_u["lon"], row_v["lat"], row_v["lon"]
            )
            time_min = (dist_km / speed_kmh) * 60

            G.add_edge(
                node_u,
                node_v,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="metro",
                line="Metro 1",
                co2=co2_factor,
                cost=0.0,
            )
            G.add_edge(
                node_v,
                node_u,
                length=dist_km * 1000,
                travel_time=time_min,
                mode="metro",
                line="Metro 1",
                co2=co2_factor,
                cost=0.0,
            )


def add_hub_candidates_layer(G, hubs_df):
    """Đánh dấu tọa độ 15 ứng viên Hub vào đồ thị."""
    for idx, row in hubs_df.iterrows():
        node_id = f"hub_{row['hub_id']}"
        G.add_node(
            node_id,
            y=float(row["lat"]),
            x=float(row["lon"]),
            mode="hub_candidate",
            hub_name=str(row["name"]).strip(),
            hub_id=row["hub_id"],
        )


def connect_multimodal_layers(G, metro_df, waterbus_df, hubs_df=None, max_transfer_dist_km=1.5):
    """Kết nối ga Metro, bến Waterbus và các Hub ứng viên vào mạng lưới đường bộ Quận 1."""
    print("  -> Connecting Metro, Waterbus stations & Hub candidates to District 1 Road Network...")
    road_nodes = [
        n
        for n, d in G.nodes(data=True)
        if isinstance(n, int) and d.get("mode") not in ["metro_station", "waterbus_station", "hub_candidate"]
    ]
    G_road = G.subgraph(road_nodes)

    # 1. Kết nối ga Metro với node đường bộ gần nhất
    for _, row in metro_df.iterrows():
        station_name = str(row["name"]).strip()
        station_node_id = f"metro_{station_name}"
        if station_node_id in G.nodes:
            nearest_road_node = ox.distance.nearest_nodes(
                G_road, X=row["lon"], Y=row["lat"]
            )
            road_lat = G.nodes[nearest_road_node]["y"]
            road_lon = G.nodes[nearest_road_node]["x"]
            dist_km = calculate_distance(
                row["lat"], row["lon"], road_lat, road_lon
            )

            walk_time_min = (dist_km / 5.0) * 60  # Đi bộ 5 km/h
            transfer_time_min = round(1.0 + walk_time_min, 2)  # 1 phút overhead
            G.add_edge(
                nearest_road_node,
                station_node_id,
                length=dist_km * 1000,
                travel_time=transfer_time_min,
                mode="transfer",
                transfer_type="metro",
                cost=7500.0,
                co2=0.0,
            )
            G.add_edge(
                station_node_id,
                nearest_road_node,
                length=dist_km * 1000,
                travel_time=transfer_time_min,
                mode="transfer",
                transfer_type="metro",
                cost=7500.0,
                co2=0.0,
            )

    # 2. Kết nối bến Waterbus với node đường bộ gần nhất
    for idx, row in waterbus_df.iterrows():
        station_name = str(row["name"]).strip()
        station_node_id = f"waterbus_{idx}"
        if station_node_id in G.nodes:
            nearest_road_node = ox.distance.nearest_nodes(
                G_road, X=row["lon"], Y=row["lat"]
            )
            road_lat = G.nodes[nearest_road_node]["y"]
            road_lon = G.nodes[nearest_road_node]["x"]
            dist_km = calculate_distance(
                row["lat"], row["lon"], road_lat, road_lon
            )

            walk_time_min = (dist_km / 5.0) * 60  # Đi bộ 5 km/h
            transfer_time_min = round(2.0 + walk_time_min, 2)  # 2 phút overhead chờ tàu
            G.add_edge(
                nearest_road_node,
                station_node_id,
                length=dist_km * 1000,
                travel_time=transfer_time_min,
                mode="transfer",
                transfer_type="waterbus",
                cost=7500.0,
                co2=0.0,
            )
            G.add_edge(
                station_node_id,
                nearest_road_node,
                length=dist_km * 1000,
                travel_time=transfer_time_min,
                mode="transfer",
                transfer_type="waterbus",
                cost=7500.0,
                co2=0.0,
            )

    # 3. Kết nối 15 Hub ứng viên vào node đường bộ gần nhất
    if hubs_df is not None:
        for _, row in hubs_df.iterrows():
            hub_node_id = f"hub_{row['hub_id']}"
            if hub_node_id in G.nodes:
                nearest_road_node = ox.distance.nearest_nodes(
                    G_road, X=row["lon"], Y=row["lat"]
                )
                road_lat = G.nodes[nearest_road_node]["y"]
                road_lon = G.nodes[nearest_road_node]["x"]
                dist_km = calculate_distance(
                    row["lat"], row["lon"], road_lat, road_lon
                )
                G.add_edge(
                    nearest_road_node,
                    hub_node_id,
                    length=dist_km * 1000,
                    travel_time=dist_km * 2,
                    mode="transfer",
                    transfer_type="hub",
                    cost=0.0,
                    co2=0.0,
                )
                G.add_edge(
                    hub_node_id,
                    nearest_road_node,
                    length=dist_km * 1000,
                    travel_time=dist_km * 2,
                    mode="transfer",
                    transfer_type="hub",
                    cost=0.0,
                    co2=0.0,
                )


def build_graph(
    metro_df,
    metro_edges_df,
    waterbus_df,
    hubs_df,
    orders_df,
    save_path=None,
):
    """Xây dựng Đồ thị Đa phương thức sử dụng OSMnx lấy riêng bản đồ Quận 1."""
    if save_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        save_path = os.path.join(base_dir, "results", "multimodal_graph.pkl")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    print("[2/7] Fetching District 1 map via OSMnx & Building Multimodal Graph...")

    # 1. Tải bản đồ giao thông đường bộ từ OpenStreetMap (Sử dụng Bounding Box)
    # Lấy tọa độ Min/Max của TẤT CẢ các điểm (Metro, Waterbus, Hub, Orders)
    all_lats = pd.concat([metro_df["lat"], waterbus_df["lat"], hubs_df["lat"], orders_df["lat"]])
    all_lons = pd.concat([metro_df["lon"], waterbus_df["lon"], hubs_df["lon"], orders_df["lon"]])
    
    # Tính Bounding Box (Mở rộng thêm 0.01 độ ~ 1.1km mỗi hướng để làm vùng đệm)
    min_lat, max_lat = all_lats.min() - 0.01, all_lats.max() + 0.01
    min_lon, max_lon = all_lons.min() - 0.01, all_lons.max() + 0.01
    bbox = (min_lon, min_lat, max_lon, max_lat) # Format OSMnx v2.x: (left, bottom, right, top)

    print(f"  -> Bounding Box: Lats [{min_lat:.4f}, {max_lat:.4f}], Lons [{min_lon:.4f}, {max_lon:.4f}]")
    try:
        G = ox.graph_from_bbox(bbox=bbox, network_type="drive")
        print(f"  -> Successfully loaded Expanded Road Map ({len(G)} nodes).")
    except Exception as e:
        print(f"  [!] Lỗi khi tải bản đồ OSMnx: {e}")
        return None

    # Gán thuộc tính mặc định cho đường bộ
    for u, v, key, data in G.edges(keys=True, data=True):
        length_km = data.get("length", 0) / 1000
        data["travel_time"] = (length_km / 30) * 60  # Vận tốc shipper 30 km/h
        data["mode"] = "road"
        data["co2"] = 0.12
        data["cost"] = length_km * 3000.0  # Chi phí xe máy 3,000 VND / km

    # 2. Đánh dấu các tầng giao thông công cộng & 15 Hub ứng viên
    add_metro_layer_with_edges(
        G, metro_df, metro_edges_df, speed_kmh=40, co2_factor=0.02
    )
    add_waterbus_layer(G, waterbus_df, speed_kmh=20, co2_factor=0.05)
    add_hub_candidates_layer(G, hubs_df)

    # 3. Kết nối liên thông mạng lưới đa phương thức
    connect_multimodal_layers(G, metro_df, waterbus_df, hubs_df)

    with open(save_path, "wb") as f:
        pickle.dump(G, f)

    print(
        "  -> Graph saved successfully with District 1 road network, Metro, Waterbus, and 15 Hub candidates."
    )
    return G

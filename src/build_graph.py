import math
import pickle
import re
import unicodedata
import networkx as nx
import osmnx as ox
import pandas as pd

ox.settings.log_console = True


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính trái đất (km)
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
    """Giữ nguyên logic nối tuần tự cho bến sông (Waterbus)"""
    for idx, row in df.iterrows():
        node_id = f"waterbus_{idx}"
        # Khởi tạo Node với thuộc tính tên ga thực tế từ CSV để chuẩn hóa đối chiếu
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
    name = str(name).strip().lower()
    # Loại bỏ dấu tiếng Việt
    name = unicodedata.normalize("NFKD", name)
    name = "".join([c for c in name if not unicodedata.combining(c)])
    name = name.replace("đ", "d")
    # Loại bỏ ký tự đặc biệt
    name = re.sub(r"[^a-z0-9]", "", name)
    # Chuẩn hóa viết tắt viết thường
    name = name.replace("tp", "thanhpho")
    name = name.replace("kcncao", "khucongnghecao")
    name = name.replace("kcn", "khucongnghecao")
    name = name.replace("dhqg", "daihocquocgia")
    name = name.replace("bxmmoi", "benxemiendongmoi")
    name = name.replace("miendong", "benxemiendongmoi")
    name = name.replace("suoitien", "daihocquocgia")  # Suối Tiên quy về ĐHQG/BXM Mới
    return name


def add_metro_layer_with_edges(
    G, metro_df, edges_df, speed_kmh=40, co2_factor=0.02
):
    """Khởi tạo tất cả ga Metro và nối các ga dựa trên file HCMC_Metro_Edges.csv

    có chuẩn hóa tên và dự phòng kết nối tuần tự
    """
    station_coords = {}

    # Bước 1: Thêm toàn bộ các ga (Nodes) vào đồ thị
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
        # Lưu tọa độ và tên gốc theo tên đã chuẩn hóa
        norm_name = normalize_name(station_name)
        station_coords[norm_name] = (row["lat"], row["lon"], station_name)

    # Bước 2: Duyệt qua file Edges để vẽ các đoạn đường ray nối giữa các ga
    for _, edge in edges_df.iterrows():
        from_st = str(edge["from_station"]).strip()
        to_st = str(edge["to_station"]).strip()
        line_name = edge["line"]
        norm_from = normalize_name(from_st)
        norm_to = normalize_name(to_st)

        # Kiểm tra xem cả 2 ga này có tồn tại trong file tọa độ metro.csv không
        if norm_from in station_coords and norm_to in station_coords:
            coord_u = station_coords[norm_from]
            coord_v = station_coords[norm_to]
            node_u = f"metro_{coord_u[2]}"
            node_v = f"metro_{coord_v[2]}"

            dist_km = calculate_distance(
                coord_u[0], coord_u[1], coord_v[0], coord_v[1]
            )
            time_min = (dist_km / speed_kmh) * 60

            # Tạo liên kết 2 chiều cho đường ray Metro
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

    # Bước 3: Tự động nối tuần tự các ga Metro Line 1 làm dự phòng
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


def connect_multimodal_layers(G, metro_df, waterbus_df, max_transfer_dist_km=1.5):
    print("  -> Connecting Metro and Waterbus stations to Road Network...")
    road_nodes = [
        n
        for n, d in G.nodes(data=True)
        if d.get("mode") not in ["metro_station", "waterbus_station"]
    ]
    G_road = G.subgraph(road_nodes)

    # Kết nối ga Metro với điểm giao thông đường bộ gần nhất
    for _, row in metro_df.iterrows():
        station_name = row["name"].strip()
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

            if dist_km <= max_transfer_dist_km:
                # Tính transfer_time động: 1 phút overhead + thời gian đi bộ (5 km/h)
                # Thực tế hơn: ga gần (50m) chỉ mất ~1.6 phút, ga xa (500m) mất ~7 phút
                walk_time_min = (dist_km / 5.0) * 60  # vận tốc đi bộ 5 km/h
                transfer_time_min = round(1.0 + walk_time_min, 2)  # 1 phút overhead cố định
                # Vé metro 15,000đ -> gán 7,500đ cho mỗi chiều chuyển tiếp
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
                print(
                    f"     [Connect] Metro ga: {station_name} <-> Đường bộ node: {nearest_road_node} ({dist_km:.3f} km)"
                )
            else:
                print(
                    f"     [Skip] Metro ga {station_name} quá xa mạng đường bộ Q1 ({dist_km:.3f} km)"
                )

    # Kết nối bến Waterbus với điểm giao thông đường bộ gần nhất
    for idx, row in waterbus_df.iterrows():
        station_name = row["name"].strip()
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

            if dist_km <= max_transfer_dist_km:
                # Tính transfer_time động: 2 phút overhead (đợi tàu) + thời gian đi bộ (5 km/h)
                walk_time_min = (dist_km / 5.0) * 60
                transfer_time_min = round(2.0 + walk_time_min, 2)  # 2 phút overhead do tần suất thấp hơn metro
                # Vé waterbus 15,000đ -> gán 7,500đ cho mỗi chiều chuyển tiếp
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
                print(
                    f"     [Connect] Waterbus bến: {station_name} <-> Đường bộ node: {nearest_road_node} ({dist_km:.3f} km)"
                )
            else:
                print(
                    f"     [Skip] Waterbus bến {station_name} quá xa mạng đường bộ Q1 ({dist_km:.3f} km)"
                )


def build_graph(
    metro_df,
    metro_edges_df,
    waterbus_df,
    hubs_df,
    orders_df,
    save_path="results/multimodal_graph.pkl",
):
    print("[2/7] Building Multimodal Graph with dynamic Bounding Box...")

    # Tính toán bounding box bao phủ toàn bộ hệ thống (biên an toàn 0.015 độ)
    all_lats = pd.concat(
        [metro_df["lat"], waterbus_df["lat"], hubs_df["lat"], orders_df["lat"]]
    )
    all_lons = pd.concat(
        [metro_df["lon"], waterbus_df["lon"], hubs_df["lon"], orders_df["lon"]]
    )

    west = all_lons.min() - 0.015
    east = all_lons.max() + 0.015
    south = all_lats.min() - 0.015
    north = all_lats.max() + 0.015

    bbox = (west, south, east, north)
    print(
        f"  -> Calculated system bounding box: west={west:.4f}, south={south:.4f}, east={east:.4f}, north={north:.4f}"
    )

    # 1. Tải Road Graph từ OpenStreetMap bằng Bounding Box
    G = ox.graph_from_bbox(bbox=bbox, network_type="drive")

    # Gán thuộc tính mặc định cho đường bộ
    for u, v, key, data in G.edges(keys=True, data=True):
        length_km = data.get("length", 0) / 1000
        data["travel_time"] = (length_km / 30) * 60  # Vận tốc shipper 30 km/h
        data["mode"] = "road"
        data["co2"] = 0.12
        data["cost"] = (
            length_km * 3000.0
        )  # Chi phí xe máy xăng/khấu hao: 3,000 VND / km

    # 2. Áp dụng các tầng giao thông công cộng đầu vào công nghệ cao
    add_metro_layer_with_edges(
        G, metro_df, metro_edges_df, speed_kmh=40, co2_factor=0.02
    )
    add_waterbus_layer(G, waterbus_df, speed_kmh=20, co2_factor=0.05)

    # 3. Kết nối liên thông mạng lưới đa phương thức
    connect_multimodal_layers(G, metro_df, waterbus_df)

    with open(save_path, "wb") as f:
        pickle.dump(G, f)

    print(
        "  -> Graph saved completely with multi-line Metro connectivity and transfer edges."
    )
    return G
import os
import pickle
import pandas as pd
import numpy as np
import networkx as nx
import osmnx as ox
import joblib
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Hàm Haversine tính khoảng cách giữa 2 điểm (km)
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

class VRPSolver:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.base_dir = base_dir
        self.model_path = os.path.join(base_dir, "src", "traffic_model.pkl")
        self.features_path = os.path.join(base_dir, "src", "traffic_model_features.pkl")
        
        # Load mô hình AI dự đoán tốc độ
        if os.path.exists(self.model_path) and os.path.exists(self.features_path):
            self.model = joblib.load(self.model_path)
            self.feature_cols = joblib.load(self.features_path)
            print("  -> Loaded AI Traffic Model successfully.")
        else:
            self.model = None
            self.feature_cols = None
            print("  -> [!] AI Model not found. Using default speeds (30 km/h).")

    def predict_edge_speed(self, road_type, weather, is_rush_hour):
        """Sử dụng mô hình AI để dự đoán vận tốc trên đường bộ."""
        if self.model is None:
            # Fallback nếu không có mô hình AI
            return 30.0

        # Khớp loại đường theo định dạng của OSMnx
        # map từ OSMnx highway type sang road_type của mô hình AI
        road_map = {
            'primary': 'primary',
            'secondary': 'secondary',
            'tertiary': 'secondary',
            'residential': 'residential',
            'living_street': 'residential',
            'unclassified': 'residential'
        }
        mapped_road = road_map.get(road_type, 'residential')

        # Khởi tạo vector đặc trưng cho case này
        case = {
            'is_rush_hour': int(is_rush_hour),
            f'road_type_{mapped_road}': 1,
            f'weather_{weather}': 1
        }
        
        row = pd.DataFrame([case])
        # Đảm bảo đầy đủ các cột như lúc huấn luyện
        for col in self.feature_cols:
            if col not in row.columns:
                row[col] = 0
        row = row[self.feature_cols]
        
        # Dự đoán tốc độ
        pred_speed = self.model.predict(row)[0]
        return max(5.0, pred_speed)  # Tối thiểu là 5km/h để tránh chia cho 0 hoặc đứng im

    def update_graph_weights_with_ai(self, G, weather, is_rush_hour):
        """Cập nhật lại thời gian di chuyển trên đồ thị đường bộ dựa trên dự báo của AI."""
        print(f"  -> Updating graph edges with AI speed predictions (Weather={weather}, Rush={is_rush_hour})...")
        G_copied = G.copy()
        
        for u, v, k, d in G_copied.edges(keys=True, data=True):
            mode = d.get("mode", "road")
            length_km = d.get("length", 0) / 1000.0
            
            if mode == "road":
                # Lấy loại đường từ thuộc tính highway
                highway = d.get("highway", "residential")
                if isinstance(highway, list):
                    highway = highway[0]
                
                # Dự đoán tốc độ xe máy bằng AI
                speed_kmh = self.predict_edge_speed(highway, weather, is_rush_hour)
                d["actual_speed"] = speed_kmh
                
                # Cập nhật thời gian di chuyển (travel_time) tính bằng phút
                d["travel_time"] = (length_km / speed_kmh) * 60.0
                
            elif mode == "metro":
                # Tốc độ Metro không đổi do chạy ray riêng biệt (40 km/h)
                d["actual_speed"] = 40.0
                d["travel_time"] = (length_km / 40.0) * 60.0
                
            elif mode == "waterbus":
                # Tốc độ Waterbus không đổi (20 km/h)
                d["actual_speed"] = 20.0
                d["travel_time"] = (length_km / 20.0) * 60.0
                
        return G_copied

    def solve_vrp_for_hub(self, G, hub_row, hub_orders, max_capacity_kg=20.0, num_vehicles=5, weather="clear", is_rush_hour=False):
        """Giải bài toán VRP cho 1 Hub cụ thể bằng Google OR-Tools."""
        if len(hub_orders) == 0:
            return []

        # Tách đồ thị đường bộ riêng biệt cho chặng cuối bằng xe máy
        road_nodes = [n for n, d in G.nodes(data=True) 
                      if isinstance(n, int) and d.get("mode") not in ["metro_station", "waterbus_station", "hub_candidate"]]
        G_road = G.subgraph(road_nodes)

        # Định vị Node đường bộ gần Hub và các Đơn hàng nhất
        hub_node = ox.distance.nearest_nodes(G_road, X=hub_row['lon'], Y=hub_row['lat'])
        
        order_nodes = []
        order_weights = []
        order_ids = []
        for _, o in hub_orders.iterrows():
            o_node = ox.distance.nearest_nodes(G_road, X=o['lon'], Y=o['lat'])
            order_nodes.append(o_node)
            order_weights.append(o['weight_kg'])
            order_ids.append(o['order_id'])

        # Danh sách tất cả các điểm trong VRP (Điểm 0 là Hub, các điểm tiếp theo là đơn hàng)
        all_vrp_nodes = [hub_node] + order_nodes
        num_locations = len(all_vrp_nodes)

        # 1. Tính toán ma trận thời gian di chuyển (Travel Time Matrix)
        time_matrix = np.zeros((num_locations, num_locations))
        distance_matrix = np.zeros((num_locations, num_locations))
        
        # Dự đoán tốc độ trung bình chặng cuối của khu vực bằng mô hình AI
        avg_speed_kmh = self.predict_edge_speed('residential', weather, is_rush_hour)
        
        # Danh sách tọa độ thực tế
        coords = [(hub_row['lat'], hub_row['lon'])] + [(o['lat'], o['lon']) for _, o in hub_orders.iterrows()]

        for i in range(num_locations):
            for j in range(num_locations):
                if i == j:
                    time_matrix[i][j] = 0
                    distance_matrix[i][j] = 0
                elif i == 0 or j == 0:
                    # Đi từ Hub <-> Đơn hàng: Tính toán đường đi thực tế trên đồ thị đường bộ
                    try:
                        path = nx.shortest_path(G_road, source=all_vrp_nodes[i], target=all_vrp_nodes[j], weight="travel_time")
                        total_time = 0.0
                        total_dist = 0.0
                        for u_idx in range(len(path) - 1):
                            edge_data = G_road[path[u_idx]][path[u_idx+1]][0]
                            total_time += edge_data.get("travel_time", 0)
                            total_dist += edge_data.get("length", 0) / 1000.0
                        time_matrix[i][j] = int(total_time * 100)
                        distance_matrix[i][j] = total_dist
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        # Dự phòng bằng Haversine nếu đồ thị bị đứt gãy
                        dist_km = haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1]) * 1.3
                        time_matrix[i][j] = int((dist_km / avg_speed_kmh) * 60 * 100)
                        distance_matrix[i][j] = dist_km
                else:
                    # Đi giữa các Đơn hàng chặng cuối: Xấp xỉ khoảng cách Haversine * 1.3 (hệ số vòng vèo đô thị)
                    # Giúp tăng tốc độ tính toán gấp 100 lần cho ma trận 100x100
                    dist_km = haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1]) * 1.3
                    time_min = (dist_km / avg_speed_kmh) * 60.0
                    time_matrix[i][j] = int(time_min * 100)
                    distance_matrix[i][j] = dist_km

        # Khối lượng của từng điểm (Hub=0, các điểm tiếp theo = weight_kg)
        demands = [0] + [int(w * 10) for w in order_weights]  # Nhân 10 để tránh số thực
        vehicle_capacities = [int(max_capacity_kg * 10)] * num_vehicles

        # 2. Khởi tạo Mô hình OR-Tools
        manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        def to_signed_64(val):
            val = int(val)
            if val >= 2**63:
                val -= 2**64
            return val

        # Đăng ký hàm tính chi phí di chuyển (Thời gian)
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(to_signed_64(from_index))
            to_node = manager.IndexToNode(to_signed_64(to_index))
            # Đảm bảo index hợp lệ trước khi truy cập ma trận
            if from_node < 0 or from_node >= num_locations or to_node < 0 or to_node >= num_locations:
                return 999999
            return int(time_matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Đăng ký hàm tính tải trọng
        def demand_callback(from_index):
            from_node = manager.IndexToNode(to_signed_64(from_index))
            if from_node < 0 or from_node >= num_locations:
                return 0
            return int(demands[from_node])

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        # Thêm ràng buộc tải trọng cho xe máy
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # Không tích lũy tải trọng lúc bắt đầu
            vehicle_capacities,
            True,  # Bắt đầu với tải trọng rỗng
            "Capacity"
        )

        # 3. Thiết lập thông số tìm kiếm
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 5  # Giới hạn giải trong 5 giây mỗi Hub

        # 4. Giải bài toán
        solution = routing.SolveWithParameters(search_parameters)

        # 5. Trích xuất lộ trình chi tiết
        routes = []
        if solution:
            for vehicle_id in range(num_vehicles):
                index = routing.Start(vehicle_id)
                route_nodes = []
                route_order_ids = []
                route_load = 0.0
                route_dist = 0.0
                
                prev_node_idx = 0
                while not routing.IsEnd(index):
                    node_idx = manager.IndexToNode(to_signed_64(index))
                    route_nodes.append(node_idx)
                    
                    if node_idx > 0:
                        # Điểm giao hàng
                        order_weight = order_weights[node_idx - 1]
                        route_load += order_weight
                        route_order_ids.append(order_ids[node_idx - 1])
                        
                    route_dist += distance_matrix[prev_node_idx][node_idx]
                    prev_node_idx = node_idx
                    index = solution.Value(routing.NextVar(index))
                
                # Điểm kết thúc quay về Hub
                node_idx = manager.IndexToNode(to_signed_64(index))
                route_nodes.append(node_idx)
                route_dist += distance_matrix[prev_node_idx][node_idx]

                if len(route_order_ids) > 0:  # Chỉ lấy xe có chạy
                    routes.append({
                        "vehicle_id": vehicle_id + 1,
                        "order_ids": route_order_ids,
                        "load_kg": round(route_load, 2),
                        "distance_km": round(route_dist, 2),
                        "time_min": round(solution.ObjectiveValue() / 100.0, 2)  # Quy đổi lại phút
                    })
        else:
            print(f"     [!] CẢNH BÁO: Không tìm thấy lời giải VRP khả thi cho Hub {hub_row['name']}!")
        return routes

    def solve_all(self, G, orders_df, selected_hubs, weather="clear", is_rush_hour=False):
        """Giải VRP chặng cuối cho toàn bộ các Hub được chọn."""
        print(f"\n[4/7] Solving Last-mile VRP with OR-Tools (Weather={weather}, Rush Hour={is_rush_hour})...")
        
        # Cập nhật vận tốc các cạnh trong đồ thị bằng AI
        G_ai = self.update_graph_weights_with_ai(G, weather, is_rush_hour)
        
        all_hub_routes = []
        
        # Duyệt qua từng Hub đã chọn
        for _, hub in selected_hubs.iterrows():
            hub_id = hub['hub_id']
            # Lọc các đơn hàng thuộc cụm của Hub này (đã gán bởi K-Medoids)
            hub_orders = orders_df[orders_df['assigned_hub_id'] == hub_id]
            
            # Tính toán số lượng xe máy cần thiết dựa trên tổng khối lượng hàng hóa của Hub
            total_weight = hub_orders['weight_kg'].sum()
            max_capacity_kg = 20.0
            required_vehicles = int(np.ceil(total_weight / max_capacity_kg)) + 3
            
            print(f"  -> Hub {int(hub_id)}: {hub['name']} | Giải VRP cho {len(hub_orders)} đơn hàng (Tổng khối lượng: {total_weight:.2f} kg, Cần tối thiểu {required_vehicles} xe)...")
            
            routes = self.solve_vrp_for_hub(G_ai, hub, hub_orders, max_capacity_kg=max_capacity_kg, num_vehicles=required_vehicles, weather=weather, is_rush_hour=is_rush_hour)
            
            for r in routes:
                r['hub_id'] = hub_id
                r['hub_name'] = hub['name']
                all_hub_routes.append(r)
                
        # Tổng kết kết quả
        total_vehicles = len(all_hub_routes)
        total_dist = sum(r['distance_km'] for r in all_hub_routes)
        total_load = sum(r['load_kg'] for r in all_hub_routes)
        
        print(f"  -> VRP Solved Successfully!")
        print(f"     + Tổng số xe máy hoạt động: {total_vehicles} xe")
        print(f"     + Tổng quãng đường giao hàng chặng cuối: {total_dist:.2f} km")
        print(f"     + Tổng khối lượng hàng đã giao: {total_load:.2f} kg")
        
        # Lưu kết quả phân tuyến thành file CSV
        routes_flat = []
        for r in all_hub_routes:
            for seq, o_id in enumerate(r['order_ids']):
                routes_flat.append({
                    "hub_id": r['hub_id'],
                    "hub_name": r['hub_name'],
                    "vehicle_id": r['vehicle_id'],
                    "delivery_sequence": seq + 1,
                    "order_id": o_id,
                    "route_distance_km": r['distance_km'],
                    "route_load_kg": r['load_kg']
                })
        
        df_routes = pd.DataFrame(routes_flat)
        os.makedirs(os.path.join(self.base_dir, "results"), exist_ok=True)
        df_routes.to_csv(os.path.join(self.base_dir, "results", "vrp_routes.csv"), index=False)
        print(f"  -> Detailed routes saved to results/vrp_routes.csv")
        
        return all_hub_routes

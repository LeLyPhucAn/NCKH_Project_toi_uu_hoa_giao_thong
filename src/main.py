import os
import sys
import pickle

# Đảm bảo terminal in được tiếng Việt UTF-8 không lỗi trên Windows
sys.stdout.reconfigure(encoding='utf-8')

from load_data import load_data
from build_graph import build_graph
from select_hub import select_hub
from vrp_solver import VRPSolver
from routing import routing
from evaluation import evaluation
from simulation import simulation


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. Nạp và làm sạch dữ liệu
    metro, metro_edges, waterbus, hubs, orders = load_data()
    if metro is None:
        print("[!] Lỗi nạp dữ liệu. Kết thúc Pipeline.")
        return

    # 2. Xây dựng đồ thị đa phương thức (OSMnx Bounding Box)
    graph_path = os.path.join(results_dir, "multimodal_graph.pkl")
    G = None
    if os.path.exists(graph_path):
        try:
            with open(graph_path, 'rb') as f:
                G = pickle.load(f)
            print("[2/7] Graph loaded from cache.")
        except Exception:
            print("[!] Cache lỗi hoặc cấu trúc cũ không khớp. Tiến hành tạo lại Graph...")
            os.remove(graph_path)

    if G is None:
        G = build_graph(metro, metro_edges, waterbus, hubs, orders, graph_path)

    # 3. Chọn Hub tối ưu bằng K-Medoids toàn cục (chọn 3 Hub trong 6 Hub gần Q1)
    selected_hubs = select_hub(hubs, orders, num_hubs=3)

    # 4. Giải bài toán lộ trình VRP chặng cuối bằng Google OR-Tools kết hợp dự báo tốc độ AI
    vrp = VRPSolver(base_dir=base_dir)
    
    # Kịch bản 1: Giờ bình thường, thời tiết nắng đẹp (Clear)
    print("\n" + "="*50)
    print("KỊCH BẢN 1: GIỜ BÌNH THƯỜNG - NẮNG ĐẸP (Off-Peak, Clear)")
    print("="*50)
    routes_clear = vrp.solve_all(G, orders, selected_hubs, weather="clear", is_rush_hour=False)
    
    # Kịch bản 2: Giờ cao điểm, trời mưa to ngập lụt (Peak, Heavy Rain)
    print("\n" + "="*50)
    print("KỊCH BẢN 2: GIỜ CAO ĐIỂM - MƯA TO NGẬP LỤT (Peak, Heavy Rain)")
    print("="*50)
    routes_rain = vrp.solve_all(G, orders, selected_hubs, weather="heavy_rain", is_rush_hour=True)

    # 5. Chạy các đánh giá so sánh khác (nếu cần)
    print("\n" + "="*50)
    print("5. ĐÁNH GIÁ VÀ MÔ PHỎNG SO SÁNH")
    print("="*50)
    routing_results = routing(G, orders, selected_hubs)
    evaluation(routing_results)
    
    # 6. Chạy mô phỏng hệ thống và xuất simulation_log.txt
    simulation()

    print("\n[7/7] Pipeline Hoàn Thành!")


if __name__ == "__main__":
    main()
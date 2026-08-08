import os
import random
import pandas as pd
from datetime import datetime, timedelta


def simulation():
    print("[6/7] Running Systems-Oriented Event Simulation...")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # === FIX: Đọc kết quả thực từ routing thay vì hardcode ===
    routing_path = os.path.join(results_dir, "routing_results.csv")
    improvement_path = os.path.join(results_dir, "improvement_results.csv")

    try:
        df = pd.read_csv(routing_path)
        df_improve = pd.read_csv(improvement_path) if os.path.exists(improvement_path) else None
    except Exception as e:
        print(f"  -> [!] Không đọc được routing_results: {e}")
        df = None
        df_improve = None

    lines = []
    lines.append("=" * 90)
    lines.append("           MULTIMODAL TRANSPORTATION SIMULATION SYSTEM LOG")
    lines.append("     Hệ thống Logistics Đa phương thức TP.HCM — Phân tích thực tế")
    lines.append(f"     Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 90)

    if df is not None and not df.empty:
        # --- PHẦN 1: Tóm tắt KPI từ dữ liệu thực ---
        lines.append("")
        lines.append("[SECTION 1: KPI TỔNG HỢP THỰC TẾ TỪ THUẬT TOÁN]")
        lines.append("-" * 90)

        summary = df.groupby(['traffic_condition', 'scenario']).agg(
            avg_time=('time', 'mean'),
            avg_dist=('distance', 'mean'),
            avg_co2=('co2', 'mean'),
            avg_cost=('cost', 'mean'),
            count=('order_id', 'count')
        ).reset_index()

        for _, row in summary.iterrows():
            lines.append(
                f"  [{row['traffic_condition']:8s}] [{row['scenario']:20s}] "
                f"Avg Time: {row['avg_time']:6.2f} min | "
                f"Avg Dist: {row['avg_dist']:5.2f} km | "
                f"Avg CO2: {row['avg_co2']:5.3f} kg | "
                f"Avg Cost: {row['avg_cost']:8.0f} VND | "
                f"Orders: {row['count']}"
            )

        # --- PHẦN 2: Bảng % cải thiện ---
        if df_improve is not None and not df_improve.empty:
            lines.append("")
            lines.append("[SECTION 2: % CẢI THIỆN SO VỚI ROAD ONLY (BASELINE)]")
            lines.append("-" * 90)
            for _, row in df_improve.iterrows():
                if row['scenario'] == 'Road Only':
                    continue
                lines.append(
                    f"  [{row['traffic_condition']:8s}] [{row['scenario']:20s}] "
                    f"Thời gian: {row['time_improvement_pct']:+.1f}% | "
                    f"CO2: {row['co2_improvement_pct']:+.1f}% | "
                    f"Chi phí: {row['cost_improvement_pct']:+.1f}%"
                )

        # --- PHẦN 3: Mô phỏng chi tiết 1 đơn hàng thực ---
        lines.append("")
        lines.append("[SECTION 3: MÔ PHỎNG CHI TIẾT ĐƠN HÀNG ĐẠI DIỆN — PEAK HOUR]")
        lines.append("-" * 90)

        peak_df = df[df['traffic_condition'] == 'Peak'].copy()
        if not peak_df.empty:
            # Lấy 1 đơn ngẫu nhiên có đủ 4 kịch bản để so sánh
            order_counts = peak_df.groupby('order_id')['scenario'].count()
            full_orders = order_counts[order_counts == 4].index
            if len(full_orders) > 0:
                sample_order = full_orders[0]
                order_data = peak_df[peak_df['order_id'] == sample_order]
                hub_id = order_data['hub_id'].values[0]

                lines.append(f"  Đơn hàng: Order_{sample_order} | Hub xuất phát: {hub_id} | Giờ: Peak (17:00)")
                lines.append("")

                start_time = datetime(2025, 1, 1, 17, 0, 0)
                for _, row in order_data.iterrows():
                    scenario = row['scenario']
                    t_min = row['time']
                    dist = row['distance']
                    co2 = row['co2']
                    cost = row['cost']
                    modes = row.get('modes_used', 'road')
                    arrive_time = start_time + timedelta(minutes=t_min)

                    lines.append(f"  >> Kịch bản: {scenario}")
                    lines.append(f"     17:00:00  [DEPART]  Xuất phát từ {hub_id}")
                    lines.append(f"     {arrive_time.strftime('%H:%M:%S')}  [ARRIVE]  Giao hàng thành công")
                    lines.append(f"     Phương tiện sử dụng: {modes}")
                    lines.append(f"     Thời gian: {t_min:.2f} phút | Quãng đường: {dist:.2f} km | CO2: {co2:.4f} kg | Chi phí: {cost:,.0f} VND")
                    lines.append("")

                # So sánh Road Only vs Full Multimodal
                road = order_data[order_data['scenario'] == 'Road Only']
                multi = order_data[order_data['scenario'] == 'Full Multimodal']
                if not road.empty and not multi.empty:
                    r_t = road['time'].values[0]
                    m_t = multi['time'].values[0]
                    r_c = road['co2'].values[0]
                    m_c = multi['co2'].values[0]
                    lines.append(f"  [KẾT LUẬN ĐƠN ORDER_{sample_order}]")
                    lines.append(f"     Full Multimodal tiết kiệm: {r_t - m_t:.2f} phút ({(r_t-m_t)/r_t*100:.1f}%) | CO2 giảm: {r_c - m_c:.4f} kg ({(r_c-m_c)/r_c*100:.1f}%)")

        # --- PHẦN 4: Thống kê phân phối ---
        lines.append("")
        lines.append("[SECTION 4: THỐNG KÊ PHÂN PHỐI KẾT QUẢ]")
        lines.append("-" * 90)
        total_orders = df['order_id'].nunique()
        road_only = df[(df['scenario'] == 'Road Only') & (df['traffic_condition'] == 'Peak')]
        multi = df[(df['scenario'] == 'Full Multimodal') & (df['traffic_condition'] == 'Peak')]
        lines.append(f"  Tổng đơn hoàn thành routing: {total_orders}")
        if not road_only.empty and not multi.empty:
            lines.append(f"  Road Only (Peak) — min: {road_only['time'].min():.1f} | max: {road_only['time'].max():.1f} | std: {road_only['time'].std():.2f} phút")
            lines.append(f"  Multimodal (Peak) — min: {multi['time'].min():.1f} | max: {multi['time'].max():.1f} | std: {multi['time'].std():.2f} phút")

    else:
        lines.append("")
        lines.append("  [!] Không có dữ liệu routing để mô phỏng.")
        lines.append("  Vui lòng chạy lại pipeline từ bước Routing.")

    lines.append("")
    lines.append("=" * 90)
    lines.append("                     END OF SIMULATION LOG")
    lines.append("=" * 90)

    log_path = os.path.join(results_dir, "simulation_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print("  -> System simulation log saved with real data from routing results.")
from datetime import datetime, timedelta
import pandas as pd
from repositories.result_repository import ResultRepository
from core.logger import get_logger

logger = get_logger("SimulationService")


class SimulationService:
    @staticmethod
    def execute_simulation() -> str:
        logger.info("Đang sinh log mô phỏng sự kiện vận chuyển theo thời gian thực...")
        df = ResultRepository.load_routing_results()
        summary_df, improve_df = ResultRepository.load_summary_kpis()

        lines = []
        lines.append("=" * 90)
        lines.append("           MULTIMODAL TRANSPORTATION SIMULATION SYSTEM LOG")
        lines.append("     Hệ thống Logistics Đa phương thức TP.HCM — Phân tích thực tế")
        lines.append(f"     Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 90)

        if df is not None and not df.empty:
            lines.append("")
            lines.append("[SECTION 1: KPI TỔNG HỢP THỰC TẾ T TỪ THUẬT TOÁN]")
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

            if improve_df is not None and not improve_df.empty:
                lines.append("")
                lines.append("[SECTION 2: % CẢI THIỆN SO VỚI ROAD ONLY (BASELINE)]")
                lines.append("-" * 90)
                for _, row in improve_df.iterrows():
                    if row['scenario'] == 'Road Only':
                        continue
                    lines.append(
                        f"  [{row['traffic_condition']:8s}] [{row['scenario']:20s}] "
                        f"Thời gian: {row['time_improvement_pct']:+.1f}% | "
                        f"CO2: {row['co2_improvement_pct']:+.1f}% | "
                        f"Chi phí: {row['cost_improvement_pct']:+.1f}%"
                    )

            lines.append("")
            lines.append("[SECTION 3: MÔ PHỎNG CHI TIẾT ĐƠN HÀNG ĐẠI DIỆN — PEAK HOUR]")
            lines.append("-" * 90)

            peak_df = df[df['traffic_condition'] == 'Peak'].copy()
            if not peak_df.empty:
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

        lines.append("=" * 90)
        lines.append("                     END OF SIMULATION LOG")
        lines.append("=" * 90)

        ResultRepository.save_simulation_log(lines)
        logger.info("Đã lưu nhật ký mô phỏng vào results/simulation_log.txt.")
        return "\n".join(lines)

    @staticmethod
    def get_simulation_log() -> str:
        return ResultRepository.load_simulation_log()

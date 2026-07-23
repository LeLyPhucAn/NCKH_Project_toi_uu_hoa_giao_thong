import os
import pandas as pd
from core.config.settings import settings


class ResultRepository:
    """Repository lưu trữ và truy xuất các báo cáo kết quả tối ưu hóa."""

    @staticmethod
    def save_selected_hubs(df: pd.DataFrame):
        path = os.path.join(settings.RESULTS_DIR, "selected_hubs.csv")
        df.to_csv(path, index=False)

    @staticmethod
    def load_selected_hubs() -> pd.DataFrame:
        path = os.path.join(settings.RESULTS_DIR, "selected_hubs.csv")
        if os.path.exists(path):
            return pd.read_csv(path)
        return None

    @staticmethod
    def save_routing_results(df: pd.DataFrame):
        path = os.path.join(settings.RESULTS_DIR, "routing_results.csv")
        df.to_csv(path, index=False)

    @staticmethod
    def load_routing_results() -> pd.DataFrame:
        path = os.path.join(settings.RESULTS_DIR, "routing_results.csv")
        if os.path.exists(path):
            return pd.read_csv(path)
        return None

    @staticmethod
    def save_summary_kpis(all_summary: pd.DataFrame, all_improve: pd.DataFrame, results_out: dict):
        all_summary.to_csv(os.path.join(settings.RESULTS_DIR, "summary_results.csv"), index=False)
        if all_improve is not None and not all_improve.empty:
            all_improve.to_csv(os.path.join(settings.RESULTS_DIR, "improvement_results.csv"), index=False)

        try:
            with pd.ExcelWriter(os.path.join(settings.RESULTS_DIR, "summary_results.xlsx"), engine="openpyxl") as writer:
                for strategy, data in results_out.items():
                    sheet = strategy[:28]
                    data['summary'].to_excel(writer, index=False, sheet_name=f"KPI_{sheet}")
                    data['improvement'].to_excel(writer, index=False, sheet_name=f"Improve_{sheet}")
        except Exception:
            pass

    @staticmethod
    def load_summary_kpis():
        summary_path = os.path.join(settings.RESULTS_DIR, "summary_results.csv")
        improve_path = os.path.join(settings.RESULTS_DIR, "improvement_results.csv")

        summary_df = pd.read_csv(summary_path) if os.path.exists(summary_path) else None
        improve_df = pd.read_csv(improve_path) if os.path.exists(improve_path) else None

        return summary_df, improve_df

    @staticmethod
    def save_simulation_log(lines: list):
        path = os.path.join(settings.RESULTS_DIR, "simulation_log.txt")
        with open(path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    @staticmethod
    def load_simulation_log() -> str:
        path = os.path.join(settings.RESULTS_DIR, "simulation_log.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return "Chưa có file log. Vui lòng thực thi Pipeline."

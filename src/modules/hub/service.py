import pandas as pd
from repositories.data_repository import DataRepository
from repositories.result_repository import ResultRepository
from shared.algorithms.greedy_pmedian import run_greedy_pmedian
from core.logger import get_logger

logger = get_logger("HubService")


class HubService:
    @staticmethod
    def select_optimal_hubs(num_hubs: int = 5) -> pd.DataFrame:
        logger.info(f"Đang thực thi chọn {num_hubs} Micro Hubs (p-Median + Haversine)...")
        hubs_df = DataRepository.load_hubs()
        orders_df = DataRepository.load_orders()

        selected_hubs = run_greedy_pmedian(hubs_df, orders_df, num_hubs=num_hubs)
        ResultRepository.save_selected_hubs(selected_hubs)
        logger.info(f"Đã chọn {len(selected_hubs)} Hubs tối ưu và lưu vào results/selected_hubs.csv")
        return selected_hubs

    @staticmethod
    def get_selected_or_candidate_hubs():
        selected = ResultRepository.load_selected_hubs()
        if selected is not None and not selected.empty:
            selected['is_selected'] = True
            return selected.to_dict(orient="records")
        candidates = DataRepository.load_hubs()
        candidates['is_selected'] = False
        return candidates.to_dict(orient="records")

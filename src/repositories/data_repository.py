import os
import pandas as pd
from core.config.settings import settings
from core.exceptions.base import NotFoundException
from shared.utils.data_cleaner import clean_dataframe


class DataRepository:
    """Repository quản lý toàn bộ việc nạp & chuẩn hóa dữ liệu CSV đầu vào."""

    @staticmethod
    def load_metro() -> pd.DataFrame:
        path = os.path.join(settings.DATA_DIR, "metro.csv")
        if not os.path.exists(path):
            raise NotFoundException("Không tìm thấy dữ liệu metro.csv")
        return clean_dataframe(pd.read_csv(path))

    @staticmethod
    def load_metro_edges() -> pd.DataFrame:
        path = os.path.join(settings.DATA_DIR, "HCMC_Metro_Edges.csv")
        if not os.path.exists(path):
            raise NotFoundException("Không tìm thấy dữ liệu HCMC_Metro_Edges.csv")
        return clean_dataframe(pd.read_csv(path))

    @staticmethod
    def load_waterbus() -> pd.DataFrame:
        path = os.path.join(settings.DATA_DIR, "waterbus.csv")
        if not os.path.exists(path):
            raise NotFoundException("Không tìm thấy dữ liệu waterbus.csv")
        return clean_dataframe(pd.read_csv(path))

    @staticmethod
    def load_hubs() -> pd.DataFrame:
        path = os.path.join(settings.DATA_DIR, "hub_candidates.csv")
        if not os.path.exists(path):
            raise NotFoundException("Không tìm thấy dữ liệu hub_candidates.csv")
        return clean_dataframe(pd.read_csv(path))

    @staticmethod
    def load_orders(limit: int = 0) -> pd.DataFrame:
        path = os.path.join(settings.DATA_DIR, "orders.csv")
        if not os.path.exists(path):
            raise NotFoundException("Không tìm thấy dữ liệu orders.csv")
        df = clean_dataframe(pd.read_csv(path))
        if 'weight' not in df.columns:
            df['weight'] = 5.0
        if 'status' not in df.columns:
            df['status'] = 'pending'
        if limit > 0:
            df = df.head(limit)
        return df

    @staticmethod
    def save_orders(df: pd.DataFrame):
        path = os.path.join(settings.DATA_DIR, "orders.csv")
        df.to_csv(path, index=False)

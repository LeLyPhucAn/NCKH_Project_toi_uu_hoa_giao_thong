import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Xóa khoảng trắng thừa, chuẩn hóa tên cột và gọt bỏ ký tự lạ lọt vào tọa độ."""
    if df is None or df.empty:
        return df

    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={'lng': 'lon', 'long': 'lon'}, inplace=True)

    if 'lat' in df.columns:
        df['lat'] = df['lat'].astype(str).str.replace(r'[a-zA-Z\s]', '', regex=True).astype(float)
    if 'lon' in df.columns:
        df['lon'] = df['lon'].astype(str).str.replace(r'[a-zA-Z\s]', '', regex=True).astype(float)

    return df

"""
TRAIN TRAFFIC SPEED PREDICTION MODEL
=====================================
Mo hinh Random Forest du doan van toc giao thong
Dau vao: road_type, weather, is_rush_hour
Dau ra: actual_speed_kmh
"""
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE_DIR  = r"d:\NCKH_Project_toi_uu_hoa_giao_thong"
DATA_PATH = os.path.join(BASE_DIR, "data", "traffic_training_data.csv")
MODEL_OUT = os.path.join(BASE_DIR, "src",  "traffic_model.pkl")

print("=" * 60)
print("   AI TRAINING - TRAFFIC SPEED PREDICTION MODEL")
print("=" * 60)

# ----------------------------------------------------------
# BUOC 1: TIEN XU LY DU LIEU (Data Preprocessing)
# ----------------------------------------------------------
print("\n[1/5] Tien xu ly du lieu...")
df = pd.read_csv(DATA_PATH)
print(f"  -> Doc du lieu: {len(df):,} dong, {len(df.columns)} cot")

# Kiem tra gia tri rong
missing = df.isnull().sum().sum()
print(f"  -> Gia tri rong (NaN): {missing} (Sach!)" if missing == 0 else f"  -> [!] Co {missing} gia tri rong!")

# Chuyen True/False -> 1/0
df['is_rush_hour'] = df['is_rush_hour'].astype(int)

# One-Hot Encoding cho cac cot chu
df_encoded = pd.get_dummies(df, columns=['road_type', 'weather'], dtype=int)

print(f"  -> Sau Encoding: {len(df_encoded.columns)} cot (toan so)")
feature_cols = [c for c in df_encoded.columns if c != 'actual_speed_kmh']
print(f"  -> Features (bien du doan): {feature_cols}")
print(f"  -> Target  (bien muc tieu): actual_speed_kmh")

# ----------------------------------------------------------
# BUOC 2: PHAN TACH TAP TRAIN / TEST (Train-Test Split)
# ----------------------------------------------------------
print("\n[2/5] Phan tach tap Train/Test (80/20)...")
X = df_encoded[feature_cols]
y = df_encoded['actual_speed_kmh']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"  -> Tap Train: {len(X_train):,} dong (day cho AI hoc)")
print(f"  -> Tap Test : {len(X_test):,} dong (kiem tra AI sau khi hoc)")

# ----------------------------------------------------------
# BUOC 3: HUAN LUYEN MO HINH (Model Training - Random Forest)
# ----------------------------------------------------------
print("\n[3/5] Huan luyen mo hinh Random Forest...")
print("  -> Dang huan luyen (100 cay quyet dinh)...")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1  # Su dung toan bo CPU de chay nhanh hon
)
model.fit(X_train, y_train)
print("  -> Huan luyen HOAN THANH!")

# ----------------------------------------------------------
# BUOC 4: DANH GIA MO HINH (Model Evaluation)
# ----------------------------------------------------------
print("\n[4/5] Danh gia mo hinh tren tap Test...")
y_pred = model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)

print(f"\n  +------------------------------------------+")
print(f"  | KET QUA CHAM DIEM AI                     |")
print(f"  |------------------------------------------|")
print(f"  | MAE  (Sai so trung binh) : {mae:>7.3f} km/h  |")
print(f"  | RMSE (Sai so RMS)        : {rmse:>7.3f} km/h  |")
print(f"  | R2   (Diem chinh xac)    : {r2:>7.4f}        |")
print(f"  +------------------------------------------+")

if r2 >= 0.9:
    print("  -> Mo hinh DAT CHUAN (R2 >= 0.9) - XUAT SAC!")
elif r2 >= 0.8:
    print("  -> Mo hinh DAT CHUAN (R2 >= 0.8) - TOT!")
else:
    print("  -> Mo hinh chua dat chuan, can kiem tra lai du lieu.")

# Muc do quan trong cua tung feature
print("\n  -> Muc do anh huong (Feature Importance):")
fi = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
for name, score in fi.head(5).items():
    bar = "█" * int(score * 50)
    print(f"     {name:<30s}: {score:.4f} {bar}")

# ----------------------------------------------------------
# BUOC 5: LUU MO HINH (Model Export)
# ----------------------------------------------------------
print(f"\n[5/5] Luu mo hinh va feature list...")
joblib.dump(model, MODEL_OUT)
# Luu them feature list de dung khi predict
feature_path = os.path.join(BASE_DIR, "src", "traffic_model_features.pkl")
joblib.dump(feature_cols, feature_path)

print(f"  -> Mo hinh da luu: {MODEL_OUT}")
print(f"  -> Feature list  : {feature_path}")

# Test nhanh voi 1 truong hop thuc te
print("\n  -> DEMO DU DOAN NHANH:")
demo_cases = [
    {"road_type": "primary",     "weather": "clear",      "is_rush_hour": 0},
    {"road_type": "primary",     "weather": "heavy_rain", "is_rush_hour": 1},
    {"road_type": "residential", "weather": "flooded",    "is_rush_hour": 1},
]
for case in demo_cases:
    row = pd.DataFrame([case])
    row['is_rush_hour'] = int(row['is_rush_hour'][0])
    row_encoded = pd.get_dummies(row, columns=['road_type', 'weather'], dtype=int)
    # Dam bao du column giong luc train
    for col in feature_cols:
        if col not in row_encoded.columns:
            row_encoded[col] = 0
    row_encoded = row_encoded[feature_cols]
    speed = model.predict(row_encoded)[0]
    print(f"     {case['road_type']:<12} | {case['weather']:<12} | Rush:{case['is_rush_hour']} => {speed:.1f} km/h")

print("\n" + "=" * 60)
print("   HOAN THANH! Mo hinh AI da san sang.")
print("=" * 60)

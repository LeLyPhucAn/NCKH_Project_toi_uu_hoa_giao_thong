"""
Script sua loi Lop Du lieu (Data Layer)
- Sua metro.csv: Xoa chu "Tren" dong 14
- Sua hub_candidates.csv: Loc bot Hub xa Q1
- Sua HCMC_Metro_Edges.csv: Chi giu Metro Line 1, tinh khoang cach that (Haversine)
"""
import pandas as pd
import numpy as np
import math
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ============================================================
# HAM TINH KHOANG CACH HAVERSINE (km)
# ============================================================
def haversine_km(lat1, lon1, lat2, lon2):
    """Tinh khoang cach giua 2 toa do GPS theo cong thuc Haversine (don vi: km)."""
    R = 6371.0  # Ban kinh Trai Dat (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# ============================================================
# 1. SUA FILE metro.csv
# ============================================================
print("=" * 60)
print("[1/3] Sua file metro.csv...")
print("=" * 60)

metro_path = os.path.join(DATA_DIR, 'metro.csv')
# Doc file bang text de sua loi "Tren"
with open(metro_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Thay the "Tren " bang "" (xoa chu Tren)
if 'Tren ' in content:
    content = content.replace('Tren ', '')
    with open(metro_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  -> Da xoa chu 'Tren' o dong 14 (Ga Dai Hoc Quoc Gia).")
else:
    print("  -> Khong tim thay loi 'Tren'. File da sach.")

# Doc lai file da sua de xac nhan
metro_df = pd.read_csv(metro_path)
print(f"  -> Tong so ga Metro: {len(metro_df)}")
print(f"  -> Cac cot: {list(metro_df.columns)}")
print(f"  -> Kiem tra dong 13 (Dai Hoc Quoc Gia): lat = {metro_df.iloc[12]['lat']} (kieu: {type(metro_df.iloc[12]['lat']).__name__})")
print()


# ============================================================
# 2. SUA FILE hub_candidates.csv
# ============================================================
print("=" * 60)
print("[2/3] Sua file hub_candidates.csv...")
print("=" * 60)

hub_path = os.path.join(DATA_DIR, 'hub_candidates.csv')
hub_df = pd.read_csv(hub_path)

print(f"  -> TRUOC khi sua: {len(hub_df)} Hub")

# Chi giu lai Hub 1, 2, 3, 4, 5, 15 (gan Quan 1)
keep_ids = [1, 2, 3, 4, 5, 15]
hub_df = hub_df[hub_df['hub_id'].isin(keep_ids)].copy()

# Danh lai so ID tu 1-6
hub_df.reset_index(drop=True, inplace=True)
hub_df['hub_id'] = range(1, len(hub_df) + 1)

# Luu file
hub_df.to_csv(hub_path, index=False)
print(f"  -> SAU khi sua: {len(hub_df)} Hub")
print(f"  -> Danh sach Hub con lai:")
for _, row in hub_df.iterrows():
    print(f"     Hub {int(row['hub_id'])}: {row['name']} ({row['lat']:.4f}, {row['lon']:.4f})")
print()


# ============================================================
# 3. SUA FILE HCMC_Metro_Edges.csv
# ============================================================
print("=" * 60)
print("[3/3] Sua file HCMC_Metro_Edges.csv...")
print("=" * 60)

edges_path = os.path.join(DATA_DIR, 'HCMC_Metro_Edges.csv')
old_edges = pd.read_csv(edges_path)
print(f"  -> TRUOC khi sua: {len(old_edges)} edges, {old_edges['Line'].nunique()} tuyen Metro")

# Xay dung lai tu dau chi voi Metro Line 1
# Lay toa do tu metro.csv (da sua)
stations = metro_df[['id', 'name', 'lat', 'lon']].copy()

# Tao 13 canh (edges) noi 14 ga lien tiep
new_edges = []
for i in range(len(stations) - 1):
    s1 = stations.iloc[i]
    s2 = stations.iloc[i + 1]
    
    dist = haversine_km(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
    
    new_edges.append({
        'Edge_ID': i + 1,
        'Line': 'Metro 1',
        'From_Station': s1['name'],
        'To_Station': s2['name'],
        'Weight_km': dist
    })

new_edges_df = pd.DataFrame(new_edges)

# Luu file
new_edges_df.to_csv(edges_path, index=False)

print(f"  -> SAU khi sua: {len(new_edges_df)} edges, chi Metro Line 1")
print(f"  -> Ten ga: KHONG DAU (khop voi metro.csv)")
print(f"  -> Cot Weight_km: Khoang cach thuc te (Haversine)")
print()
print("  -> Chi tiet cac canh:")
for _, row in new_edges_df.iterrows():
    print(f"     Edge {int(row['Edge_ID'])}: {row['From_Station']} -> {row['To_Station']} = {row['Weight_km']} km")

print()
print("=" * 60)
print("HOAN THANH! Da sua xong 3 file du lieu.")
print("=" * 60)

"""
Script sua loi toa do Don hang (Orders Data Layer)
- Tai mang luoi giao thong duong bo va cac vung song ho tai Quan 1 tu OpenStreetMap.
- Loi bo cac vi tri thuoc mat nuoc (Song Sai Gon, Kenh Ben Nghe) va cac cau tren song.
- Dieu chinh (snap) toan bo toa do don hang nam tren song, ngoai Quan 1 hoac qua xa duong bo ve cac nut duong dat lien hop ly tai Quan 1.
- Ghi de file data/orders.csv da chuan hoa.
"""
import os
import pandas as pd
import numpy as np
import osmnx as ox
from shapely.geometry import Point

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
ORDERS_PATH = os.path.join(DATA_DIR, "orders.csv")


def fix_orders_dataset():
    print("=" * 60)
    print("Bat dau xu ly & sua doi toa do don hang (data/orders.csv)...")
    print("=" * 60)

    # 1. Doc du lieu don hang hien tai
    if not os.path.exists(ORDERS_PATH):
        raise FileNotFoundError(f"Khong tim thay file: {ORDERS_PATH}")
    
    orders = pd.read_csv(ORDERS_PATH)
    print(f"  -> Tong so don hang ban dau: {len(orders)}")

    # 2. Tai ban do Quan 1 va danh sach song/kenh tu OpenStreetMap
    place_name = "District 1, Ho Chi Minh City, Vietnam"
    print("  -> Tai ban do giao thong duong bo & mat nuoc Quan 1 qua OSMnx...")
    
    G = ox.graph_from_place(place_name, network_type="drive")
    
    try:
        water_gdf = ox.features_from_place(place_name, tags={"natural": "water", "waterway": True})
        water_union = water_gdf.union_all()
        print("  -> Da tai thanh cong cac vung song/kenh tai Quan 1.")
    except Exception as e:
        print(f"  [!] Canh bao: Khong the lay vung mat nuoc tu OSM: {e}")
        water_union = None

    d1_gdf = ox.geocode_to_gdf(place_name)
    d1_poly = d1_gdf.geometry.iloc[0]

    # 3. Loc danh sach cac nut duong bo tren DAT LIEN (Loai bo cac nut nam trong long song hoac tren cau qua song lon)
    land_nodes = []
    for n, d in G.nodes(data=True):
        if not isinstance(n, int):
            continue
        pt = Point(d["x"], d["y"])
        # Nut phai nam trong ranh gioi Q1 va KHONG nam trong long song
        if d1_poly.contains(pt) and (water_union is None or not water_union.contains(pt)):
            land_nodes.append(n)

    print(f"  -> Tong so nut giao thong Q1: {len(G.nodes)}")
    print(f"  -> So nut duong bo tren dat lien (da loc bo long song/cau): {len(land_nodes)}")

    G_land = G.subgraph(land_nodes)

    # 4. Duyet qua tung don hang va dieu chinh toa do
    fixed_orders = []
    adjusted_count = 0
    original_valid_count = 0

    for idx, row in orders.iterrows():
        o_id = int(row["order_id"])
        lat = float(row["lat"])
        lon = float(row["lon"])
        weight = float(row["weight_kg"]) if "weight_kg" in row else float(row.get("weight", 5.0))

        pt = Point(lon, lat)
        is_water = water_union.contains(pt) if water_union is not None else False
        is_in_d1 = d1_poly.contains(pt) if d1_poly is not None else True

        # Nut duong bo dat lien gan nhat
        nearest_land_node, dist_m = ox.distance.nearest_nodes(G_land, X=lon, Y=lat, return_dist=True)
        node_data = G_land.nodes[nearest_land_node]

        # Neu don hang nam duoi song, nam ngoai Q1 hoac khoang cach toi duong > 30m -> Snap ve nut dat lien
        if is_water or not is_in_d1 or dist_m > 30.0:
            new_lat = node_data["y"]
            new_lon = node_data["x"]
            adjusted_count += 1
        else:
            new_lat = lat
            new_lon = lon
            original_valid_count += 1

        fixed_orders.append({
            "order_id": o_id,
            "lat": round(new_lat, 6),
            "lon": round(new_lon, 6),
            "weight_kg": weight
        })

    df_fixed = pd.DataFrame(fixed_orders)

    # 5. Kiem tra lai lan cuoi: Dam bao 0 don hang nam duoi song
    in_water_check = 0
    if water_union is not None:
        for _, row in df_fixed.iterrows():
            if water_union.contains(Point(row["lon"], row["lat"])):
                in_water_check += 1

    # 6. Ghi file moi
    df_fixed.to_csv(ORDERS_PATH, index=False)
    
    print("-" * 60)
    print(f"  -> Da dieu chinh hop ly: {adjusted_count} don hang")
    print(f"  -> Toa do ban dau chuan: {original_valid_count} don hang")
    print(f"  -> So don hang con nam duoi song/kenh: {in_water_check} (Yeu cau = 0)")
    print(f"  -> Da luu du lieu moi vao: {ORDERS_PATH}")
    print("=" * 60)
    return df_fixed


if __name__ == "__main__":
    fix_orders_dataset()

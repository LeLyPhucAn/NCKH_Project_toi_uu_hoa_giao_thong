import os
import pandas as pd
import folium

# Định vị đường dẫn linh hoạt (chạy từ thư mục gốc hoặc thư mục src đều không bị lỗi)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data") if os.path.exists(os.path.join(BASE_DIR, "data")) else "data"

metro = pd.read_csv(os.path.join(DATA_DIR, "metro.csv"))
waterbus = pd.read_csv(os.path.join(DATA_DIR, "waterbus.csv"))
hub = pd.read_csv(os.path.join(DATA_DIR, "hub_candidates.csv"))
orders = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))

# print("Metro preview:")
# print(metro.head())

# Tọa độ trung tâm của bản đồ (ví dụ: trung tâm TP.HCM)
m = folium.Map(location=[10.7769, 106.7009], zoom_start=12)

# Metro 
for _, row in metro.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=row["name"],
        icon=folium.Icon(color="red")
    ).add_to(m)

# Waterbus
for _, row in waterbus.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=row["name"],
        icon=folium.Icon(color="blue")
    ).add_to(m)

# Hub candidates
for _, row in hub.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=row["name"],
        icon=folium.Icon(color="green")
    ).add_to(m)

# Orders
for _, row in orders.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=2,
        fill=True
    ).add_to(m)

# Lưu bản đồ vào file HTML
output_file = os.path.join(BASE_DIR, "multimodal_map_v1.2.html")
m.save(output_file)
print(f"Map exported successfully to: {output_file}")

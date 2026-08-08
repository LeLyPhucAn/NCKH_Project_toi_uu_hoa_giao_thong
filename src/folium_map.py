import os
import pandas as pd
import folium

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(base_dir, "data")

metro = pd.read_csv(os.path.join(data_dir, "metro.csv"))
waterbus = pd.read_csv(os.path.join(data_dir, "waterbus.csv"))
hub = pd.read_csv(os.path.join(data_dir, "hub_candidates.csv"))
orders = pd.read_csv(os.path.join(data_dir, "orders.csv"))

print(f"Drawing map with {len(metro)} Metro, {len(waterbus)} Waterbus, {len(hub)} Hubs, {len(orders)} Orders...")

# Tọa độ trung tâm của bản đồ (Trung tâm TP.HCM)
m = folium.Map(location=[10.7769, 106.7009], zoom_start=12)

# Metro (Marker màu đỏ)
for _, row in metro.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"Metro: {row['name']}",
        icon=folium.Icon(color="red", icon="train", prefix="fa")
    ).add_to(m)

# Waterbus (Marker màu xanh dương)
for _, row in waterbus.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"Waterbus: {row['name']}",
        icon=folium.Icon(color="blue", icon="ship", prefix="fa")
    ).add_to(m)

# Hub candidates (Marker màu xanh lá)
for _, row in hub.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f"Hub: {row['name']}",
        icon=folium.Icon(color="green", icon="building", prefix="fa")
    ).add_to(m)

# Orders (CircleMarker chấm cam nhỏ)
for _, row in orders.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=3,
        color="#ff7800",
        fill=True,
        fill_color="#ff7800",
        fill_opacity=0.6,
        popup=f"Order #{int(row['order_id'])} ({row['weight_kg']} kg)"
    ).add_to(m)

# Lưu bản đồ vào file HTML ở thư mục gốc
output_html = os.path.join(base_dir, "multimodal_map_v1.html")
m.save(output_html)
print(f"-> Map updated successfully: {output_html}")

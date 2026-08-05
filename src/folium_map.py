import pandas as pd 
metro = pd.read_csv("data/metro.csv")
waterbus = pd.read_csv("data/waterbus.csv")
hub = pd.read_csv("data/hub_candidates.csv")
orders = pd.read_csv("data/orders.csv")
print(metro.head())
# Tọa độ trung tâm của bản đồ (ví dụ: trung tâm TP.HCM)
import folium
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
m.save("multimodal_map_v1.html")

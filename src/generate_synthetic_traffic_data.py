import pandas as pd
import numpy as np
import os

def generate_traffic_data(num_samples=10000):
    """
    Sinh ngẫu nhiên bộ dữ liệu tốc độ giao thông dựa trên quy luật thời tiết và giờ cao điểm.
    Phục vụ đề tài NCKH Tối ưu hóa Giao thông Đa phương thức Quận 1.
    """
    print(f"Bắt đầu sinh {num_samples} dòng dữ liệu...")
    
    # 1. Định nghĩa các giá trị ngẫu nhiên
    road_types = ['primary', 'secondary', 'residential']
    weathers = ['clear', 'light_rain', 'moderate_rain', 'heavy_rain', 'flooded']
    
    # Tỉ lệ phân phối (Xác suất xảy ra)
    road_probs = [0.4, 0.4, 0.2] # Đường chính và nhánh nhiều hơn
    weather_probs = [0.6, 0.15, 0.1, 0.1, 0.05] # Chủ yếu là trời nắng
    
    # Sinh ngẫu nhiên các cột đặc trưng (Features)
    np.random.seed(42) # Cố định seed để kết quả đồng nhất
    data = {
        'road_type': np.random.choice(road_types, num_samples, p=road_probs),
        'weather': np.random.choice(weathers, num_samples, p=weather_probs),
        'is_rush_hour': np.random.choice([0, 1], num_samples, p=[0.7, 0.3]) # 30% là giờ cao điểm
    }
    
    df = pd.DataFrame(data)
    
    # 2. Định nghĩa hệ số theo Logic của NotebookLM
    # Vận tốc cơ bản
    base_speed = {
        'primary': 43.2,
        'secondary': 35.0,
        'residential': 25.0
    }
    
    # Hệ số phạt thời tiết (Đã trừ đi % giảm)
    weather_penalty = {
        'clear': 1.0,
        'light_rain': 1 - 0.0183,    # Giảm 1.83%
        'moderate_rain': 1 - 0.0262, # Giảm 2.62%
        'heavy_rain': 1 - 0.0415 - 0.29, # Giảm 4.15% + 29% hành vi tài xế = ~33.15%
        'flooded': 0.50              # Giảm 50%
    }
    
    # Hệ số phạt giờ cao điểm
    rush_hour_penalty = 1 - 0.326 # Giảm 32.6%
    
    # 3. Tính toán Tốc độ mục tiêu (Label)
    actual_speeds = []
    for index, row in df.iterrows():
        # Lấy vận tốc nền
        speed = base_speed[row['road_type']]
        
        # Áp dụng phạt thời tiết
        speed = speed * weather_penalty[row['weather']]
        
        # Áp dụng phạt giờ cao điểm nếu có
        if row['is_rush_hour'] == 1:
            speed = speed * rush_hour_penalty
            
        # Thêm sai số ngẫu nhiên (Gaussian Noise) +/- 2 km/h để dữ liệu tự nhiên
        noise = np.random.normal(0, 1.5) 
        speed = speed + noise
        
        # Giới hạn tốc độ không được rớt xuống dưới 5 km/h (Bò trên đường)
        speed = max(5.0, speed)
        
        actual_speeds.append(round(speed, 2))
        
    df['actual_speed_kmh'] = actual_speeds
    
    # 4. Xuất ra file CSV
    # Đảm bảo thư mục data tồn tại
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, 'traffic_training_data.csv')
    df.to_csv(output_path, index=False)
    print(f"Đã lưu file thành công tại: {output_path}")
    
    # Hiển thị vài dòng mẫu
    print("\nSample Data:")
    print(df.head(10))

if __name__ == '__main__':
    generate_traffic_data()

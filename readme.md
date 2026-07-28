# 📌 Multimodal AI Logistics System (Tối ưu giao thông Quận 1)

> Hệ thống ứng dụng Trí tuệ Nhân tạo (Machine Learning) và Tối ưu hóa Toán học (OR-Tools) để phân phối đơn hàng đa phương thức (Xe máy, Metro, Waterbus), nhằm minh chứng hiệu quả giảm thiểu ùn tắc và cắt giảm khí thải CO2 tại lõi trung tâm Quận 1, TP.HCM.

---

# 📖 Mục lục

- [1. Giới thiệu](#1-giới-thiệu)
- [2. Mục tiêu](#2-mục-tiêu)
- [3. Tính năng cốt lõi](#3-tính-năng-cốt-lõi)
- [4. Kiến trúc hệ thống](#4-kiến-trúc-hệ-thống)
- [5. Công nghệ sử dụng](#5-công-nghệ-sử-dụng)
- [6. Cấu trúc thư mục](#6-cấu-trúc-thư-mục)
- [7. Cài đặt & Cấu hình](#7-cài-đặt--cấu-hình)
- [8. Chạy chương trình](#8-chạy-chương-trình)
- [9. API Endpoints](#9-api-endpoints)
- [10. Quy trình hoạt động](#10-quy-trình-hoạt-động)
- [11. Thành viên & Roadmap](#11-thành-viên--roadmap)

---

# 1. Giới thiệu

## Tổng quan
Đây là dự án phần mềm Nghiên cứu Khoa học (NCKH) mô phỏng và định tuyến tự động dòng chảy logistics trong đô thị lớn. Khác với các hệ thống giao hàng thông thường chỉ đi đường bộ, hệ thống này tích hợp thêm hệ thống giao thông công cộng (Metro, Tàu thủy) để luân chuyển hàng hóa. Đặc biệt, hệ thống có khả năng nhận biết thời tiết (mưa ngập) để tự động đổi lộ trình.

## Đối tượng sử dụng
- **Hội đồng Khoa học:** Đánh giá tính khả thi, xem xét báo cáo giảm phát thải CO2.
- **Doanh nghiệp Logistics (Admin):** Nhập dữ liệu đơn hàng, điều phối hàng hóa né kẹt xe.

---

# 2. Mục tiêu

Hệ thống nhằm giải quyết 3 bài toán lớn của đô thị TP.HCM (đặc biệt tại Quận 1):
- Tối ưu hóa vị trí đặt kho bãi (Micro-hub) tránh sai số bằng Toán học tuyệt đối.
- Giảm thiểu kẹt xe bằng cách đẩy hàng hóa từ đường bộ xuống tàu điện ngầm / tàu thủy.
- Đưa ra minh chứng số liệu cứng (Hard Data) về việc cắt giảm lượng khí thải CO2.

---

# 3. Tính năng cốt lõi

## Lớp Backend (Engine)
- Tự động tải bản đồ số (OpenStreetMap) khu vực Quận 1.
- AI dự đoán phạt tốc độ giao thông dựa trên thời tiết (Trời mưa/Nắng).
- Thuật toán OR-Tools tự động khoanh vùng và chọn vị trí Hub tối ưu nhất.
- Thuật toán Dijkstra tìm đường đi ngắn nhất kết hợp đa phương thức.
- Tự động xuất báo cáo Excel đối chiếu CO2 giữa 2 kịch bản.

## Lớp Frontend (Dashboard UI)
- Giao diện trực quan xem bản đồ và lộ trình.
- Nút Toggle chuyển đổi kịch bản thời tiết (Trời mưa/Nắng).
- Bảng Dashboard so sánh KPI thời gian và lượng phát thải trực tiếp.

---

# 4. Kiến trúc hệ thống

Hệ thống được thiết kế tách rời Frontend và Backend thông qua REST API.

```text
[ Dữ liệu CSV ] -> [ Backend Python (AI + Routing Engine) ]
                               │
                               ▼ (REST API)
                               │
[ Người dùng ] <-> [ Frontend Dashboard UI (v0.dev) ]
```

*(Chi tiết xem thêm tại tài liệu Sơ đồ luồng xử lý `docs/system_architecture.md`)*

---

# 5. Công nghệ sử dụng

## Backend & Thuật toán (Core)
- **Ngôn ngữ:** Python 3.10+
- **Routing & Đồ thị:** NetworkX, OSMnx
- **Tối ưu hóa (Optimization):** Google OR-Tools, Scikit-learn (K-Medoids)
- **AI / Machine Learning:** XGBoost / Random Forest
- **API Framework:** FastAPI

## Frontend (Dashboard)
- React / Next.js (Khởi tạo tự động bằng v0.dev)
- Tailwind CSS

## Database (Lưu trữ Flat-file)
- Sử dụng Pandas xử lý trực tiếp các file `.csv` tốc độ cao.

---

# 6. Cấu trúc thư mục

```text
project/
│
├── data/                          # Chứa dữ liệu đầu vào (Input)
│   ├── metro_q1.csv               # Tọa độ ga Metro tại Quận 1
│   ├── waterbus_q1.csv            # Tọa độ bến Waterbus
│   ├── hub_candidates.csv         # Ứng viên Hub
│   └── orders.csv                 # Dữ liệu đơn hàng
├── results/                       # Chứa kết quả đầu ra (Output)
│   ├── summary_results.xlsx       # Báo cáo CO2
│   └── selected_hubs_optimal.csv
├── src/                           # Backend Python
│   ├── load_data.py               # Chuẩn hóa dữ liệu
│   ├── build_graph.py             # Xây dựng đồ thị Quận 1
│   ├── select_hub_optimized.py    # Thuật toán OR-Tools/K-Medoids
│   ├── routing_ai_enhanced.py     # AI XGBoost & Dijkstra
│   ├── evaluation.py              # Công thức toán học tính CO2
│   └── main_api.py                # Chạy server FastAPI
├── frontend/                      # Code React UI sinh từ v0
└── README.md
```

---

# 7. Cài đặt & Cấu hình

**Bước 1: Clone project**
```bash
git clone https://github.com/your-repo/multimodal-logistics-ai.git
cd multimodal-logistics-ai
```

**Bước 2: Cài đặt thư viện Backend**
```bash
pip install pandas numpy scipy networkx osmnx scikit-learn ortools xgboost fastapi uvicorn
```

---

# 8. Chạy chương trình

**1. Khởi động Backend API (Python Engine)**
```bash
python -m uvicorn src.main_api:app --reload
```
*(Server sẽ chạy tại `http://localhost:8000`)*

**2. Khởi động Frontend Dashboard**
*(Sau khi tải code React từ v0 về thư mục frontend)*
```bash
cd frontend
npm install
npm run dev
```

---

# 9. API Endpoints

Hệ thống cung cấp các API để Frontend giao tiếp lấy dữ liệu:

- `POST /api/optimize-hub` : Chạy thuật toán tìm Hub tối ưu.
- `POST /api/calculate-routes` : Truyền tham số thời tiết `{"weather": "rain"}` để AI dự đoán và trả về lộ trình tối ưu.
- `GET /api/reports/co2` : Lấy số liệu đối chiếu lượng phát thải CO2 để vẽ biểu đồ.

Tài liệu API (Swagger UI): `http://localhost:8000/docs`

---

# 10. Quy trình hoạt động

Quy trình ra quyết định theo thời gian thực:

1. **User** chọn trạng thái "Trời đang mưa to" trên Frontend.
2. Gửi tín hiệu xuống **Backend API**.
3. **Mô hình AI** phân tích nhận thấy đường bộ Quận 1 đang kẹt cứng. AI gạt trọng số phạt lên đồ thị đường bộ.
4. Thuật toán **Dijkstra** tính toán lại và bẻ lái dòng hàng hóa tập kết về Ga Bến Thành (Metro).
5. Tính toán khoảng cách, nhân với hệ số phát thải, trả kết quả **Response** lên UI.

---

# 11. Thành viên & Roadmap

## Đội ngũ thực hiện
| Họ tên | Vai trò trong NCKH |
|---------|----------|
| Bạn | Phân tích Toán học, AI & Backend |
| Bạn | Xây dựng Giao diện (Frontend) |

## Roadmap (Tiến độ 14 ngày)
- [x] Lấy dữ liệu hạ tầng và cấu trúc bản đồ Quận 1.
- [ ] Xây dựng thuật toán chọn Hub (OR-Tools / K-Medoids).
- [ ] Huấn luyện AI dự đoán tốc độ giao thông.
- [ ] Bọc Backend bằng FastAPI.
- [ ] Tích hợp giao diện Dashboard sinh bởi v0.dev.
# TÀI LIỆU KIẾN TRÚC HỆ THỐNG DOANH NGHIỆP (ENTERPRISE LOGISTICS ARCHITECTURE)

**Dự án:** Multimodal Urban Freight Transportation (Tối ưu hóa Logistics Đa phương thức đô thị tại TP.HCM)  
**Tác giả:** Nguyễn Đức Phát, Lê Lý Phúc An, Nguyễn Đình Phúc, Lê Thành An — Trường ĐH Giao thông Vận tải TP.HCM  
**GVHD:** Thầy Võ Nguyễn Minh Tân  
**Mô hình Kiến trúc:** **Modular Monolith + Layered Clean Architecture (Enterprise Grade 9.5/10)**

---

## 1. Cấu trúc Thư mục Mã nguồn (Directory Structure)

Hệ thống được thiết kế theo tư duy **Feature-First (Modular Monolith)** kết hợp **Clean Architecture**, phân tách 4 tầng rõ ràng: `Core` ➔ `Domain` ➔ `Repositories` ➔ `Modules` ➔ `Presentation`.

```
project/
├── data/                          # Chứa dữ liệu đầu vào GIS (CSV: metro, waterbus, hubs, orders)
├── results/                       # Chứa kết quả tính toán (pkl cache, csv, xlsx, txt)
├── tests/                         # Bộ kiểm thử tự động (Unit Tests & Integration Tests)
│   ├── unit/                      # Tests công thức Haversine, Greedy p-Median, Dijkstra
│   └── api/                       # Tests tích hợp REST API endpoints với TestClient
├── index.html                     # Giao diện Web App Dashboard Doanh nghiệp (Leaflet + Chart.js)
└── src/                           # Mã nguồn Python chuẩn Doanh nghiệp
    ├── core/                      # Cấu hình tập trung, Logger & Exceptions
    │   ├── config/settings.py     # Pydantic Settings quản lý môi trường (Dev/Prod)
    │   ├── constants/transport.py # Hằng số vận tải: Hệ số CO2, Vận tốc, Chi phí
    │   ├── exceptions/base.py     # Custom Domain Exceptions & FastAPI Handlers
    │   └── logging/logger.py      # Logger tập trung
    ├── domain/                    # Tầng nghiệp vụ cốt lõi (Domain Entities & Models)
    │   └── entities.py            # Pydantic Entities: Order, Hub, RouteMetric, KPIRecord
    ├── shared/                    # Các thuật toán & tiện ích thuần túy (Pure Functions)
    │   ├── utils/haversine.py     # Công thức Haversine (Scalar & Vectorized)
    │   ├── utils/data_cleaner.py  # Regex làm sạch tọa độ
    │   └── algorithms/            # Thuật toán độc lập (Dijkstra, p-Median, K-NN Matcher)
    ├── repositories/              # Tầng Truy xuất Dữ liệu (Repository Pattern)
    │   ├── data_repository.py     # Nạp & lưu CSV đầu vào
    │   ├── graph_repository.py    # Dựng & lưu Cache Đồ thị Mạng lưới (.pkl)
    │   └── result_repository.py   # Lưu báo cáo kết quả (CSV/Excel/Log)
    ├── modules/                   # Các Module nghiệp vụ độc lập (Domain Modules)
    │   ├── hub/                   # Module Micro Hubs (Service, Schemas DTO, API)
    │   ├── routing/               # Module Định tuyến Dijkstra (Service, Schemas DTO, API)
    │   ├── analytics/             # Module KPI & CO2 (Service, Schemas DTO, API)
    │   └── simulation/            # Module Mô phỏng ABM (Service, Schemas DTO, API)
    ├── server.py                  # Lắp ráp ứng dụng FastAPI Server chuẩn
    ├── main.py                    # Adapter điều phối Pipeline CLI
    └── api_server.py              # Runner khởi chạy Server
```

---

## 2. Các Tầng Kiến trúc & Nguyên lý Thiết kế (Design Principles)

### 📌 1. Dependency Inversion & Repository Pattern (`src/repositories/`)
* Tầng nghiệp vụ (`Service`) không truy cập trực tiếp vào đĩa hay thư viện bên thứ ba.
* Mọi thao tác nạp/lưu dữ liệu đều qua `DataRepository`, `GraphRepository` và `ResultRepository`.
* **Lợi ích:** Khi chuyển nguồn lưu trữ từ CSV sang cơ sở dữ liệu **PostgreSQL / PostGIS / Redis**, tầng Service và API giữ nguyên 100%.

### 📌 2. Pure Algorithms (`src/shared/algorithms/`)
* Các thuật toán `dijkstra.py`, `greedy_pmedian.py`, `haversine.py` là **Hàm thuần túy (Pure Functions)**, hoàn toàn độc lập với FastAPI, CSV hay Logger.
* Rất dễ dàng cho việc **Unit Test** và tối ưu thuật toán.

### 3. Pydantic DTOs & Validation (`src/modules/*/schemas.py`)
* API trả về các DTOs chuẩn mực (`HubResponse`, `RouteDetailResponse`, `KPISummaryResponse`) thay vì Dictionary thô.
* Đảm bảo tính nhất quán dữ liệu đầu ra và tự động tạo tài liệu **OpenAPI / Swagger UI**.

### 📌 4. Custom Exception Handling (`src/core/exceptions/base.py`)
* Hệ thống định nghĩa các ngoại lệ nghiệp vụ chuyên biệt (`NotFoundException`, `RoutingException`, `HubSelectionException`).
* FastAPI Exception Handler tự động bắt lỗi và chuẩn hóa JSON Response cho Frontend.

---

## 3. Kiểm thử Tự động (Automated Testing)

Dự án đã tích hợp bộ kiểm thử tự động sử dụng `pytest`:

```bash
# Chạy toàn bộ Unit Tests & Integration API Tests
py -3.12 -m pytest tests/
```

---

## 4. Hướng dẫn Vận hành Hệ thống

### **Cách 1: Khởi chạy API Server Backend**
```bash
py -3.12 src/server.py
```
Server chạy tại: `http://127.0.0.1:8000` (Tự động tải giao diện `index.html` tại trang chủ `/`).

### **Cách 2: Chạy Pipeline CLI thủ công**
```bash
py -3.12 src/main.py
```
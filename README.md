# AI Data Trust Platform

Nền tảng hỗ trợ đánh giá độ tin cậy dữ liệu (Data Trust Platform) sử dụng các kỹ thuật phân tích dữ liệu, kiểm tra chất lượng dữ liệu và AI hỗ trợ giải thích kết quả.

> 🚧 Đây là phiên bản demo/prototype đang trong quá trình phát triển. Một số tính năng và cải tiến về kiến trúc hệ thống sẽ được tiếp tục hoàn thiện trong các phiên bản sau.

---

## 📌 Tổng quan

Trong các hệ thống dữ liệu hiện đại, chất lượng dữ liệu đóng vai trò quan trọng trong việc đảm bảo kết quả phân tích chính xác và độ tin cậy của các ứng dụng AI.

**AI Data Trust Platform** được xây dựng nhằm hỗ trợ người dùng đánh giá tình trạng của một bộ dữ liệu thông qua các bước:

- Thu thập và phân tích thông tin dữ liệu
- Đánh giá chất lượng dữ liệu
- Tính toán điểm tin cậy (Trust Score)
- Phát hiện dữ liệu bất thường
- Phân tích sự thay đổi dữ liệu (Data Drift)
- Cung cấp giải thích thông qua AI Assistant

---

## ✨ Chức năng chính

### 1. Phân tích dữ liệu (Data Profiling)

Hệ thống tự động phân tích dataset:

- Thông tin cấu trúc dữ liệu
- Kiểu dữ liệu của các thuộc tính
- Thống kê cơ bản
- Tỷ lệ dữ liệu thiếu
- Kiểm tra bản ghi trùng lặp


### 2. Đánh giá chất lượng dữ liệu (Data Quality Assessment)

Kiểm tra các vấn đề phổ biến:

- Missing value
- Sai lệch kiểu dữ liệu
- Dữ liệu trùng lặp
- Kiểm tra tính nhất quán
- Phân loại mức độ ảnh hưởng của lỗi dữ liệu


### 3. Tính toán Data Trust Score

Hệ thống xây dựng điểm đánh giá tổng quan về độ tin cậy của dataset dựa trên các tiêu chí:

- Completeness (Đầy đủ)
- Consistency (Nhất quán)
- Validity (Hợp lệ)
- Các chỉ số chất lượng dữ liệu khác


### 4. Phát hiện dữ liệu bất thường (Anomaly Detection)

Hỗ trợ phát hiện các mẫu dữ liệu bất thường bằng:

- IQR-based detection
- Z-score analysis
- Isolation Forest


### 5. Phân tích Data Drift

So sánh sự thay đổi giữa các phiên bản dữ liệu:

- Schema Drift
- Thay đổi phân phối dữ liệu
- PSI (Population Stability Index)
- Phân tích sự thay đổi theo từng thuộc tính


### 6. Phát hiện rủi ro dữ liệu cá nhân (Privacy Risk Scan)

Kiểm tra các trường dữ liệu có khả năng chứa thông tin nhạy cảm:

- PII detection
- Nhận diện mẫu dữ liệu có nguy cơ
- Cảnh báo rủi ro bảo mật dữ liệu


### 7. AI Assistant (Prototype)

Trợ lý AI hỗ trợ giải thích kết quả phân tích:

- Giải thích nguyên nhân Trust Score
- Phân tích các vấn đề chất lượng dữ liệu
- Đề xuất hướng cải thiện dữ liệu

---

## 🏗️ Kiến trúc hệ thống

```
                    Người dùng
                       |
                       |
                 Streamlit UI
                       |
          ---------------------------
          |                         |
    Data Trust Engine          AI Assistant
          |
 -----------------------------------------
 |          |          |                  |
Profiling  Quality  Anomaly            Drift
          |
          |
       Reports
```

---

## 🛠️ Công nghệ sử dụng

### Ngôn ngữ

- Python

### Xử lý dữ liệu

- Pandas
- NumPy

### Machine Learning

- Scikit-learn

### Backend API

- FastAPI

### Frontend

- Streamlit

### Visualization

- Plotly

### Database

- SQL Database

---

## 📂 Cấu trúc thư mục

```
ai-data-trust-platform/

├── api/                  # Backend API
├── app/                  # Streamlit application
├── data/                 # Dataset mẫu và báo cáo
├── database/             # Database layer
├── docs/                 # Tài liệu mô tả
├── notebooks/            # Notebook thử nghiệm
├── src/                  # Core processing modules
│
├── tests/                # Unit tests
├── requirements.txt
├── README.md
└── .env.example
```

---

## 🚀 Cài đặt và chạy thử

### 1. Clone repository

```bash
git clone https://github.com/Hungnguyencode/ai-data-trust-platform.git

cd ai-data-trust-platform
```

### 2. Tạo môi trường ảo

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/Mac:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Tạo file `.env` dựa trên file:

```
.env.example
```

### 5. Chạy ứng dụng

Chạy Streamlit:

```bash
streamlit run app/streamlit_app.py
```

Chạy API:

```bash
uvicorn api.main:app --reload
```

---

## 📊 Luồng demo

1. Upload dataset
2. Hệ thống phân tích dữ liệu
3. Kiểm tra các vấn đề chất lượng
4. Tính toán Trust Score
5. Phát hiện anomaly và drift
6. Sinh báo cáo
7. Sử dụng AI Assistant để giải thích kết quả

---

## 🚧 Trạng thái phát triển

### Đã hoàn thành

✅ Data Profiling  
✅ Data Quality Validation  
✅ Trust Score Calculation  
✅ Anomaly Detection  
✅ Data Drift Analysis  
✅ Privacy Risk Scan  
✅ AI Assistant cơ bản  


### Định hướng phát triển

- Hoàn thiện kiến trúc API
- Docker hóa hệ thống
- Cải thiện quản lý database
- Nâng cấp AI Assistant
- Bổ sung khả năng monitoring dữ liệu


---

## 📌 Lưu ý

Đây là một dự án học tập và nghiên cứu thử nghiệm.

Phiên bản hiện tại tập trung vào việc minh họa quy trình đánh giá chất lượng dữ liệu và kiến trúc của một hệ thống Data Trust Platform. Dự án chưa hướng tới việc triển khai ở môi trường doanh nghiệp thực tế.

---

## 👤 Tác giả

Hung Nguyen

GitHub:
https://github.com/Hungnguyencode

# DSK System - Hệ thống Phân tích Thị trường BĐS

Hệ thống này giúp cào tin tức bất động sản từ nhiều nguồn RSS, phân tích chiến lược bằng AI (Gemini) và hiển thị kết quả trên Dashboard Streamlit.

## 🚀 Tính năng chính
- **Crawler**: Cào tin đa luồng từ >20 đầu báo uy tín.
- **AI Analyzer**: Trích xuất dữ liệu D-S-K (Data - Strategy - Knowledge) bằng Gemini Flash 2.5.
- **Dashboard**: Hiển thị bảng điều khiển trực quan (Looker Studio style).

## 🛠️ Cài đặt

1. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình API Key:**
   - Tạo file `.env` từ file mẫu `.env.example`.
   - Điền Gemini API Key vào biến `GEMINI_API_KEY`.

## 📈 Cách sử dụng

1. **Cào dữ liệu:**
   ```bash
   python bds_crawler.py
   ```

2. **Phân tích AI:**
   ```bash
   python ai_analyzer.py
   ```

3. **Mở Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

## 🐳 Cài đặt với Docker (Khuyên dùng)

Nếu bạn đã cài đặt Docker và Docker Compose, bạn có thể khởi chạy hệ thống nhanh chóng mà không cần cài đặt Python thủ công:

1. **Cấu hình API Key:**
   - Tạo file `.env` từ file mẫu `.env.example`.
   - Điền Gemini API Key vào biến `GEMINI_API_KEY`.

2. **Khởi chạy Dashboard:**
   ```bash
   docker-compose up --build
   ```
   - Dashboard sẽ sẵn sàng tại: `http://localhost:8501`

3. **Chạy Crawler hoặc Analyzer trong Docker:**
   ```bash
   docker exec -it dsk_dashboard python bds_crawler.py
   docker exec -it dsk_dashboard python ai_analyzer.py
   ```

## 📁 Cấu trúc dự án
- `bds_crawler.py`: Module thu thập tin tức.
- `ai_analyzer.py`: Module xử lý ngôn ngữ tự nhiên.
- `dashboard.py`: Giao diện người dùng.
- `requirements.txt`: Danh sách thư viện.
- `Dockerfile` & `docker-compose.yml`: Cấu hình container hóa.
- `.gitignore`: Các file được loại bỏ khi đẩy lên Git.

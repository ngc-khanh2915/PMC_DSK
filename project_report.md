# Báo cáo Dự án: DSK System - Hệ thống Phân tích Thị trường BĐS Thông minh

## 1. Tổng quan dự án
**DSK System** (Data - Strategy - Knowledge) là một hệ thống tự động hóa toàn diện quy trình thu thập, phân tích và trình diễn thông tin thị trường bất động sản. Hệ thống sử dụng trí tuệ nhân tạo (Gemini AI) để biến các bản tin thô thành các chỉ số chiến lược và kế hoạch hành động cụ thể cho các phòng ban trong doanh nghiệp.

## 2. Các tính năng chính

### 🌐 Hệ thống Thu thập (Crawler)
- **Đa nguồn tin**: Tự động quét tin tức từ hơn 20 nguồn báo chí uy tín tại Việt Nam (VnExpress, CafeF, Tuổi Trẻ, Dân Trí, VietNamNet, v.v.).
- **Lọc tin chuẩn Playbook**: Sử dụng bộ lọc từ khóa (Whitelist/Blacklist) để chỉ giữ lại các tin tức giá trị về dự án, quy hoạch, chính sách, hạ tầng và loại bỏ các tin tức rác (trang trí, phong thủy, án mạng...).
- **Xử lý đa luồng**: Tốc độ cào nhanh với cơ chế `asyncio/aiohttp`, hỗ trợ tối đa 50 yêu cầu cùng lúc.
- **Chống trùng lặp**: Sử dụng thuật toán TF-IDF và Cosine Similarity để so khớp nội dung, đảm bảo không lưu trữ các tin tức có nội dung tương tự nhau (độ chính xác > 85%).

### 🤖 Phân tích AI Chiến lược (AI Analyzer)
- **Gemini Intelligence**: Sử dụng mô hình `gemini-2.5-flash` đóng vai trò Giám đốc Chiến lược PMC để bóc tách dữ liệu.
- **Trích xuất D-S-K**:
    - **DATA**: Tên dự án, Chủ đầu tư, Vị trí, Quy mô pháp lý, Mốc thời gian.
    - **STRATEGY**: Bối cảnh 5W1H (Who, What, Where, When, Why, How), sự kiện đổi trạng thái của thị trường.
    - **KNOWLEDGE**: Phân tích lợi ích/rủi ro cho các Stakeholders và dự báo xu hướng 3-6 tháng tới.
- **Chỉ số hóa**: Tự động gán "Điểm Sức khỏe" (Health Score) cho các sự kiện và phân loại theo loại hình BĐS, vòng đời dự án.
- **Kế hoạch hành động (Action Plan)**: Tự động đề xuất các đầu việc cụ thể cho 5 phòng ban: BD (Phát triển kinh doanh), R&D, Pháp lý, Tài chính, và Marketing.

### 📊 Bảng điều khiển Trực quan (Dashboard)
- **Giao diện Premium**: Thiết kế hiện đại theo phong cách "Intelligence Hub" với Dark Mode và font chữ tối ưu.
- **Phân tích dữ liệu đa chiều**:
    - **Strategic**: Biểu đồ hình quạt về nhóm sự kiện, biểu đồ Radar về cơ hội dịch vụ PMC.
    - **Data & Lifecycle**: Bản đồ nhiệt (Treemap) địa lý, biểu đồ Phễu (Funnel) vòng đời dự án.
    - **Knowledge**: Ma trận cơ hội và biểu đồ cột về "sức khỏe" thị trường theo khu vực.
- **Kanban Action Plan**: Hiển thị các hành động cần thực hiện cho từng bộ phận dưới dạng thẻ Kanban.
- **Intelligence Feed**: Danh sách tin tức chi tiết kèm theo các tab phân tích chuyên sâu (5W1H, Stakeholders, Forecast).

## 3. Quy trình hoạt động

1. **Giai đoạn 1: Cào dữ liệu (`bds_crawler.py`)**  
   Hệ thống đọc danh sách RSS -> Cào text thô -> Lọc từ khóa -> Lọc trùng lặp -> Lưu vào SQLite Database.

2. **Giai đoạn 2: Phân tích AI (`ai_analyzer.py`)**  
   Hệ thống đọc các tin chưa xử lý -> Gửi yêu cầu phân tích tới Gemini AI kèm Prompt chuyên gia -> Nhận kết quả JSON -> Cập nhật ngược lại Database và xóa các tin được xác định là "Tin rác".

3. **Giai đoạn 3: Trình diễn (`dashboard.py`)**  
   Streamlit kết nối với Database -> Xử lý dữ liệu thời gian thực -> Hiển thị các biểu đồ tương tác và bảng chi tiết cho người dùng cuối.

## 4. Công nghệ sử dụng
- **Ngôn ngữ**: Python
- **Xử lý dữ liệu**: Pandas, SQL/SQLite.
- **AI/NLP**: Google Gemini API, Scikit-learn (TF-IDF).
- **Cào dữ liệu**: Feedparser, Trafilatura, Asyncio, Aiohttp.
- **Frontend/Visualization**: Streamlit, Plotly.

## 5. Cấu trúc thư mục dự án
- `bds_crawler.py`: Module module thu thập và lọc tin bài.
- `ai_analyzer.py`: Module phân tích ngôn ngữ tự nhiên và trích xuất số liệu.
- `dashboard.py`: Giao diện Dashboard hiển thị báo cáo.
- `bds_news.db`: Cơ sở dữ liệu SQLite lưu trữ toàn bộ thông tin.
- `requirements.txt`: Danh sách các thư viện cần cài đặt.
- `.env`: Cấu hình API Key (không công khai).

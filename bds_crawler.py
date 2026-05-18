import feedparser
import trafilatura
import asyncio
import aiohttp
import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'bds_news.db')

# ==========================================
# NGUỒN RSS — 20 TỜ BÁO
# ==========================================
rss_feeds = {
    "VnExpress":          ["https://vnexpress.net/rss/bat-dong-san.rss",
                           "https://vnexpress.net/rss/kinh-doanh.rss",
                           "https://vnexpress.net/rss/phap-luat.rss",
                           "https://vnexpress.net/rss/khoa-hoc.rss"],
    "CafeF":              ["https://cafef.vn/bat-dong-san.rss",
                           "https://cafef.vn/vi-mo-dau-tu.rss"],
    "Tuổi Trẻ":           ["https://tuoitre.vn/rss/kinh-doanh.rss",
                           "https://tuoitre.vn/rss/phap-luat.rss",
                           "https://tuoitre.vn/rss/khoa-hoc.rss"],
    "Thanh Niên":         ["https://thanhnien.vn/rss/kinh-te.rss"],
    "Dân Trí":            ["https://dantri.com.vn/rss/bat-dong-san.rss",
                           "https://dantri.com.vn/rss/kinh-doanh.rss"],
    "Tiền Phong":         ["https://tienphong.vn/rss/dia-oc-166.rss",
                           "https://tienphong.vn/rss/kinh-te-3.rss"],
    "Sài Gòn Giải Phóng": ["https://www.sggp.org.vn/rss/kinhte-89.rss",
                           "https://www.sggp.org.vn/rss/xaydungdiaoc-205.rss"],
    "Nhân Dân":           ["https://nhandan.vn/rss/kinhte-thitruong.rss"],
    "Kinh tế Sài Gòn":    ["https://vnbusiness.vn/bat-dong-san.rss",
                           "https://vnbusiness.vn/thi-truong.rss"],
    "Lao Động":           ["https://laodong.vn/rss/bat-dong-san.rss",
                           "https://laodong.vn/rss/kinh-doanh.rss"],
    "Kinh tế Đô thị":     ["https://tieudung.kinhtedothi.vn/bat-dong-san.rss",
                           "https://tieudung.kinhtedothi.vn/trangchu.rss"],
    "Hà Nội Mới":         ["https://hanoimoi.vn/rss/home.rss"],
    "Người Lao Động":     ["https://nld.com.vn/rss/kinh-te.rss"],
    "VietNamNet":         ["https://vietnamnet.vn/rss/bat-dong-san.rss"],
    "Xây dựng":           ["https://baoxaydung.com.vn/rss/bat-dong-san.rss"],
    "Đầu tư":             ["https://baodautu.vn/bat-dong-san.rss"],
    "Đấu thầu":           ["https://baodauthau.vn/rss/bat-dong-san.rss"],
    "Pháp luật TPHCM":    ["https://plo.vn/rss/bat-dong-san.rss",
                           "https://plo.vn/rss/kinh-te.rss"],
    "VietnamPlus":        ["https://www.vietnamplus.vn/rss/kinh-te.rss"],
    "Tin tức":            ["http://baotintuc.vn/rss/kinh-te-167.rss",
                           "http://baotintuc.vn/rss/bat-dong-san-174.rss"]
}

# ==========================================
# BỘ LỌC TIN — 3 NHÓM THEO FRAMEWORK PMC
# ==========================================

# TIN RÁC TUYỆT ĐỐI — loại bỏ ngay, không analyze
black_keywords = [
    # Thể thao
    'hlv ', 'cầu thủ', 'bóng đá', 'bóng rổ', 'thể thao', 'giải đấu',
    'vô địch', 'tuyển thủ', 'câu lạc bộ', 'v.league', 'ngoại hạng anh',
    'world cup', 'euro ', 'champions league',
    # Giải trí
    'showbiz', 'nghệ sĩ', 'ca sĩ', 'diễn viên', 'phim ', 'hoa hậu',
    'tử vi', 'phong thủy',
    # Ẩm thực / đời sống cá nhân
    'ẩm thực', 'món ăn', 'nhà hàng', 'quán ăn', 'nấu ăn', 'công thức',
    'mẹo vặt', 'cách làm', 'dọn nhà', 'nội thất', 'trang trí',
    # Tai nạn thông thường
    'tai nạn giao thông', 'đâm xe', 'lật xe',
]

# NHÓM 1 — TÁC ĐỘNG TRỰC TIẾP (BĐS, Pháp luật, Hạ tầng, Quy hoạch)
white_group1 = [
    'bất động sản', 'nhà đất', 'đất nền', 'căn hộ', 'chung cư',
    'quy hoạch', 'hạ tầng', 'giao thông', 'metro', 'cao tốc', 'vành đai',
    'lãi suất', 'tín dụng', 'ngân hàng', 'cho vay', 'trái phiếu',
    'chủ đầu tư', 'dự án', 'khu đô thị', 'khu công nghiệp',
    'luật đất đai', 'luật nhà ở', 'luật kinh doanh bđs',
    'pccc', 'phòng cháy', 'quản lý vận hành', 'ban quản trị',
    'phí bảo trì', 'hội nghị nhà chung cư',
    'đấu thầu', 'đấu giá', 'thanh tra', 'kiểm tra',
    'cất nóc', 'động thổ', 'khánh thành', 'bàn giao', 'mở bán',
    'm&a', 'fdi', 'vốn đầu tư',
]

# NHÓM 2 — TÁC ĐỘNG GIÁN TIẾP (PropTech, Công nghệ, Lao động, Y tế)
white_group2 = [
    'trí tuệ nhân tạo', 'ai ', 'iot', 'smart building', 'tòa nhà thông minh',
    'chuyển đổi số', 'công nghệ', 'proptech', 'fintech',
    'năng lượng tái tạo', 'điện mặt trời', 'tiết kiệm năng lượng',
    'lao động', 'nhân sự', 'tuyển dụng', 'tiền lương', 'bảo hiểm',
    'y tế', 'sức khỏe cộng đồng', 'dịch bệnh', 'môi trường sống',
    'giáo dục', 'đại học', 'trường học', 'khu công nghệ cao',
    'quỹ đổi mới', 'khoa học', 'nghiên cứu',
    'tiêu dùng', 'thị trường bán lẻ', 'logistics',
]

# NHÓM 3 — CẢNH BÁO SỚM (Vĩ mô quốc tế, FDI, ESG, Địa chính trị)
white_group3 = [
    'fed ', 'cục dự trữ liên bang', 'lãi suất mỹ', 'lạm phát toàn cầu',
    'fdi ', 'đầu tư nước ngoài', 'chuỗi cung ứng', 'supply chain',
    'esg', 'phát triển bền vững', 'net zero', 'carbon',
    'biến đổi khí hậu', 'ngập lụt', 'môi trường',
    'địa chính trị', 'thương mại quốc tế', 'xuất nhập khẩu',
    'kinh tế thế giới', 'tăng trưởng toàn cầu', 'suy thoái',
    'trump', 'trung quốc và việt nam', 'asean', 'cptpp', 'rcep',
]

# Gộp tất cả white keywords
white_keywords = white_group1 + white_group2 + white_group3


async def fetch_html(session, url, semaphore):
    async with semaphore:
        try:
            async with session.get(url, timeout=15) as response:
                return await response.text()
        except:
            return None


async def extract_contents(entries):
    semaphore = asyncio.Semaphore(50)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html(session, entry['link'], semaphore) for entry in entries]
        htmls = await asyncio.gather(*tasks)
        results = []
        for html, entry in zip(htmls, entries):
            if html:
                text = trafilatura.extract(html)
                if text and len(text) > 150:
                    entry['content'] = text
                    results.append(entry)
        return results


def crawl_bds_news():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] KHỞI ĐỘNG CRAWLER — FRAMEWORK 3 NHÓM PMC")
    conn = sqlite3.connect(DB_FILE)
    try:
        df_existing = pd.read_sql("SELECT Link, `Nội dung` FROM articles", conn)
    except:
        df_existing = pd.DataFrame(columns=['Link', 'Nội dung'])

    existing_links  = set(df_existing['Link'].tolist())
    existing_corpus = df_existing['Nội dung'].fillna("").tolist()

    vectorizer   = None
    tfidf_matrix = None
    if len(existing_corpus) > 0:
        vectorizer   = TfidfVectorizer(max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(existing_corpus)

    raw_entries = []
    for source, urls in rss_feeds.items():
        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.link
                if link in existing_links:
                    continue

                title_lower = entry.title.lower()

                # Lọc tin rác tuyệt đối
                if any(kw in title_lower for kw in black_keywords):
                    continue

                # Giữ lại nếu khớp bất kỳ white keyword nào (3 nhóm)
                is_relevant = any(kw in title_lower for kw in white_keywords)

                # Hoặc đến từ chuyên mục BĐS/kinh tế rõ ràng
                is_relevant_url = any(seg in url for seg in [
                    'bat-dong-san', 'kinh-doanh', 'kinh-te', 'phap-luat',
                    'quy-hoach', 'dau-tu', 'tai-chinh', 'khoa-hoc', 'cong-nghe'
                ])

                if is_relevant or is_relevant_url:
                    raw_entries.append({
                        'source':   source,
                        'title':    entry.title,
                        'link':     link,
                        'pub_date': entry.get('published', entry.get('pubDate', ''))
                    })
                    existing_links.add(link)

    if not raw_entries:
        print("[XONG] Không có tin tức mới.")
        conn.close()
        return

    print(f"Đã gom được {len(raw_entries)} link. Đang cào đa luồng...")
    crawled_articles = asyncio.run(extract_contents(raw_entries))

    final_articles = []
    print(f"Cào xong {len(crawled_articles)} bài. Đang lọc trùng lặp...")
    for article in crawled_articles:
        text         = article['content']
        is_duplicate = False
        if vectorizer is not None:
            new_vec = vectorizer.transform([text])
            if cosine_similarity(new_vec, tfidf_matrix).max() > 0.85:
                is_duplicate = True

        if not is_duplicate:
            final_articles.append({
                "Nguồn":        article['source'],
                "Tiêu đề":      article['title'],
                "Link":         article['link'],
                "Ngày đăng":    article['pub_date'],
                "Nội dung":     text,
                "Thời gian cào": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if vectorizer is not None:
                existing_corpus.append(text)
                tfidf_matrix = vectorizer.fit_transform(existing_corpus)

    if final_articles:
        df_new = pd.DataFrame(final_articles)
        df_new.to_sql('articles', conn, if_exists='append', index=False)
        print(f"\n[HOÀN TẤT] Đã lưu {len(final_articles)} tin mới vào Database!")
    else:
        print("\n[HOÀN TẤT] Toàn tin trùng lặp, đã bỏ qua.")
    conn.close()


if __name__ == "__main__":
    crawl_bds_news()

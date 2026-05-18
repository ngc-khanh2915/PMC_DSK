"""
PMC Intelligence — Auto Scheduler
Chạy nền tự động: Crawler → Analyzer theo lịch cố định
Cách dùng: python scheduler.py
"""
import schedule
import time
import subprocess
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON   = sys.executable  # dùng đúng python trong venv hiện tại

CRAWLER_SCRIPT  = os.path.join(BASE_DIR, 'bds_crawler.py')
ANALYZER_SCRIPT = os.path.join(BASE_DIR, 'ai_analyzer.py')

LOG_FILE = os.path.join(BASE_DIR, 'scheduler.log')


def log(msg: str):
    ts  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def run_script(script_path: str, label: str):
    log(f"▶ Bắt đầu {label}...")
    try:
        result = subprocess.run(
            [PYTHON, script_path],
            capture_output=False,   # in thẳng ra terminal
            text=True,
            cwd=BASE_DIR
        )
        if result.returncode == 0:
            log(f"✓ {label} hoàn tất.")
        else:
            log(f"✗ {label} kết thúc với lỗi (exit code {result.returncode}).")
    except Exception as e:
        log(f"✗ {label} gặp lỗi nghiêm trọng: {e}")


def job_crawl():
    run_script(CRAWLER_SCRIPT, 'CRAWLER')


def job_analyze():
    run_script(ANALYZER_SCRIPT, 'ANALYZER')


def job_crawl_then_analyze():
    """Crawler xong rồi mới analyze — dùng cho lịch buổi chiều và buổi tối."""
    run_script(CRAWLER_SCRIPT,  'CRAWLER')
    run_script(ANALYZER_SCRIPT, 'ANALYZER')


# ==========================================
# LỊCH CHẠY: 2 lần/ngày
# ==========================================
# Lần 1: 16:00 — Crawler + Analyzer (tin trong ngày)
# Lần 2: 23:00 — Crawler + Analyzer (tin cuối ngày)

# Lần 1 — Buổi chiều
schedule.every().day.at("16:00").do(job_crawl)
schedule.every().day.at("16:30").do(job_analyze)

# Lần 2 — Buổi tối
schedule.every().day.at("23:00").do(job_crawl)
schedule.every().day.at("23:30").do(job_analyze)

# ==========================================
# CHẠY NGAY KHI KHỞI ĐỘNG (tùy chọn)
# ==========================================
# Bỏ comment dòng dưới nếu muốn chạy ngay 1 lần khi start scheduler
# job_crawl_then_analyze()


if __name__ == "__main__":
    log("=" * 55)
    log("PMC INTELLIGENCE SCHEDULER — KHỞI ĐỘNG")
    log(f"Lịch chạy: Crawler 16:00 → Analyzer 16:30 | Crawler 23:00 → Analyzer 23:30")
    log(f"Python: {PYTHON}")
    log(f"Thư mục: {BASE_DIR}")
    log("=" * 55)

    while True:
        schedule.run_pending()
        time.sleep(30)  # kiểm tra mỗi 30 giây
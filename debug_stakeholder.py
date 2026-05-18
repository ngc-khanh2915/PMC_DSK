"""Chạy trên VPS để xem raw text Phân tích Stakeholders"""
import sqlite3, os
DB = os.path.expanduser('~/dsk-system/bds_news.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
    SELECT "Tiêu đề", "Phân tích Stakeholders"
    FROM articles
    WHERE "Phân tích Stakeholders" IS NOT NULL 
      AND "Phân tích Stakeholders" != ''
    LIMIT 3
""")
for row in cur.fetchall():
    print(f"\n{'='*60}")
    print(f"Tiêu đề: {row[0][:60]}")
    print(f"---RAW STAKEHOLDERS---")
    print(repr(row[1][:800]))  # repr để thấy \n, space, ký tự đặc biệt
conn.close()

import sqlite3

conn = sqlite3.connect('bds_news.db')

# Kiểm tra trước
total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
print(f"Tổng tin: {total}")

# Reset tất cả tin để phân loại lại với logic mới
result = conn.execute("""
    UPDATE articles 
    SET "Tóm tắt" = NULL
    WHERE "Nhóm Sự kiện" IN (
        'Địa chính trị','Công nghệ & ESG','Kinh tế Vĩ mô',
        'Tài chính & Tín dụng','Dịch vụ BĐS'
    )
    OR "Tóm tắt" LIKE '%thủy sản%'
    OR "Tóm tắt" LIKE '%hàng không%'
    OR "Tóm tắt" LIKE '%du lịch%'
    OR "Tóm tắt" LIKE '%bitcoin%'
    OR "Tóm tắt" LIKE '%tiền số%'
""")

print(f"Đã reset: {result.rowcount} tin")
conn.commit()

# Kiểm tra lại
remaining = conn.execute(
    "SELECT COUNT(*) FROM articles WHERE \"Tóm tắt\" IS NOT NULL AND \"Tóm tắt\" != ''"
).fetchone()[0]
print(f"Tin còn giữ nguyên: {remaining}")
conn.close()
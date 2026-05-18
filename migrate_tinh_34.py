"""
migrate_tinh_34.py
─────────────────
Chuẩn hóa cột "Tỉnh Thành" trong bds_news.db
về đúng 34 tỉnh thành sau sáp nhập 2025.

Chạy: python3 migrate_tinh_34.py
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bds_news.db')

# ── 34 tỉnh chuẩn ────────────────────────────────────────────────
TINH_34 = [
    'Hà Nội','Tuyên Quang','Lào Cai','Thái Nguyên','Phú Thọ',
    'Bắc Ninh','Hưng Yên','Hải Phòng','Ninh Bình','Quảng Trị',
    'Đà Nẵng','Quảng Ngãi','Gia Lai','Khánh Hòa','Lâm Đồng',
    'Đắk Lắk','TP.HCM','Đồng Nai','Tây Ninh','Cần Thơ',
    'Vĩnh Long','Đồng Tháp','Cà Mau','An Giang',
    'Huế','Lai Châu','Điện Biên','Sơn La','Lạng Sơn',
    'Quảng Ninh','Thanh Hóa','Nghệ An','Hà Tĩnh','Cao Bằng',
]

# ── Mapping đầy đủ tên cũ → tên mới ─────────────────────────────
TINH_MAP = {
    # Hà Nội
    'hà nội':'Hà Nội','ha noi':'Hà Nội',
    'tp hà nội':'Hà Nội','tp.hà nội':'Hà Nội',
    'thành phố hà nội':'Hà Nội','tp. hà nội':'Hà Nội',

    # Tuyên Quang (← Hà Giang + Tuyên Quang)
    'hà giang':'Tuyên Quang','ha giang':'Tuyên Quang',
    'tuyên quang':'Tuyên Quang',

    # Lào Cai (← Yên Bái + Lào Cai)
    'yên bái':'Lào Cai','yen bai':'Lào Cai','lào cai':'Lào Cai',

    # Thái Nguyên (← Bắc Kạn + Thái Nguyên)
    'bắc kạn':'Thái Nguyên','bac kan':'Thái Nguyên',
    'thái nguyên':'Thái Nguyên',

    # Phú Thọ (← Vĩnh Phúc + Hòa Bình + Phú Thọ)
    'vĩnh phúc':'Phú Thọ','hòa bình':'Phú Thọ','phú thọ':'Phú Thọ',

    # Bắc Ninh (← Bắc Giang + Bắc Ninh)
    'bắc giang':'Bắc Ninh','bắc ninh':'Bắc Ninh',

    # Hưng Yên (← Thái Bình + Hưng Yên)
    'thái bình':'Hưng Yên','hưng yên':'Hưng Yên',

    # Hải Phòng (← Hải Dương + Hải Phòng)
    'hải dương':'Hải Phòng','hai duong':'Hải Phòng',
    'hải phòng':'Hải Phòng','tp.hải phòng':'Hải Phòng',
    'tp hải phòng':'Hải Phòng',

    # Ninh Bình (← Hà Nam + Nam Định + Ninh Bình)
    'hà nam':'Ninh Bình','nam định':'Ninh Bình','ninh bình':'Ninh Bình',

    # Quảng Trị (← Quảng Bình + Quảng Trị)
    'quảng bình':'Quảng Trị','quảng trị':'Quảng Trị',

    # Đà Nẵng (← Quảng Nam + Đà Nẵng)
    'quảng nam':'Đà Nẵng','đà nẵng':'Đà Nẵng',
    'da nang':'Đà Nẵng','tp.đà nẵng':'Đà Nẵng',
    'tp đà nẵng':'Đà Nẵng','thành phố đà nẵng':'Đà Nẵng',

    # Quảng Ngãi (← Kon Tum + Quảng Ngãi)
    'kon tum':'Quảng Ngãi','quảng ngãi':'Quảng Ngãi',

    # Gia Lai (← Bình Định + Gia Lai)
    'bình định':'Gia Lai','gia lai':'Gia Lai',

    # Khánh Hòa (← Ninh Thuận + Khánh Hòa)
    'ninh thuận':'Khánh Hòa','khánh hòa':'Khánh Hòa',
    'nha trang':'Khánh Hòa',

    # Lâm Đồng (← Đắk Nông + Bình Thuận + Lâm Đồng)
    'đắk nông':'Lâm Đồng','bình thuận':'Lâm Đồng',
    'lâm đồng':'Lâm Đồng','đà lạt':'Lâm Đồng','phan thiết':'Lâm Đồng',

    # Đắk Lắk (← Phú Yên + Đắk Lắk)
    'phú yên':'Đắk Lắk','đắk lắk':'Đắk Lắk','buôn ma thuột':'Đắk Lắk',

    # TP.HCM (← TP.HCM + Bình Dương + Bà Rịa–Vũng Tàu)
    'hồ chí minh':'TP.HCM','ho chi minh':'TP.HCM',
    'tp.hcm':'TP.HCM','tphcm':'TP.HCM','tp hcm':'TP.HCM',
    'tp. hcm':'TP.HCM','thành phố hồ chí minh':'TP.HCM',
    'hcm':'TP.HCM','sài gòn':'TP.HCM',
    'tp. hồ chí minh':'TP.HCM','tp.hồ chí minh':'TP.HCM','tp hồ chí minh':'TP.HCM',
    'bình dương':'TP.HCM',
    'bà rịa - vũng tàu':'TP.HCM','bà rịa–vũng tàu':'TP.HCM',
    'bà rịa – vũng tàu':'TP.HCM','bà rịa-vũng tàu':'TP.HCM',
    'vũng tàu':'TP.HCM','brvt':'TP.HCM',

    # Đồng Nai (← Đồng Nai + Bình Phước)
    'bình phước':'Đồng Nai','đồng nai':'Đồng Nai','dong nai':'Đồng Nai',

    # Tây Ninh (← Tây Ninh + Long An)
    'long an':'Tây Ninh','tây ninh':'Tây Ninh',

    # Cần Thơ (← Cần Thơ + Sóc Trăng + Hậu Giang)
    'sóc trăng':'Cần Thơ','hậu giang':'Cần Thơ',
    'cần thơ':'Cần Thơ','tp.cần thơ':'Cần Thơ','tp cần thơ':'Cần Thơ',

    # Vĩnh Long (← Bến Tre + Vĩnh Long + Trà Vinh)
    'bến tre':'Vĩnh Long','trà vinh':'Vĩnh Long','vĩnh long':'Vĩnh Long',

    # Đồng Tháp (← Tiền Giang + Đồng Tháp)
    'tiền giang':'Đồng Tháp','đồng tháp':'Đồng Tháp','mỹ tho':'Đồng Tháp',

    # Cà Mau (← Bạc Liêu + Cà Mau)
    'bạc liêu':'Cà Mau','cà mau':'Cà Mau',

    # An Giang (← Kiên Giang + An Giang)
    'kiên giang':'An Giang','an giang':'An Giang','phú quốc':'An Giang','phu quoc':'An Giang',

    # Giữ nguyên 11 tỉnh
    'huế':'Huế','thừa thiên huế':'Huế','tt huế':'Huế','tt-huế':'Huế',
    'lai châu':'Lai Châu','điện biên':'Điện Biên',
    'sơn la':'Sơn La','lạng sơn':'Lạng Sơn',
    'quảng ninh':'Quảng Ninh','hạ long':'Quảng Ninh',
    'thanh hóa':'Thanh Hóa','nghệ an':'Nghệ An',
    'hà tĩnh':'Hà Tĩnh','cao bằng':'Cao Bằng',
}

# ── Hàm chuẩn hóa 1 giá trị ─────────────────────────────────────
def normalize(val: str) -> str:
    # Tin không gắn địa lý cụ thể (chính sách, vĩ mô) → để rỗng, không phân loại tỉnh
    if not val or val.strip() in ('', 'nan', 'None', 'Không rõ',
                                   'Chưa xác định', 'Không áp dụng',
                                   'Không xác định', 'N/A'):
        return ''

    # Tách theo dấu phẩy, lấy từng phần
    parts = [p.strip() for p in val.split(',')]
    for p in parts:
        p_low = p.lower().strip()

        # 1. Lookup trực tiếp
        m = TINH_MAP.get(p_low)
        if m:
            return m

        # 2. Khớp chính xác với TINH_34
        if p in TINH_34:
            return p

        # 3. Fuzzy — tỉnh 34 nằm trong chuỗi hoặc ngược lại
        for t34 in TINH_34:
            if t34.lower() in p_low or p_low in t34.lower():
                return t34

        # 4. Partial match — loại bỏ "TP.", "tỉnh " rồi thử lại
        p_clean = re.sub(r'^(tp\.?|tỉnh|thành phố|tp\. )\s*', '', p_low).strip()
        m2 = TINH_MAP.get(p_clean)
        if m2:
            return m2
        for t34 in TINH_34:
            if t34.lower() in p_clean or p_clean in t34.lower():
                return t34

    return ''  # Không nhận dạng được tỉnh VN → để rỗng


# ── Chạy migration ───────────────────────────────────────────────
TABLE_NAME = 'articles'
TINH_COL   = 'Tỉnh Thành'

def run_migration():
    print(f"Kết nối DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Kiểm tra bảng tồn tại
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Các bảng trong DB: {tables}")

    if TABLE_NAME not in tables:
        print(f"❌ Không tìm thấy bảng '{TABLE_NAME}'! Các bảng hiện có: {tables}")
        conn.close()
        return

    # Kiểm tra cột tồn tại
    cur.execute(f"PRAGMA table_info({TABLE_NAME})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"Các cột trong bảng '{TABLE_NAME}': {cols}")

    tinh_col = TINH_COL
    if tinh_col not in cols:
        print(f"❌ Không tìm thấy cột '{tinh_col}'!")
        print(f"   Hint: Các cột có sẵn: {cols}")
        conn.close()
        return

    print(f"✅ Bảng: '{TABLE_NAME}' | Cột: '{tinh_col}'")

    # Thống kê trước
    cur.execute(f'SELECT COUNT(DISTINCT "{tinh_col}") FROM {TABLE_NAME}')
    before_count = cur.fetchone()[0]
    print(f"\n📊 Trước migration: {before_count} giá trị tỉnh thành khác nhau")

    # Lấy tất cả giá trị unique
    cur.execute(f'SELECT DISTINCT "{tinh_col}" FROM {TABLE_NAME}')
    unique_vals = [r[0] for r in cur.fetchall()]

    # Build mapping bảng cập nhật
    update_map = {}
    unknown = []
    for v in unique_vals:
        normed = normalize(str(v) if v else '')
        update_map[v] = normed
        if normed == 'Không rõ' and v not in ('', None, 'Không rõ',
                                                'Chưa xác định'):
            unknown.append(v)

    # Hiển thị unknown để kiểm tra
    if unknown:
        print(f"\n⚠️  {len(unknown)} giá trị không nhận dạng được (→ 'Không rõ'):")
        for u in sorted(unknown)[:30]:
            print(f"   • {repr(u)}")
        if len(unknown) > 30:
            print(f"   ... và {len(unknown)-30} giá trị khác")

    # Thực hiện UPDATE
    print(f"\n🔄 Đang cập nhật {len(update_map)} giá trị...")
    updated = 0
    skipped = 0
    for old_val, new_val in update_map.items():
        if old_val == new_val:
            continue
        # Cả 2 trường hợp: chuẩn hóa về tỉnh đúng HOẶC về rỗng (tin không có tỉnh cụ thể)
        cur.execute(
            f'UPDATE {TABLE_NAME} SET "{tinh_col}" = ? WHERE "{tinh_col}" = ?',
            (new_val, old_val)
        )
        rows = cur.rowcount
        if new_val == '':
            skipped += rows
            if rows > 0 and old_val not in ('', None):
                print(f"   — '{old_val}' → rỗng (không thuộc 34 tỉnh VN) ({rows} bài)")
        else:
            updated += rows
            if rows > 0:
                print(f"   ✓ '{old_val}' → '{new_val}' ({rows} bài)")

    conn.commit()

    # Thống kê sau
    cur.execute(f'SELECT COUNT(DISTINCT "{tinh_col}") FROM {TABLE_NAME}')
    after_count = cur.fetchone()[0]
    cur.execute(f'SELECT "{tinh_col}", COUNT(*) as cnt FROM {TABLE_NAME} '
                f'GROUP BY "{tinh_col}" ORDER BY cnt DESC LIMIT 20')
    top = cur.fetchall()

    print(f"\n✅ Migration hoàn tất!")
    print(f"   Trước: {before_count} giá trị → Sau: {after_count} giá trị")
    print(f"   Đã chuẩn hóa về tỉnh đúng: {updated} bài viết")
    print(f"   Không có tỉnh cụ thể (chính sách/vĩ mô): {skipped} bài (để rỗng, đúng business logic)")
    print(f"\n📋 Top 20 tỉnh thành sau migration:")
    for t, c in top:
        flag = "✓" if t in TINH_34 else ("—" if t == 'Không rõ' else "?")
        print(f"   {flag} {t}: {c} bài")

    conn.close()


if __name__ == '__main__':
    run_migration()

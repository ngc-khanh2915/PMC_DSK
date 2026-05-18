import pandas as pd
from google import genai
from google.genai import types
import json
import time
import os
import sqlite3
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

API_KEY = os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY chưa được đặt. Thêm vào file .env hoặc biến môi trường.")
client = genai.Client(api_key=API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE  = os.path.join(BASE_DIR, 'bds_news.db')

# ==========================================
# CẤU HÌNH
# ==========================================
CONTENT_LIMIT   = 3000   # ký tự cho Tầng 1 (phân tích đầy đủ)
CONTENT_LITE    = 600    # ký tự cho Tầng 2 (tóm tắt ngắn)
MODEL           = 'gemini-2.5-flash'
SLEEP_NORMAL    = 1.5
SLEEP_RATELIMIT = 20

# ==========================================
# PHÂN TẦNG RULE-BASED — KHÔNG TỐN API
# ==========================================

# TẦNG 3 — Rác tuyệt đối: lọc bỏ TRƯỚC khi gọi API
TIER3_TRASH = [
    # Giải trí/Showbiz
    'xổ số','giải độc đắc','vé số','trúng số','kết quả xổ số',
    'lập kỷ lục xổ số','xổ số miền','xổ số kiến thiết',
    'bóng đá','cầu thủ','hlv ','giải đấu','vô địch','world cup','champions league',
    'showbiz','nghệ sĩ','ca sĩ','diễn viên','hoa hậu','người mẫu',
    'tử vi','phong thủy','bói toán','cung hoàng đạo',
    # Tiền số/Crypto — không liên quan dịch vụ BĐS
    'bitcoin','crypto','tiền số','tiền ảo','coin ','token ',
    'thị trường tiền số','kho chứa bitcoin','ngủ quên bitcoin',
    'ethereum','blockchain coin','defi ','nft ',
    # Video/Clip không liên quan
    'video:','clip:','quả trứng gà','biến thành đặc sản',
    'đặc sản vùng miền','ẩm thực địa phương',
    # Mẹo vặt/Trang trí cá nhân
    'thiết kế ánh sáng','mẹo trang trí','nội thất phòng khách',
    'decor phòng','sơn nhà','chọn màu sơn','gạch ốp lát phòng',
    'cách làm','công thức nấu','món ăn ngon','nhà hàng review','quán ăn ngon',
    'làm đẹp','skincare','mỹ phẩm','thời trang','outfit',
    # Chuyện lạ/Cảm xúc
    'chuyện lạ','kỳ lạ','bí ẩn','tâm sự','trái tim nhân ái',
    'câu chuyện cảm động','nhật ký phóng viên',
]

# TẦNG 2 — Gián tiếp/Cảnh báo: tóm tắt ngắn, không D-S-K đầy đủ
TIER2_INDIRECT = [
    # Năng lượng/Nhiên liệu (ảnh hưởng vận hành tòa nhà)
    'giá xăng','xăng dầu','nhiên liệu','giá điện','tiết kiệm điện',
    'cây xăng','găm hàng xăng','thiếu xăng',
    # Vật liệu xây dựng
    'vật liệu xây dựng','giá thép','giá xi măng','giá cát','giá gạch',
    'đầu cơ vật liệu','thao túng vật liệu',
    # Thực phẩm/F&B (ảnh hưởng suất ăn)
    'giá thịt','giá heo','giá gạo','giá rau','giá thực phẩm',
    'f&b tăng giá','hàng quán tăng giá','giá nguyên liệu f&b',
    # Giao thông đô thị (gián tiếp hạ tầng)
    'ùn tắc giao thông','kẹt xe','xe điện','trạm sạc','metro vận hành',
    'xe buýt điện','giao thông xanh',
    # Y tế/Dịch bệnh (ảnh hưởng vận hành tòa nhà)
    'cúm a','dịch bệnh','bùng phát dịch','virus','lây nhiễm',
    'y tế cộng đồng','sức khỏe cộng đồng',
    # Môi trường/ESG
    'biến đổi khí hậu','ngập lụt','ô nhiễm không khí','net zero',
    'phát thải carbon','năng lượng tái tạo','điện mặt trời',
    # Công nghệ gián tiếp
    'chuyển đổi số','trí tuệ nhân tạo','iot','smart city',
    'proptech','fintech','blockchain',
    # Lao động/Nhân sự
    'tiền lương tối thiểu','bảo hiểm xã hội','tuyển dụng lao động',
    'thị trường lao động','việc làm',
    # Tài chính vĩ mô gián tiếp
    'lãi suất fed','fed tăng lãi','kinh tế mỹ','kinh tế toàn cầu',
    'chuỗi cung ứng','logistics quốc tế','địa chính trị',
    # An toàn/Rủi ro vận hành (quan trọng nhưng không phải BĐS)
    'trơn trượt','an toàn lao động','tai nạn lao động',
    'cháy nổ nhà máy','sập công trình',
    # Du lịch/Hàng không — gián tiếp, không phải BĐS trực tiếp
    'du lịch sinh thái','khảo sát du lịch','điểm du lịch',
    'hàng không tăng chuyến','tăng chuyến bay','vé máy bay',
    'du lịch lễ','mùa du lịch','khách du lịch','lượng khách',
    'giá vé máy bay','hãng hàng không','vietnam airlines',
    'giá nông sản','thị trường nông sản',
    # Thủy sản/Nông nghiệp — gián tiếp
    'ngành thủy sản','xuất khẩu thủy sản','nuôi trồng thủy sản',
    'ứng dụng ai thủy sản','công nghệ nông nghiệp',
    # An toàn thực phẩm — gián tiếp (cảnh báo vận hành)
    'an toàn thực phẩm','thực phẩm bẩn','ngộ độc thực phẩm',
    'vụ heo bệnh','thịt heo bệnh','suất ăn trường học',
    'dịch vụ suất ăn công nghiệp','ô nhiễm thực phẩm',
    # Giá gas/nhiên liệu sinh hoạt — gián tiếp
    'giá gas','giá khí gas','bình gas tăng','gas điều chỉnh',
    # Chứng khoán (gián tiếp)
    'vnindex','chứng khoán','cổ phiếu','vn-index',
    # Thời tiết — gián tiếp, ảnh hưởng vận hành tòa nhà
    'nắng nóng','nắng gay gắt','nhiệt độ tăng','폭염',
    'mưa bão','bão số','lũ lụt','ngập úng','triều cường',
    'thời tiết','dự báo thời tiết','khí hậu tháng',
    # Chính sách nước ngoài không liên quan VN
    'czech ','đức đề xuất','eu quy định','mỹ ban hành',
    'nhật bản chính sách','hàn quốc luật','trung quốc ban hành',
    # Vi phạm đô thị/giao thông
    'bãi xe trái phép','lấn chiếm vỉa hè','vi phạm lòng đường',
    'tắc nghẽn giao thông','ùn tắc kéo dài',
]

# TẦNG 1 — Trực tiếp HOT: phân tích đầy đủ D-S-K
TIER1_DIRECT = [
    # BĐS dự án cụ thể
    'bất động sản','nhà đất','đất nền','căn hộ','chung cư',
    'khu đô thị','khu công nghiệp','kcn ','văn phòng cho thuê',
    'mặt bằng thương mại','tòa nhà','cao ốc','shophouse',
    'villa','biệt thự','penthouse','condotel','officetel',
    # Sự kiện dự án
    'mở bán','động thổ','cất nóc','khánh thành','bàn giao',
    'khởi công','nghiệm thu','tái định cư','giải phóng mặt bằng',
    # Pháp lý BĐS
    'sổ đỏ','sổ hồng','pháp lý dự án','luật đất đai','luật nhà ở',
    'luật kinh doanh bđs','nghị định bđs','thông tư bđs',
    'sang tên','chuyển nhượng quyền sử dụng đất',
    # Vận hành tòa nhà (core PMC)
    'quản lý vận hành','ban quản trị','phí dịch vụ','phí bảo trì',
    'hội nghị nhà chung cư','pccc','phòng cháy chữa cháy',
    'thang máy','hệ thống kỹ thuật tòa nhà','facility management',
    'quản lý chung cư','tranh chấp chung cư','ban quản lý',
    # Quy hoạch & Hạ tầng chiến lược
    'quy hoạch đô thị','quy hoạch vùng','quy hoạch tỉnh',
    'hạ tầng giao thông','metro','cao tốc','vành đai',
    'sân bay','cảng biển','khu kinh tế','khu chế xuất',
    # Tài chính BĐS trực tiếp
    'tín dụng bđs','vay mua nhà','lãi suất mua nhà',
    'trái phiếu bđs','m&a bđs','fdi bđs','quỹ đầu tư bđs',
    'giá nhà','thị trường bđs','nguồn cung nhà ở',
    # CĐT lớn (tên riêng)
    'vinhomes','masterise','sun group','him lam','novaland',
    'becamex','hud ','vinaconex','coteccons','hòa bình',
    'capitaland','lotte','gelex','bw industrial','kim oanh',
    'an gia','nam long','khang điền','phát đạt','đất xanh',
    # Chính sách trực tiếp
    'nhà ở xã hội','noxh','nhà ở công nhân','cải tạo chung cư cũ',
    'đấu thầu bđs','đấu giá đất','bảng giá đất',
    'phân quyền quản lý chung cư','giám sát vận hành chung cư',
    # Rủi ro pháp lý BĐS
    'bắt giam chủ đầu tư','khởi tố bđs','lừa đảo bđs',
    'dự án treo','dự án chậm tiến độ','vi phạm môi trường khách sạn',
]

# TIÊU CHÍ HOT — chỉ áp dụng cho Tầng 1 (BĐS trực tiếp)
# HOT = có dự án/CĐT cụ thể + số liệu lớn HOẶC chính sách có hiệu lực
# KHÔNG HOT: nhận định xu hướng chung, số liệu thị trường tổng hợp,
#            tin du lịch/hàng không, tin tài chính không có dự án BĐS cụ thể
HOT_SIGNALS = [
    # Số liệu tài chính lớn và cụ thể
    'tỷ đô','triệu đô','nghìn tỷ','trăm tỷ','tỷ usd','tỷ đồng đầu tư',
    '1.000 căn','10.000 căn','100.000 căn','181.000 căn',
    'ha đất','m² sàn','m2 sàn','triệu m²',
    # Sự kiện pháp lý/hành chính quan trọng với dự án BĐS
    'bắt giam','khởi tố bđs','thanh tra dự án',
    'thu hồi dự án','hủy giấy phép','thu hồi đất',
    # Chính sách BĐS có hiệu lực cụ thể
    'có hiệu lực từ ngày','ban hành nghị định','quốc hội thông qua luật',
    'chính phủ phê duyệt quy hoạch','thủ tướng phê duyệt dự án',
    'ubnd phê duyệt','phê duyệt chủ trương đầu tư',
    # Dự án/CĐT siêu lớn cụ thể
    'lotte eco smart city','vinhomes grand','bw industrial','kim oanh',
    'khu đô thị đại học quốc gia','sân bay long thành',
    'metro thủ thiêm','vành đai 4','cao tốc bắc nam',
    # Biến động thị trường BĐS có số liệu rõ ràng
    'lập mặt bằng giá mới','tăng 30%','tăng 40%','tăng 50%',
    'kỷ lục giá bđs','cao nhất lịch sử bđs',
]

# Tín hiệu KHÔNG phải HOT dù có số lớn
NOT_HOT_PATTERNS = [
    'doanh thu kinh doanh bđs','tổng doanh thu thị trường',
    'chỉ số thị trường','tăng trưởng gdp','kim ngạch xuất khẩu',
    'thị trường chứng khoán','vnindex lấy lại','vn-index tăng',
    'hàng không tăng chuyến','tăng chuyến bay','giá vé máy bay',
    'du lịch tăng','lượng khách tăng','doanh thu du lịch',
]


def classify_tier(title: str, content: str) -> int:
    """
    Phân loại tầng xử lý bằng rule-based TRƯỚC khi gọi API.
    Trả về: 1=Phân tích đầy đủ | 2=Tóm tắt ngắn | 3=Rác bỏ qua
    """
    text = (title + ' ' + content[:300]).lower()

    # Tầng 3 trước — rác tuyệt đối
    if any(kw in text for kw in TIER3_TRASH):
        return 3

    # Tầng 1 — BĐS trực tiếp
    if any(kw in text for kw in TIER1_DIRECT):
        return 1

    # Tầng 2 — Gián tiếp
    if any(kw in text for kw in TIER2_INDIRECT):
        return 2

    # Mặc định Tầng 2 (tóm tắt ngắn, không bỏ qua)
    return 2


def is_hot(title: str, content: str) -> bool:
    """
    Xác định tin HOT: có số liệu lớn cụ thể / chính sách có hiệu lực / dự án BĐS trọng điểm.
    KHÔNG HOT: nhận định xu hướng, số liệu thị trường tổng hợp, tin du lịch/hàng không.
    """
    text = (title + ' ' + content[:500]).lower()
    # Kiểm tra NOT_HOT trước
    if any(pat in text for pat in NOT_HOT_PATTERNS):
        return False
    return any(sig in text for sig in HOT_SIGNALS)


def smart_truncate(content: str, limit: int) -> str:
    if len(content) <= limit:
        return content
    truncated = content[:limit]
    last_period = max(truncated.rfind('。'), truncated.rfind('. '), truncated.rfind('.\n'))
    if last_period > limit * 0.7:
        return truncated[:last_period + 1]
    return truncated


def parse_json_safe(raw: str) -> dict:
    raw = raw.strip()
    if '```' in raw:
        raw = raw.replace('```json', '').replace('```', '')
    start = raw.find('{')
    end   = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end+1]
    return json.loads(raw)


def build_prompt_full(title: str, content: str) -> str:
    """
    TẦNG 1 — Phân tích đầy đủ D-S-K cho tin BĐS Trực tiếp.
    Áp dụng phương pháp luận PMC Intelligence hoàn chỉnh.
    """
    return f"""Bạn là Giám đốc Chiến lược của PMC (Property Management Company Việt Nam).
Phân tích bài báo BĐS theo phương pháp luận D-S-K. TRẢ VỀ JSON THUẦN TÚY.

╔══════════════════════════════════════════════════════════╗
║  BƯỚC 1: PHÂN LOẠI TIN                                  ║
╚══════════════════════════════════════════════════════════╝

Tin_Rac = "Có" CHỈ KHI: xổ số, showbiz, mẹo vặt trang trí cá nhân,
  thiết kế ánh sáng phòng ở, giải trí thuần túy không có số liệu kinh tế.

TUYỆT ĐỐI KHÔNG đánh rác nếu có: tên dự án BĐS, tên CĐT, số tiền đầu tư,
  diện tích, số căn, quy hoạch, pháp lý BĐS, vận hành tòa nhà, PCCC,
  sổ đỏ/hồng, KCN, khách sạn/resort vi phạm, trái phiếu BĐS.

⚠ Đọc TOÀN BỘ NỘI DUNG — không phán xét từ tiêu đề.

╔══════════════════════════════════════════════════════════╗
║  BƯỚC 2: PHÂN NHÓM                                      ║
╚══════════════════════════════════════════════════════════╝

Nhom_Tin:
• "Nhóm 1 - Trực tiếp": BĐS dự án cụ thể, Quy hoạch hạ tầng, Vận hành tòa nhà,
  Pháp lý BĐS, Nhà ở xã hội, KCN, CĐT, Tài chính BĐS trực tiếp
• "Nhóm 2 - Gián tiếp": Chính sách chung (không phải BĐS), Tài chính vĩ mô VN,
  Công nghệ ứng dụng, Lao động, Y tế cộng đồng, An toàn thực phẩm,
  Du lịch & hàng không, Giá nhiên liệu/gas sinh hoạt, Thủy sản/Nông nghiệp
• "Nhóm 3 - Cảnh báo sớm": Kinh tế quốc tế, Fed, Địa chính trị THUẦN TÚY,
  ESG, Chuỗi cung ứng toàn cầu

⚠ QUAN TRỌNG — PHÂN NHÓM ĐÚNG:
- Tin về hàng không, du lịch lễ hội → Nhóm 2 (KHÔNG phải Địa chính trị N3)
- Tin về an toàn thực phẩm, suất ăn công nghiệp → Nhóm 2 (KHÔNG phải Dịch vụ BĐS N1)
- Tin về giá gas/xăng dầu/nhiên liệu sinh hoạt → Nhóm 2 (KHÔNG phải Dịch vụ BĐS N1)
- Tin về AI/công nghệ trong thủy sản, nông nghiệp → Nhóm 2 (KHÔNG phải N1)
- Tin về xung đột Trung Đông ảnh hưởng giá nhiên liệu → Nhóm 3 (có yếu tố địa chính trị)
- Tin chính sách nước ngoài (Czech, Mỹ, EU, Nhật...) không có yếu tố VN → Nhóm 3
- Tin thời tiết (nắng nóng, mưa bão, lũ lụt) → Nhóm 2 / Rủi ro vận hành tòa nhà
- Tin vi phạm đô thị/giao thông (bãi xe trái phép, lấn chiếm vỉa hè) → Nhóm 2
- Tin nhân sự nội bộ nhà nước (không liên quan BĐS) → Nhóm 2 / Chính sách & Pháp lý
• "Nhóm 3 - Cảnh báo sớm": Kinh tế quốc tế, Fed, Địa chính trị,
  ESG, Chuỗi cung ứng toàn cầu

Nhom_Su_Kien (chọn 1):
Thị trường BĐS | Quy hoạch & Hạ tầng | Dịch vụ BĐS |
Chính sách & Pháp lý | Tài chính & Tín dụng |
Kinh tế Vĩ mô | Công nghệ & ESG | Địa chính trị

╔══════════════════════════════════════════════════════════╗
║  BƯỚC 3: ĐIỀN SỐ LIỆU                                   ║
╚══════════════════════════════════════════════════════════╝

Diem_Suc_khoe: Chỉ điền nếu có CĐT/dự án cụ thể
  +7 đến +10: Tích cực mạnh (mở bán thành công, pháp lý sạch, đầu tư lớn)
  +4 đến +6:  Tích cực vừa (tiến triển tốt, khánh thành, bàn giao đúng hạn)
  +1 đến +3:  Tích cực nhẹ (tin khởi động, kế hoạch)
  0:          Trung lập hoặc tin vĩ mô không có dự án cụ thể
  -1 đến -3:  Rủi ro nhẹ (chậm tiến độ, tranh chấp nhỏ)
  -4 đến -6:  Rủi ro vừa (vi phạm, bị phạt, tranh chấp lớn)
  -7 đến -10: Rủi ro nghiêm trọng (bắt giam CĐT, thu hồi dự án, lừa đảo)

Loai_hinh_BDS: Chọn ĐÚNG 1 loại hình duy nhất dựa trên ngữ cảnh chính của bài
(KHÔNG ghép nhiều loại, KHÔNG dùng dấu phẩy):
• "Khu phức hợp": Dự án tích hợp nhiều chức năng (nhà ở + TM + VP + tiện ích)
• "Chung cư": Căn hộ chung cư thông thường, cao cấp, trung cấp, bình dân
• "Nhà ở Xã hội": Nhà ở xã hội, nhà ở công nhân, nhà ở giá thấp cho người thu nhập thấp
• "Văn phòng / Thương mại": Tòa nhà văn phòng, TTTM, mặt bằng bán lẻ, shophouse
• "BĐS Công nghiệp / KCN": Khu công nghiệp, nhà xưởng, kho logistics, IDC, data center
• "Nghỉ dưỡng": Resort, khách sạn, condotel, villa nghỉ dưỡng, bất động sản du lịch
• "Công trình công cộng": Trường học, bệnh viện, khu vui chơi, công trình hạ tầng xã hội
• "BĐS Khác": Đất nền, nhà phố, biệt thự đơn lẻ không thuộc các loại trên
• "Không áp dụng": Tin vĩ mô, chính sách chung, không có dự án BĐS cụ thể

⚠ VÍ DỤ ĐÚNG:
- "Dự án The Infinity gồm chung cư + TTTM + VP" → Khu phức hợp
- "Bàn giao 500 căn hộ The Sun" → Chung cư
- "KCN Thăng Long mở rộng thu hút FDI" → BĐS Công nghiệp / KCN
- "Resort 5 sao Phú Quốc khai trương" → Nghỉ dưỡng
- "Chính sách lãi suất Fed" → Không áp dụng
- "Nhà ở xã hội 2.000 tỷ Ninh Bình" → Nhà ở Xã hội (KHÔNG phải Chung cư)

Vong_doi: Chọn ĐÚNG 1 giai đoạn duy nhất dựa trên ngữ cảnh bài viết
  (KHÔNG ghép nhiều giai đoạn, KHÔNG dựa vào từ khóa lặp lại):
• "Chuẩn bị đầu tư": Dự án đang lên kế hoạch, phê duyệt, khảo sát, chưa khởi công
• "Xây dựng": Đang thi công, khởi công, cất nóc
• "Nghiệm thu & Bàn giao": Hoàn thành xây dựng, đang bàn giao, nghiệm thu
• "Vận hành": Đã đưa vào sử dụng, đang hoạt động, quản lý vận hành
• "Mở bán": Đang mở bán, chào bán, ra mắt sản phẩm
• "Không áp dụng": Tin vĩ mô, chính sách chung, không có dự án cụ thể

⚠ VÍ DỤ ĐÚNG:
- "dự án đang thi công nước rút" → Xây dựng (KHÔNG phải "Chuẩn bị đầu tư, Xây dựng")
- "bàn giao 500 căn hộ" → Nghiệm thu & Bàn giao
- "tin về chính sách lãi suất" → Không áp dụng

╔══════════════════════════════════════════════════════════╗
║  OUTPUT JSON                                             ║
╚══════════════════════════════════════════════════════════╝

{{
    "Tin_Rac": "Có/Không",
    "Nhom_Tin": "Nhóm 1/2/3",
    "Tom_tat": "1-2 câu súc tích, nêu số liệu chính (tiền, diện tích, căn hộ...)",
    "Nhom_Su_Kien": "Chọn 1 trong 8 nhóm",
    "Loai_hinh_BDS": "Chọn đúng hoặc Không áp dụng",
    "Vong_doi": "Chọn đúng hoặc Không áp dụng",
    "Tinh_Thanh": "Tỉnh/TP cụ thể | Toàn quốc | Quốc tế",
    "Dien_tich": 0,
    "Tong_von": 0,
    "So_luong_SP": 0,
    "Cac_Dich_vu_PMC": "Dịch vụ liên quan, cách nhau dấu phẩy. Chọn từ: Quản lý vận hành, Bảo trì, Tư vấn giám sát, An ninh, Vệ sinh, Cảnh quan, Quản lý rác thải, Môi giới, Mua sắm, Suất ăn",
    "Diem_Suc_khoe": 0,
    "DATA": {{
        "Du_an": "Tên dự án cụ thể hoặc Không áp dụng",
        "Chu_dau_tu": "Tên CĐT/tổ chức hoặc Không áp dụng",
        "Khu_vuc": "Địa chỉ chi tiết nhất có thể",
        "Quy_mo_Phap_ly": "Số liệu quy mô + tình trạng pháp lý",
        "Moc_thoi_gian": "Các mốc thời gian quan trọng trong bài"
    }},
    "STRATEGY": {{
        "Context_5W1H": "What: [...] | Who: [...] | Where: [...] | When: [...] | Why: [...] | How: [...]",
        "State_Change": "Từ trạng thái [A] → [B]. Tác động cụ thể đến PMC và thị trường BĐS?"
    }},
    "KNOWLEDGE": {{
        "Stakeholders": "(1) PMC/Chuỗi DV BĐS — Lợi ích: [...] Rủi ro: [...]\\n(2) Chủ đầu tư — Lợi ích: [...] Rủi ro: [...]\\n(3) Nhà thầu/Ngân hàng — Lợi ích: [...] Rủi ro: [...]\\n(4) Nhà nước — Lợi ích: [...] Rủi ro: [...]\\n(5) Cư dân/Người dùng cuối — Lợi ích: [...] Rủi ro: [...]",
        "Du_bao": "Dự báo tác động 3-6 tháng tới BĐS và hoạt động PMC. Nêu con số cụ thể nếu có."
    }},
    "ACTION_TEXT": "- BD: [hành động cụ thể]\\n- R&D: [hành động cụ thể]\\n- Legal: [hành động cụ thể]\\n- Finance: [hành động cụ thể]\\n- Marketing: [hành động cụ thể]",
    "ACTION_KANBAN": {{
        "BD": "Hành động ngắn nhất | High/Medium/Low",
        "RnD": "Hành động ngắn nhất | High/Medium/Low",
        "Legal": "Hành động ngắn nhất | High/Medium/Low",
        "Finance": "Hành động ngắn nhất | High/Medium/Low",
        "Marketing": "Hành động ngắn nhất | High/Medium/Low"
    }}
}}
Tiêu đề: {title}
Nội dung: {content}"""


def build_prompt_lite(title: str, content: str) -> str:
    """
    TẦNG 2 — Tóm tắt ngắn cho tin Gián tiếp/Cảnh báo sớm.
    Chỉ ghi nhận, không phân tích sâu. Tiết kiệm ~70% token.
    """
    return f"""Bạn là chuyên gia phân tích PMC. Đây là tin kinh tế-xã hội gián tiếp.
CHỈ tóm tắt ngắn và gắn nhãn — KHÔNG phân tích D-S-K đầy đủ. TRẢ VỀ JSON THUẦN TÚY.

Tin_Rac = "Có" CHỈ KHI: xổ số, showbiz, mẹo trang trí cá nhân, thiết kế ánh sáng,
  giải trí không liên quan kinh tế. Các tin kinh tế-xã hội dù nhỏ vẫn là "Không".

Rui_ro_Van_hanh: Nếu tin liên quan đến rủi ro vật lý/vận hành tòa nhà PMC,
ghi ngắn gọn. Ví dụ:
- "Xăng tăng → chi phí máy phát điện tòa nhà tăng"
- "Cúm A bùng phát → cần tăng cường vệ sinh, kiểm soát ra vào tòa nhà"
- "Đá granite trơn ướt → kiểm tra xử lý chống trơn sàn tòa nhà"
- "Vật liệu XD tăng → ảnh hưởng chi phí bảo trì, sửa chữa"

Nhom_Su_Kien (chọn 1):
Thị trường BĐS | Quy hoạch & Hạ tầng | Dịch vụ BĐS |
Chính sách & Pháp lý | Tài chính & Tín dụng |
Kinh tế Vĩ mô | Công nghệ & ESG | Địa chính trị

{{
    "Tin_Rac": "Có/Không",
    "Nhom_Tin": "Nhóm 2 - Gián tiếp / Nhóm 3 - Cảnh báo sớm",
    "Tom_tat": "1 câu ngắn gọn, nêu số liệu nếu có",
    "Nhom_Su_Kien": "Chọn 1 trong 8 nhóm",
    "Loai_hinh_BDS": "Không áp dụng",
    "Vong_doi": "Không áp dụng",
    "Tinh_Thanh": "Tỉnh/TP | Toàn quốc | Quốc tế",
    "Dien_tich": 0,
    "Tong_von": 0,
    "So_luong_SP": 0,
    "Cac_Dich_vu_PMC": "",
    "Diem_Suc_khoe": 0,
    "DATA": {{
        "Du_an": "Không áp dụng",
        "Chu_dau_tu": "Không áp dụng",
        "Khu_vuc": "",
        "Quy_mo_Phap_ly": "",
        "Moc_thoi_gian": ""
    }},
    "STRATEGY": {{"Context_5W1H": "", "State_Change": ""}},
    "KNOWLEDGE": {{
        "Stakeholders": "",
        "Du_bao": "1 câu tác động ngắn gọn đến PMC nếu có, để trống nếu không"
    }},
    "ACTION_TEXT": "",
    "ACTION_KANBAN": {{"BD": "", "RnD": "", "Legal": "", "Finance": "", "Marketing": ""}},
    "Rui_ro_Van_hanh": "Mô tả ngắn rủi ro vận hành tòa nhà nếu có. Để trống nếu không liên quan."
}}
Tiêu đề: {title}
Nội dung: {content}"""


def save_result(cursor, data: dict, link: str, hot: bool = False):
    action_kb = data.get('ACTION_KANBAN', {})
    d_data    = data.get('DATA', {})
    s_data    = data.get('STRATEGY', {})
    k_data    = data.get('KNOWLEDGE', {})

    # Gắn rủi ro vận hành vào Dự báo
    du_bao = k_data.get('Du_bao', '')
    rui_ro = data.get('Rui_ro_Van_hanh', '')
    if rui_ro and rui_ro.strip():
        du_bao = f"⚠ Rủi ro vận hành: {rui_ro}\n\n{du_bao}".strip()

    # Gắn nhãn HOT vào Tóm tắt
    tom_tat = data.get('Tom_tat', '')
    if hot and data.get('Tin_Rac') != 'Có':
        tom_tat = f"🔥 {tom_tat}"

    sql = '''UPDATE articles
             SET "Tin_Rac"=?, "Tóm tắt"=?, "Nhóm Sự kiện"=?, "Loại hình BĐS"=?,
                 "Vòng đời"=?, "Tỉnh Thành"=?, "Diện tích"=?, "Tổng vốn"=?,
                 "Số lượng SP"=?, "Các Dịch vụ PMC"=?, "Điểm Sức khỏe"=?,
                 "Khu vực"=?, "Dự án"=?, "Chủ đầu tư"=?, "Quy mô & Pháp lý"=?,
                 "Mốc thời gian"=?, "Thông tin Chiến lược"=?, "Phân tích Stakeholders"=?,
                 "Dự báo"=?, "Đề xuất Hành động"=?,
                 "Action_BD"=?, "Action_RnD"=?, "Action_Legal"=?,
                 "Action_Finance"=?, "Action_Marketing"=?
             WHERE "Link"=?'''
    cursor.execute(sql, (
        data.get('Tin_Rac', 'Không'),
        tom_tat,
        data.get('Nhom_Su_Kien', ''),
        data.get('Loai_hinh_BDS', 'Không áp dụng'),
        data.get('Vong_doi', 'Không áp dụng'),
        data.get('Tinh_Thanh', 'Không rõ'),
        str(data.get('Dien_tich', 0)),
        str(data.get('Tong_von', 0)),
        str(data.get('So_luong_SP', 0)),
        str(data.get('Cac_Dich_vu_PMC', '')),
        str(data.get('Diem_Suc_khoe', 0)),
        d_data.get('Khu_vuc', ''),
        d_data.get('Du_an', ''),
        d_data.get('Chu_dau_tu', ''),
        d_data.get('Quy_mo_Phap_ly', ''),
        d_data.get('Moc_thoi_gian', ''),
        f"**Bối cảnh:**\n{s_data.get('Context_5W1H', '')}\n\n**Chuyển đổi:**\n{s_data.get('State_Change', '')}",
        k_data.get('Stakeholders', ''),
        du_bao,
        data.get('ACTION_TEXT', ''),
        action_kb.get('BD', ''),
        action_kb.get('RnD', ''),
        action_kb.get('Legal', ''),
        action_kb.get('Finance', ''),
        action_kb.get('Marketing', ''),
        link
    ))


def analyze_news(limit: int = 0):
    if not os.path.exists(DB_FILE):
        return print("Chưa có Database!")

    conn   = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Schema
    new_cols = [
        'Tin_Rac', 'Tóm tắt', 'Nhóm Sự kiện', 'Loại hình BĐS', 'Vòng đời', 'Tỉnh Thành',
        'Diện tích', 'Tổng vốn', 'Số lượng SP', 'Các Dịch vụ PMC', 'Điểm Sức khỏe',
        'Khu vực', 'Dự án', 'Chủ đầu tư', 'Quy mô & Pháp lý', 'Mốc thời gian',
        'Thông tin Chiến lược', 'Phân tích Stakeholders', 'Dự báo', 'Đề xuất Hành động',
        'Action_BD', 'Action_RnD', 'Action_Legal', 'Action_Finance', 'Action_Marketing'
    ]
    cursor.execute("PRAGMA table_info(articles)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    for col in new_cols:
        if col not in existing_cols:
            try: cursor.execute(f'ALTER TABLE articles ADD COLUMN "{col}" TEXT')
            except: pass
    conn.commit()

    # Lấy tin chưa analyze
    df_all = pd.read_sql("SELECT * FROM articles", conn)
    mask = (
        df_all['Tóm tắt'].isna() |
        (df_all['Tóm tắt'].astype(str).str.strip() == '') |
        (df_all['Tóm tắt'].astype(str).str.lower().isin(['nan', 'none']))
    )
    df = df_all[mask].copy()
    if 'Thời gian cào' in df.columns:
        df = df.sort_values('Thời gian cào', ascending=False)

    total    = len(df)
    total_db = len(df_all)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PMC Intelligence Analyzer")
    print(f"DB: {total_db} bài | Chưa analyze: {total} | Đã analyze: {total_db-total}")

    if total == 0:
        print("[XONG] Tất cả đã analyze!")
        conn.close()
        return

    # Phân tầng rule-based (0 API call)
    tiers = {1: [], 2: [], 3: []}
    hot_set = set()
    for _, row in df.iterrows():
        t_str = str(row['Tiêu đề'])
        c_str = str(row['Nội dung'])
        t = classify_tier(t_str, c_str)
        tiers[t].append(row)
        if t == 1 and is_hot(t_str, c_str):
            hot_set.add(str(row['Link']))

    n1, n2, n3 = len(tiers[1]), len(tiers[2]), len(tiers[3])
    print(f"Phân tầng: T1(Full)×{n1} | T2(Lite)×{n2} | T3(Skip)×{n3} | HOT×{len(hot_set)}")

    # Ước tính token
    t1c = sum(min(len(str(r['Nội dung'])), CONTENT_LIMIT) for r in tiers[1])
    t2c = sum(min(len(str(r['Nội dung'])), CONTENT_LITE)  for r in tiers[2])
    print(f"Token: T1≈{t1c:,} | T2≈{t2c:,} | T3=0 (tiết kiệm ~{100*n3//max(total,1)}% từ skip)")
    print(f"Model: {MODEL}\n")

    # Tầng 3 — đánh rác không gọi API
    for row in tiers[3]:
        cursor.execute(
            'UPDATE articles SET "Tin_Rac"=?, "Tóm tắt"=? WHERE "Link"=?',
            ('Có', 'Tin rác — tự động phân loại', str(row['Link']))
        )
    conn.commit()
    if n3 > 0:
        print(f"[T3] Đánh rác {n3} tin (0 API call)\n")

    # Tầng 1 trước (HOT ưu tiên), rồi Tầng 2
    hot_rows    = [r for r in tiers[1] if str(r['Link']) in hot_set]
    normal_rows = [r for r in tiers[1] if str(r['Link']) not in hot_set]
    queue = (
        [(1, True, r) for r in hot_rows] +
        [(1, False, r) for r in normal_rows] +
        [(2, False, r) for r in tiers[2]]
    )
    if limit > 0:
        queue = queue[:limit]
        print(f"[LIMIT] Giới hạn {limit} bài/lần chạy\n")

    count = n_rac = n_hot_done = n1_done = n2_done = 0

    for tier, hot, row in queue:
        title   = str(row['Tiêu đề'])
        content = str(row['Nội dung'])
        link    = str(row['Link'])

        if len(content) < 100:
            continue

        if tier == 1:
            content_cut = smart_truncate(content, CONTENT_LIMIT)
            prompt      = build_prompt_full(title, content_cut)
            tag         = '🔥T1' if hot else 'T1'
        else:
            content_cut = smart_truncate(content, CONTENT_LITE)
            prompt      = build_prompt_lite(title, content_cut)
            tag         = 'T2'

        count += 1
        print(f"[{count}/{len(queue)}][{tag}] {title[:58]}...")

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                data = parse_json_safe(response.text)
                save_result(cursor, data, link, hot=hot)
                conn.commit()

                # Track token usage
                try:
                    _um = getattr(response, 'usage_metadata', None)
                    _tk = int(getattr(_um, 'total_token_count', 0) or 0) if _um else 0
                    if _tk > 0:
                        _uf  = os.path.join(BASE_DIR, 'api_usage.json')
                        _td  = datetime.now().strftime('%Y-%m-%d')
                        _u   = {'today_date': _td, 'today_tokens': 0,
                                'today_requests': 0, 'total_tokens': 0,
                                'total_requests': 0, 'history': []}
                        if os.path.exists(_uf):
                            try:
                                import json as _json
                                with open(_uf, 'r', encoding='utf-8') as _f:
                                    _loaded = _json.load(_f)
                                if _loaded.get('today_date') != _td:
                                    _h = _loaded.get('history', [])
                                    _h.append({'date': _loaded['today_date'],
                                               'tokens': _loaded.get('today_tokens', 0),
                                               'requests': _loaded.get('today_requests', 0)})
                                    _loaded.update({'today_date': _td, 'today_tokens': 0,
                                                    'today_requests': 0, 'history': _h[-30:]})
                                _u.update(_loaded)
                            except Exception:
                                pass
                        _u['today_tokens']   += _tk
                        _u['today_requests'] += 1
                        _u['total_tokens']   += _tk
                        _u['total_requests'] += 1
                        import json as _json
                        with open(_uf, 'w', encoding='utf-8') as _f:
                            _json.dump(_u, _f, indent=2)
                except Exception:
                    pass

                rac  = data.get('Tin_Rac', 'Không')
                nhom = data.get('Nhom_Tin', '')
                sk   = data.get('Nhom_Su_Kien', '?')
                sc   = data.get('Diem_Suc_khoe', 0)

                if rac == 'Có':
                    n_rac += 1
                    print(f"  🗑 TIN RÁC")
                else:
                    n_tag = '[N1]' if '1' in nhom else '[N2]' if '2' in nhom else '[N3]'
                    hot_mark = ' ⭐HOT' if hot else ''
                    sc_str = f" SK:{sc:+d}" if sc != 0 else ''
                    print(f"  ✓ {n_tag} {sk}{sc_str}{hot_mark}")
                    if tier == 1: n1_done += 1
                    else: n2_done += 1
                    if hot: n_hot_done += 1

                time.sleep(SLEEP_NORMAL)
                break

            except Exception as e:
                err = str(e)
                if "429" in err or "Quota" in err or "RESOURCE_EXHAUSTED" in err:
                    wait = SLEEP_RATELIMIT * (attempt + 1)
                    print(f"  ⚠ Rate limit — chờ {wait}s...")
                    time.sleep(wait)
                elif attempt == 2:
                    print(f"  ✗ Bỏ qua: {err[:80]}")
                    break
                else:
                    print(f"  ↻ Thử lại {attempt+1}...")
                    time.sleep(3)

    # Dọn rác
    deleted = cursor.execute("DELETE FROM articles WHERE Tin_Rac = 'Có'").rowcount
    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"[HOÀN TẤT] Đã xử lý: {count} bài (T3 skip: {n3})")
    print(f"Kết quả: N1×{n1_done} | N2×{n2_done} | HOT×{n_hot_done} | Rác×{n_rac}")
    print(f"Đã xóa khỏi DB: {deleted} tin rác")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    _ap = argparse.ArgumentParser()
    _ap.add_argument('--limit', type=int, default=0, help='Max articles per run (0=unlimited)')
    _args = _ap.parse_args()
    analyze_news(limit=_args.limit)

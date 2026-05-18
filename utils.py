import json
import os
import random
import re
import smtplib
import sqlite3
import string
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────
# CONSTANTS — Chart theme
# ─────────────────────────────────────────────────────────────────
PLOT_BG    = "#FFFFFF"
PAPER_BG   = "rgba(0,0,0,0)"
FONT_COLOR = "#4A5568"
GRID_COLOR = "#E5E9F0"
PLOT_FONT  = dict(family="Plus Jakarta Sans", size=12, color=FONT_COLOR)
ACCENT     = ["#2563EB","#16A34A","#D97706","#DC2626","#7C3AED",
              "#0EA5E9","#059669","#EA580C","#0891B2"]

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DB_FILE        = os.path.join(BASE_DIR, "bds_news.db")
API_USAGE_FILE = os.path.join(BASE_DIR, "api_usage.json")
GEMINI_DAILY_LIMIT = 250_000  # free tier estimate (tokens/day)


# ─────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────
def apply_theme(fig, legend: bool = True) -> go.Figure:
    """Apply light-theme styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=PLOT_FONT,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=(
            dict(bgcolor="rgba(0,0,0,0)", font=dict(color=FONT_COLOR, size=11))
            if legend else dict(visible=False)
        ),
        xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
                   tickfont=dict(color=FONT_COLOR)),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
                   tickfont=dict(color=FONT_COLOR)),
    )
    return fig

# Keep legacy alias used throughout rendering code
dark = apply_theme


def chg_color(chg: float):
    """Return (hex_color, display_string) for a percentage change value."""
    if chg > 0:
        return "#3fb950", f"▲ +{chg:.2f}%"
    if chg < 0:
        return "#f85149", f"▼ {chg:.2f}%"
    return "#7d8590", "— Không đổi"


# ─────────────────────────────────────────────────────────────────
# MACRO DATA
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def load_macro() -> dict:
    """Load real-time + static macro indicators for Vietnam RE market."""
    results: dict = {}
    try:
        import yfinance as yf
        for key, ticker in {"usdvnd": "USDVND=X", "vnindex": "^VNINDEX"}.items():
            try:
                hist = yf.Ticker(ticker).history(period="2d")
                if len(hist) >= 2:
                    prev, curr = hist["Close"].iloc[-2], hist["Close"].iloc[-1]
                    results[key] = {
                        "value": curr,
                        "change": ((curr - prev) / prev) * 100,
                        "ok": True,
                    }
                elif len(hist) == 1:
                    results[key] = {"value": hist["Close"].iloc[-1], "change": 0, "ok": True}
                else:
                    results[key] = {"value": None, "change": 0, "ok": False}
            except Exception:
                results[key] = {"value": None, "change": 0, "ok": False}
    except ImportError:
        pass

    # Static indicators (manually updated)
    results["nhnn_cv"]   = {"value": 7.50, "change": 0,    "ok": True, "static": True,
                             "note": "LS cho vay mua nhà TB · sbv.gov.vn"}
    results["tdung_bds"] = {"value": 19.0, "change": 1.5,  "ok": True, "static": True,
                             "note": "Tăng trưởng tín dụng BĐS (%YoY) · sbv.gov.vn"}
    results["gdp"]       = {"value": 7.09, "change": 0.34, "ok": True, "static": True,
                             "note": "GDP tăng trưởng (%YoY) · gso.gov.vn"}
    results["cpi"]       = {"value": 3.84, "change": 0.12, "ok": True, "static": True,
                             "note": "CPI tháng gần nhất (%YoY) · gso.gov.vn"}
    results["fdi"]       = {"value": 4.12, "change": 8.5,  "ok": True, "static": True,
                             "note": "FDI giải ngân YTD (tỷ USD) · mpi.gov.vn"}
    results["gia_dien"]  = {"value": 2103, "change": 0,    "ok": True, "static": True,
                             "note": "Giá điện bình quân (đ/kWh) · evn.com.vn"}

    # Ensure realtime keys always exist
    results.setdefault("usdvnd",  {"value": None, "change": 0, "ok": False})
    results.setdefault("vnindex", {"value": None, "change": 0, "ok": False})
    return results


# ─────────────────────────────────────────────────────────────────
# NORMALIZATION HELPERS
# ─────────────────────────────────────────────────────────────────

# ── Loại hình BĐS ────────────────────────────────────────────────
_NOXH_KW = [
    "nhà ở xã hội", "noxh", "nhà ở công nhân",
    "nhà ở giá thấp", "nhà ở giá rẻ",
]

_LOAI_MAP = {
    "Căn hộ": "Chung cư", "Chung cư": "Chung cư", "Nhà ở": "Chung cư",
    "Căn hộ chung cư": "Chung cư", "Chung cư cao cấp": "Chung cư",
    "Chung cư/Nhà ở xã hội": "Nhà ở Xã hội",
    "Nhà ở xã hội": "Nhà ở Xã hội",
    "Chung cư / Nhà ở xã hội": "Nhà ở Xã hội",
    "Nhà ở công nhân": "Nhà ở Xã hội",
    "Khu phức hợp / Thương mại dịch vụ": "Khu phức hợp",
    "Khu phức hợp / TTTM": "Khu phức hợp",
    "Khu đô thị": "Khu phức hợp",
    "BĐS Công nghiệp": "BĐS Công nghiệp / KCN",
    "Công nghiệp": "BĐS Công nghiệp / KCN",
    "Khu công nghiệp": "BĐS Công nghiệp / KCN",
    "Khu chế xuất": "BĐS Công nghiệp / KCN",
    "Logistics": "BĐS Công nghiệp / KCN",
    "BĐS Công nghiệp / IDC": "Data Center / IDC",
    "IDC": "Data Center / IDC",
    "Data center": "Data Center / IDC",
    "Data Center": "Data Center / IDC",
    "Trung tâm dữ liệu": "Data Center / IDC",
    "Văn phòng / TTTM": "Văn phòng / Thương mại",
    "Văn phòng": "Văn phòng / Thương mại",
    "TTTM": "Văn phòng / Thương mại",
    "Trung tâm thương mại": "Văn phòng / Thương mại",
    "Shophouse": "Văn phòng / Thương mại",
    "Trường học": "Trường học",
    "Cơ sở giáo dục": "Trường học",
    "Đại học": "Trường học",
    "Bệnh viện": "Bệnh viện / Y tế",
    "Bệnh viện / Y tế": "Bệnh viện / Y tế",
    "Cơ sở y tế": "Bệnh viện / Y tế",
    "Phòng khám": "Bệnh viện / Y tế",
    "Trường học / Bệnh viện / Khu vui chơi": "Công trình công cộng",
    "Trường học / Bệnh viện": "Công trình công cộng",
    "Công trình hạ tầng": "Công trình công cộng",
    "Bất động sản khác": "BĐS Khác", "Khác": "BĐS Khác",
    "Đất nền": "BĐS Khác", "Nhà phố": "BĐS Khác",
    "Phòng lab": "BĐS Khác", "Phòng thí nghiệm": "BĐS Khác",
    "Cơ sở nghiên cứu": "BĐS Khác",
}

_VALID_LOAI = [
    "Khu phức hợp", "Chung cư", "Nhà ở Xã hội",
    "BĐS Công nghiệp / KCN", "Data Center / IDC",
    "Nghỉ dưỡng", "Văn phòng / Thương mại",
    "Trường học", "Bệnh viện / Y tế",
    "Công trình công cộng", "BĐS Khác", "Không áp dụng",
]


def _norm_loai(row: pd.Series) -> str:
    txt = (str(row.get("Tóm tắt", "")) + " " + str(row.get("Tiêu đề", ""))).lower()
    val = str(row.get("Loại hình BĐS", "")).strip()
    if any(k in txt for k in _NOXH_KW):
        return "Nhà ở Xã hội"
    first_part = val.split(",")[0].strip()
    mapped_first = _LOAI_MAP.get(first_part, first_part)
    if mapped_first in _VALID_LOAI:
        return mapped_first
    mapped_val = _LOAI_MAP.get(val, val)
    return mapped_val if mapped_val else "BĐS Khác"


# ── CĐT classification ────────────────────────────────────────────
_GOV_EXACT = [
    "chính phủ việt nam", "chính phủ", "quốc hội",
    "ban quản lý khu kinh tế", "ban quản lý khu công nghiệp",
]
_GOV_PREFIX = [
    "ubnd ", "ủy ban nhân dân", "bộ xây dựng", "bộ tài chính",
    "bộ kế hoạch", "bộ giao thông", "bộ công thương", "bộ nông nghiệp",
    "bộ quốc phòng", "bộ công an", "bộ y tế", "bộ giáo dục",
    "bộ tài nguyên", "bộ nội vụ", "sở xây dựng", "sở tài chính",
    "sở kế hoạch", "sở giao thông", "sở tài nguyên", "cục quản lý",
    "tổng cục", "hội đồng nhân dân", "thành phố hà nội",
    "thành phố hồ chí minh", "tỉnh ",
]
_PRIVATE_OVERRIDE = [
    "vinaconex", "vinspeed", "viwaseen", "hud ", "becamex",
    "lilama", "idico", "viglacera", "vnpt", "mobifone",
    "evn ", "petrovietnam", "pvn", "pvfc", "pvgas",
]


def classify_cdt(name: str) -> str:
    """Return 'gov' or 'private' for a developer name."""
    if not name or name in ["Không áp dụng", "Chưa có thông tin", ""]:
        return "unknown"
    n = str(name).lower().strip()
    if any(p in n for p in _PRIVATE_OVERRIDE):
        return "private"
    if any(n == g or n.startswith(g) for g in _GOV_EXACT):
        return "gov"
    if any(n.startswith(g) for g in _GOV_PREFIX):
        return "gov"
    if any(g in n for g in ["ubnd", "ủy ban nhân dân", "ban quản lý khu"]):
        return "gov"
    return "private"


# ── Tỉnh thành normalization ──────────────────────────────────────
_TINH_MAP = {
    "tp.hà nội": "Hà Nội", "tp hà nội": "Hà Nội",
    "thành phố hà nội": "Hà Nội", "ha noi": "Hà Nội",
    "hà giang": "Tuyên Quang", "ha giang": "Tuyên Quang",
    "tuyên quang": "Tuyên Quang",
    "yên bái": "Lào Cai", "yen bai": "Lào Cai", "lào cai": "Lào Cai",
    "bắc kạn": "Thái Nguyên", "bac kan": "Thái Nguyên",
    "thái nguyên": "Thái Nguyên",
    "vĩnh phúc": "Phú Thọ", "hòa bình": "Phú Thọ", "phú thọ": "Phú Thọ",
    "bắc giang": "Bắc Ninh", "bắc ninh": "Bắc Ninh",
    "thái bình": "Hưng Yên", "hưng yên": "Hưng Yên",
    "hải dương": "Hải Phòng", "hải phòng": "Hải Phòng",
    "hai duong": "Hải Phòng", "tp.hải phòng": "Hải Phòng",
    "hà nam": "Ninh Bình", "nam định": "Ninh Bình", "ninh bình": "Ninh Bình",
    "quảng bình": "Quảng Trị", "quảng trị": "Quảng Trị",
    "quảng nam": "Đà Nẵng", "đà nẵng": "Đà Nẵng",
    "da nang": "Đà Nẵng", "tp.đà nẵng": "Đà Nẵng",
    "kon tum": "Quảng Ngãi", "quảng ngãi": "Quảng Ngãi",
    "bình định": "Gia Lai", "gia lai": "Gia Lai",
    "ninh thuận": "Khánh Hòa", "khánh hòa": "Khánh Hòa",
    "đắk nông": "Lâm Đồng", "bình thuận": "Lâm Đồng",
    "lâm đồng": "Lâm Đồng", "đà lạt": "Lâm Đồng",
    "phú yên": "Đắk Lắk", "đắk lắk": "Đắk Lắk",
    "hồ chí minh": "TP.HCM", "ho chi minh": "TP.HCM",
    "tp.hcm": "TP.HCM", "tphcm": "TP.HCM", "tp hcm": "TP.HCM",
    "tp. hcm": "TP.HCM", "thành phố hồ chí minh": "TP.HCM",
    "hcm": "TP.HCM", "sài gòn": "TP.HCM",
    "tp. hồ chí minh": "TP.HCM", "tp.hồ chí minh": "TP.HCM",
    "bình dương": "TP.HCM",
    "bà rịa - vũng tàu": "TP.HCM", "bà rịa–vũng tàu": "TP.HCM",
    "bà rịa – vũng tàu": "TP.HCM", "bà rịa-vũng tàu": "TP.HCM",
    "brvt": "TP.HCM", "vũng tàu": "TP.HCM",
    "bà rịa vũng tàu": "TP.HCM",
    "bình phước": "Đồng Nai", "đồng nai": "Đồng Nai", "dong nai": "Đồng Nai",
    "long an": "Tây Ninh", "tây ninh": "Tây Ninh",
    "sóc trăng": "Cần Thơ", "hậu giang": "Cần Thơ",
    "cần thơ": "Cần Thơ", "tp.cần thơ": "Cần Thơ",
    "bến tre": "Vĩnh Long", "trà vinh": "Vĩnh Long", "vĩnh long": "Vĩnh Long",
    "tiền giang": "Đồng Tháp", "đồng tháp": "Đồng Tháp",
    "bạc liêu": "Cà Mau", "cà mau": "Cà Mau",
    "kiên giang": "An Giang", "an giang": "An Giang",
    "huế": "Huế", "thừa thiên huế": "Huế", "tt huế": "Huế",
    "lai châu": "Lai Châu", "điện biên": "Điện Biên",
    "sơn la": "Sơn La", "lạng sơn": "Lạng Sơn",
    "quảng ninh": "Quảng Ninh", "thanh hóa": "Thanh Hóa",
    "nghệ an": "Nghệ An", "hà tĩnh": "Hà Tĩnh", "cao bằng": "Cao Bằng",
}

_TINH_34 = [
    "Hà Nội", "Tuyên Quang", "Lào Cai", "Thái Nguyên", "Phú Thọ",
    "Bắc Ninh", "Hưng Yên", "Hải Phòng", "Ninh Bình", "Quảng Trị",
    "Đà Nẵng", "Quảng Ngãi", "Gia Lai", "Khánh Hòa", "Lâm Đồng",
    "Đắk Lắk", "TP.HCM", "Đồng Nai", "Tây Ninh", "Cần Thơ",
    "Vĩnh Long", "Đồng Tháp", "Cà Mau", "An Giang",
    "Huế", "Lai Châu", "Điện Biên", "Sơn La", "Lạng Sơn",
    "Quảng Ninh", "Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Cao Bằng",
]


def norm_tinh(val) -> str:
    if not val or str(val).strip() in (
        "", "nan", "None", "Không rõ", "Chưa xác định", "Không áp dụng"
    ):
        return ""
    parts = [p.strip() for p in str(val).split(",")]
    result = []
    for p in parts:
        p_low = p.lower().strip()
        mapped = _TINH_MAP.get(p_low)
        if mapped:
            if mapped not in result:
                result.append(mapped)
            continue
        p_norm = p.strip()
        if p_norm in _TINH_34:
            if p_norm not in result:
                result.append(p_norm)
            continue
        found = next((t for t in _TINH_34
                      if t.lower() in p_low or p_low in t.lower()), None)
        if found and found not in result:
            result.append(found)
    return result[0] if result else ""


# ── Chủ đầu tư normalization ──────────────────────────────────────
_CDT_MERGE = {
    "sun property (thành viên sun group)": "Sun Group",
    "sun property": "Sun Group",
    "vinhomes": "Vinhomes (Vingroup)",
    "ubnd tp hà nội": "UBND TP. Hà Nội",
    "ubnd tp. hà nội": "UBND TP. Hà Nội",
    "ubnd thành phố hà nội": "UBND TP. Hà Nội",
    "ủy ban nhân dân thành phố hà nội": "UBND TP. Hà Nội",
    "ubnd tphcm": "UBND TP. Hồ Chí Minh",
    "ubnd tp hcm": "UBND TP. Hồ Chí Minh",
    "ubnd tp. hcm": "UBND TP. Hồ Chí Minh",
    "ubnd tp. hồ chí minh": "UBND TP. Hồ Chí Minh",
    "ủy ban nhân dân tp.hcm": "UBND TP. Hồ Chí Minh",
    "thành phố hà nội": "UBND TP. Hà Nội",
}


def norm_cdt(val) -> str:
    v = str(val).strip()
    return _CDT_MERGE.get(v.lower(), v)


# ── Nhóm Sự kiện normalization ────────────────────────────────────
def normalize_nhom_sk(sk: str) -> str:
    sk = str(sk).strip()
    if any(x in sk for x in [
        "Dịch vụ bất động sản", "Dịch vụ BĐS", "Quản lý Vận hành",
        "Vận hành tòa nhà", "PCCC", "Ban quản trị", "Phí bảo trì",
        "Bảo trì", "An ninh tòa nhà",
    ]):
        return "Dịch vụ BĐS"
    if any(x in sk for x in [
        "Quy hoạch", "Hạ tầng", "Giao thông", "Metro", "Cao tốc", "Vành đai"
    ]):
        return "Quy hoạch & Hạ tầng"
    if any(x in sk for x in [
        "Chính sách", "Pháp lý", "Luật", "Quy định", "Nghị định", "Thông tư"
    ]):
        return "Chính sách & Pháp lý"
    if any(x in sk for x in [
        "Thị trường", "Stakeholders", "Chủ đầu tư", "Dự án",
        "Mở bán", "Nguồn cung",
    ]):
        return "Thị trường BĐS"
    if any(x in sk for x in [
        "Tài chính", "Tín dụng", "Ngân hàng", "Chứng khoán", "Trái phiếu",
        "Lãi suất", "FDI", "Dòng vốn ngoại", "Vốn ngoại", "M&A",
    ]):
        return "Tài chính & Tín dụng"
    if any(x in sk for x in [
        "Vĩ mô", "Kinh tế", "GDP", "Lạm phát", "CPI", "Fed"
    ]):
        return "Kinh tế Vĩ mô"
    if any(x in sk for x in [
        "PropTech", "Công nghệ", "Chuyển đổi số", "AI", "IoT", "ESG", "Môi trường"
    ]):
        return "Công nghệ & ESG"
    if any(x in sk for x in [
        "Địa chính trị", "Chuỗi cung ứng", "Xung đột", "Quốc tế"
    ]):
        return "Địa chính trị"
    return "Thị trường BĐS"


def map_nhom_tin(sk_norm: str) -> str:
    N1 = ["Thị trường BĐS", "Quy hoạch & Hạ tầng", "Dịch vụ BĐS", "Chính sách & Pháp lý"]
    N2 = ["Tài chính & Tín dụng"]
    N3 = ["Kinh tế Vĩ mô", "Công nghệ & ESG", "Địa chính trị"]
    if sk_norm in N1:
        return "Nhóm 1 - Trực tiếp"
    if sk_norm in N2:
        return "Nhóm 2 - Gián tiếp"
    if sk_norm in N3:
        return "Nhóm 3 - Cảnh báo sớm"
    return "Nhóm 1 - Trực tiếp"


# ── Vòng đời normalization ────────────────────────────────────────
_VONGDOI_VALID = [
    "Chuẩn bị đầu tư", "Xây dựng", "Nghiệm thu & Bàn giao",
    "Vận hành", "Giai đoạn cải tạo", "Mở bán",
]


def norm_vongdoi(val) -> str:
    val = str(val).strip()
    if val in ["Không áp dụng", "Chưa xác định", "", "Chưa có thông tin"]:
        return val
    parts = [p.strip() for p in val.split(",")]
    for p in parts:
        if p in _VONGDOI_VALID:
            return p
    for vd in _VONGDOI_VALID:
        if vd.lower() in val.lower():
            return vd
    return parts[0] if parts else val


# ─────────────────────────────────────────────────────────────────
# MAIN DATA LOADER
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    """Load, clean and enrich all articles from SQLite DB."""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE, timeout=20)
    try:
        df = pd.read_sql("SELECT * FROM articles", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

    if df.empty or "Tóm tắt" not in df.columns:
        return pd.DataFrame()

    df["Tóm tắt"] = df["Tóm tắt"].fillna("")
    df = df[df["Tóm tắt"].str.strip() != ""].copy()
    if "Tin_Rac" in df.columns:
        df = df[df["Tin_Rac"].fillna("Không") != "Có"].copy()
    if df.empty:
        return df

    # ── Parse dates (3-layer fallback) ───────────────────────────
    df["Ngày đăng (Chuẩn)"] = pd.to_datetime(df["Ngày đăng"], errors="coerce", utc=True)

    if "Thời gian cào" in df.columns:
        cao_ts = pd.to_datetime(df["Thời gian cào"], errors="coerce", utc=True)
        df["Ngày đăng (Chuẩn)"] = df["Ngày đăng (Chuẩn)"].fillna(cao_ts)

    def _extract_ctx_date(row):
        text = str(row.get("Tóm tắt", "")) + " " + str(row.get("Tiêu đề", ""))
        _today = datetime.now().date()
        candidates = []
        for pat in [
            r"\b(\d{1,2})[/\-](\d{1,2})[/\-](202[0-9])\b",
            r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(202[0-9])",
        ]:
            for m in re.finditer(pat, text, re.IGNORECASE):
                try:
                    from datetime import date as _date
                    g = m.groups()
                    dt = _date(int(g[2]), int(g[1]), int(g[0]))
                    if _date(2020, 1, 1) <= dt <= _today:
                        candidates.append(dt)
                except Exception:
                    continue
        if not candidates:
            return pd.NaT
        return pd.Timestamp(max(candidates), tz="UTC")

    null_mask = df["Ngày đăng (Chuẩn)"].isna()
    if null_mask.any():
        df.loc[null_mask, "Ngày đăng (Chuẩn)"] = df[null_mask].apply(_extract_ctx_date, axis=1)

    df["Ngày đăng (Chuẩn)"] = df["Ngày đăng (Chuẩn)"].fillna(
        pd.Timestamp("2020-01-01", tz="UTC")
    )
    df["Chỉ Ngày"] = df["Ngày đăng (Chuẩn)"].dt.date
    df["Đầu Báo"] = df["Nguồn"].apply(lambda x: str(x).split(" - ")[0])

    # Numeric columns
    for col in ["Diện tích", "Tổng vốn", "Số lượng SP", "Điểm Sức khỏe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Expected columns
    expected = [
        "Nhóm Sự kiện", "Loại hình BĐS", "Vòng đời", "Tỉnh Thành",
        "Các Dịch vụ PMC", "Khu vực", "Dự án", "Chủ đầu tư",
        "Quy mô & Pháp lý", "Mốc thời gian", "Thông tin Chiến lược",
        "Phân tích Stakeholders", "Dự báo", "Đề xuất Hành động",
        "Action_BD", "Action_RnD", "Action_Legal", "Action_Finance",
        "Action_Marketing",
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("")

    # Apply normalizations
    df["Loại hình BĐS"] = df.apply(_norm_loai, axis=1)
    df["CĐT_Type"]      = df["Chủ đầu tư"].apply(classify_cdt)
    df["Tỉnh Thành"]    = df["Tỉnh Thành"].apply(norm_tinh)
    df["Chủ đầu tư"]    = df["Chủ đầu tư"].apply(norm_cdt)
    df["Vòng đời"]      = df["Vòng đời"].apply(norm_vongdoi)
    df["Nhóm Sự kiện"]  = df["Nhóm Sự kiện"].apply(normalize_nhom_sk)
    df["Nhóm Tin"]      = df["Nhóm Sự kiện"].apply(map_nhom_tin)

    df["_db_order"] = range(len(df))
    df = (
        df.sort_values(["Chỉ Ngày", "_db_order"], ascending=[False, False])
        .reset_index(drop=True)
        .drop(columns=["_db_order"])
    )
    return df


# ─────────────────────────────────────────────────────────────────
# BUSINESS LOGIC HELPERS (used by tab renderers)
# ─────────────────────────────────────────────────────────────────

def compute_is_hot(df: pd.DataFrame) -> pd.Series:
    """Compute Is_Hot flag on a filtered dataframe."""
    base = (
        df["Tóm tắt"].str.startswith("🔥", na=False) |
        (df["Điểm Sức khỏe"].abs() >= 7)
    )
    mask_not_bds = (
        df["Nhóm Tin"].isin(["Nhóm 2 - Gián tiếp", "Nhóm 3 - Cảnh báo sớm"]) &
        df["Dự án"].isin(["Không áp dụng", "", "Chưa có thông tin"])
    )
    base[mask_not_bds] = False
    return base


def priority_score(row: pd.Series) -> float:
    """Calculate lead priority score for sales pipeline."""
    s = row["Cnt"]
    if row["Is_Hot"]:
        s += 10
    if row["VD"] == "Chuẩn bị đầu tư":
        s += 5
    elif row["VD"] == "Xây dựng":
        s += 3
    s += max(0, row["SK"])
    return round(s, 1)


def build_lead_agg(base_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-project lead data from filtered dataframe."""
    JUNK_S = [
        "", "Không áp dụng", "Chưa có thông tin", "N/A", "Không rõ",
        "Chưa xác định", "Nhiều dự án", "Thị trường BĐS",
        "Hội nghị", "Diễn đàn",
    ]
    lead = base_df[~base_df["Dự án"].isin(JUNK_S)].copy()
    lead = lead[lead["Dự án"].str.len() > 4]
    lead = lead[~lead["Dự án"].str.lower().str.startswith(
        ("không", "chưa", "n/a", "none", "nan", "nhiều", "thị trường", "hội nghị")
    )]

    if lead.empty:
        return pd.DataFrame()

    agg = lead.groupby("Dự án").agg(
        Loai=("Loại hình BĐS", "first"),
        Tinh=("Tỉnh Thành", "first"),
        VD=("Vòng đời", "first"),
        CDT=("Chủ đầu tư", "first"),
        SK=("Điểm Sức khỏe", "mean"),
        Cnt=("Dự án", "count"),
        Is_Hot=("Is_Hot", "any"),
        Ngay=("Ngày đăng (Chuẩn)", "max"),
        Action_BD=("Action_BD", "first"),
    ).reset_index()
    agg["SK"] = agg["SK"].round(1)
    agg["Priority"] = agg.apply(priority_score, axis=1)
    return agg.sort_values("Priority", ascending=False)


# ─────────────────────────────────────────────────────────────────
# SHARED COLOR MAPS (used by tab renderers)
# ─────────────────────────────────────────────────────────────────
_COLORS_8 = ["#58a6ff","#388bfd","#1f6feb","#79c0ff",
             "#f0b429","#f85149","#d2a8ff","#8b949e"]
_GROUP_ORDER = [
    "Thị trường BĐS","Quy hoạch & Hạ tầng","Dịch vụ BĐS","Chính sách & Pháp lý",
    "Tài chính & Tín dụng","Kinh tế Vĩ mô","Công nghệ & ESG","Địa chính trị",
]
color_map_evt = {g: _COLORS_8[i] for i, g in enumerate(_GROUP_ORDER)}

LOAI_CLR = {
    "BĐS Công nghiệp / KCN": "#1f6feb",
    "Data Center / IDC":      "#388bfd",
    "Khu phức hợp":           "#58a6ff",
    "Chung cư":               "#79c0ff",
    "Nhà ở Xã hội":           "#3fb950",
    "Nghỉ dưỡng":             "#d2a8ff",
    "Văn phòng / Thương mại": "#f0b429",
    "Trường học":             "#56d364",
    "Bệnh viện / Y tế":       "#ffa198",
    "Công trình công cộng":   "#a5d6ff",
    "BĐS Khác":               "#484f58",
}

JUNK_ACT = ["", "0", "Không áp dụng", "Chưa có thông tin",
            "Chưa có", "N/A", "None", "nan"]


# ─────────────────────────────────────────────────────────────────
# API USAGE TRACKING
# ─────────────────────────────────────────────────────────────────
def load_api_usage() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    default = {
        "today_date": today,
        "today_tokens": 0,
        "today_requests": 0,
        "total_tokens": 0,
        "total_requests": 0,
        "daily_limit": GEMINI_DAILY_LIMIT,
        "history": [],
    }
    if not os.path.exists(API_USAGE_FILE):
        return default
    try:
        with open(API_USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("today_date") != today:
            history = data.get("history", [])
            history.append({
                "date": data.get("today_date"),
                "tokens": data.get("today_tokens", 0),
                "requests": data.get("today_requests", 0),
            })
            data.update({
                "today_date": today,
                "today_tokens": 0,
                "today_requests": 0,
                "history": history[-30:],
            })
        return {**default, **data}
    except Exception:
        return default


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def send_reset_otp(otp: str) -> tuple:
    smtp_user    = os.getenv("SMTP_USER", "")
    smtp_pass    = os.getenv("SMTP_PASS", "")
    notify_email = os.getenv("NOTIFY_EMAIL", "")

    if not (smtp_user and smtp_pass and notify_email):
        return False, "Chưa cấu hình SMTP_USER / SMTP_PASS / NOTIFY_EMAIL trong .env"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "DSK Dashboard – Mã OTP đặt lại mật khẩu"
    msg["From"]    = smtp_user
    msg["To"]      = notify_email

    html = f"""
    <div style="font-family:sans-serif;max-width:420px;margin:auto;
                padding:28px;border:1px solid #e0e0e0;border-radius:10px;">
      <h2 style="color:#2563EB;margin-bottom:6px;">🔐 DSK Dashboard</h2>
      <p style="color:#374151;">Mã OTP để đặt lại mật khẩu của bạn:</p>
      <div style="font-size:36px;font-weight:bold;letter-spacing:10px;
                  color:#2563EB;text-align:center;padding:18px 0;
                  background:#EFF6FF;border-radius:8px;margin:16px 0;">
        {otp}
      </div>
      <p style="color:#6b7280;font-size:13px;">
        Mã có hiệu lực trong <b>10 phút</b>.<br>
        Không chia sẻ mã này với bất kỳ ai.
      </p>
    </div>"""

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True, ""
    except smtplib.SMTPAuthenticationError:
        return False, "Sai SMTP_USER hoặc SMTP_PASS (Gmail cần App Password)"
    except Exception as exc:
        # fallback: try STARTTLS port 587
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True, ""
        except Exception:
            return False, str(exc)


def save_password_to_env(new_pass: str) -> bool:
    env_path = os.path.join(BASE_DIR, ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        new_lines = []
        for line in lines:
            if line.startswith("DASHBOARD_PASS="):
                new_lines.append(f"DASHBOARD_PASS={new_pass}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nDASHBOARD_PASS={new_pass}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        os.environ["DASHBOARD_PASS"] = new_pass
        return True
    except Exception:
        return False


def save_api_key_to_env(new_key: str) -> bool:
    env_path = os.path.join(BASE_DIR, ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        new_lines = []
        for line in lines:
            if line.startswith("GEMINI_API_KEY="):
                new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nGEMINI_API_KEY={new_key}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        os.environ["GEMINI_API_KEY"] = new_key
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────
def init_session_state():
    """Initialize all dashboard session state keys."""
    defaults = {
        "chart_filter_evt":  None,
        "chart_filter_type": None,
        "chart_filter_geo":  None,
        "authenticated":     False,
        "feed_page":         1,
        "feed_total":        0,
        "ap_page":           1,
        "sl_page":           1,
        "k1_page":           1,
        "gemini_api_key":    os.getenv("GEMINI_API_KEY", ""),
        "show_reset":        False,
        "otp_code":          "",
        "otp_expires":       None,
        "otp_sent":          False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
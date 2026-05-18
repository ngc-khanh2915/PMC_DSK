import os
import sys
from datetime import datetime, timedelta

import streamlit as st

from utils import (
    BASE_DIR,
    compute_is_hot, generate_otp, init_session_state, load_data,
    save_password_to_env, send_reset_otp,
)
from styles import load_css
from tabs import (
    tab1_data, tab2_strategic, tab3_knowledge,
    tab4_action, tab5_sales, tab6_control,
    tab7_account, news_feed,
)

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="DSK Dashboard", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────
load_css()


# ─────────────────────────────────────────────────────────────────
# SESSION STATE + AUTH
# ─────────────────────────────────────────────────────────────────
init_session_state()

try:
    from dotenv import load_dotenv as _ld
    _ld(os.path.join(BASE_DIR, ".env"))
except Exception:
    pass

_AUTH_USER = os.getenv("DASHBOARD_USER", "admin")
_AUTH_PASS = os.getenv("DASHBOARD_PASS", "admin123")

if not st.session_state.authenticated:
    _la, _lc, _ra = st.columns([1, 1.2, 1])
    with _lc:
        st.markdown("""
        <div style='background:var(--bg-surface);border:1.5px solid var(--border);
             border-radius:var(--radius-lg);padding:32px 28px;margin-top:40px;text-align:center;'>
          <div style='font-size:28px;margin-bottom:8px;'>🔐</div>
          <div style='font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:4px;'>
            DSK Dashboard</div>
          <div style='font-size:12px;color:var(--text-secondary);margin-bottom:24px;'>
            Vui lòng đăng nhập để tiếp tục</div>
        </div>""", unsafe_allow_html=True)

        if not st.session_state.show_reset:
            with st.form("login_form"):
                _uname = st.text_input("Tên đăng nhập", placeholder="admin")
                _upass = st.text_input("Mật khẩu", type="password", placeholder="••••••••")
                if st.form_submit_button("Đăng nhập", type="primary", use_container_width=True):
                    if _uname == _AUTH_USER and _upass == _AUTH_PASS:
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu!")
            if st.button("🔑 Quên mật khẩu?", use_container_width=True):
                st.session_state.show_reset = True
                st.rerun()
        else:
            _notify = os.getenv("NOTIFY_EMAIL", "")
            _smtp_ok = bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASS") and _notify)

            if not _smtp_ok:
                st.error("Chức năng quên mật khẩu chưa được cấu hình.")
                st.info("Cần thêm SMTP_USER, SMTP_PASS, NOTIFY_EMAIL vào file .env")
            else:
                _parts  = _notify.split("@")
                _masked = (_parts[0][:2] + "***@" + _parts[1]) if len(_parts) == 2 else _notify

                if not st.session_state.otp_sent:
                    st.markdown(
                        f"<div style='font-size:13px;color:var(--text-secondary);"
                        f"margin-bottom:14px;'>Mã OTP sẽ được gửi đến: "
                        f"<b style='color:var(--accent);'>{_masked}</b></div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("📧 Gửi mã OTP", type="primary", use_container_width=True):
                        _otp = generate_otp()
                        _ok, _err = send_reset_otp(_otp)
                        if _ok:
                            st.session_state.otp_code    = _otp
                            st.session_state.otp_expires = datetime.now() + timedelta(minutes=10)
                            st.session_state.otp_sent    = True
                            st.rerun()
                        else:
                            st.error(f"Không gửi được email: {_err}")
                else:
                    _exp = st.session_state.otp_expires
                    _exp_str = _exp.strftime("%H:%M:%S") if _exp else "?"
                    st.success(f"Đã gửi OTP đến {_masked} · hết hạn lúc {_exp_str}")
                    with st.form("reset_pass_form", clear_on_submit=True):
                        _rotp     = st.text_input("Mã OTP (6 số)", placeholder="● ● ● ● ● ●")
                        _rnew     = st.text_input("Mật khẩu mới", type="password",
                                                   placeholder="Tối thiểu 6 ký tự")
                        _rconfirm = st.text_input("Xác nhận mật khẩu mới", type="password",
                                                   placeholder="Nhập lại")
                        if st.form_submit_button("🔒 Đặt mật khẩu mới", type="primary",
                                                  use_container_width=True):
                            _now = datetime.now()
                            if _exp and _now > _exp:
                                st.error("Mã OTP đã hết hạn. Vui lòng gửi lại.")
                                st.session_state.otp_sent = False
                                st.session_state.otp_code = ""
                                st.rerun()
                            elif _rotp != st.session_state.otp_code:
                                st.error("Mã OTP không đúng.")
                            elif len(_rnew) < 6:
                                st.error("Mật khẩu mới phải có ít nhất 6 ký tự.")
                            elif _rnew != _rconfirm:
                                st.error("Mật khẩu xác nhận không khớp.")
                            else:
                                if save_password_to_env(_rnew):
                                    st.session_state.otp_code    = ""
                                    st.session_state.otp_expires = None
                                    st.session_state.otp_sent    = False
                                    st.session_state.show_reset  = False
                                    st.success("Đặt mật khẩu mới thành công! Hãy đăng nhập lại.")
                                    st.rerun()
                                else:
                                    st.error("Không lưu được. Kiểm tra quyền ghi file .env")
                    if st.button("🔄 Gửi lại OTP", use_container_width=True):
                        st.session_state.otp_sent = False
                        st.session_state.otp_code = ""
                        st.rerun()

            if st.button("← Quay lại đăng nhập", use_container_width=True):
                st.session_state.show_reset  = False
                st.session_state.otp_sent    = False
                st.session_state.otp_code    = ""
                st.session_state.otp_expires = None
                st.rerun()
    st.stop()

df = load_data()


# ─────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────
col_logo, col_time = st.columns([3, 1])
with col_logo:
    st.markdown(f"""
    <div style="padding:24px 0 16px 0;border-bottom:1px solid #21262d;margin-bottom:20px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">📊</span>
        <div>
          <div class="hero-title">DSK DASHBOARD</div>
          <div class="hero-subtitle">Real-time Intelligence Hub · Powered by AI</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
with col_time:
    st.markdown(f"""
    <div style="padding:24px 0 16px 0;text-align:right;">
      <div style="font-family:'JetBrains Mono';font-size:12px;color:#7d8590;">Cập nhật lúc</div>
      <div style="font-family:'JetBrains Mono';font-size:18px;color:#58a6ff;font-weight:700;">
        {datetime.now().strftime('%H:%M')}</div>
      <div style="font-size:12px;color:#484f58;">{datetime.now().strftime('%d/%m/%Y')}</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────
if df.empty:
    import subprocess as _sub_early

    st.warning(
        "⏳ **Chưa có dữ liệu phân tích.** "
        "Hãy chạy **Crawler** để thu thập tin tức từ RSS, "
        "sau đó chạy **Analyzer** để AI phân tích. "
        "Sau khi hoàn thành, nhấn **F5** để xem dashboard."
    )
    _ec1, _ec2, _ec3 = st.columns(3)
    _do_e_crawl = _do_e_analyze = _do_e_both = False
    with _ec1:
        if st.button("🕷️ Chạy Crawler", use_container_width=True, type="primary", key="early_crawl"):
            _do_e_crawl = True
    with _ec2:
        if st.button("🤖 Chạy Analyzer", use_container_width=True, type="primary", key="early_analyze"):
            _do_e_analyze = True
    with _ec3:
        if st.button("🔄 Crawl + Analyze", use_container_width=True, key="early_both"):
            _do_e_both = True

    _early_slot = st.empty()

    def _early_stream(script_path, label, prev=""):
        _acc = prev + f"\n▶ [{label}] Khởi động...\n" + "─" * 52 + "\n"
        _early_slot.code(_acc, language=None)
        try:
            _env = os.environ.copy()
            _env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"})
            _p = _sub_early.Popen(
                [sys.executable, script_path],
                stdout=_sub_early.PIPE, stderr=_sub_early.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=BASE_DIR, bufsize=1, env=_env,
            )
            for _ln in iter(_p.stdout.readline, ""):
                _acc += _ln
                _early_slot.code(_acc[-4000:], language=None)
            _p.wait()
            _acc += "\n" + "─" * 52 + "\n"
            _acc += ("✓ Hoàn thành! Nhấn F5 để xem dashboard.\n"
                     if _p.returncode == 0 else f"✗ Lỗi (exit {_p.returncode})\n")
        except Exception as _ex:
            _acc += f"\n✗ Lỗi: {_ex}\n"
        _early_slot.code(_acc[-4000:], language=None)
        return _acc

    if _do_e_crawl or _do_e_analyze or _do_e_both:
        _eout = ""
        if _do_e_crawl or _do_e_both:
            _eout = _early_stream(os.path.join(BASE_DIR, "bds_crawler.py"), "CRAWLER", _eout)
        if _do_e_analyze or _do_e_both:
            _eout = _early_stream(os.path.join(BASE_DIR, "ai_analyzer.py"), "ANALYZER", _eout)
        st.cache_data.clear()
    st.stop()


# ─────────────────────────────────────────────────────────────────
# MAIN FILTERS
# ─────────────────────────────────────────────────────────────────
with st.form("filter_form"):
    fc1, fc2, fc3, fc4, fc5 = st.columns([1, 1, 2, 1, 0.5])
    with fc1:
        time_option = st.selectbox("📅 Thời gian",
            ["Tất cả", "30 ngày qua", "7 ngày qua", "Ngày mới nhất"])
    with fc2:
        nhom_filter = st.selectbox("🎯 Nhóm tin",
            ["Tất cả", "Nhóm 1 - Trực tiếp", "Nhóm 2 - Gián tiếp", "Nhóm 3 - Cảnh báo sớm"])
    with fc3:
        source_filter = st.multiselect("📰 Nguồn tin",
            options=sorted(df["Đầu Báo"].unique()),
            default=list(df["Đầu Báo"].unique()))
    with fc4:
        only_hot = st.checkbox("🔥 Chỉ HOT", value=False)
    with fc5:
        st.markdown("<br>", unsafe_allow_html=True)
        st.form_submit_button("⚡ Lọc")

today      = datetime.now().date()
latest_day = df["Chỉ Ngày"].max() if not df.empty else today
src_f      = source_filter if source_filter else list(df["Đầu Báo"].unique())

if time_option == "7 ngày qua":
    dff = df[(df["Chỉ Ngày"] >= today - timedelta(days=7)) & df["Đầu Báo"].isin(src_f)]
elif time_option == "30 ngày qua":
    dff = df[(df["Chỉ Ngày"] >= today - timedelta(days=30)) & df["Đầu Báo"].isin(src_f)]
elif time_option == "Ngày mới nhất":
    dff = df[(df["Chỉ Ngày"] == latest_day) & df["Đầu Báo"].isin(src_f)]
else:
    dff = df[df["Đầu Báo"].isin(src_f)]

if nhom_filter != "Tất cả":
    dff = dff[dff["Nhóm Tin"] == nhom_filter]
if dff.empty:
    st.warning("📭 Không có dữ liệu phù hợp.")
    st.stop()

dff = dff.copy()
dff["Is_Hot"] = compute_is_hot(dff)
if only_hot:
    dff = dff[dff["Is_Hot"]]

df_te = (
    dff.assign(**{"Loại hình BĐS": dff["Loại hình BĐS"].str.split(",")})
    .explode("Loại hình BĐS")
)
df_te["Loại hình BĐS"] = df_te["Loại hình BĐS"].str.strip()


# ─────────────────────────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────────────────────────
top_evt     = dff["Nhóm Sự kiện"].mode()[0] if not dff["Nhóm Sự kiện"].empty else "N/A"
top_type    = df_te["Loại hình BĐS"].mode()[0] if not df_te.empty else "N/A"
top_src     = dff["Đầu Báo"].mode()[0] if not dff.empty else "N/A"
top_src_cnt = dff["Đầu Báo"].value_counts().iloc[0] if not dff.empty else 0
n_hot       = dff["Is_Hot"].sum()
n1 = (dff["Nhóm Tin"] == "Nhóm 1 - Trực tiếp").sum()
n2 = (dff["Nhóm Tin"] == "Nhóm 2 - Gián tiếp").sum()
n3 = (dff["Nhóm Tin"] == "Nhóm 3 - Cảnh báo sớm").sum()

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">📌 Tổng sự kiện</div>
    <div class="metric-value">{len(dff)}</div>
    <div class="metric-sub">N1:{n1} · N2:{n2} · N3:{n3}</div>
  </div>
  <div class="metric-card red">
    <div class="metric-label">🔥 Tin HOT</div>
    <div class="metric-value">{n_hot}</div>
    <div class="metric-sub">ưu tiên theo dõi</div>
  </div>
  <div class="metric-card green">
    <div class="metric-label">⚡ Nhóm SĐK nóng nhất</div>
    <div class="metric-value" style="font-size:14px;padding-top:4px;">{top_evt}</div>
    <div class="metric-sub">tỷ trọng cao nhất</div>
  </div>
  <div class="metric-card amber">
    <div class="metric-label">🏢 Phân khúc nổi bật</div>
    <div class="metric-value" style="font-size:14px;padding-top:6px;">{top_type}</div>
    <div class="metric-sub">đề cập nhiều nhất</div>
  </div>
  <div class="metric-card purple">
    <div class="metric-label">📰 Nguồn dẫn dắt</div>
    <div class="metric-value" style="font-size:16px;padding-top:4px;">{top_src}</div>
    <div class="metric-sub">{top_src_cnt} bài viết</div>
  </div>
</div>""", unsafe_allow_html=True)

# Chart-click filter badge
active_filters = []
if st.session_state.chart_filter_evt:
    active_filters.append(f"Sự kiện: {st.session_state.chart_filter_evt}")
if st.session_state.chart_filter_type:
    active_filters.append(f"Loại hình: {st.session_state.chart_filter_type}")
if st.session_state.chart_filter_geo:
    active_filters.append(f"Tỉnh/TP: {st.session_state.chart_filter_geo}")
if active_filters:
    caf, ccl = st.columns([4, 1])
    with caf:
        st.markdown(
            f"<div class='filter-active'>🔎 Lọc từ biểu đồ: "
            f"<b>{'  ·  '.join(active_filters)}</b></div>",
            unsafe_allow_html=True,
        )
    with ccl:
        if st.button("✕ Xóa bộ lọc"):
            st.session_state.chart_filter_evt = None
            st.session_state.chart_filter_type = None
            st.session_state.chart_filter_geo = None
            st.rerun()

st.markdown("""
<div class="section-header">
  <span class="section-badge">Analytics</span>
  <span class="section-title">Tổng quan Thị trường (Executive Summary)</span>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# GEO DATAFRAME (shared across tabs)
# ─────────────────────────────────────────────────────────────────
dg = (
    dff[["Tỉnh Thành"]].copy()
    .assign(**{"Tỉnh Thành": dff["Tỉnh Thành"].str.split(",")})
    .explode("Tỉnh Thành")
)
dg["Tỉnh Thành"] = dg["Tỉnh Thành"].str.strip()
_JUNK_GEO = ["Không rõ", "Chưa có thông tin", "Toàn quốc", "Quốc tế",
             "Nhật Bản", "Bắc Kinh", "Mỹ", "Trung Quốc", ""]
dg = dg[~dg["Tỉnh Thành"].isin(_JUNK_GEO)]


# ─────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 DATA", "🎯 STRATEGIC INFO", "🧠 KNOWLEDGE HUB",
    "⚡ ACTION PLAN", "🤖 SALES INTELLIGENCE", "⚙️ CONTROL", "👤 TÀI KHOẢN",
])

with tab1:
    tab1_data.render(dff, df_te, dg)

with tab2:
    tab2_strategic.render(dff, df_te)

with tab3:
    tab3_knowledge.render(dff, dg)

with tab4:
    tab4_action.render(dff, time_option)

with tab5:
    tab5_sales.render(dff)

with tab6:
    tab6_control.render()

with tab7:
    tab7_account.render()

news_feed.render(df, dff, df_te, dg)

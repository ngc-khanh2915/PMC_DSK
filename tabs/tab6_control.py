import json
import os
import smtplib
import subprocess
import sys
import sqlite3 as _sqlite3
import threading
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    BASE_DIR, DB_FILE, FONT_COLOR, dark,
    API_USAGE_FILE, GEMINI_DAILY_LIMIT,
    load_api_usage, save_api_key_to_env,
)


def render():
    _CTRL_DIR        = BASE_DIR
    _CRAWLER_SCRIPT  = os.path.join(_CTRL_DIR, "bds_crawler.py")
    _ANALYZER_SCRIPT = os.path.join(_CTRL_DIR, "ai_analyzer.py")
    _SCHED_CFG_PATH  = os.path.join(_CTRL_DIR, "scheduler_config.json")

    @st.cache_resource
    def _get_proc_state():
        return {"running": False, "output": "", "proc": None}

    @st.cache_resource
    def _get_sched_state():
        default = {
            "enabled": False, "run_time": "08:00", "limit": 0,
            "notify_email": "", "smtp_host": "smtp.gmail.com",
            "smtp_port": 587, "smtp_user": "", "smtp_pass": "",
            "last_run_date": None, "sched_thread_started": False,
        }
        if os.path.exists(_SCHED_CFG_PATH):
            try:
                with open(_SCHED_CFG_PATH, "r", encoding="utf-8") as f:
                    default.update(json.load(f))
            except Exception:
                pass
        return default

    _PROC  = _get_proc_state()
    _SCHED = _get_sched_state()

    def _save_sched_cfg():
        save = {k: v for k, v in _SCHED.items() if k != "sched_thread_started"}
        with open(_SCHED_CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(save, f, ensure_ascii=False, indent=2)

    def _bg_runner(scripts, limit=0):
        for sp, lbl in scripts:
            if not _PROC["running"]: break
            _PROC["output"] += f"\n▶ [{lbl}] Khởi động...\n" + "─"*52 + "\n"
            _env = os.environ.copy()
            _env.update({"PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1","PYTHONUNBUFFERED":"1"})
            cmd = [sys.executable, sp]
            if lbl == "ANALYZER" and limit > 0:
                cmd += ["--limit", str(limit)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace",
                                    cwd=_CTRL_DIR, bufsize=1, env=_env)
            _PROC["proc"] = proc
            for ln in iter(proc.stdout.readline, ""):
                _PROC["output"] += ln
            proc.wait()
            _PROC["output"] += "\n" + "─"*52 + "\n"
            _PROC["output"] += "✓ Hoàn thành!\n" if proc.returncode == 0 else f"✗ Lỗi (exit {proc.returncode})\n"
        _PROC["running"] = False
        _PROC["proc"]    = None

    def _send_notify_email(cfg, summary):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[DSK] Kết quả chạy tự động {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            msg["From"]    = cfg["smtp_user"]
            msg["To"]      = cfg["notify_email"]
            msg.attach(MIMEText(summary, "plain", "utf-8"))
            with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as srv:
                srv.ehlo(); srv.starttls(); srv.ehlo()
                srv.login(cfg["smtp_user"], cfg["smtp_pass"])
                srv.sendmail(cfg["smtp_user"], cfg["notify_email"], msg.as_string())
            return True, "OK"
        except Exception as e:
            return False, str(e)

    def _build_email_summary():
        try:
            with _sqlite3.connect(DB_FILE, timeout=10) as ec:
                tot = ec.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
                ana = ec.execute(
                    "SELECT COUNT(*) FROM articles WHERE \"Tóm tắt\" IS NOT NULL "
                    "AND TRIM(\"Tóm tắt\") != '' AND \"Tóm tắt\" NOT IN ('nan','none')"
                ).fetchone()[0]
                hot = ec.execute(
                    "SELECT COUNT(*) FROM articles WHERE \"Tóm tắt\" LIKE '🔥%'"
                ).fetchone()[0]
            return (f"DSK Intelligence — Báo cáo tự động\n"
                    f"Thời gian: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n"
                    f"Tổng bài: {tot}\nĐã phân tích: {ana}\nTin HOT: {hot}\n\n"
                    f"Chi tiết: http://localhost:8501")
        except Exception:
            return "Không lấy được thống kê từ DB."

    def _sched_loop(sched, proc_state, scripts_fn):
        while True:
            time.sleep(30)
            if not sched["enabled"]: continue
            now = datetime.now()
            th, tm = map(int, sched["run_time"].split(":"))
            today_s = now.strftime("%Y-%m-%d")
            if now.hour == th and now.minute == tm and sched["last_run_date"] != today_s:
                sched["last_run_date"] = today_s
                _save_sched_cfg()
                if not proc_state["running"]:
                    proc_state["output"]  = f"[AUTO {now.strftime('%H:%M')}] Lịch tự động kích hoạt\n"
                    proc_state["running"] = True
                    _bg_runner(scripts_fn(), sched.get("limit", 0))
                    if sched["notify_email"] and sched["smtp_user"]:
                        _send_notify_email(sched, _build_email_summary())

    if not _SCHED["sched_thread_started"]:
        _SCHED["sched_thread_started"] = True
        threading.Thread(
            target=_sched_loop,
            args=(_SCHED, _PROC,
                  lambda: [(_CRAWLER_SCRIPT,"CRAWLER"),(_ANALYZER_SCRIPT,"ANALYZER")]),
            daemon=True,
        ).start()

    # Header
    st.markdown("""
    <div style='background:var(--accent-light);border:1.5px solid #BFDBFE;
         border-radius:var(--radius-md);padding:14px 18px;margin-bottom:18px;'>
      <div style='font-size:14px;font-weight:700;color:var(--accent);margin-bottom:6px;'>
        ⚙️ Control Panel — Thu thập &amp; Phân tích dữ liệu</div>
      <div style='font-size:12px;color:var(--text-secondary);'>
        Chạy Crawler và AI Analyzer ngay từ dashboard — không cần mở terminal.</div>
    </div>""", unsafe_allow_html=True)

    # ── API Key & Usage ──────────────────────────────────────────────
    st.markdown("<div class='chart-title'>🔑 Cấu hình API Gemini</div>", unsafe_allow_html=True)
    st.markdown("<div class='api-key-box'>", unsafe_allow_html=True)

    _cur_key = os.getenv("GEMINI_API_KEY", "")
    _ak_col, _btn_col = st.columns([4, 1])
    with _ak_col:
        _new_key = st.text_input(
            "API Key Gemini",
            value=_cur_key,
            type="password",
            placeholder="AIzaSy...",
            key="ctrl_api_key_input",
            help="Key lưu vào .env — có hiệu lực lần chạy Analyzer tiếp theo",
            label_visibility="collapsed",
        )
        if _cur_key:
            st.markdown(
                f"<div style='font-size:12px;font-weight:600;color:var(--green);"
                f"margin-top:4px;'>🟢 Key hiện tại: "
                f"<code style='background:var(--bg-subtle);padding:2px 6px;"
                f"border-radius:4px;color:var(--text-primary);'>"
                f"{_cur_key[:10]}{'•' * 12}</code> "
                f"<span style='color:var(--text-muted);'>({len(_cur_key)} ký tự)</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size:12px;font-weight:600;color:var(--amber);"
                "margin-top:4px;'>🟡 Chưa có API Key — hãy nhập và lưu</div>",
                unsafe_allow_html=True,
            )
    with _btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Lưu Key", key="ctrl_save_api_key",
                     use_container_width=True, type="primary"):
            if _new_key.strip():
                _ok = save_api_key_to_env(_new_key.strip())
                if _ok:
                    st.success("Đã lưu! Khởi động lại Analyzer để áp dụng.")
                    st.session_state.gemini_api_key = _new_key.strip()
                else:
                    st.error("Không ghi được .env — kiểm tra quyền file.")
            else:
                st.warning("Key không được để trống.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Usage Display ────────────────────────────────────────────────
    _usage     = load_api_usage()
    _today_t   = _usage["today_tokens"]
    _today_req = _usage["today_requests"]
    _total_t   = _usage["total_tokens"]
    _limit     = _usage.get("daily_limit", GEMINI_DAILY_LIMIT)
    _pct       = min(100, int(_today_t / max(_limit, 1) * 100))
    _bar_clr   = "#DC2626" if _pct >= 90 else "#D97706" if _pct >= 70 else "#16A34A"
    _badge_cls = "danger"  if _pct >= 90 else "warn"    if _pct >= 70 else "ok"
    _badge_lbl = ("🔴 Nguy hiểm" if _pct >= 90
                  else "🟡 Cần chú ý" if _pct >= 70 else "🟢 Bình thường")

    st.markdown(f"""
    <div class='api-usage-box'>
      <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
        <span style='font-size:12px;font-weight:700;color:var(--text-secondary);'>
          📊 Token hôm nay</span>
        <span class='api-badge {_badge_cls}'>{_badge_lbl}</span>
      </div>
      <div class='usage-bar-wrap'>
        <div class='usage-bar-fill'
             style='width:{_pct}%;background:{_bar_clr};'></div>
      </div>
      <div style='display:flex;justify-content:space-between;
                  margin-top:5px;font-size:11px;color:var(--text-muted);'>
        <span>{_today_t:,} tokens · {_today_req} requests</span>
        <span>{_pct}% / {_limit:,}</span>
      </div>
      <div style='margin-top:4px;font-size:11px;color:var(--text-muted);'>
        Tổng cộng (all-time): <b>{_total_t:,}</b> tokens
      </div>
    </div>""", unsafe_allow_html=True)

    if _pct >= 90:
        st.error("⚠️ Sắp hết quota hôm nay! Cân nhắc đổi API key mới hoặc chờ ngày mai reset.")
    elif _pct >= 70:
        st.warning(f"💡 Đã dùng {_pct}% quota — còn khoảng {_limit - _today_t:,} tokens hôm nay.")

    st.markdown("<br>", unsafe_allow_html=True)

    # DB stats
    def _get_ctrl_stats():
        if not os.path.exists(DB_FILE): return 0, 0, 0
        try:
            with _sqlite3.connect(DB_FILE, timeout=10) as cc:
                tot  = cc.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
                ana  = cc.execute(
                    "SELECT COUNT(*) FROM articles WHERE \"Tóm tắt\" IS NOT NULL "
                    "AND TRIM(\"Tóm tắt\") != '' AND \"Tóm tắt\" NOT IN ('nan','none')"
                ).fetchone()[0]
                return tot, ana, tot - ana
        except Exception:
            return 0, 0, 0

    _db_tot, _db_ana, _db_pend = _get_ctrl_stats()
    _pct_done = int(_db_ana / max(_db_tot, 1) * 100)

    _csm1, _csm2, _csm3, _csm4 = st.columns(4)
    for _ccol, _clabel, _cval, _ccls in [
        (_csm1, "🗄️ Tổng bài",      str(_db_tot),  ""),
        (_csm2, "✅ Đã phân tích",  str(_db_ana),  " green"),
        (_csm3, "⏳ Chờ phân tích", str(_db_pend), " amber" if _db_pend > 0 else ""),
        (_csm4, "📊 Hoàn thành",   f"{_pct_done}%", " purple"),
    ]:
        with _ccol:
            st.markdown(
                f"<div class='metric-card{_ccls}'>"
                f"<div class='metric-label'>{_clabel}</div>"
                f"<div class='metric-value'>{_cval}</div></div>",
                unsafe_allow_html=True)

    st.markdown("<br><div class='chart-title'>Chạy thủ công</div>", unsafe_allow_html=True)
    _lim_c, _ = st.columns([1, 3])
    with _lim_c:
        _run_limit = st.number_input(
            "Giới hạn bài/lần (Analyzer)", min_value=0, max_value=9999,
            value=0, step=50, key="ctrl_limit",
            help="0 = không giới hạn.")

    _is_running = _PROC["running"]
    _cbc1, _cbc2, _cbc3, _cbc4 = st.columns(4)
    _do_crawl = _do_analyze = _do_both = _do_stop = False

    for _ccol, _title, _desc, _key, _is_stop in [
        (_cbc1, "🕷️ Crawler",      "RSS 20 tờ báo, lưu DB.",       "ctrl_crawl",   False),
        (_cbc2, "🤖 Analyzer",     "Gemini AI phân tích D-S-K.",    "ctrl_analyze", False),
        (_cbc3, "🔄 Crawl + Analyze","1 chu kỳ đầy đủ.",            "ctrl_both",    False),
        (_cbc4, "⏹ Dừng",          "Huỷ tiến trình đang chạy.",    "ctrl_stop",    True),
    ]:
        with _ccol:
            _bg  = "var(--red-light)" if _is_stop else "var(--bg-surface)"
            _bc  = "#FECACA"          if _is_stop else "var(--border)"
            _tc  = "#DC2626"          if _is_stop else "var(--text-primary)"
            _dis = (not _is_running)  if _is_stop else _is_running
            st.markdown(
                f"<div style='background:{_bg};border:1px solid {_bc};border-radius:var(--radius-md);"
                f"padding:12px 14px;margin-bottom:8px;'>"
                f"<div style='font-size:12px;font-weight:700;color:{_tc};margin-bottom:4px;'>"
                f"{_title}</div>"
                f"<div style='font-size:11px;color:var(--text-secondary);'>{_desc}</div></div>",
                unsafe_allow_html=True)
            if st.button(f"▶ {_title.split()[1]}" if not _is_stop else "⏹ Dừng",
                         disabled=_dis, use_container_width=True,
                         type="primary" if not _is_stop else "secondary",
                         key=_key):
                if _is_stop:   _do_stop   = True
                elif "Crawl" in _title and "Analyze" in _title: _do_both    = True
                elif "Crawler" in _title: _do_crawl   = True
                else:          _do_analyze = True

    _output_slot = st.empty()
    if _is_running:
        st.info("⏳ Đang chạy — trang tự làm mới mỗi 1s...")

    if _do_stop:
        if _PROC["proc"]:
            try: _PROC["proc"].terminate()
            except Exception: pass
        _PROC["running"] = False
        _PROC["output"] += "\n⏹ Dừng bởi người dùng.\n"
        st.rerun()

    if _do_crawl or _do_analyze or _do_both:
        _PROC["output"]  = ""
        _PROC["running"] = True
        _scripts = []
        if _do_crawl or _do_both:   _scripts.append((_CRAWLER_SCRIPT,  "CRAWLER"))
        if _do_analyze or _do_both: _scripts.append((_ANALYZER_SCRIPT, "ANALYZER"))
        threading.Thread(target=_bg_runner, args=(_scripts, _run_limit), daemon=True).start()
        st.rerun()

    if _PROC["running"]:
        _output_slot.code(_PROC["output"][-5000:] or "Đang khởi động...", language=None)
        time.sleep(1)
        st.rerun()
    elif _PROC["output"]:
        _output_slot.code(_PROC["output"][-5000:], language=None)

    if _PROC["output"] and not _PROC["running"]:
        if st.button("🗑️ Xóa", key="ctrl_clear"):
            _PROC["output"] = ""
            st.cache_data.clear()
            st.rerun()

    # Run statistics chart
    st.markdown("<br><div class='chart-title'>Thống kê bài crawl theo ngày</div>",
                unsafe_allow_html=True)
    _sf1, _sf2 = st.columns([1, 4])
    with _sf1:
        _stat_range = st.selectbox("Lọc khoảng", ["7 ngày","30 ngày","90 ngày","Tất cả"],
                                   key="ctrl_stat_range")
    if os.path.exists(DB_FILE):
        try:
            with _sqlite3.connect(DB_FILE, timeout=10) as stc:
                _df_filter = {
                    "7 ngày":  "AND date(\"Thời gian cào\") >= date('now','-7 days')",
                    "30 ngày": "AND date(\"Thời gian cào\") >= date('now','-30 days')",
                    "90 ngày": "AND date(\"Thời gian cào\") >= date('now','-90 days')",
                    "Tất cả":  "",
                }[_stat_range]
                _stat_df = pd.read_sql(
                    f"SELECT date(\"Thời gian cào\") as Ngay, COUNT(*) as \"Số bài\" "
                    f"FROM articles WHERE \"Thời gian cào\" IS NOT NULL {_df_filter} "
                    f"GROUP BY Ngay ORDER BY Ngay", stc)
            if not _stat_df.empty:
                _stat_df["Ngay"] = pd.to_datetime(_stat_df["Ngay"])
                _fig_stat = px.bar(_stat_df, x="Ngay", y="Số bài",
                                   color_discrete_sequence=["#2563EB"])
                _fig_stat.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    height=200, margin=dict(l=0,r=0,t=10,b=0),
                    xaxis=dict(showgrid=False,
                               tickfont=dict(color="#4A5568", size=11),
                               title_font=dict(color="#4A5568")),
                    yaxis=dict(showgrid=True, gridcolor="#EEF1F6",
                               tickfont=dict(color="#4A5568", size=11),
                               title_font=dict(color="#4A5568")),
                    font=dict(family="Plus Jakarta Sans", size=11, color="#4A5568"),
                )
                st.plotly_chart(_fig_stat, use_container_width=True)
                _peak_day = _stat_df.loc[_stat_df['Số bài'].idxmax(), 'Ngay'].strftime('%d/%m')
                st.markdown(
                    f"<div style='font-size:12px;font-weight:600;color:var(--text-secondary);"
                    f"margin-top:6px;'>"
                    f"Tổng <b style='color:var(--accent);'>{_stat_df['Số bài'].sum():,}</b> bài &nbsp;·&nbsp; "
                    f"Trung bình <b style='color:var(--accent);'>{int(_stat_df['Số bài'].mean())}</b> bài/ngày &nbsp;·&nbsp; "
                    f"Cao nhất <b style='color:var(--red);'>{_stat_df['Số bài'].max()}</b> bài"
                    f" <span style='color:var(--text-muted);'>({_peak_day})</span></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("Chưa có dữ liệu crawl trong khoảng thời gian này.")
        except Exception as se:
            st.warning(f"Không đọc được thống kê: {se}")

    # Scheduler config
    st.markdown("<br><div class='chart-title'>Lịch tự động + Thông báo Email</div>",
                unsafe_allow_html=True)
    with st.expander("⚙️ Cấu hình lịch & email", expanded=False):
        sc1, sc2 = st.columns(2)
        with sc1:
            _sched_enabled = st.toggle("Bật lịch tự động",  value=_SCHED["enabled"], key="sched_tog")
            _sched_time    = st.text_input("Giờ chạy (HH:MM)", value=_SCHED["run_time"], key="sched_time")
            _sched_limit   = st.number_input("Giới hạn bài/lần", min_value=0, max_value=9999,
                                             value=int(_SCHED.get("limit",0)), step=10, key="sched_lim")
        with sc2:
            _sched_email   = st.text_input("Email nhận thông báo", value=_SCHED["notify_email"], key="sched_email")
            _sched_user    = st.text_input("Gmail gửi",            value=_SCHED["smtp_user"],    key="sched_user")
            _sched_pass    = st.text_input("App password",         value=_SCHED["smtp_pass"],
                                           type="password", key="sched_pass")
        sb1, sb2, sb3 = st.columns(3)
        with sb1:
            if st.button("💾 Lưu cấu hình", key="sched_save", use_container_width=True, type="primary"):
                _SCHED.update({
                    "enabled": _sched_enabled, "run_time": _sched_time.strip(),
                    "limit": _sched_limit, "notify_email": _sched_email.strip(),
                    "smtp_host": "smtp.gmail.com", "smtp_port": 587,
                    "smtp_user": _sched_user.strip(), "smtp_pass": _sched_pass.strip(),
                })
                _save_sched_cfg()
                st.success(f"Đã lưu! Scheduler chạy lúc {_sched_time}")
        with sb2:
            if st.button("📧 Test Email", key="sched_test", use_container_width=True):
                if _sched_user and _sched_pass and _sched_email:
                    ok, msg = _send_notify_email(
                        {**_SCHED, "smtp_user": _sched_user, "smtp_pass": _sched_pass,
                         "notify_email": _sched_email}, _build_email_summary())
                    st.success("Email gửi thành công!") if ok else st.error(f"Lỗi: {msg}")
                else:
                    st.warning("Điền đủ Gmail gửi, App password và Email nhận.")
        with sb3:
            st.info(f"Lịch: {_SCHED['run_time']} · {'🟢 BẬT' if _SCHED['enabled'] else '⚪ TẮT'}")

    _log_path = os.path.join(_CTRL_DIR, "scheduler.log")
    if os.path.exists(_log_path):
        with st.expander("📋 Scheduler Log", expanded=False):
            try:
                with open(_log_path, "r", encoding="utf-8", errors="replace") as lf:
                    st.code("".join(lf.readlines()[-15:]) or "(Chưa có log)", language=None)
            except Exception as le:
                st.error(f"Không đọc được log: {le}")

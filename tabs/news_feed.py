import io
import os
import re
import sys
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from utils import compute_is_hot, load_macro


def render(df, dff, df_te, dg):
    # ── Report Export ─────────────────────────────────────────────
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from report_generator import get_report_b64
        _has_report = True
    except Exception:
        _has_report = False

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📄 Xuất Báo cáo Intelligence — HTML in A4", expanded=False):
        rp1, rp2, rp3 = st.columns([1.2, 1, 1])
        with rp1:
            rp_period = st.selectbox("📅 Kỳ báo cáo",
                ["7 ngày qua","30 ngày qua","Tháng này","Hôm nay","Tùy chọn"],
                key="rp_period")
        with rp2:
            rp_from = st.date_input("Từ ngày", key="rp_from",
                value=datetime.now().date()-timedelta(days=7)) if rp_period == "Tùy chọn" else None
        with rp3:
            rp_to = st.date_input("Đến ngày", key="rp_to",
                value=datetime.now().date()) if rp_period == "Tùy chọn" else None

        if st.button("🖨️ Tạo báo cáo", type="primary", key="gen_report"):
            _now = datetime.now()
            if rp_period == "Hôm nay":
                _df_d, _dt2 = _now.date(), _now.date()
            elif rp_period == "7 ngày qua":
                _df_d, _dt2 = (_now-timedelta(days=7)).date(), _now.date()
            elif rp_period == "30 ngày qua":
                _df_d, _dt2 = (_now-timedelta(days=30)).date(), _now.date()
            elif rp_period == "Tháng này":
                _df_d, _dt2 = _now.date().replace(day=1), _now.date()
            else:
                _df_d, _dt2 = rp_from, rp_to
            _rdf = df[(df["Chỉ Ngày"] >= _df_d) & (df["Chỉ Ngày"] <= _dt2)].copy()
            _rdf["Is_Hot"] = compute_is_hot(_rdf)
            if _has_report:
                _b64 = get_report_b64(_rdf, df, load_macro(), rp_period, _df_d, _dt2)
                st.markdown(
                    f"<a href='data:text/html;base64,{_b64}' target='_blank' "
                    f"style='display:inline-block;background:#1f6feb;color:white;"
                    f"padding:10px 22px;border-radius:8px;text-decoration:none;"
                    f"font-weight:700;font-size:14px;margin-top:10px;'>"
                    f"Mở báo cáo → In hoặc Lưu PDF</a>",
                    unsafe_allow_html=True)
                st.caption(f"Kỳ: {_df_d.strftime('%d/%m/%Y')} — {_dt2.strftime('%d/%m/%Y')} "
                           f"| {len(_rdf)} sự kiện | {int(_rdf['Is_Hot'].sum())} HOT")
            else:
                st.error("Không tải được report_generator.py")

    # ── Intelligence Feed (News cards) ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div class="section-header">
  <span class="section-badge" style="background:#23863622;border-color:#23863655;color:#3fb950;">
    Intelligence Feed</span>
  <span class="section-title">📋 Nhật Ký Cơ Hội Kinh Doanh</span>
</div>""", unsafe_allow_html=True)

    ff1, ff2, ff3, ff4 = st.columns([1.5, 1.5, 2, 1])
    with ff1:
        sel_evt = st.selectbox("📌 Nhóm Sự kiện",
            ["Tất cả"] + sorted(dff["Nhóm Sự kiện"].unique().tolist()))
    with ff2:
        sel_type = st.selectbox("🏢 Loại hình BĐS",
            ["Tất cả"] + sorted([x for x in df_te["Loại hình BĐS"].unique()
                                  if x not in ["","Không áp dụng","Chưa có thông tin","BĐS Khác"]]))
    with ff3:
        search = st.text_input("🔍 Tìm kiếm...",
            placeholder="Tiêu đề / dự án / tỉnh thành...")
    with ff4:
        sel_geo = st.selectbox("📍 Tỉnh/TP",
            ["Tất cả"] + sorted([x for x in dg["Tỉnh Thành"].unique()
                                  if x not in ["","Không rõ"]] if not dg.empty else []))

    dd = dff.copy()
    if st.session_state.chart_filter_evt:
        dd = dd[dd["Nhóm Sự kiện"] == st.session_state.chart_filter_evt]
    if st.session_state.chart_filter_type:
        dd = dd[dd["Loại hình BĐS"].str.contains(st.session_state.chart_filter_type, na=False)]
    if st.session_state.chart_filter_geo:
        dd = dd[dd["Tỉnh Thành"].str.contains(st.session_state.chart_filter_geo, na=False)]
    if sel_evt != "Tất cả":
        dd = dd[dd["Nhóm Sự kiện"] == sel_evt]
    if sel_type != "Tất cả":
        dd = dd[dd["Loại hình BĐS"].str.contains(sel_type, na=False)]
    if sel_geo != "Tất cả":
        dd = dd[dd["Tỉnh Thành"].str.contains(sel_geo, na=False)]
    if search:
        dd = dd[
            dd["Tiêu đề"].str.contains(search, case=False, na=False) |
            dd["Dự án"].str.contains(search, case=False, na=False) |
            dd["Tỉnh Thành"].str.contains(search, case=False, na=False)
        ]
    dd = dd.sort_values("Chỉ Ngày", ascending=False).reset_index(drop=True)

    col_info, col_export = st.columns([4, 1])
    with col_info:
        st.markdown(
            f"<p style='color:#7d8590;font-size:13px;margin:8px 0;'>"
            f"Tìm thấy <b style='color:#58a6ff'>{len(dd)}</b> bài viết phù hợp.</p>",
            unsafe_allow_html=True)
    with col_export:
        if not dd.empty:
            export_cols = [
                "Tiêu đề","Nguồn","Ngày đăng","Nhóm Sự kiện","Loại hình BĐS",
                "Vòng đời","Tỉnh Thành","Dự án","Chủ đầu tư","Tóm tắt",
                "Điểm Sức khỏe","Dự báo","Link",
            ]
            export_df = dd[[c for c in export_cols if c in dd.columns]].copy()
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="PMC Intelligence")
            st.download_button(
                "📥 Xuất Excel", data=buf.getvalue(),
                file_name=f"PMC_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    # News cards with pagination
    if not dd.empty:
        PPG = 10
        total_pg = max(1, (len(dd)-1)//PPG+1)
        if "feed_page" not in st.session_state: st.session_state.feed_page = 1
        if len(dd) != st.session_state.get("feed_total", len(dd)):
            st.session_state.feed_page = 1
        st.session_state.feed_total = len(dd)
        page = st.session_state.feed_page

        for idx, row in dd.iloc[(page-1)*PPG : page*PPG].iterrows():
            is_hot2   = row.get("Is_Hot", False)
            nhom_t    = row.get("Nhóm Tin","")
            card_cls  = "news-card hot" if is_hot2 else "news-card"
            nhom_cls  = "n1" if "1" in nhom_t else "n2" if "2" in nhom_t else "n3" if "3" in nhom_t else ""
            if nhom_cls: card_cls += f" {nhom_cls}"
            nhom_label = ""
            if "1" in nhom_t:   nhom_label = "<span class='tag tag-n1'>N1 Trực tiếp</span>"
            elif "2" in nhom_t: nhom_label = "<span class='tag tag-n2'>N2 Gián tiếp</span>"
            elif "3" in nhom_t: nhom_label = "<span class='tag tag-n3'>N3 Cảnh báo</span>"
            hot_badge = "<span class='tag tag-hot'>🔥 HOT</span>" if is_hot2 else ""

            st.markdown(f"""<div class="{card_cls}">
          <div class="news-meta">
            <span class="tag tag-time">🕒 {str(row.get('Ngày đăng',''))[:16]}</span>
            <span class="tag tag-source">📰 {row.get('Nguồn','')}</span>
            {nhom_label}{hot_badge}
            <span class="tag tag-event">{row.get('Nhóm Sự kiện','')}</span>
            <span class="tag tag-type">🏢 {row.get('Loại hình BĐS','')}</span>
            <span class="tag tag-lifecycle">🔄 {row.get('Vòng đời','')}</span>
          </div>
          <div class="news-title">{row.get('Tiêu đề','')}</div>
          <div class="news-summary">{row.get('Tóm tắt','')}</div>
        </div>""", unsafe_allow_html=True)

            with st.expander("🔍 Phân tích D–S–K"):
                td, ts, tk, ta = st.tabs(["📊 DATA","🎯 STRATEGIC","🧠 KNOWLEDGE","⚡ ACTION"])
                with td:
                    d1, d2, d3 = st.columns(3)
                    for w, lbl, key_n in [
                        (d1,"📁 Dự án","Dự án"),
                        (d2,"👑 Chủ đầu tư","Chủ đầu tư"),
                        (d3,"📍 Khu vực","Khu vực"),
                    ]:
                        with w:
                            st.markdown(
                                f"<div class='info-block'><div class='label'>{lbl}</div>"
                                f"<div class='value'>{row.get(key_n,'')}</div></div>",
                                unsafe_allow_html=True)
                    d4, d5 = st.columns(2)
                    with d4:
                        st.markdown(
                            f"<div class='info-block'><div class='label'>📐 Quy mô & Pháp lý</div>"
                            f"<div class='value'>{row.get('Quy mô & Pháp lý','')}</div></div>",
                            unsafe_allow_html=True)
                    with d5:
                        st.markdown(
                            f"<div class='info-block'><div class='label'>📅 Mốc thời gian</div>"
                            f"<div class='value'>{row.get('Mốc thời gian','')}</div></div>",
                            unsafe_allow_html=True)
                with ts:
                    raw_st = row.get("Thông tin Chiến lược","")
                    rendered_st = False
                    try:
                        bm = re.search(r"\*?\*?Bối\s*cảnh\*?\*?\s*[:\-]?\s*(.*?)(?=\*?\*?Chuyển\s*đổi|$)",
                                       raw_st, re.DOTALL|re.IGNORECASE)
                        cm = re.search(r"\*?\*?Chuyển\s*đổi\*?\*?\s*[:\-]?\s*(.*?)$",
                                       raw_st, re.DOTALL|re.IGNORECASE)
                        boi_canh  = bm.group(1).strip() if bm else ""
                        chuyen_doi = cm.group(1).strip() if cm else ""
                        w_keys = {
                            "What": ("❓","Sự kiện gì?","#1f6feb","#0d2040"),
                            "Who":  ("👤","Ai liên quan?","#8957e5","#1a0d40"),
                            "Where":("📍","Ở đâu?","#1a7f37","#0d2818"),
                            "When": ("📅","Khi nào?","#9e6a03","#2d1f00"),
                            "Why":  ("💡","Tại sao?","#bf4b00","#2d1200"),
                            "How":  ("⚙️","Như thế nào?","#1b7c83","#0d2428"),
                        }
                        w_data = {}
                        for key_w in w_keys:
                            m = re.search(
                                rf"{key_w}\s*[:\-]\s*(.*?)(?=(?:What|Who|Where|When|Why|How)\s*[:\-]|$)",
                                boi_canh, re.DOTALL|re.IGNORECASE)
                            if m: w_data[key_w] = m.group(1).strip().rstrip(".")
                        if w_data or chuyen_doi:
                            rendered_st = True
                            st.markdown("<div class='info-block-label'>🎯 Bối cảnh 5W1H</div>",
                                        unsafe_allow_html=True)
                            w_items = list(w_keys.items())
                            for ri in range(0, len(w_items), 3):
                                cols_w = st.columns(3)
                                for ci, (key_w, (icon, desc, border, bg)) in enumerate(w_items[ri:ri+3]):
                                    val_w = w_data.get(key_w,"")
                                    with cols_w[ci]:
                                        st.markdown(
                                            f"<div style='background:{bg};border:1px solid {border}44;"
                                            f"border-top:3px solid {border};border-radius:8px;"
                                            f"padding:12px 14px;min-height:80px;margin-bottom:8px;'>"
                                            f"<div style='font-size:10px;color:{border};font-weight:700;"
                                            f"text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px;'>"
                                            f"{icon} {key_w} — {desc}</div>"
                                            f"<div style='font-size:13px;color:#c9d1d9;line-height:1.6;'>"
                                            f"{val_w if val_w else '<span style=\"color:#484f58;font-style:italic;\">Không rõ</span>'}"
                                            f"</div></div>", unsafe_allow_html=True)
                            if chuyen_doi:
                                st.markdown(
                                    "<div class='info-block-label' style='border-left:3px solid #f0b429;"
                                    "padding-left:8px;margin-top:8px;'>🔄 Chuyển đổi trạng thái</div>",
                                    unsafe_allow_html=True)
                                st.markdown(
                                    f"<div style='background:#2d1f00;border:1px solid #9e6a03;"
                                    f"border-radius:8px;padding:14px 16px;'>"
                                    f"<span style='font-size:14px;color:#f0e3a0;line-height:1.7;'>"
                                    f"{chuyen_doi}</span></div>", unsafe_allow_html=True)
                    except Exception:
                        rendered_st = False
                    if not rendered_st:
                        st.markdown("<div class='info-block-label'>🎯 Thông tin chiến lược</div>",
                                    unsafe_allow_html=True)
                        st.markdown(raw_st)
                with tk:
                    st.markdown("<div class='info-block-label'>👥 Phân tích Stakeholders</div>",
                                unsafe_allow_html=True)
                    raw_sh = row.get("Phân tích Stakeholders","")
                    rendered = False
                    try:
                        def _parse_sh(raw):
                            if not raw or not raw.strip(): return []
                            text = re.sub(r"\*+","",raw).strip()
                            has_dash   = bool(re.search(r".{2,40}[—–]\s*[Ll]ợi\s*[Íí]ch", text))
                            has_number = bool(re.search(r"\(\d+\)", text))
                            has_nl     = bool(re.search(r"[Ll]ợi\s*[Íí]ch.*?\n.*?[Rr]ủi\s*[Rr]o", text, re.DOTALL))
                            results = []
                            if has_dash:
                                pat = re.compile(r"(?:(?:^|\. +))([^.—–\n]{2,50}?)\s*[—–]\s*[Ll]ợi\s*[Íí]ch\s*:")
                                positions = [(m.start(), m.group(1).strip(), m.end()) for m in pat.finditer(text)]
                                for i, (ps, name, bs) in enumerate(positions):
                                    body = text[bs:(positions[i+1][0] if i+1<len(positions) else len(text))].strip()
                                    rm = re.search(r"\s*[Rr]ủi\s*[Rr]o\s*:\s*(.*?)(?=\.\s*$|$)", body, re.DOTALL)
                                    li = body[:rm.start()].strip().rstrip(".") if rm else body.strip()
                                    ri = rm.group(1).strip().rstrip(".") if rm else ""
                                    nc = re.sub(r"[Rr]ủi\s*[Rr]o.*$","",name).strip().rstrip(".")
                                    if nc: results.append({"name":nc,"loi_ich":li,"rui_ro":ri})
                            elif has_nl:
                                lines = text.replace("\\n","\n").split("\n")
                                gr = re.compile(r"^\s*-?\s*\((\d+)\)\s*(.*?)\s*:?\s*$")
                                lr = re.compile(r"^\s*[-–]?\s*[Ll]ợi\s*[Íí]ch\s*:?\s*(.*)")
                                rr = re.compile(r"^\s*[-–]?\s*[Rr]ủi\s*[Rr]o\s*:?\s*(.*)")
                                grps = []; cur = [None,[],[]]; st2 = [None]
                                for line in lines:
                                    gm=gr.match(line); lm=lr.match(line); rm=rr.match(line)
                                    if gm:
                                        if cur[0] is not None or cur[1] or cur[2]:
                                            grps.append((cur[0],list(cur[1]),list(cur[2])))
                                        cur=[gm.group(2).strip().rstrip(":"),[],[]]; st2[0]=None
                                    elif lm: st2[0]="li"; v=lm.group(1).strip(); (cur[1] if v else []).append(v) if v else None
                                    elif rm: st2[0]="ri"; v=rm.group(1).strip(); (cur[2] if v else []).append(v) if v else None
                                    elif line.strip() and st2[0]=="li": cur[1].append(line.strip())
                                    elif line.strip() and st2[0]=="ri": cur[2].append(line.strip())
                                if cur[0] is not None or cur[1] or cur[2]: grps.append((cur[0],cur[1],cur[2]))
                                for nm, ll, rl in grps:
                                    results.append({"name":nm or "","loi_ich":" ".join(ll).strip(),"rui_ro":" ".join(rl).strip()})
                            elif has_number:
                                parts = re.split(r"\(\d+\)\s*", text)
                                for p in [x.strip() for x in parts if x.strip()]:
                                    if not re.search(r"[Ll]ợi\s*[Íí]ch|[Rr]ủi\s*[Rr]o", p): continue
                                    ci2 = p.find(":"); nm=p[:ci2].strip() if ci2>0 else ""; body=p[ci2+1:].strip() if ci2>0 else p
                                    if not body.strip(): continue
                                    lm2 = re.search(r"[Ll]ợi\s*[Íí]ch\s*:\s*(.*?)(?=\s*[Rr]ủi\s*[Rr]o\s*:|$)",body,re.DOTALL)
                                    rm2 = re.search(r"[Rr]ủi\s*[Rr]o\s*:\s*(.*?)$",body,re.DOTALL)
                                    li = lm2.group(1).strip() if lm2 else body
                                    ri = rm2.group(1).strip() if rm2 else ""
                                    results.append({"name":nm,"loi_ich":li,"rui_ro":ri})
                            return results
                        sh_groups = _parse_sh(raw_sh)
                        if sh_groups:
                            rendered = True
                            st.markdown(
                                "<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:6px;'>"
                                "<div style='background:#1a4a2e;border-radius:6px 6px 0 0;padding:6px 12px;"
                                "font-size:11px;font-weight:700;color:#56d364;text-transform:uppercase;text-align:center;'>"
                                "✅ Lợi ích</div>"
                                "<div style='background:#4a1a1a;border-radius:6px 6px 0 0;padding:6px 12px;"
                                "font-size:11px;font-weight:700;color:#f85149;text-transform:uppercase;text-align:center;'>"
                                "⚠️ Rủi ro</div></div>",
                                unsafe_allow_html=True)
                            for g in sh_groups:
                                if g["name"]:
                                    st.markdown(
                                        f"<div style='background:#161b22;border:1px solid #30363d;border-radius:6px;"
                                        f"padding:6px 14px;margin:8px 0 4px 0;font-size:12px;font-weight:700;"
                                        f"color:#79c0ff;'>📌 {g['name']}</div>", unsafe_allow_html=True)
                                cl2, cr2 = st.columns(2)
                                with cl2:
                                    li_txt = g["loi_ich"] or "<span style='color:#484f58;font-style:italic;'>—</span>"
                                    st.markdown(
                                        f"<div style='background:#0d2818;border:1px solid #238636;border-radius:0 0 6px 6px;"
                                        f"padding:10px 14px;min-height:60px;'>"
                                        f"<span style='font-size:13px;color:#aff5b4;line-height:1.7;'>{li_txt}</span></div>",
                                        unsafe_allow_html=True)
                                with cr2:
                                    ri_txt = g["rui_ro"] or "<span style='color:#484f58;font-style:italic;'>—</span>"
                                    st.markdown(
                                        f"<div style='background:#2d0f0f;border:1px solid #b62324;border-radius:0 0 6px 6px;"
                                        f"padding:10px 14px;min-height:60px;'>"
                                        f"<span style='font-size:13px;color:#ffa198;line-height:1.7;'>{ri_txt}</span></div>",
                                        unsafe_allow_html=True)
                    except Exception:
                        rendered = False
                    if not rendered:
                        st.markdown(raw_sh)
                    st.markdown(
                        "<div class='info-block-label' style='margin-top:20px;border-left:3px solid #3fb950;"
                        "padding-left:8px;'>📈 Dự báo xu hướng</div>", unsafe_allow_html=True)
                    st.markdown(row.get("Dự báo",""))
                with ta:
                    st.markdown(
                        "<div class='info-block-label' style='border-left:3px solid #f85149;padding-left:8px;'>"
                        "🚀 Đề xuất Hành động PMC</div>", unsafe_allow_html=True)
                    st.markdown(row.get("Đề xuất Hành động",""))

            st.markdown(
                f"<a href='{row.get('Link','#')}' target='_blank' class='news-link' "
                f"style='display:block;margin:-8px 0 16px 0;padding:0 4px;'>"
                f"🔗 Đọc bản tin gốc ➔</a>", unsafe_allow_html=True)

        # Pagination bar
        st.markdown("<br>", unsafe_allow_html=True)

        def _get_page_range(cur, total, window=2):
            pages = set([1, total])
            for i in range(max(1, cur-window), min(total+1, cur+window+1)):
                pages.add(i)
            return sorted(pages)

        page_range = _get_page_range(page, total_pg)
        pg_cols = st.columns([1.2] + [0.6]*len(page_range) + [0.8, 1.2])

        with pg_cols[0]:
            if st.button("⏮ Đầu", use_container_width=True, disabled=(page==1), key="pg_first"):
                st.session_state.feed_page = 1; st.rerun()

        prev_shown = None
        for ci, pn in enumerate(page_range):
            with pg_cols[ci+1]:
                if prev_shown is not None and pn - prev_shown > 1:
                    st.markdown("<div style='text-align:center;color:#484f58;line-height:38px;'>…</div>",
                                unsafe_allow_html=True)
                else:
                    is_cur   = (pn == page)
                    btn_type = "primary" if is_cur else "secondary"
                    label    = f"**{pn}**" if is_cur else str(pn)
                    if st.button(label, key=f"pg_n{pn}", use_container_width=True, type=btn_type):
                        st.session_state.feed_page = pn; st.rerun()
            prev_shown = pn

        with pg_cols[-2]:
            if st.button("Tiếp ▶", use_container_width=True, disabled=(page==total_pg), key="pg_next"):
                st.session_state.feed_page = min(total_pg, page+1); st.rerun()
        with pg_cols[-1]:
            if st.button("Cuối ⏭", use_container_width=True, disabled=(page==total_pg), key="pg_last"):
                st.session_state.feed_page = total_pg; st.rerun()

        st.markdown(
            f"<p style='text-align:center;color:#7d8590;font-size:12px;margin-top:4px;'>"
            f"Trang <b style='color:#58a6ff;'>{page}</b> / {total_pg} · {len(dd)} bài</p>",
            unsafe_allow_html=True)

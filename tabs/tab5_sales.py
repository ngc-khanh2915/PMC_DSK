import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import LOAI_CLR, ACCENT, FONT_COLOR, dark, build_lead_agg


def render(dff):
    st.markdown("""
    <div style='background:#0d2040;border:1px solid #1f6feb44;border-radius:8px;
         padding:12px 16px;margin-bottom:12px;'>
      <span style='color:#58a6ff;font-weight:700;font-size:13px;'>🤖 Sales Intelligence Hub</span>
      <span style='color:#7d8590;font-size:12px;'> — Lead Pipeline ưu tiên · Phân vùng sale · Xuất dữ liệu AI Agent</span>
    </div>""", unsafe_allow_html=True)

    view_col, _ = st.columns([2,3])
    with view_col:
        view_mode = st.radio("Chế độ xem",
            ["📋 Lead Pipeline","📊 Executive View","🤖 AI Agent Export"],
            horizontal=True, key="sl_view_mode")

    sl1, sl2, sl3, sl4 = st.columns(4)
    _vung_map = {
        "Tất cả": [],
        "Miền Bắc": ["Hà Nội","Tuyên Quang","Lào Cai","Thái Nguyên","Phú Thọ",
                     "Bắc Ninh","Hưng Yên","Hải Phòng","Ninh Bình","Lai Châu",
                     "Điện Biên","Sơn La","Lạng Sơn","Quảng Ninh","Thanh Hóa","Cao Bằng"],
        "Miền Trung": ["Nghệ An","Hà Tĩnh","Quảng Trị","Huế","Đà Nẵng",
                       "Quảng Ngãi","Gia Lai","Khánh Hòa","Lâm Đồng","Đắk Lắk"],
        "Miền Nam": ["TP.HCM","Đồng Nai","Tây Ninh","Cần Thơ","Vĩnh Long",
                     "Đồng Tháp","Cà Mau","An Giang"],
    }
    with sl1:
        sel_intent = st.selectbox("🎯 Giai đoạn ưu tiên",
            ["Tất cả","Chuẩn bị đầu tư","Xây dựng","Nghiệm thu & Bàn giao","Vận hành"],
            key="sl_intent")
    with sl2:
        VALID_LOAI_S = ["Tất cả","BĐS Công nghiệp / KCN","Data Center / IDC",
                        "Khu phức hợp","Chung cư","Nhà ở Xã hội","Nghỉ dưỡng",
                        "Văn phòng / Thương mại","Trường học","Bệnh viện / Y tế",
                        "Công trình công cộng","BĐS Khác"]
        sel_loai_s = st.selectbox("🏢 Dòng BĐS", VALID_LOAI_S, key="sl_loai")
    with sl3:
        sel_vung = st.selectbox("📍 Vùng miền", list(_vung_map.keys()), key="sl_vung")
    with sl4:
        sel_hot_only = st.checkbox("🔥 Chỉ HOT", value=False, key="sl_hot")

    # Build lead data
    lead_base = dff.copy()
    if sel_intent != "Tất cả":
        lead_base = lead_base[lead_base["Vòng đời"] == sel_intent]
    if sel_loai_s != "Tất cả":
        lead_base = lead_base[lead_base["Loại hình BĐS"] == sel_loai_s]
    if sel_vung != "Tất cả":
        tinh_list = _vung_map[sel_vung]
        lead_base = lead_base[lead_base["Tỉnh Thành"].apply(
            lambda x: str(x).strip() in tinh_list)]
    if sel_hot_only:
        lead_base = lead_base[lead_base["Is_Hot"]]

    lead_agg = build_lead_agg(lead_base)

    # Metric row
    m1, m2, m3, m4 = st.columns(4)
    for col, label, val, color in [
        (m1, "Tổng Lead",     len(lead_agg),                        "#1f6feb"),
        (m2, "HOT Lead",      lead_agg["Is_Hot"].sum() if not lead_agg.empty else 0, "#f85149"),
        (m3, "In-Market Now", (lead_agg["VD"]=="Chuẩn bị đầu tư").sum() if not lead_agg.empty else 0, "#3fb950"),
        (m4, "Tỉnh/TP",      lead_base[lead_base["Tỉnh Thành"]!=""]["Tỉnh Thành"].nunique(), "#f0b429"),
    ]:
        with col:
            st.markdown(
                f"<div style='background:#161b22;border:1px solid {color}44;"
                f"border-top:3px solid {color};border-radius:8px;padding:12px;text-align:center;'>"
                f"<div style='font-size:24px;font-weight:800;color:{color};'>{val}</div>"
                f"<div style='font-size:10px;color:#7d8590;text-transform:uppercase;'>{label}</div>"
                f"</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Executive View ────────────────────────────────────────────
    if view_mode == "📊 Executive View":
        st.markdown("<div class='chart-title'>Bức tranh Lead tổng thể</div>",
                    unsafe_allow_html=True)
        if not lead_agg.empty:
            ex1, ex2 = st.columns(2)
            with ex1:
                loai_cnt = lead_agg.groupby("Loai")["Cnt"].sum().reset_index().sort_values("Cnt", ascending=True)
                fig_ex = px.bar(loai_cnt, y="Loai", x="Cnt", orientation="h",
                                color="Cnt", color_continuous_scale=[[0,"#1f4e8c"],[1,"#58a6ff"]],
                                text_auto=True, labels={"Loai":"","Cnt":"Lần nhắc"})
                dark(fig_ex, legend=False)
                fig_ex.update_layout(height=280, coloraxis_showscale=False,
                    title=dict(text="Lead theo Dòng BĐS", font=dict(color="#7d8590", size=11)))
                st.plotly_chart(fig_ex, use_container_width=True)
            with ex2:
                def _get_vung(tinh):
                    t = str(tinh).strip()
                    for v, tl in _vung_map.items():
                        if v == "Tất cả": continue
                        if t in tl: return v
                    return "Khác"
                lead_agg["Vung"] = lead_agg["Tinh"].apply(_get_vung)
                vung_cnt = lead_agg.groupby("Vung").agg(So_lead=("Dự án","count")).reset_index()
                fig_vung = px.bar(vung_cnt, x="Vung", y="So_lead", color="Vung",
                                  color_discrete_map={"Miền Bắc":"#2563EB","Miền Trung":"#16A34A",
                                                      "Miền Nam":"#D97706","Khác":"#9CA3AF"},
                                  text_auto=True, labels={"So_lead":"Số lead","Vung":""})
                dark(fig_vung, legend=False)
                fig_vung.update_layout(height=280,
                    title=dict(text="Lead theo Vùng miền", font=dict(color="#7d8590", size=11)))
                st.plotly_chart(fig_vung, use_container_width=True)

            st.markdown("<div class='chart-title'>Top 10 Lead — Priority Score cao nhất</div>",
                        unsafe_allow_html=True)
            for rank, (_, row) in enumerate(lead_agg.head(10).iterrows(), 1):
                hot_mk  = "🔥 " if row["Is_Hot"] else ""
                vd_color = "#3fb950" if row["VD"] == "Chuẩn bị đầu tư" else "#7d8590"
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;padding:6px 12px;"
                    f"background:#161b22;border-radius:6px;margin-bottom:4px;"
                    f"border-left:3px solid #1f6feb;'>"
                    f"<span style='font-family:JetBrains Mono;font-size:14px;color:#484f58;"
                    f"font-weight:700;min-width:24px;'>#{rank}</span>"
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:13px;font-weight:600;color:#e6edf3;'>"
                    f"{hot_mk}{str(row['Dự án'])[:50]}</div>"
                    f"<div style='font-size:10px;color:#7d8590;'>{row['Loai']} · "
                    f"📍{str(row['Tinh']).split(',')[0]} · "
                    f"<span style='color:{vd_color};'>{row['VD']}</span></div></div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-family:JetBrains Mono;font-size:16px;font-weight:700;"
                    f"color:#58a6ff;'>{int(row['Priority'])}</div>"
                    f"<div style='font-size:9px;color:#484f58;'>PRIORITY</div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

    # ── AI Agent Export ───────────────────────────────────────────
    elif view_mode == "🤖 AI Agent Export":
        st.markdown("<div class='chart-title'>Xuất dữ liệu có cấu trúc cho AI Agent</div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#1a0d40;border:1px solid #6e40c944;border-radius:6px;"
            "padding:10px 14px;margin-bottom:12px;font-size:12px;color:#d2a8ff;'>"
            "<b>Hướng dẫn:</b> 1. Xuất Excel → Upload vào AI Agent làm input · "
            "2. Priority Score xác định thứ tự tiếp cận · "
            "3. In_Market=YES → tiếp cận ngay</div>",
            unsafe_allow_html=True)
        if not lead_agg.empty:
            preview_df = lead_agg[["Dự án","Loai","Tinh","VD","CDT","SK","Priority","Cnt","Action_BD"]].head(20).copy()
            preview_df.columns = ["Dự án","Loại hình","Tỉnh/TP","Vòng đời","Chủ đầu tư",
                                   "Điểm SK","Priority","Số lần","Action BD"]
            st.dataframe(preview_df, use_container_width=True, height=380,
                         column_config={
                             "Priority": st.column_config.NumberColumn(format="%d"),
                             "Điểm SK":  st.column_config.NumberColumn(format="%.1f"),
                         })
            exp1, exp2 = st.columns(2)
            with exp1:
                buf_ai = io.BytesIO()
                export_ai = lead_agg.copy()
                export_ai["In_Market"] = (export_ai["VD"]=="Chuẩn bị đầu tư").map({True:"YES",False:""})
                export_ai["HOT"]       = export_ai["Is_Hot"].map({True:"HOT",False:""})
                export_ai2 = export_ai[["Dự án","Loai","Tinh","VD","CDT","SK","Priority",
                                         "Cnt","In_Market","HOT","Action_BD"]].copy()
                export_ai2.columns = ["Du_An","Loai_Hinh","Tinh_TP","Vong_Doi","Chu_Dau_Tu",
                                       "Diem_SK","Priority","So_Lan","In_Market","HOT","Action_BD"]
                with pd.ExcelWriter(buf_ai, engine="openpyxl") as writer:
                    export_ai2.to_excel(writer, index=False, sheet_name="AI_Agent_Leads")
                st.download_button(
                    "📥 Xuất Excel cho AI Agent", data=buf_ai.getvalue(),
                    file_name=f"PMC_AI_Leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, type="primary")
            with exp2:
                st.download_button(
                    "📄 Xuất CSV (API input)",
                    data=export_ai2.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name=f"PMC_AI_Leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True)

    # ── Lead Pipeline ─────────────────────────────────────────────
    else:
        sale_l, sale_r = st.columns([3, 1])
        with sale_r:
            st.markdown("<div class='chart-title'>Phân vùng Lead</div>", unsafe_allow_html=True)
            if not lead_base.empty:
                for vung, tinhlist in {k: v for k, v in _vung_map.items() if k != "Tất cả"}.items():
                    cnt   = lead_base["Tỉnh Thành"].apply(lambda x: any(t in str(x) for t in tinhlist)).sum()
                    pct   = int(cnt / max(len(lead_base), 1) * 100)
                    color = {"Miền Bắc":"#2563EB","Miền Trung":"#16A34A","Miền Nam":"#D97706"}.get(vung,"#9CA3AF")
                    st.markdown(
                        f"<div style='margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
                        f"<span style='font-size:12px;color:#c9d1d9;font-weight:600;'>{vung}</span>"
                        f"<span style='font-family:JetBrains Mono;font-size:12px;color:{color};'>{cnt}</span></div>"
                        f"<div style='background:#21262d;border-radius:3px;height:6px;'>"
                        f"<div style='background:{color};width:{pct}%;height:6px;border-radius:3px;'></div>"
                        f"</div></div>", unsafe_allow_html=True)
            st.markdown("<br><div class='chart-title'>Xuất dữ liệu AI Agent</div>",
                        unsafe_allow_html=True)
            if not lead_agg.empty:
                export_s = lead_agg[["Dự án","Loai","Tinh","VD","CDT","SK","Priority","Cnt"]].copy()
                export_s.columns = ["Du_An","Loai_Hinh","Tinh_TP","Vong_Doi","Chu_Dau_Tu",
                                     "Diem_SK","Priority","So_Lan"]
                buf_s = io.BytesIO()
                with pd.ExcelWriter(buf_s, engine="openpyxl") as writer:
                    export_s.to_excel(writer, index=False, sheet_name="Sales_Leads")
                st.download_button(
                    "📥 Xuất Lead List", data=buf_s.getvalue(),
                    file_name=f"PMC_Leads_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
                st.caption(f"{len(export_s)} leads · Sorted by Priority")

        with sale_l:
            st.markdown(
                "<div class='chart-title'>Lead Pipeline — Ưu tiên tiếp cận theo Priority Score</div>",
                unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:11px;color:#7d8590;margin-bottom:8px;'>"
                "Priority = HOT(+10) + Chuẩn bị đầu tư(+5) + Điểm SK + Số lần nhắc"
                " · <span style='color:#3fb950;font-weight:600;'>In-Market Now</span>"
                " = đang Chuẩn bị đầu tư</div>", unsafe_allow_html=True)

            if lead_agg.empty:
                st.info("Chưa có lead phù hợp. Điều chỉnh bộ lọc.")
            else:
                VD_BADGE = {
                    "Chuẩn bị đầu tư":       ("#3fb950","IN-MARKET"),
                    "Xây dựng":               ("#f0b429","BUILDING"),
                    "Nghiệm thu & Bàn giao":  ("#79c0ff","HANDOVER"),
                    "Vận hành":               ("#484f58","OPS"),
                }
                PPG_S = 15
                total_pg_s = max(1, (len(lead_agg)-1)//PPG_S+1)
                if "sl_page" not in st.session_state: st.session_state.sl_page = 1
                sig_s = f"{sel_intent}_{sel_loai_s}_{sel_vung}_{sel_hot_only}_{len(lead_agg)}"
                if st.session_state.get("sl_sig") != sig_s:
                    st.session_state.sl_page = 1
                    st.session_state.sl_sig = sig_s
                cur_pg_s = st.session_state.sl_page

                for _, row in lead_agg.iloc[(cur_pg_s-1)*PPG_S : cur_pg_s*PPG_S].iterrows():
                    loai_s = str(row["Loai"])
                    clr_s  = LOAI_CLR.get(loai_s, "#484f58")
                    vd_s   = str(row["VD"])
                    vd_b, vd_lbl = VD_BADGE.get(vd_s, ("#484f58",""))
                    hot_s  = row["Is_Hot"]
                    sk_s   = row["SK"]
                    sk_col = "#3fb950" if sk_s > 2 else "#f85149" if sk_s < -2 else "#7d8590"
                    tinh_s = str(row["Tinh"]).split(",")[0]
                    cdt_s  = str(row["CDT"])[:28] if str(row["CDT"]) not in ["Không áp dụng","","Chưa có thông tin"] else ""
                    action_s = str(row["Action_BD"]).replace("High","").replace("Medium","").replace("Low","").strip()
                    action_s = action_s[:60] if len(action_s) > 5 else ""
                    pri_s  = row["Priority"]
                    try:
                        ngay_val  = pd.Timestamp(row["Ngay"])
                        ngay_str  = ngay_val.strftime("%d/%m/%Y")
                        delta     = (datetime.now().date() - ngay_val.date()).days
                        ago_str   = "Hôm nay" if delta == 0 else "Hôm qua" if delta == 1 else f"{delta} ngày trước"
                        ngay_disp = f"🕒 {ngay_str} · {ago_str}"
                    except Exception:
                        ngay_disp = ""

                    html_s = (
                        f"<div style='display:flex;align-items:stretch;gap:0;margin-bottom:6px;"
                        f"background:#161b22;border-radius:8px;overflow:hidden;"
                        f"border:1px solid {'#f85149' if hot_s else '#21262d'};'>"
                        f"<div style='background:{clr_s}22;border-right:1px solid {clr_s}44;"
                        f"padding:8px 10px;display:flex;flex-direction:column;align-items:center;"
                        f"justify-content:center;min-width:52px;'>"
                        f"<div style='font-family:JetBrains Mono;font-size:16px;font-weight:800;color:{clr_s};'>"
                        f"{int(pri_s)}</div>"
                        f"<div style='font-size:8px;color:#484f58;text-transform:uppercase;'>PRIORITY</div>"
                        f"</div>"
                        f"<div style='flex:1;padding:8px 12px;'>"
                        f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:4px;'>"
                        + ("🔥 " if hot_s else "") +
                        f"<span style='font-size:13px;font-weight:700;color:#e6edf3;'>"
                        f"{str(row['Dự án'])[:50]}</span></div>"
                        f"<div style='display:flex;gap:6px;flex-wrap:wrap;align-items:center;'>"
                        f"<span style='font-size:10px;color:{clr_s};'>{loai_s}</span>"
                        f"<span style='font-size:10px;color:#7d8590;'>· 📍{tinh_s}</span>"
                    )
                    if cdt_s: html_s += f"<span style='font-size:10px;color:#7d8590;'>· 👑{cdt_s}</span>"
                    if vd_lbl:
                        html_s += (f"<span style='background:{vd_b}22;border:1px solid {vd_b}55;"
                                   f"color:{vd_b};font-size:9px;font-weight:700;"
                                   f"padding:1px 5px;border-radius:3px;'>{vd_lbl}</span>")
                    html_s += "</div>"
                    if action_s: html_s += f"<div style='font-size:11px;color:#7d8590;margin-top:4px;'>📋 {action_s}</div>"
                    if ngay_disp: html_s += f"<div style='font-size:10px;color:#484f58;margin-top:3px;'>{ngay_disp}</div>"
                    html_s += (
                        f"</div>"
                        f"<div style='padding:8px 12px;text-align:right;display:flex;"
                        f"flex-direction:column;justify-content:center;gap:4px;min-width:60px;'>"
                        f"<span style='font-family:JetBrains Mono;font-size:11px;color:#58a6ff;'>"
                        f"{row['Cnt']}x</span>"
                        f"<span style='font-family:JetBrains Mono;font-size:11px;color:{sk_col};'>"
                        f"SK:{sk_s:+.1f}</span></div></div>"
                    )
                    st.markdown(html_s, unsafe_allow_html=True)

                if total_pg_s > 1:
                    psp1, psp2, psp3 = st.columns([1,2,1])
                    with psp1:
                        if st.button("◀ Trước", key="sl_prev", disabled=(cur_pg_s==1)):
                            st.session_state.sl_page = max(1, cur_pg_s-1); st.rerun()
                    with psp2:
                        st.markdown(
                            f"<div style='text-align:center;color:#7d8590;font-size:12px;padding:6px 0;'>"
                            f"Trang <b style='color:#58a6ff;'>{cur_pg_s}</b>/{total_pg_s} · "
                            f"{len(lead_agg)} leads</div>", unsafe_allow_html=True)
                    with psp3:
                        if st.button("Tiếp ▶", key="sl_next", disabled=(cur_pg_s==total_pg_s)):
                            st.session_state.sl_page = min(total_pg_s, cur_pg_s+1); st.rerun()

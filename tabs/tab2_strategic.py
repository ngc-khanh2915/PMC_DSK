import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import color_map_evt, ACCENT, FONT_COLOR, dark, load_macro, chg_color


def render(dff, df_te):
    c1, c2, c3 = st.columns([1.2, 1.4, 1.0])

    # Event donut
    with c1:
        st.markdown(
            "<div class='chart-title'>Nhóm Sự kiện — Xung lực thị trường (nhấp để lọc)</div>",
            unsafe_allow_html=True)
        evt = dff["Nhóm Sự kiện"].value_counts().reset_index()
        evt.columns = ["Sự kiện", "Số lượng"]
        total_e = evt["Số lượng"].sum()
        fig = go.Figure(go.Pie(
            labels=evt["Sự kiện"], values=evt["Số lượng"], hole=0.60,
            marker_colors=[color_map_evt.get(s, "#484f58") for s in evt["Sự kiện"]],
            textinfo="percent", textfont_size=12,
            hovertemplate="<b>%{label}</b><br>%{value} · %{percent}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{total_e}</b><br>Sự kiện", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=20, color="#1A2340"))
        dark(fig, legend=True)
        fig.update_layout(height=420,
                          legend=dict(orientation="h", x=0, y=-0.12,
                                      font=dict(size=11, color=FONT_COLOR), itemwidth=80))
        sel_e = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="donut_evt")
        if sel_e and sel_e.get("selection", {}).get("points"):
            clicked = sel_e["selection"]["points"][0].get("label")
            if clicked and clicked != st.session_state.chart_filter_evt:
                st.session_state.chart_filter_evt = clicked
                st.rerun()

    # Stacked bar: type × lifecycle
    with c2:
        st.markdown(
            "<div class='chart-title'>Loại hình BĐS × Vòng đời (nhấp để lọc)</div>",
            unsafe_allow_html=True)
        ds = df_te[~df_te["Loại hình BĐS"].isin([
            "Chưa có thông tin","Bất động sản khác","Khác","","Không áp dụng","BĐS Khác"
        ])]
        ds = ds[~ds["Vòng đời"].isin(["Chưa xác định","Chưa có thông tin","","Không áp dụng"])]
        if not ds.empty:
            sd = ds.groupby(["Loại hình BĐS","Vòng đời"]).size().reset_index(name="Số lượng")
            fig = px.bar(sd, y="Loại hình BĐS", x="Số lượng", color="Vòng đời",
                         orientation="h", barmode="stack",
                         color_discrete_sequence=ACCENT, text_auto=True)
            dark(fig)
            fig.update_layout(height=420, yaxis_title=None, xaxis_title=None,
                              margin=dict(t=10,b=10,l=10,r=10),
                              legend=dict(orientation="h", x=0, y=-0.15,
                                          font=dict(size=10, color=FONT_COLOR),
                                          bgcolor="rgba(0,0,0,0)"))
            fig.update_traces(textfont_size=10)
            sel_t = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="bar_type")
            if sel_t and sel_t.get("selection", {}).get("points"):
                clicked = sel_t["selection"]["points"][0].get("y")
                if clicked and clicked != st.session_state.chart_filter_type:
                    st.session_state.chart_filter_type = clicked
                    st.rerun()
        else:
            st.info("Chưa đủ dữ liệu.")

    # Macro panel
    with c3:
        st.markdown("<div class='chart-title'>Chỉ số Kinh tế Vĩ mô</div>", unsafe_allow_html=True)
        macro = load_macro()

        def _macro_card(label, icon, key, fmt_fn, url=None):
            d = macro.get(key, {})
            val, chg, ok, static, note = (
                d.get("value"), d.get("change", 0),
                d.get("ok", False), d.get("static", False), d.get("note", ""),
            )
            color, chg_str = chg_color(chg)
            val_str = fmt_fn(val) if ok and val is not None else "N/A"
            chg_html = (f"<span style='font-size:11px;color:{color};'>"
                        f"{chg_str if not static else note}</span>")
            link_html = (f"<a href='{url}' target='_blank' style='font-size:9px;color:#484f58;"
                         f"text-decoration:none;'>↗ Nguồn</a>" if url else "")
            return (
                f"<div style='background:#0d1117;border:1px solid #21262d;border-radius:8px;"
                f"padding:10px 12px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                f"<div><div style='font-size:10px;color:#7d8590;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:.6px;margin-bottom:3px;'>{icon} {label}</div>"
                f"<div style='font-family:JetBrains Mono;font-size:18px;font-weight:700;"
                f"color:#e6edf3;line-height:1;'>{val_str}</div>{chg_html}</div>"
                f"<div style='text-align:right;'>{link_html}</div></div></div>"
            )

        st.markdown("<div style='max-height:420px;overflow-y:auto;padding-right:4px;'>",
                    unsafe_allow_html=True)
        for grp_label, cards in [
            ("💳 Tín dụng", [
                ("LS Cho vay mua nhà", "🏠", "nhnn_cv",  lambda v: f"{v:.2f}%/năm",   "https://www.sbv.gov.vn"),
                ("Tăng trưởng TD BĐS", "📈", "tdung_bds", lambda v: f"{v:.1f}% YoY", "https://www.sbv.gov.vn"),
            ]),
            ("📊 Tăng trưởng & Lạm phát", [
                ("GDP Tăng trưởng", "🇻🇳", "gdp", lambda v: f"{v:.2f}% YoY", "https://www.gso.gov.vn"),
                ("CPI Nội địa",     "🛒",  "cpi", lambda v: f"{v:.2f}% YoY", "https://www.gso.gov.vn"),
            ]),
            ("💹 Dòng vốn", [
                ("FDI Giải ngân YTD", "💹", "fdi",    lambda v: f"${v:.2f}B",      "https://www.mpi.gov.vn"),
                ("Tỷ giá USD/VND",    "💵", "usdvnd", lambda v: f"{v:,.0f} ₫", "https://finance.yahoo.com/quote/USDVND%3DX"),
            ]),
            ("⚙️ Chi phí & Thị trường", [
                ("Giá Điện TB", "⚡", "gia_dien", lambda v: f"{v:,.0f} đ/kWh", "https://www.evn.com.vn"),
                ("VN-Index",    "📉", "vnindex",  lambda v: f"{v:,.0f} điểm",  "https://finance.yahoo.com/quote/%5EVNINDEX"),
            ]),
        ]:
            st.markdown(
                f"<div style='font-size:10px;color:#484f58;text-transform:uppercase;"
                f"letter-spacing:.5px;padding:4px 0 2px 0;'>{grp_label}</div>",
                unsafe_allow_html=True)
            for args in cards:
                st.markdown(_macro_card(*args), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Nhóm tin + Source stats
    st.markdown("<br><div class='chart-title'>Phân bổ 3 Nhóm Tin & Thống kê Nguồn</div>",
                unsafe_allow_html=True)
    col_n, col_s = st.columns([1, 2])
    with col_n:
        nhom_counts = dff["Nhóm Tin"].value_counts().reset_index()
        nhom_counts.columns = ["Nhóm", "Số lượng"]
        fig = px.bar(nhom_counts, x="Nhóm", y="Số lượng", color="Nhóm",
                     color_discrete_map={
                         "Nhóm 1 - Trực tiếp":    "#58a6ff",
                         "Nhóm 2 - Gián tiếp":    "#3fb950",
                         "Nhóm 3 - Cảnh báo sớm": "#f0b429",
                     }, text_auto=True)
        dark(fig, legend=False)
        fig.update_layout(height=220, xaxis_title=None, yaxis_title=None,
                          xaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)
    with col_s:
        sc = dff["Đầu Báo"].value_counts().reset_index()
        sc.columns = ["Nguồn", "Số lượng"]
        mx = sc["Số lượng"].max()
        cols_s = st.columns(3)
        for i, (_, r) in enumerate(sc.iterrows()):
            pct = int(r["Số lượng"] / mx * 100)
            with cols_s[i % 3]:
                st.markdown(
                    f"<div style='background:#0d1117;border:1px solid #21262d;border-radius:6px;"
                    f"padding:8px 12px;margin-bottom:5px;'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:5px;'>"
                    f"<span style='font-size:12px;color:#c9d1d9;font-weight:500;'>{r['Nguồn']}</span>"
                    f"<span style='font-family:JetBrains Mono;font-size:12px;color:#58a6ff;font-weight:600;'>"
                    f"{r['Số lượng']}</span></div>"
                    f"<div style='background:#21262d;border-radius:3px;height:3px;'>"
                    f"<div style='background:linear-gradient(90deg,#1f6feb,#58a6ff);width:{pct}%;"
                    f"height:3px;border-radius:3px;'></div></div></div>",
                    unsafe_allow_html=True)

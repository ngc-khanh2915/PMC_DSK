import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import dark, FONT_COLOR, ACCENT


def render(dff, df_te, dg):
    cl, cr = st.columns(2)

    # Geo treemap
    with cl:
        st.markdown("<div class='chart-title'>Phân bố Địa lý — Mật độ Dự án (nhấp để lọc)</div>",
                    unsafe_allow_html=True)
        if not dg.empty:
            gc = dg["Tỉnh Thành"].value_counts().reset_index()
            gc.columns = ["Tỉnh Thành", "Số lượng"]
            fig = px.treemap(gc, path=["Tỉnh Thành"], values="Số lượng",
                             color="Số lượng",
                             color_continuous_scale=[[0,"#0d1117"],[0.4,"#1f6feb"],[1.0,"#58a6ff"]])
            dark(fig, legend=False)
            fig.update_layout(height=300)
            fig.update_traces(textfont=dict(size=13, color="white"),
                              hovertemplate="<b>%{label}</b><br>%{value} tin<extra></extra>")
            sel_g = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="treemap_geo")
            if sel_g and sel_g.get("selection", {}).get("points"):
                clicked = sel_g["selection"]["points"][0].get("label")
                if clicked and clicked != st.session_state.chart_filter_geo:
                    st.session_state.chart_filter_geo = clicked
                    st.rerun()
        else:
            st.info("Không có dữ liệu địa lý.")

    # Lifecycle funnel
    with cr:
        st.markdown("<div class='chart-title'>Dòng chảy Dự án — Project Lifecycle Funnel</div>",
                    unsafe_allow_html=True)
        lc_order = ["Chuẩn bị đầu tư", "Xây dựng", "Nghiệm thu & Bàn giao", "Vận hành"]
        lc_vals  = [dff["Vòng đời"].value_counts().get(s, 0) for s in lc_order]
        fig = go.Figure(go.Funnel(
            y=lc_order, x=lc_vals, textinfo="value+percent initial",
            marker=dict(color=["#1f6feb","#388bfd","#f0b429","#79c0ff"],
                        line=dict(width=1, color="#0d1117")),
            connector=dict(line=dict(color="#21262d", width=2)),
            textfont=dict(color="white", size=13),
        ))
        dark(fig, legend=False)
        fig.update_layout(height=300, yaxis=dict(tickfont=dict(color=FONT_COLOR, size=12)))
        st.plotly_chart(fig, use_container_width=True)
        nghiem_thu = dff["Vòng đời"].value_counts().get("Nghiệm thu & Bàn giao", 0)
        tong_vd = dff[~dff["Vòng đời"].isin(["Không áp dụng","","Chưa xác định"])]["Vòng đời"].count()
        if tong_vd > 0 and nghiem_thu / tong_vd < 0.20:
            st.markdown(
                f"<div style='background:#2d1f00;border:1px solid #f0b429;border-left:3px solid #f0b429;"
                f"border-radius:6px;padding:8px 14px;'>"
                f"<span style='font-size:11px;color:#f0b429;font-weight:700;'>⚠ BOTTLENECK:</span>"
                f"<span style='font-size:12px;color:#f0e3a0;'> Nghiệm thu & Bàn giao chỉ "
                f"{nghiem_thu/tong_vd*100:.0f}% — thị trường đang ách tắc.</span></div>",
                unsafe_allow_html=True,
            )

    # Top projects + developers
    st.markdown("<br>", unsafe_allow_html=True)
    col_proj, col_cdt = st.columns(2)

    with col_proj:
        st.markdown("<div class='chart-title'>Top 15 Dự án được nhắc đến nhiều nhất</div>",
                    unsafe_allow_html=True)
        JUNK_DA = [
            "", "Chưa có thông tin", "Không áp dụng", "0", "Không có",
            "Không rõ", "Chưa xác định", "N/A", "Không xác định",
            "Không liên quan", "Không", "None", "nan", "Nhiều dự án",
            "Chưa có", "Thị trường Chứng khoán Việt Nam",
            "Thị trường Bất động sản Việt Nam", "Toàn quốc",
            "Thị trường", "Thị trường BĐS", "Nhiều dự án bất động sản",
            "Nhiều dự án", "Các dự án bất động sản",
            "Hội nghị xúc tiến đầu tư",
            "Tập đoàn Hóa chất Đức Giang",
            "Hội nghị xúc tiến đầu tư Gia Lai 2026",
        ]
        JUNK_DA_PATTERNS = [
            "hội nghị", "diễn đàn", "hội thảo", "tập đoàn hóa chất",
            "nhiều dự án", "các dự án của", "thị trường chứng khoán",
        ]
        dp = dff[~dff["Dự án"].isin(JUNK_DA)].copy()
        dp = dp[dp["Dự án"].str.len() > 5]
        dp = dp[~dp["Dự án"].str.lower().str.startswith(("không","chưa","n/a","none","nan"))]
        dp = dp[dp["Dự án"].str.lower().apply(
            lambda x: not any(p in x for p in JUNK_DA_PATTERNS))]

        def _norm_proj(name):
            n = str(name).strip()
            if re.match(r"^\d+\s*[\(\[,]", n): return None
            if re.match(r"^[a-zàáâãèéêìíòóôõùúýăđơư]", n): return None
            if "," in n: return None
            n = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", n).strip()
            if len(n) < 5: return None
            nl = n.lower()
            nl = re.sub(r"sân bay quốc tế\s*", "sân bay ", nl)
            nl = re.sub(r"đường vành đai\s*", "vành đai ", nl)
            nl = re.sub(r"tp\.?\s*hcm|thành phố hồ chí minh|tp\s+hồ chí minh", "tphcm", nl)
            nl = re.sub(r"\bkhu đô thị\s+", "", nl)
            nl = re.sub(r"\bdự án\s+", "", nl)
            nl = re.sub(r"\s+", " ", nl).strip()
            _ORG = [r"^tổng công ty\b", r"^tập đoàn\b", r"^công ty\b",
                    r"^ban quản", r"^ubnd\b", r"^bộ \w", r"^sở \w",
                    r"^ngân hàng\b", r"^hiệp hội\b", r"^hội \w"]
            if any(re.match(p, nl) for p in _ORG): return None
            return nl

        dp["_proj_key"] = dp["Dự án"].apply(_norm_proj)
        dp = dp[dp["_proj_key"].notna()]
        _shortest = dp.groupby("_proj_key")["Dự án"].apply(
            lambda x: min(x, key=len)).to_dict()
        dp["Dự án"] = dp["_proj_key"].map(_shortest)

        if not dp.empty:
            proj_counts = (
                dp.groupby("Dự án")
                .agg(So_lan=("Dự án","count"),
                     Loai_hinh=("Loại hình BĐS","first"),
                     Tinh_Thanh=("Tỉnh Thành","first"))
                .reset_index()
                .sort_values("So_lan", ascending=True)
                .tail(15)
            )
            fig = px.bar(proj_counts, y="Dự án", x="So_lan", orientation="h",
                         color="So_lan",
                         color_continuous_scale=[[0,"#1f4e8c"],[0.5,"#1f6feb"],[1.0,"#58a6ff"]],
                         text_auto=True,
                         hover_data={"Loai_hinh": True, "Tinh_Thanh": True},
                         labels={"So_lan": "Số lần đề cập", "Dự án": ""})
            dark(fig, legend=False)
            fig.update_layout(height=380, coloraxis_showscale=False,
                              yaxis=dict(tickfont=dict(size=11, color=FONT_COLOR)))
            fig.update_traces(textfont=dict(size=11, color="white"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu dự án.")

    with col_cdt:
        st.markdown("<div class='chart-title'>Chủ đầu tư — Tư nhân & Cơ quan Nhà nước</div>",
                    unsafe_allow_html=True)
        JUNK_CDT = [
            "", "Chưa có thông tin", "Không áp dụng", "0", "Không có",
            "Không rõ", "Chưa xác định", "N/A", "Không xác định",
            "Nhiều chủ đầu tư", "Chưa có", "Không", "None", "nan",
            "Công dân", "Người dân", "Cá nhân", "Hộ dân",
            "Không rõ chủ đầu tư",
            "Tập đoàn Hóa chất Đức Giang",
            "Công ty CP Dịch vụ Suất ăn Công nghiệp Hà Nội",
            "Vietnam Airlines", "Vietnam Airlines Group",
            "Saigontourist Group", "Petrovietnam", "Tập đoàn Dầu khí",
        ]
        dc = dff[~dff["Chủ đầu tư"].isin(JUNK_CDT)].copy()
        dc = dc[dc["Chủ đầu tư"].str.len() > 3]
        dc = dc[~dc["Chủ đầu tư"].str.lower().str.startswith(
            ("không","chưa","n/a","none","nan","công dân","người dân"))]
        dc_pr = dc[dc["CĐT_Type"] == "private"]
        dc_gv = dc[dc["CĐT_Type"] == "gov"]

        cdt1, cdt2 = st.columns(2)
        with cdt1:
            st.markdown(
                "<div style='font-size:11px;color:#58a6ff;font-weight:600;margin-bottom:4px;'>"
                "🏢 Tư nhân</div>", unsafe_allow_html=True)
            if not dc_pr.empty:
                ps = (dc_pr.groupby("Chủ đầu tư")
                      .agg(So_lan=("Chủ đầu tư","count"), SK_TB=("Điểm Sức khỏe","mean"))
                      .reset_index()
                      .sort_values("So_lan", ascending=True)
                      .tail(10))
                ps["color"] = ps["SK_TB"].apply(
                    lambda x: "#3fb950" if x > 2 else "#f85149" if x < -2 else "#f0b429")
                fig = go.Figure(go.Bar(
                    y=ps["Chủ đầu tư"], x=ps["So_lan"], orientation="h",
                    marker_color=ps["color"].tolist(),
                    text=ps.apply(lambda r: f"{r['So_lan']}|SK:{r['SK_TB']:+.1f}", axis=1),
                    textposition="inside", textfont=dict(size=9, color="white"),
                    hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
                ))
                dark(fig, legend=False)
                fig.update_layout(height=320, xaxis_title=None,
                                  margin=dict(t=5,b=5,l=5,r=5),
                                  yaxis=dict(tickfont=dict(size=10, color=FONT_COLOR)))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

        with cdt2:
            st.markdown(
                "<div style='font-size:11px;color:#f0b429;font-weight:600;margin-bottom:4px;'>"
                "🏛 Cơ quan Nhà nước</div>", unsafe_allow_html=True)
            if not dc_gv.empty:
                gs = (dc_gv.groupby("Chủ đầu tư")
                      .agg(So_lan=("Chủ đầu tư","count"))
                      .reset_index()
                      .sort_values("So_lan", ascending=True)
                      .tail(10))
                fig = go.Figure(go.Bar(
                    y=gs["Chủ đầu tư"], x=gs["So_lan"], orientation="h",
                    marker_color="#f0b429", text=gs["So_lan"],
                    textposition="inside", textfont=dict(size=9, color="black"),
                    hovertemplate="<b>%{y}</b><br>%{x} lần<extra></extra>",
                ))
                dark(fig, legend=False)
                fig.update_layout(height=320, xaxis_title=None,
                                  margin=dict(t=5,b=5,l=5,r=5),
                                  yaxis=dict(tickfont=dict(size=10, color=FONT_COLOR)))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(
                    "<div style='color:#7d8590;padding:20px;text-align:center;font-size:13px;'>"
                    "Chưa phát hiện cơ quan nhà nước</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:11px;color:#484f58;'>🟢 SK>+2 &nbsp;|&nbsp; "
            "🟡 Trung lập &nbsp;|&nbsp; 🔴 SK<-2</div>", unsafe_allow_html=True)

    # Daily trend
    st.markdown("<br><div class='chart-title'>Xu hướng tin tức theo ngày — Phân loại 3 Nhóm</div>",
                unsafe_allow_html=True)
    if "Chỉ Ngày" in dff.columns:
        trend = dff.groupby(["Chỉ Ngày","Nhóm Tin"]).size().reset_index(name="Số lượng")
        trend["Chỉ Ngày"] = pd.to_datetime(trend["Chỉ Ngày"])
        trend = trend.sort_values("Chỉ Ngày")
        if not trend.empty:
            fig = px.line(trend, x="Chỉ Ngày", y="Số lượng", color="Nhóm Tin", markers=True,
                          color_discrete_map={
                              "Nhóm 1 - Trực tiếp": "#58a6ff",
                              "Nhóm 2 - Gián tiếp": "#3fb950",
                              "Nhóm 3 - Cảnh báo sớm": "#f0b429",
                          },
                          labels={"Chỉ Ngày": "", "Số lượng": "Số tin"})
            dark(fig)
            fig.update_layout(height=250,
                              legend=dict(orientation="h", y=-0.3, x=0,
                                          font=dict(size=11, color=FONT_COLOR)),
                              xaxis=dict(tickformat="%d/%m"))
            fig.update_traces(line=dict(width=2), marker=dict(size=6))
            st.plotly_chart(fig, use_container_width=True)

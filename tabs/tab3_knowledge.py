import pandas as pd
import plotly.express as px
import streamlit as st

from utils import LOAI_CLR, ACCENT, FONT_COLOR, dark


def render(dff, dg):
    k1, k2 = st.columns(2)

    with k1:
        st.markdown("<div class='chart-title'>Bản đồ Dự án — Phân loại theo Dòng BĐS</div>",
                    unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px;color:#7d8590;margin-bottom:8px;'>"
                    "Tất cả dự án xuất hiện trên báo chí · Bức tranh cơ hội thị trường</div>",
                    unsafe_allow_html=True)
        kf1, kf2, kf3 = st.columns(3)
        time_opts_k = {"Tất cả": 0, "7 ngày": 7, "30 ngày": 30, "3 tháng": 90}
        with kf1:
            sel_time_k = st.selectbox("📅 Thời gian", list(time_opts_k.keys()), key="k1_time")
        with kf2:
            VALID_LOAI_K = [
                "Khu phức hợp","Chung cư","Nhà ở Xã hội",
                "BĐS Công nghiệp / KCN","Data Center / IDC",
                "Nghỉ dưỡng","Văn phòng / Thương mại",
                "Trường học","Bệnh viện / Y tế",
                "Công trình công cộng","BĐS Khác",
            ]
            loai_opts_k = ["Tất cả"] + [l for l in VALID_LOAI_K if l in dff["Loại hình BĐS"].values]
            sel_loai_k = st.selectbox("🏢 Dòng BĐS", loai_opts_k, key="k1_loai")
        with kf3:
            tinh_opts_k = ["Tất cả"] + sorted([
                x for x in dg["Tỉnh Thành"].unique()
                if x not in ["","Không rõ","Toàn quốc","Quốc tế"]
            ] if not dg.empty else [])
            sel_tinh_k = st.selectbox("📍 Tỉnh/TP", tinh_opts_k, key="k1_tinh")

        JUNK_PROJ_K = [
            "","Không áp dụng","Chưa có thông tin","0","N/A","Không rõ",
            "Chưa xác định","Không có","None","nan","Nhiều dự án",
            "Thị trường BĐS","Thị trường Chứng khoán Việt Nam",
            "Hội nghị","Diễn đàn","Hội thảo",
        ]
        base_df_k = dff.copy()
        days_k = time_opts_k[sel_time_k]
        if days_k > 0:
            cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days_k)
            base_df_k = base_df_k[base_df_k["Ngày đăng (Chuẩn)"] >= cutoff]

        proj_df_k = base_df_k[~base_df_k["Dự án"].isin(JUNK_PROJ_K)].copy()
        proj_df_k = proj_df_k[proj_df_k["Dự án"].str.len() > 4]
        proj_df_k = proj_df_k[~proj_df_k["Dự án"].str.lower().str.startswith(
            ("không","chưa","n/a","none","nan","nhiều","thị trường","hội nghị","diễn đàn"))]
        if sel_loai_k != "Tất cả":
            proj_df_k = proj_df_k[proj_df_k["Loại hình BĐS"] == sel_loai_k]
        if sel_tinh_k != "Tất cả":
            proj_df_k = proj_df_k[proj_df_k["Tỉnh Thành"].str.contains(sel_tinh_k, na=False)]

        if not proj_df_k.empty:
            proj_agg_k = proj_df_k.groupby("Dự án").agg(
                Loai_hinh=("Loại hình BĐS","first"),
                Tinh_Thanh=("Tỉnh Thành","first"),
                Vong_doi=("Vòng đời","first"),
                So_lan=("Dự án","count"),
                SK_TB=("Điểm Sức khỏe","mean"),
                Is_Hot=("Is_Hot","any"),
                CĐT=("Chủ đầu tư","first"),
                Ngay=("Ngày đăng (Chuẩn)","max"),
            ).reset_index()
            proj_agg_k["SK_TB"] = proj_agg_k["SK_TB"].round(1)
            proj_agg_k = proj_agg_k.sort_values(
                ["Is_Hot","So_lan","Ngay"], ascending=[False,False,False])

            total_k = len(proj_agg_k)
            hot_k   = proj_agg_k["Is_Hot"].sum()
            st.markdown(
                f"<div style='font-size:12px;color:#58a6ff;margin-bottom:8px;'>"
                f"📊 <b>{total_k}</b> dự án · 🔥 <b>{hot_k}</b> HOT</div>",
                unsafe_allow_html=True)

            PPG_K = 10
            total_pg_k = max(1, (total_k - 1) // PPG_K + 1)
            if "k1_page" not in st.session_state:
                st.session_state.k1_page = 1
            filter_sig = f"{sel_time_k}_{sel_loai_k}_{sel_tinh_k}_{total_k}"
            if st.session_state.get("k1_filter_sig") != filter_sig:
                st.session_state.k1_page = 1
                st.session_state.k1_filter_sig = filter_sig
            cur_pg_k = st.session_state.k1_page

            for _, p in proj_agg_k.iloc[(cur_pg_k-1)*PPG_K : cur_pg_k*PPG_K].iterrows():
                loai_k = str(p["Loai_hinh"])
                clr_k  = LOAI_CLR.get(loai_k, "#484f58")
                hot_b  = "🔥 " if p["Is_Hot"] else ""
                sc_k   = p["SK_TB"]
                sc_col = "#3fb950" if sc_k > 2 else "#f85149" if sc_k < -2 else "#7d8590"
                sc_str = f"SK:{sc_k:+.1f}" if sc_k != 0 else ""
                vd_k   = str(p["Vong_doi"]) if str(p["Vong_doi"]) not in ["Không áp dụng","","Chưa xác định"] else ""
                tinh_k = str(p["Tinh_Thanh"]).split(",")[0].strip()
                cdt_k  = str(p["CĐT"]) if str(p["CĐT"]) not in ["Không áp dụng","","Chưa có thông tin"] else ""
                html_k = (
                    f"<div style='display:flex;align-items:center;gap:8px;padding:6px 10px;"
                    f"margin-bottom:4px;background:#161b22;border-radius:6px;"
                    f"border-left:3px solid {clr_k};'>"
                    f"<div style='flex:1;min-width:0;overflow:hidden;'>"
                    f"<div style='font-size:13px;font-weight:600;color:#e6edf3;"
                    f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>"
                    f"{hot_b}{str(p['Dự án'])}</div>"
                    f"<div style='font-size:10px;color:#7d8590;margin-top:2px;'>"
                    f"<span style='color:{clr_k};'>{loai_k}</span>"
                )
                if tinh_k: html_k += f" · 📍{tinh_k}"
                if vd_k:   html_k += f" · 🔄{vd_k}"
                if cdt_k:  html_k += f" · 👑{cdt_k[:22]}"
                html_k += (
                    f"</div></div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-family:JetBrains Mono;font-size:11px;color:#58a6ff;'>"
                    f"{str(p['So_lan'])}x</div>"
                )
                if sc_str:
                    html_k += f"<div style='font-size:10px;color:{sc_col};'>{sc_str}</div>"
                html_k += "</div></div>"
                st.markdown(html_k, unsafe_allow_html=True)

            if total_pg_k > 1:
                pk1, pk2, pk3, pk4 = st.columns([1,2,2,1])
                with pk1:
                    if st.button("◀", key="k1_prev", disabled=(cur_pg_k == 1)):
                        st.session_state.k1_page = max(1, cur_pg_k - 1); st.rerun()
                with pk2:
                    st.markdown(
                        f"<div style='text-align:center;color:#7d8590;font-size:12px;padding:6px 0;'>"
                        f"Trang <b style='color:#58a6ff;'>{cur_pg_k}</b>/{total_pg_k}</div>",
                        unsafe_allow_html=True)
                with pk3:
                    st.markdown(
                        f"<div style='text-align:center;color:#7d8590;font-size:12px;padding:6px 0;'>"
                        f"{total_k} dự án</div>", unsafe_allow_html=True)
                with pk4:
                    if st.button("▶", key="k1_next", disabled=(cur_pg_k == total_pg_k)):
                        st.session_state.k1_page = min(total_pg_k, cur_pg_k + 1); st.rerun()
        else:
            st.info("Chưa có dữ liệu dự án phù hợp.")

    with k2:
        st.markdown("<div class='chart-title'>Ma trận Cơ hội — Loại hình × Vòng đời</div>",
                    unsafe_allow_html=True)
        JUNK_LH_HM = ["Chưa có thông tin","Bất động sản khác","Khác","",
                       "Không áp dụng","Không rõ"]
        df_te = (
            dff.assign(**{"Loại hình BĐS": dff["Loại hình BĐS"].str.split(",")})
            .explode("Loại hình BĐS")
        )
        df_te["Loại hình BĐS"] = df_te["Loại hình BĐS"].str.strip()
        dm = df_te[~df_te["Loại hình BĐS"].isin(JUNK_LH_HM)]
        dm = dm[~dm["Vòng đời"].isin(["Chưa xác định","Chưa có thông tin","","Không áp dụng"])]
        if not dm.empty:
            mx = pd.crosstab(dm["Loại hình BĐS"], dm["Vòng đời"])
            fig = px.imshow(mx,
                            color_continuous_scale=[[0,"#0d1117"],[0.3,"#1f4e8c"],
                                                    [0.7,"#1f6feb"],[1.0,"#58a6ff"]],
                            text_auto=True, aspect="auto")
            dark(fig, legend=False)
            fig.update_layout(height=320, coloraxis_showscale=False,
                              xaxis=dict(tickfont=dict(color=FONT_COLOR, size=11)),
                              yaxis=dict(tickfont=dict(color=FONT_COLOR, size=11)))
            fig.update_traces(textfont=dict(size=13, color="white"),
                              hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>%{z} sự kiện<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            idc_val = sum(
                mx.loc[ir, "Chuẩn bị đầu tư"]
                for ir in ["BĐS Công nghiệp / KCN","Data Center / IDC"]
                if ir in mx.index and "Chuẩn bị đầu tư" in mx.columns
            )
            if idc_val > 0:
                st.markdown(
                    f"<div style='background:#0d2818;border:1px solid #238636;border-left:3px solid #3fb950;"
                    f"border-radius:6px;padding:8px 14px;margin-top:6px;'>"
                    f"<span style='font-size:12px;color:#aff5b4;'>"
                    f"📊 <b>{idc_val} dự án KCN/IDC</b> đang Chuẩn bị đầu tư</span></div>",
                    unsafe_allow_html=True)
        else:
            st.info("Chưa đủ dữ liệu.")

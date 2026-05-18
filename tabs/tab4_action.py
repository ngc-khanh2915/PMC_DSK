import pandas as pd
import streamlit as st

from utils import JUNK_ACT, FONT_COLOR, dark


def render(dff, time_option):
    _SVC_BY_LC = {
        "Chuẩn bị đầu tư":        ["Tư vấn giám sát","Môi giới","Tư vấn pháp lý","Tư vấn vận hành"],
        "Xây dựng":                ["Tư vấn giám sát","Bảo trì thiết bị","PCCC"],
        "Nghiệm thu & Bàn giao":  ["Quản lý vận hành","Vệ sinh","An ninh","Tư vấn nghiệm thu"],
        "Vận hành":                ["Quản lý vận hành","Bảo trì","An ninh","Vệ sinh","Cảnh quan"],
    }
    _SH_BY_LC = {
        "Chuẩn bị đầu tư":       "Chủ đầu tư / Ban Giám đốc dự án",
        "Xây dựng":               "Ban QLDA / Tổng thầu xây dựng",
        "Nghiệm thu & Bàn giao": "CĐT + Ban Quản trị sơ bộ + Cư dân",
        "Vận hành":               "Ban Quản trị / Cư dân / Tenant",
    }

    def _act_priority(val):
        vl = val.lower()
        if any(k in vl for k in ["high","cấp bách","urgent"]): return "#b62324","🔴 HIGH"
        if any(k in vl for k in ["medium","trung bình"]):       return "#9e6a03","🟡 MED"
        if "low" in vl:                                          return "#1a4a2e","🟢 LOW"
        return "#30363d","⚪ —"

    st.markdown("""<div style='background:#0d2040;border:1px solid #1f6feb44;border-radius:8px;
        padding:10px 16px;margin-bottom:12px;'>
        <span style='color:#58a6ff;font-weight:700;font-size:13px;'>⚡ Action Plan — Ma trận Hành động Thị trường</span>
        <span style='color:#7d8590;font-size:12px;'> · Đồng bộ bộ lọc thời gian từ bên trên · HOT → N1 → Điểm SK</span>
    </div>""", unsafe_allow_html=True)

    ap1, ap2, ap3 = st.columns([1.5, 1.5, 1])
    with ap1:
        ap_vd = st.selectbox("🔄 Vòng đời",
            ["Tất cả","Chuẩn bị đầu tư","Xây dựng","Nghiệm thu & Bàn giao","Vận hành"],
            key="ap_vd")
    with ap2:
        _sk_opts = sorted([x for x in dff["Nhóm Sự kiện"].unique()
                           if x and x not in ["","Không áp dụng","Chưa xác định"]])
        ap_sk = st.selectbox("📌 Nhóm Sự kiện", ["Tất cả"] + _sk_opts, key="ap_sk")
    with ap3:
        ap_hot = st.checkbox("🔥 Chỉ HOT", key="ap_hot")

    action_df = dff[
        dff["Action_BD"].str.strip().ne("") & ~dff["Action_BD"].isin(JUNK_ACT)
    ].copy()
    if ap_vd != "Tất cả":   action_df = action_df[action_df["Vòng đời"] == ap_vd]
    if ap_sk != "Tất cả":   action_df = action_df[action_df["Nhóm Sự kiện"] == ap_sk]
    if ap_hot:               action_df = action_df[action_df["Is_Hot"]]

    action_df["_sort_pri"] = (
        action_df["Is_Hot"].astype(int) * 100 +
        (action_df["Nhóm Tin"] == "Nhóm 1 - Trực tiếp").astype(int) * 50 +
        action_df["Điểm Sức khỏe"].abs()
    )
    action_df = action_df.sort_values(["_sort_pri","Chỉ Ngày"], ascending=[False,False])
    total_ap  = len(action_df)
    n_hot_a   = int(action_df["Is_Hot"].sum())
    n_n1_a    = int((action_df["Nhóm Tin"] == "Nhóm 1 - Trực tiếp").sum())

    st.markdown(
        f"<div style='display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap;'>"
        f"<span style='color:#7d8590;font-size:12px;'>📋 <b style='color:#58a6ff;'>{total_ap}</b> action items</span>"
        f"<span style='color:#7d8590;font-size:12px;'>🔥 <b style='color:#f85149;'>{n_hot_a}</b> HOT</span>"
        f"<span style='color:#7d8590;font-size:12px;'>N1 <b style='color:#1f6feb;'>{n_n1_a}</b> Trực tiếp</span>"
        f"<span style='color:#7d8590;font-size:12px;'>🗓️ Kỳ: <b style='color:#f0b429;'>{time_option}</b></span>"
        f"</div>", unsafe_allow_html=True)

    if action_df.empty:
        st.info("Chưa có Action Plan trong kỳ này. Thử mở rộng bộ lọc thời gian hoặc bỏ filter.")
    else:
        AP_PER_PAGE = 15
        total_pg_ap = max(1, (total_ap - 1) // AP_PER_PAGE + 1)
        if "ap_page" not in st.session_state: st.session_state.ap_page = 1
        _ap_sig = f"{ap_vd}|{ap_sk}|{ap_hot}|{time_option}|{total_ap}"
        if st.session_state.get("_ap_sig") != _ap_sig:
            st.session_state.ap_page = 1
            st.session_state._ap_sig = _ap_sig
        ap_page = st.session_state.ap_page
        ap_rows = action_df.iloc[(ap_page-1)*AP_PER_PAGE : ap_page*AP_PER_PAGE]

        for _, row in ap_rows.iterrows():
            proj  = str(row.get("Dự án","") or "").strip()
            if not proj or proj in JUNK_ACT:
                proj = str(row.get("Tiêu đề",""))[:80]
            vd    = row.get("Vòng đời","Vận hành")
            if vd in ["Không áp dụng","Chưa xác định","","Không rõ"]: vd = "Vận hành"
            svc_r = ", ".join(_SVC_BY_LC.get(vd, ["Quản lý vận hành","Bảo trì"]))
            sh_r  = _SH_BY_LC.get(vd, "Ban Quản trị")
            score = float(row.get("Điểm Sức khỏe", 0) or 0)
            is_h  = bool(row.get("Is_Hot", False))
            tinh  = str(row.get("Tỉnh Thành","")).split(",")[0]
            loai  = str(row.get("Loại hình BĐS",""))
            cdt   = str(row.get("Chủ đầu tư",""))
            if cdt in ["","Không áp dụng","Chưa có thông tin"]: cdt = ""
            tomtat = str(row.get("Tóm tắt",""))[:200]
            sc_col = "#3fb950" if score > 0 else "#f85149" if score < 0 else "#7d8590"
            score_str = f"+{score:.0f}" if score > 0 else f"{score:.0f}"
            hot_b  = (
                "<span style='background:#b62324;color:#ffa198;padding:1px 6px;"
                "border-radius:3px;font-size:10px;font-weight:700;margin-left:6px;'>🔥 HOT</span>"
                if is_h else ""
            )
            nhom      = row.get("Nhóm Tin","")
            nhom_col  = "#1f6feb" if "Trực tiếp" in nhom else "#9e6a03" if "Gián tiếp" in nhom else "#484f58"
            try:
                ngay_s = pd.Timestamp(row["Ngày đăng (Chuẩn)"]).strftime("%d/%m/%Y")
            except Exception:
                ngay_s = ""

            st.markdown(
                f"<div style='background:#0d1117;border:1px solid {nhom_col}55;"
                f"border-radius:12px;overflow:hidden;margin-bottom:14px;"
                f"box-shadow:0 2px 8px rgba(0,0,0,.3);'>",
                unsafe_allow_html=True)

            h1, h2 = st.columns([5, 1])
            with h1:
                tags = []
                if ngay_s: tags.append(f"<span style='background:#21262d;color:#8b949e;padding:2px 8px;border-radius:4px;font-size:11px;'>🕒 {ngay_s}</span>")
                if tinh:   tags.append(f"<span style='background:#21262d;color:#8b949e;padding:2px 8px;border-radius:4px;font-size:11px;'>📍 {tinh}</span>")
                if loai and loai not in ["Không áp dụng","","Chưa có thông tin"]:
                    tags.append(f"<span style='background:{nhom_col}22;border:1px solid {nhom_col}55;color:{nhom_col};padding:2px 8px;border-radius:4px;font-size:11px;'>🏢 {loai}</span>")
                if cdt: tags.append(f"<span style='background:#21262d;color:#8b949e;padding:2px 8px;border-radius:4px;font-size:11px;'>👑 {cdt[:25]}</span>")
                tags.append(f"<span style='background:#f0b42922;border:1px solid #f0b42955;color:#f0b429;padding:2px 8px;border-radius:4px;font-size:11px;'>🔄 {vd}</span>")
                sk_val = row.get("Nhóm Sự kiện","")
                if sk_val: tags.append(f"<span style='background:{nhom_col}22;border:1px solid {nhom_col}55;color:{nhom_col};padding:2px 8px;border-radius:4px;font-size:11px;'>◉ {sk_val}</span>")
                st.markdown(
                    f"<div style='padding:14px 16px 10px 16px;background:#161b22;"
                    f"border-bottom:2px solid {nhom_col}44;'>"
                    f"<div style='font-size:16px;font-weight:800;color:#ffffff;"
                    f"line-height:1.4;margin-bottom:8px;'>{proj[:80]}{hot_b}</div>"
                    f"<div style='display:flex;gap:5px;flex-wrap:wrap;'>"
                    + " ".join(tags) + "</div></div>",
                    unsafe_allow_html=True)
            with h2:
                sc_bg = "#0d2818" if score > 0 else "#2d0f0f" if score < 0 else "#161b22"
                st.markdown(
                    f"<div style='background:{sc_bg};height:100%;min-height:80px;"
                    f"display:flex;flex-direction:column;justify-content:center;"
                    f"align-items:center;padding:12px;'>"
                    f"<div style='font-family:JetBrains Mono;font-size:28px;"
                    f"font-weight:900;color:{sc_col};line-height:1;'>{score_str}</div>"
                    f"<div style='font-size:9px;color:#7d8590;margin-top:4px;"
                    f"text-transform:uppercase;letter-spacing:.8px;'>Điểm SK</div>"
                    f"</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='height:1px;background:{nhom_col}33;margin:0;'></div>",
                        unsafe_allow_html=True)
            if tomtat:
                st.markdown(
                    f"<div style='padding:10px 16px;background:#161b22;'>"
                    f"<div style='font-size:10px;color:#58a6ff;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px;'>📰 Nội dung tin</div>"
                    f"<div style='font-size:12.5px;color:#c9d1d9;line-height:1.7;'>"
                    f"{tomtat}{'…' if len(str(row.get('Tóm tắt','')))>200 else ''}</div>"
                    f"</div>", unsafe_allow_html=True)

            dv1, dv2 = st.columns(2)
            with dv1:
                st.markdown(
                    f"<div style='padding:8px 16px 10px 16px;background:#0a1f12;'>"
                    f"<div style='font-size:10px;color:#3fb950;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px;'>"
                    f"🔧 Dịch vụ PMC đề xuất</div>"
                    f"<div style='font-size:12px;color:#aff5b4;line-height:1.6;'>{svc_r}</div>"
                    f"</div>", unsafe_allow_html=True)
            with dv2:
                st.markdown(
                    f"<div style='padding:8px 16px 10px 16px;background:#1a1200;'>"
                    f"<div style='font-size:10px;color:#f0b429;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px;'>"
                    f"👤 Đối tượng tiếp cận</div>"
                    f"<div style='font-size:12px;color:#f0e3a0;line-height:1.6;'>{sh_r}</div>"
                    f"</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='height:1px;background:{nhom_col}22;'></div>",
                        unsafe_allow_html=True)

            _a_cfg = [
                ("Action_BD",        "🏢 BD / Phát triển KD", "#1f6feb"),
                ("Action_RnD",       "🔬 R&D / Nghiên cứu",   "#8957e5"),
                ("Action_Legal",     "⚖️ Legal / Pháp lý",    "#f85149"),
                ("Action_Finance",   "💰 Finance / Tài chính", "#f0b429"),
                ("Action_Marketing", "📢 Marketing",            "#3fb950"),
            ]
            row1_cols = st.columns(2)
            row2_cols = st.columns(3)
            col_map   = [row1_cols[0], row1_cols[1], row2_cols[0], row2_cols[1], row2_cols[2]]
            for ci, (ck, lbl, br) in enumerate(_a_cfg):
                val = str(row.get(ck,"")).strip()
                if val in JUNK_ACT: val = ""
                pri_c, pri_l = _act_priority(val)
                clean = (val.replace("High","").replace("Medium","").replace("Low","")
                            .replace("|"," · ").strip()[:200])
                with col_map[ci]:
                    inner = (clean if clean else
                             "<span style='color:#484f58;font-style:italic;font-size:11px;'>Chưa có hành động</span>")
                    st.markdown(
                        f"<div style='background:#0d1117;border:1px solid {br}33;"
                        f"border-top:3px solid {br};border-radius:0 0 6px 6px;"
                        f"padding:10px 12px;min-height:80px;'>"
                        f"<div style='font-size:10px;color:{br};font-weight:700;"
                        f"margin-bottom:6px;display:flex;justify-content:space-between;"
                        f"align-items:center;letter-spacing:.3px;'>"
                        f"<span>{lbl}</span>"
                        f"<span style='background:{pri_c}22;border:1px solid {pri_c}55;"
                        f"color:{pri_c};padding:1px 6px;border-radius:3px;font-size:9px;"
                        f"font-weight:700;'>{pri_l}</span></div>"
                        f"<div style='font-size:12px;color:#c9d1d9;line-height:1.6;'>{inner}</div>"
                        f"</div>",
                        unsafe_allow_html=True)
            st.markdown("</div><div style='height:4px;'></div>", unsafe_allow_html=True)

        if total_pg_ap > 1:
            pap1, pap2, pap3 = st.columns([1,2,1])
            with pap1:
                if st.button("◀ Trước", key="ap_prev", disabled=(ap_page==1)):
                    st.session_state.ap_page = max(1, ap_page-1); st.rerun()
            with pap2:
                st.markdown(
                    f"<div style='text-align:center;color:#7d8590;font-size:12px;padding:6px 0;'>"
                    f"Trang <b style='color:#58a6ff;'>{ap_page}</b>/{total_pg_ap} · "
                    f"{total_ap} actions</div>", unsafe_allow_html=True)
            with pap3:
                if st.button("Tiếp ▶", key="ap_next", disabled=(ap_page==total_pg_ap)):
                    st.session_state.ap_page = min(total_pg_ap, ap_page+1); st.rerun()

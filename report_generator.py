import base64
import datetime as _dt
import pandas as pd
import re as _re


def build_report_html(rdf, df_all, macro, period_label, d_from, d_to):
    now = _dt.datetime.now()

    # ── Tên cột ──────────────────────────────────────────────────
    col_nhom_tin = 'Nhóm Tin'
    col_sk       = 'Nhóm Sự kiện'
    col_lh       = 'Loại hình BĐS'
    col_tinh     = 'Tỉnh Thành'
    col_title    = 'Tiêu đề'
    col_duan     = 'Dự án'
    col_cdt      = 'Chủ đầu tư'
    col_sk_diem  = 'Điểm Sức khỏe'
    col_is_hot   = 'Is_Hot'
    col_ngay     = 'Chỉ Ngày'
    col_vd       = 'Vòng đời'

    # ── Số liệu tổng quan ────────────────────────────────────────
    total  = len(rdf)
    n_hot  = int(rdf[col_is_hot].sum()) if col_is_hot in rdf.columns else 0
    n1     = int((rdf[col_nhom_tin]=='Nhóm 1 - Trực tiếp').sum())
    n2     = int((rdf[col_nhom_tin]=='Nhóm 2 - Gián tiếp').sum())
    n3     = int((rdf[col_nhom_tin]=='Nhóm 3 - Cảnh báo sớm').sum())
    n_tinh = rdf[col_tinh].nunique()
    top_sk = rdf[col_sk].mode()[0] if not rdf.empty else 'N/A'
    top_lh = rdf[col_lh].mode()[0] if not rdf.empty else 'N/A'

    # ── JUNK filter ──────────────────────────────────────────────
    JUNK_R = ['','Không áp dụng','Chưa có thông tin','N/A','Không rõ',
              'Chưa xác định','Nhiều dự án','Thị trường BĐS']

    def clean_proj(df):
        d = df[~df[col_duan].isin(JUNK_R)].copy()
        d = d[d[col_duan].str.len() > 4]
        d = d[~d[col_duan].str.lower().str.startswith(
            ('không','chưa','n/a','none','nan','nhiều','thị trường','hội nghị'))]
        return d

    # ── Top 5 tin HOT ────────────────────────────────────────────
    hot_rows = ''
    hot_df = rdf[rdf[col_is_hot]].head(5) if col_is_hot in rdf.columns else pd.DataFrame()
    for _, r in hot_df.iterrows():
        sk  = r.get(col_sk_diem, 0)
        sc  = '#16A34A' if sk > 0 else '#DC2626' if sk < 0 else '#6B7280'
        tit = str(r[col_title])[:80] + ('...' if len(str(r[col_title])) > 80 else '')
        tin = str(r[col_tinh]).split(',')[0]
        hot_rows += (
            f"<tr>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #E5E7EB;font-size:11px;'>{tit}</td>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #E5E7EB;font-size:10px;color:#6B7280;'>{tin}</td>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #E5E7EB;font-size:11px;color:{sc};font-weight:700;'>SK:{sk:+.0f}</td>"
            f"</tr>"
        )
    if not hot_rows:
        hot_rows = "<tr><td colspan='3' style='padding:8px;color:#9CA3AF;text-align:center;font-size:11px;'>Không có tin HOT trong kỳ này</td></tr>"

    # ── Top 6 dự án nhắc nhiều nhất ─────────────────────────────
    proj_rows = ''
    proj_r = clean_proj(rdf)
    if not proj_r.empty:
        proj_agg = proj_r.groupby(col_duan).agg(
            Loai=(col_lh,'first'), Tinh=(col_tinh,'first'),
            Cnt=(col_duan,'count'), SK=(col_sk_diem,'mean'),
            CDT=(col_cdt,'first'), VD=(col_vd,'first'),
        ).reset_index().sort_values('Cnt', ascending=False).head(6)
        proj_agg['SK'] = proj_agg['SK'].round(1)
        for _, p in proj_agg.iterrows():
            cdt_s  = str(p['CDT'])[:20] if str(p['CDT']) not in ['Không áp dụng','','Chưa có thông tin'] else ''
            tinh_s = str(p['Tinh']).split(',')[0]
            vd_s   = str(p['VD']) if str(p['VD']) not in ['Không áp dụng','','Chưa xác định'] else ''
            is_h   = proj_r[proj_r[col_duan]==p[col_duan]][col_is_hot].any() if col_is_hot in proj_r.columns else False
            hot_mk = "<span style='color:#DC2626;font-weight:800;'>HOT&nbsp;</span>" if is_h else ""
            proj_rows += (
                f"<tr>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:10.5px;font-weight:600;'>{hot_mk}{str(p[col_duan])[:38]}</td>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:9.5px;color:#2563EB;'>{p['Loai']}</td>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:9.5px;color:#555;'>{tinh_s}</td>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:9.5px;'>{cdt_s}</td>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:9.5px;color:#888;'>{vd_s}</td>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #F3F4F6;font-size:10.5px;color:#2563EB;font-weight:700;text-align:center;'>{p['Cnt']}x</td>"
                f"</tr>"
            )
    if not proj_rows:
        proj_rows = "<tr><td colspan='6' style='padding:8px;color:#9CA3AF;font-size:10px;'>Không có dự án cụ thể</td></tr>"

    # ── Dự án MỚI lần đầu trong kỳ ──────────────────────────────
    new_proj_rows = ''
    new_proj_count = 0
    if df_all is not None and not df_all.empty and col_ngay in df_all.columns:
        before_kw = clean_proj(df_all[df_all[col_ngay] < d_from])[col_duan].unique().tolist()
        new_proj  = clean_proj(rdf)[~clean_proj(rdf)[col_duan].isin(before_kw)]
        if not new_proj.empty:
            new_agg = new_proj.groupby(col_duan).agg(
                Loai=(col_lh,'first'), Tinh=(col_tinh,'first'),
                SK=(col_sk_diem,'mean'), CDT=(col_cdt,'first'),
                VD=(col_vd,'first'), Ngay=(col_ngay,'min'),
                Is_Hot=(col_is_hot,'any') if col_is_hot in new_proj.columns else (col_duan,'count'),
            ).reset_index().sort_values(['Is_Hot','Ngay'], ascending=[False,True]).head(6)
            new_proj_count = len(new_agg)
            for _, p in new_agg.iterrows():
                cdt_s  = str(p['CDT'])[:20] if str(p['CDT']) not in ['Không áp dụng','','Chưa có thông tin'] else ''
                tinh_s = str(p['Tinh']).split(',')[0]
                vd_s   = str(p['VD']) if str(p['VD']) not in ['Không áp dụng','','Chưa xác định'] else ''
                is_h   = p.get('Is_Hot', False)
                hot_mk = "<span style='color:#DC2626;font-weight:800;'>HOT&nbsp;</span>" if is_h else ""
                ngay_s = pd.Timestamp(p['Ngay']).strftime('%d/%m') if pd.notna(p['Ngay']) else ''
                new_proj_rows += (
                    f"<tr style='background:#F0FDF4;'>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:10.5px;font-weight:600;'>"
                    f"<span style='color:#16A34A;font-size:9px;font-weight:700;margin-right:3px;background:#DCFCE7;padding:1px 4px;border-radius:3px;'>MỚI</span>"
                    f"{hot_mk}{str(p[col_duan])[:35]}</td>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:9.5px;color:#2563EB;'>{p['Loai']}</td>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:9.5px;color:#555;'>{tinh_s}</td>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:9.5px;'>{cdt_s}</td>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:9.5px;color:#888;'>{vd_s}</td>"
                    f"<td style='padding:3px 6px;border-bottom:1px solid #D1FAE5;font-size:10px;color:#16A34A;font-weight:700;text-align:center;'>{ngay_s}</td>"
                    f"</tr>"
                )

    # ── Chính sách & Pháp lý BĐS (lọc kỹ) ─────────────────────
    CS_BDS_KW = ['bất động sản','nhà ở','đất đai','quy hoạch','chung cư',
                 'khu công nghiệp','luật đất','luật nhà','luật kinh doanh',
                 'sổ đỏ','sổ hồng','phí bảo trì','ban quản trị','pccc',
                 'căn hộ','dự án nhà','chủ đầu tư','hạ tầng đô thị',
                 'nghị định','thông tư','môi giới','chuyển nhượng','pháp lý']
    CS_TRASH_KW = [
        # Tài chính phi BĐS
        'xổ số','giải độc đắc','vé số','trúng thưởng','lập kỷ lục',
        'tiền số','bitcoin','crypto','chứng khoán','vnindex','cổ phiếu',
        # Năng lượng / hàng hóa
        'chiếu sáng quảng cáo','tiết kiệm điện','giá xăng','giá gas',
        'điện mặt trời','năng lượng tái tạo',
        # Xã hội phi BĐS
        'học phí','bảo hiểm y tế','lương tối thiểu','tiền lương',
        'hàng không','du lịch','khách sạn','resort','ẩm thực',
        # Quốc tế không liên quan trực tiếp
        'ukraine','nga ','hamas','israel','tây ban nha','pháp ','đức ',
        # Thể thao / giải trí
        'bóng đá','cầu thủ','hlv ','ca sĩ','diễn viên',
    ]
    cs_base = rdf[rdf[col_sk] == 'Chính sách & Pháp lý'].copy()
    # Bắt buộc phải là N1 Trực tiếp
    cs_base = cs_base[cs_base[col_nhom_tin] == 'Nhóm 1 - Trực tiếp']
    # Lọc bỏ tin rác
    cs_base = cs_base[~cs_base[col_title].str.lower().apply(
        lambda t: any(k in t for k in CS_TRASH_KW))]
    # Ưu tiên tin có từ khóa BĐS thực sự
    cs_bds = cs_base[cs_base[col_title].str.lower().apply(
        lambda t: any(k in t for k in CS_BDS_KW))]
    cs_df = cs_bds.head(4) if len(cs_bds) >= 1 else cs_base.head(4)
    cs_html = ''
    if not cs_df.empty:
        for _, r in cs_df.iterrows():
            tit = str(r[col_title])[:90]
            cs_html += f"<li style='margin-bottom:5px;font-size:10.5px;line-height:1.5;'>{tit}</li>"
    else:
        cs_html = "<li style='color:#9CA3AF;font-size:10.5px;'>Không có chính sách BĐS nổi bật trong kỳ này</li>"

    # ── Macro ────────────────────────────────────────────────────
    def mv(k, fmt):
        d = macro.get(k, {}); v = d.get('value')
        try: return fmt % v if v is not None else 'N/A'
        except: return 'N/A'

    ls_cv   = mv('nhnn_cv',   '%.2f%%')
    cpi_val = mv('cpi',       '%.2f%%')
    fdi_val = mv('fdi',       '$%.1fB')
    _dien_raw = macro.get('gia_dien', {}).get('value')
    dien_val = f"{_dien_raw:,.0f}" if _dien_raw is not None else "2,103"
    gdp_val = mv('gdp',       '%.2f%%')
    td_val  = mv('tdung_bds', '%.1f%%')

    # ── Phần dự án mới ──────────────────────────────────────────
    new_section = ''
    if new_proj_rows:
        new_section = f"""
      <div style='margin-top:10px;'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;
             color:#16A34A;border-left:3px solid #16A34A;padding-left:6px;margin-bottom:4px;'>
          Dự án mới lần đầu xuất hiện trong kỳ ({new_proj_count} dự án)
        </div>
        <table style='width:100%;border-collapse:collapse;'>
          <tr>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:left;border-bottom:2px solid #BBF7D0;'>Dự án</th>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:left;border-bottom:2px solid #BBF7D0;width:14%;'>Dòng BĐS</th>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:left;border-bottom:2px solid #BBF7D0;width:13%;'>Khu vực</th>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:left;border-bottom:2px solid #BBF7D0;width:18%;'>Chủ đầu tư</th>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:left;border-bottom:2px solid #BBF7D0;width:12%;'>Vòng đời</th>
            <th style='background:#F0FDF4;padding:4px 6px;font-size:9px;font-weight:700;text-transform:uppercase;color:#15803D;text-align:center;border-bottom:2px solid #BBF7D0;width:8%;'>Ngày</th>
          </tr>
          {new_proj_rows}
        </table>
      </div>"""

    # ── BUILD HTML — 2 TRANG A4 ─────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DSK Intelligence Report — {d_from.strftime('%d/%m/%Y')}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
@page {{ size: A4 portrait; margin: 0; }}
@media print {{
  body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .no-print {{ display: none !important; }}
  }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Plus Jakarta Sans', Arial, sans-serif; font-size: 11px;
        color: #111827; background: #E5E7EB; }}
/* PRINT BUTTON */
.print-btn {{
  position: fixed; bottom: 20px; right: 20px;
  background: #2563EB; color: white; border: none;
  padding: 10px 20px; border-radius: 8px; cursor: pointer;
  font-size: 13px; font-weight: 700; z-index: 999;
  box-shadow: 0 4px 14px rgba(37,99,235,.5);
  font-family: 'Plus Jakarta Sans', sans-serif; }}
/* PAGE */
.page {{
  width: 210mm;
  margin: 0 auto 8mm auto;
  background: white;
  padding: 10mm 13mm;
  box-shadow: 0 2px 20px rgba(0,0,0,.12); }}
/* HEADER */
.hdr {{
  display: flex; justify-content: space-between; align-items: flex-start;
  padding-bottom: 8px; border-bottom: 3px solid #2563EB; margin-bottom: 10px; }}
.logo {{ font-size: 20px; font-weight: 800; color: #2563EB; letter-spacing: -.5px; }}
.logo span {{ color: #16A34A; }}
.logo-sub {{ font-size: 9.5px; color: #9CA3AF; margin-top: 2px; }}
.period {{ text-align: right; }}
.period-lbl {{ font-size: 9px; color: #9CA3AF; text-transform: uppercase; letter-spacing: .5px; }}
.period-val {{ font-size: 13px; font-weight: 700; color: #111827; }}
.period-gen {{ font-size: 8.5px; color: #D1D5DB; margin-top: 2px; }}
/* SECTION HEADER */
.sec {{
  display: inline-flex; align-items: center; gap: 8px;
  margin: 10px 0 7px; }}
.sec-badge {{
  font-size: 9.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .6px; color: white; padding: 3px 10px; border-radius: 4px; }}
.badge-p1 {{ background: #2563EB; }}
.badge-p2 {{ background: #16A34A; }}
.sec-title {{ font-size: 12.5px; font-weight: 700; color: #111827; }}
/* METRICS */
.metrics {{
  display: grid; grid-template-columns: repeat(6,1fr);
  gap: 5px; margin-bottom: 8px; }}
.metric {{
  background: #F9FAFB; border: 1px solid #E5E7EB;
  border-top: 3px solid #2563EB; border-radius: 6px;
  padding: 5px 6px; text-align: center; }}
.metric.hot {{ border-top-color: #DC2626; }}
.metric.green {{ border-top-color: #16A34A; }}
.metric.amber {{ border-top-color: #D97706; }}
.metric .val {{ font-size: 19px; font-weight: 800; color: #2563EB;
                font-family: 'JetBrains Mono', monospace; line-height: 1.1; }}
.metric.hot .val {{ color: #DC2626; }}
.metric.green .val {{ color: #16A34A; }}
.metric.amber .val {{ color: #D97706; }}
.metric .lbl {{
  font-size: 8.5px; color: #6B7280; text-transform: uppercase;
  letter-spacing: .5px; margin-top: 2px; font-weight: 600; }}
/* SIGNAL BOX */
.signal {{
  background: linear-gradient(135deg,#FFFBEB,#FEF3C7);
  border-left: 4px solid #D97706;
  padding: 6px 10px; border-radius: 0 6px 6px 0; margin-bottom: 8px;
  font-size: 10.5px; }}
/* TABLE */
table {{ width: 100%; border-collapse: collapse; }}
th {{
  background: #F3F4F6; padding: 4px 6px; font-size: 9px;
  font-weight: 700; text-transform: uppercase; letter-spacing: .4px;
  color: #374151; text-align: left; border-bottom: 2px solid #D1D5DB; }}
/* SUBSEC */
.subsec {{
  font-size: 9.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .5px; margin-bottom: 4px;
  padding-left: 6px; border-left: 3px solid; }}
/* 2-COL */
.two-col {{ display: grid; grid-template-columns: 58% 40%; gap: 12px; margin-top: 8px; }}
/* MACRO */
.macro-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 4px; }}
.macro-item {{
  background: #EFF6FF; border-radius: 5px; padding: 5px 8px;
  border-left: 3px solid #BFDBFE; }}
.macro-key {{ font-size: 8.5px; color: #4B5563; text-transform: uppercase; letter-spacing: .3px; font-weight: 600; }}
.macro-val {{ font-size: 13px; font-weight: 800; color: #1E40AF;
              font-family: 'JetBrains Mono', monospace; line-height: 1.3; }}
.macro-src {{ font-size: 8px; color: #93C5FD; }}
/* FOOTER */
.footer {{
  border-top: 1px solid #E5E7EB; margin-top: 10px; padding-top: 6px;
  display: flex; justify-content: space-between;
  font-size: 8.5px; color: #9CA3AF; }}
</style>
</head>
<body>
<button class="print-btn no-print" onclick="window.print()">🖨️ In / Lưu PDF</button>

<!-- ════════════════ TRANG 1: EXECUTIVE SUMMARY ════════════════ -->
<div class="page">
  <div class="hdr">
    <div>
      <div class="logo">DSK <span>DASHBOARD</span></div>
      <div class="logo-sub">PMC Intelligence Hub · AI-powered Real-time BĐS Market Intelligence</div>
    </div>
    <div class="period">
      <div class="period-lbl">Kỳ báo cáo · {period_label}</div>
      <div class="period-val">{d_from.strftime('%d/%m/%Y')} — {d_to.strftime('%d/%m/%Y')}</div>
      <div class="period-gen">Xuất lúc {now.strftime('%H:%M %d/%m/%Y')}</div>
    </div>
  </div>

  <!-- SECTION 1 -->
  <div class="sec">
    <span class="sec-badge badge-p1">Phần 1</span>
    <span class="sec-title">Executive Summary — Tổng quan Thị trường</span>
  </div>

  <div class="metrics">
    <div class="metric"><div class="val">{total}</div><div class="lbl">Tổng sự kiện</div></div>
    <div class="metric hot"><div class="val">{n_hot}</div><div class="lbl">Tin HOT</div></div>
    <div class="metric"><div class="val">{n1}</div><div class="lbl">N1 Trực tiếp</div></div>
    <div class="metric amber"><div class="val">{n2}</div><div class="lbl">N2 Gián tiếp</div></div>
    <div class="metric"><div class="val">{n3}</div><div class="lbl">N3 Cảnh báo</div></div>
    <div class="metric green"><div class="val">{n_tinh}</div><div class="lbl">Tỉnh/TP</div></div>
  </div>

  <div class="signal">
    <strong>Nhóm nóng nhất:</strong> {top_sk} &nbsp;·&nbsp;
    <strong>Phân khúc:</strong> {top_lh} &nbsp;·&nbsp;
    <strong>N1/N2/N3:</strong> {n1} / {n2} / {n3}
  </div>

  <div class="subsec" style="color:#DC2626;border-color:#DC2626;margin-bottom:4px;">
    Tín hiệu quan trọng nhất kỳ này
  </div>
  <table>
    <tr>
      <th style="width:74%;">Tiêu đề</th>
      <th style="width:16%;">Khu vực</th>
      <th style="width:10%;">Điểm SK</th>
    </tr>
    {hot_rows}
  </table>

  <div class="footer">
    <span>PMC Intelligence Hub · dskdashboard.pmcweb.vn</span>
    <span>Dữ liệu từ {total} bài báo · AI-powered by Gemini</span>
    <span>→ Xem tiếp Trang 2: Intelligence Report</span>
  </div>
</div>

<!-- ════════════════ TRANG 2: INTELLIGENCE REPORT ════════════════ -->
<div class="page">
  <div class="hdr">
    <div>
      <div class="logo">DSK <span>DASHBOARD</span></div>
      <div class="logo-sub">PMC Intelligence Hub · AI-powered Real-time BĐS Market Intelligence</div>
    </div>
    <div class="period">
      <div class="period-lbl">Intelligence Report · {period_label}</div>
      <div class="period-val">{d_from.strftime('%d/%m/%Y')} — {d_to.strftime('%d/%m/%Y')}</div>
    </div>
  </div>

  <div class="sec">
    <span class="sec-badge badge-p2">Phần 2</span>
    <span class="sec-title">Intelligence Report — Cơ hội Kinh doanh &amp; Dự án Mới</span>
  </div>

  <div class="two-col">
    <!-- Cột trái: Dự án -->
    <div>
      <div class="subsec" style="color:#16A34A;border-color:#16A34A;">
        Top dự án được báo chí đề cập nhiều nhất
      </div>
      <table>
        <tr>
          <th>Dự án</th>
          <th style="width:14%;">Dòng BĐS</th>
          <th style="width:13%;">Khu vực</th>
          <th style="width:17%;">Chủ đầu tư</th>
          <th style="width:12%;">Vòng đời</th>
          <th style="width:8%;text-align:center;">Lần</th>
        </tr>
        {proj_rows}
      </table>
      {new_section}
    </div>

    <!-- Cột phải: Chính sách + Macro -->
    <div>
      <div class="subsec" style="color:#7C3AED;border-color:#7C3AED;">
        Chính sách &amp; Pháp lý BĐS nổi bật
      </div>
      <ul style="padding-left:14px;margin-bottom:10px;list-style:disc;">
        {cs_html}
      </ul>

      <div class="subsec" style="color:#D97706;border-color:#D97706;margin-top:10px;margin-bottom:4px;">
        Chỉ số Kinh tế Vĩ mô
      </div>
      <div class="macro-grid">
        <div class="macro-item">
          <div class="macro-key">LS Cho vay mua nhà</div>
          <div class="macro-val">{ls_cv}</div>
          <div class="macro-src">sbv.gov.vn</div>
        </div>
        <div class="macro-item">
          <div class="macro-key">CPI nội địa YoY</div>
          <div class="macro-val">{cpi_val}</div>
          <div class="macro-src">gso.gov.vn</div>
        </div>
        <div class="macro-item">
          <div class="macro-key">FDI Giải ngân YTD</div>
          <div class="macro-val">{fdi_val}</div>
          <div class="macro-src">mpi.gov.vn</div>
        </div>
        <div class="macro-item">
          <div class="macro-key">Giá Điện TB</div>
          <div class="macro-val">{dien_val} đ/kWh</div>
          <div class="macro-src">evn.com.vn</div>
        </div>
        <div class="macro-item">
          <div class="macro-key">GDP Tăng trưởng</div>
          <div class="macro-val">{gdp_val}</div>
          <div class="macro-src">gso.gov.vn</div>
        </div>
        <div class="macro-item">
          <div class="macro-key">TD BĐS Tăng trưởng</div>
          <div class="macro-val">{td_val}</div>
          <div class="macro-src">sbv.gov.vn</div>
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    <span>PMC Intelligence Hub · dskdashboard.pmcweb.vn</span>
    <span>Dữ liệu từ {total} bài báo · AI-powered by Gemini</span>
    <span>Kỳ: {d_from.strftime('%d/%m/%Y')} – {d_to.strftime('%d/%m/%Y')}</span>
  </div>
</div>

</body>
</html>"""
    return html


def get_report_b64(rdf, df_all, macro, period_label, d_from, d_to):
    html = build_report_html(rdf, df_all, macro, period_label, d_from, d_to)
    return base64.b64encode(html.encode('utf-8')).decode()

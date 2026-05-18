import streamlit as st


def load_css():
    st.markdown("""<style>
/* ════════════════════════════════════════════════════════════════
   FONTS
════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ════════════════════════════════════════════════════════════════
   MÀU SẮC TOÀN CỤC (thay đổi ở đây để áp dụng toàn bộ dashboard)
   ─────────────────────────────────────────────────────────────
   --bg-base        : màu nền trang chính
   --bg-surface     : màu nền card / form / tab panel (thường trắng)
   --bg-subtle      : màu nền nhạt hơn (thanh tab, nền row...)
   --border         : màu viền nhạt
   --border-strong  : màu viền đậm hơn
   --text-primary   : màu chữ chính (tiêu đề, nội dung quan trọng)
   --text-secondary : màu chữ phụ (nhãn, mô tả)
   --text-muted     : màu chữ mờ (placeholder, chú thích nhỏ)
   --accent         : màu xanh chủ đạo (nút primary, tab active, link)
   --accent-light   : nền xanh nhạt (badge, highlight)
   --accent-hover   : màu xanh khi hover nút
   --green          : màu xanh lá (trạng thái OK, số tốt)
   --green-light    : nền xanh lá nhạt
   --amber          : màu vàng cam (cảnh báo)
   --amber-light    : nền vàng cam nhạt
   --red            : màu đỏ (nguy hiểm, HOT, số xấu)
   --red-light      : nền đỏ nhạt
   --purple         : màu tím (badge loại hình)
   --purple-light   : nền tím nhạt
════════════════════════════════════════════════════════════════ */
:root {
  --bg-base:       #F5F7FA;
  --bg-surface:    #FFFFFF;
  --bg-elevated:   #FFFFFF;
  --bg-subtle:     #EEF1F6;
  --border:        #DDE2EC;
  --border-strong: #B8C2D4;
  --text-primary:  #1A2340;
  --text-secondary:#4A5568;
  --text-muted:    #8A96A8;
  --accent:        #2563EB;
  --accent-light:  #EFF4FF;
  --accent-hover:  #1D4ED8;
  --green:         #16A34A;
  --green-light:   #F0FDF4;
  --amber:         #D97706;
  --amber-light:   #FFFBEB;
  --red:           #DC2626;
  --red-light:     #FEF2F2;
  --purple:        #7C3AED;
  --purple-light:  #F5F3FF;
  --shadow-sm:     0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.06);
  --shadow-md:     0 4px 12px rgba(0,0,0,.08),0 2px 6px rgba(0,0,0,.05);
  --shadow-lg:     0 8px 24px rgba(0,0,0,.10),0 4px 12px rgba(0,0,0,.06);
  --radius-sm:     6px;
  --radius-md:     10px;
  --radius-lg:     14px;
}

/* ════════════════════════════════════════════════════════════════
   NỀN TRANG & FONT CHỮ TOÀN CỤC
════════════════════════════════════════════════════════════════ */
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif;color:var(--text-primary);}
.stApp{background:var(--bg-base)!important;}
.stApp>header{background:transparent!important;}
section[data-testid="stSidebar"]{display:none;}

/* ── Thanh cuộn ── */
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-subtle);}
::-webkit-scrollbar-thumb{background:var(--border-strong);border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:var(--text-muted);}

/* ════════════════════════════════════════════════════════════════
   HERO HEADER (tiêu đề lớn "DSK DASHBOARD" ở đầu trang)
   → Đổi màu gradient chữ: thay #2563EB và #0EA5E9
════════════════════════════════════════════════════════════════ */
.hero-title{font-size:26px;font-weight:800;letter-spacing:-.5px;background:linear-gradient(135deg,#2563EB,#0EA5E9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;line-height:1.1;}
.hero-subtitle{color:var(--text-muted);font-size:13px;margin-top:4px;}

/* ════════════════════════════════════════════════════════════════
   FORM (ô lọc, form đăng nhập, form đổi mật khẩu...)
════════════════════════════════════════════════════════════════ */
div[data-testid="stForm"]{background:var(--bg-surface)!important;border:1px solid var(--border)!important;border-radius:var(--radius-md)!important;padding:16px 20px!important;box-shadow:var(--shadow-sm)!important;}

/* ── Selectbox & Multiselect (ô chọn lọc) ── */
.stSelectbox>div>div,.stMultiSelect>div>div{background:var(--bg-surface)!important;border:1.5px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;box-shadow:var(--shadow-sm)!important;}
.stSelectbox>div>div:focus-within,.stMultiSelect>div>div:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(37,99,235,.12)!important;}

/* ════════════════════════════════════════════════════════════════
   NÚT BẤM
   → Nút primary (xanh):  thay --accent và --accent-hover
   → Nút thường (trắng):  thay --border, --text-secondary
════════════════════════════════════════════════════════════════ */
.stFormSubmitButton>button{background:var(--accent)!important;color:white!important;border:none!important;border-radius:var(--radius-sm)!important;font-weight:700!important;padding:8px 22px!important;box-shadow:var(--shadow-sm)!important;transition:all .2s!important;}
.stFormSubmitButton>button:hover{background:var(--accent-hover)!important;box-shadow:var(--shadow-md)!important;transform:translateY(-1px)!important;}
.stButton>button{border:1.5px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text-secondary)!important;background:var(--bg-surface)!important;font-weight:600!important;font-size:13px!important;transition:all .18s!important;box-shadow:var(--shadow-sm)!important;}
.stButton>button:hover{border-color:var(--accent)!important;color:var(--accent)!important;background:var(--accent-light)!important;box-shadow:var(--shadow-md)!important;transform:translateY(-1px)!important;}
.stButton>button[data-testid="baseButton-primary"]{background:var(--accent)!important;color:white!important;border-color:var(--accent)!important;}
.stButton>button[data-testid="baseButton-primary"]:hover{background:var(--accent-hover)!important;}
.stButton>button:disabled{opacity:.4!important;transform:none!important;cursor:not-allowed!important;}

/* ════════════════════════════════════════════════════════════════
   METRIC CARDS (5 ô thống kê đầu trang: Tổng sự kiện, HOT, v.v.)
   → Màu viền trên mỗi card: thay màu trong các .metric-card::before
   → Màu chữ số lớn: thay --text-primary trong .metric-value
   → Màu chữ nhỏ bên dưới: thay --accent trong .metric-sub
════════════════════════════════════════════════════════════════ */
.metric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:16px 0;}
@media(max-width:900px){.metric-grid{grid-template-columns:repeat(3,1fr);}}
@media(max-width:600px){.metric-grid{grid-template-columns:repeat(2,1fr);}}
.metric-card{background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:16px 18px;position:relative;overflow:hidden;transition:box-shadow .2s,transform .2s;box-shadow:var(--shadow-sm);}
.metric-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#2563EB,#0EA5E9);}  /* ← viền xanh card mặc định */
.metric-card.green::before{background:linear-gradient(90deg,#16A34A,#22C55E);}   /* ← card Nhóm SĐK nóng nhất */
.metric-card.amber::before{background:linear-gradient(90deg,#D97706,#F59E0B);}   /* ← card Phân khúc */
.metric-card.red::before{background:linear-gradient(90deg,#DC2626,#EF4444);}     /* ← card HOT */
.metric-card.purple::before{background:linear-gradient(90deg,#7C3AED,#8B5CF6);} /* ← card Nguồn dẫn dắt */
.metric-label{font-size:10.5px;color:var(--text-secondary);font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px;}
.metric-value{font-size:28px;font-weight:800;color:var(--text-primary);line-height:1;font-family:'JetBrains Mono',monospace;}
.metric-sub{font-size:12px;color:var(--accent);margin-top:5px;font-weight:600;}

/* ════════════════════════════════════════════════════════════════
   SECTION HEADER ("Analytics · Tổng quan Thị trường...")
   → Badge xanh nhỏ: thay --accent và --accent-light
   → Tiêu đề lớn: thay --text-primary
════════════════════════════════════════════════════════════════ */
.section-header{display:flex;align-items:center;gap:10px;padding:20px 0 12px 0;border-bottom:2px solid var(--border);margin-bottom:16px;}
.section-badge{background:var(--accent-light);border:1px solid #BFDBFE;color:var(--accent);padding:3px 12px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;}
.section-title{font-size:16px;font-weight:700;color:var(--text-primary);margin:0;}

/* ════════════════════════════════════════════════════════════════
   TABS (thanh tab: DATA / STRATEGIC INFO / KNOWLEDGE HUB / ...)
   → Nền thanh tab:        thay --bg-subtle trong tab-list
   → Chữ tab thường:       thay --text-muted trong [data-baseweb="tab"]
   → Chữ tab khi hover:    thay --accent trong :hover
   → Tab đang active:      thay --accent (chữ + gạch chân)
   → Nền panel tab:        thay --bg-surface trong tab-panel
════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"]{background:var(--bg-subtle)!important;border-radius:var(--radius-lg) var(--radius-lg) 0 0!important;border:1px solid var(--border)!important;border-bottom:none!important;padding:6px 8px 0 8px!important;gap:4px!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--text-muted)!important;border-radius:8px 8px 0 0!important;font-weight:600!important;font-size:13px!important;padding:8px 18px!important;border:none!important;transition:all .18s!important;}
.stTabs [data-baseweb="tab"]:hover{color:var(--accent)!important;background:var(--bg-surface)!important;}
.stTabs [aria-selected="true"]{background:var(--bg-surface)!important;color:var(--accent)!important;border-bottom:3px solid var(--accent)!important;font-weight:700!important;}
.stTabs [data-baseweb="tab-panel"]{background:var(--bg-surface)!important;border:1px solid var(--border)!important;border-radius:0 0 var(--radius-lg) var(--radius-lg)!important;padding:24px!important;box-shadow:var(--shadow-sm)!important;}

/* ════════════════════════════════════════════════════════════════
   CHART TITLE (tiêu đề nhỏ phía trên mỗi biểu đồ)
   → Màu chữ: thay --accent
   → Màu gạch chân: thay #BFDBFE
════════════════════════════════════════════════════════════════ */
.chart-title{font-size:12px;font-weight:800;color:var(--accent);text-transform:uppercase;letter-spacing:.8px;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #BFDBFE;}

/* ════════════════════════════════════════════════════════════════
   NEWS CARDS (thẻ tin tức trong News Feed)
   → Viền trái theo nhóm: N1=xanh, N2=xanh lá, N3=vàng
   → Card HOT: viền đỏ nhạt
════════════════════════════════════════════════════════════════ */
.news-card{background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:20px;margin-bottom:10px;transition:box-shadow .2s,transform .2s;box-shadow:var(--shadow-sm);}
.news-card:hover{box-shadow:var(--shadow-md);transform:translateY(-1px);}
.news-card.hot{border-color:#FECACA!important;box-shadow:0 0 0 3px rgba(220,38,38,.08),var(--shadow-md)!important;background:#FFFAFA!important;}
.news-card.n1{border-left:4px solid var(--accent);}   /* ← Nhóm 1 Trực tiếp */
.news-card.n2{border-left:4px solid var(--green);}    /* ← Nhóm 2 Gián tiếp */
.news-card.n3{border-left:4px solid var(--amber);}    /* ← Nhóm 3 Cảnh báo sớm */

/* ── Tags nhỏ trong news card ── */
.news-meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px;}
.tag{padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:.2px;}
.tag-time{background:var(--bg-subtle);color:var(--text-muted);}
.tag-source{background:var(--accent-light);color:var(--accent);border:1px solid #BFDBFE;}
.tag-event{background:#DCFCE7;color:#15803D;border:1px solid #BBF7D0;}
.tag-type{background:var(--purple-light);color:var(--purple);border:1px solid #DDD6FE;}
.tag-lifecycle{background:var(--amber-light);color:var(--amber);border:1px solid #FDE68A;}
.tag-n1{background:var(--accent-light);color:var(--accent);border:1px solid #BFDBFE;font-weight:700;}
.tag-n2{background:var(--green-light);color:var(--green);border:1px solid #BBF7D0;font-weight:700;}
.tag-n3{background:var(--amber-light);color:var(--amber);border:1px solid #FDE68A;font-weight:700;}
.tag-hot{background:var(--red);color:white;font-weight:700;animation:pulse 2s infinite;border-radius:20px;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.75;}}
.news-title{font-size:16px;font-weight:700;color:var(--accent);margin:0 0 8px 0;line-height:1.4;}
.news-summary{font-size:14px;color:var(--text-secondary);line-height:1.7;margin:0 0 12px 0;}
.news-link{font-size:13px;color:var(--accent);text-decoration:none;font-weight:600;}
.news-link:hover{text-decoration:underline;}

/* ════════════════════════════════════════════════════════════════
   FILTER BADGE (hiển thị bộ lọc đang active từ biểu đồ)
════════════════════════════════════════════════════════════════ */
.filter-active{background:var(--accent-light);border:1px solid #BFDBFE;border-radius:var(--radius-sm);padding:6px 14px;font-size:12px;color:var(--accent);margin-bottom:12px;display:inline-block;font-weight:600;}

/* ════════════════════════════════════════════════════════════════
   EXPANDER (các khối thu gọn / mở rộng)
   → Màu chữ header: thay --accent
   → Màu nền header: thay --accent-light
════════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader{background:var(--accent-light)!important;border:1px solid #BFDBFE!important;border-radius:var(--radius-sm)!important;color:var(--accent)!important;font-size:13px!important;font-weight:700!important;}
.streamlit-expanderContent{background:var(--bg-surface)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p{color:var(--accent)!important;font-weight:700!important;font-size:13px!important;}
[data-testid="stExpander"]{border:1px solid #BFDBFE!important;border-radius:var(--radius-sm)!important;background:var(--accent-light)!important;}

/* ════════════════════════════════════════════════════════════════
   INFO BLOCKS (các ô thông tin trong news card detail)
════════════════════════════════════════════════════════════════ */
.info-block{background:var(--bg-subtle);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px 14px;margin-bottom:8px;}
.info-block .label{font-size:11px;color:var(--accent);font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;}
.info-block .value{font-size:14px;color:var(--text-primary);font-weight:600;line-height:1.5;}
.info-block-label{font-size:11px;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.5px;margin:4px 0 10px 0;display:block;}

/* ════════════════════════════════════════════════════════════════
   WIDGET LABELS (nhãn chữ phía trên ô input, selectbox, radio...)
   → Đổi color để thay màu tất cả nhãn cùng lúc
════════════════════════════════════════════════════════════════ */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"],
.stSelectbox>label,[data-baseweb="label"],
.stMultiSelect>label,.stTextInput>label,
.stNumberInput>label,.stTextArea>label,
.stDateInput>label,.stTimeInput>label,
.stSlider>label,.stToggle>label{
  color:var(--text-primary)!important;font-weight:700!important;font-size:13px!important;}
.stCheckbox>label{color:var(--text-primary)!important;font-weight:600!important;}

/* ════════════════════════════════════════════════════════════════
   RADIO BUTTONS (nút chọn chế độ xem: Lead Pipeline / Executive...)
   → Màu nền unselected: thay #EEF1F6
   → Màu viền unselected: thay #B8C2D4
   → Màu chữ:            thay #111111
   → Màu nền selected:   thay #DBEAFE
   → Màu viền selected:  thay #2563EB
════════════════════════════════════════════════════════════════ */
.stRadio>[data-testid="stWidgetLabel"] p{color:var(--accent)!important;font-weight:700!important;}
.stRadio>div{gap:6px!important;}
.stRadio label{background:#EEF1F6!important;border:1.5px solid #B8C2D4!important;border-radius:var(--radius-sm)!important;padding:7px 16px!important;color:#000000!important;font-weight:700!important;font-size:13px!important;transition:all .18s!important;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;}
.stRadio label p,.stRadio label div,.stRadio label span{color:#000000!important;font-weight:700!important;}
.stRadio label:hover{background:#DBEAFE!important;border-color:#2563EB!important;color:#000000!important;}
.stRadio label:hover p,.stRadio label:hover div,.stRadio label:hover span{color:#000000!important;}
.stRadio label:has(input:checked){background:#DBEAFE!important;border-color:#2563EB!important;color:#000000!important;font-weight:800!important;box-shadow:0 0 0 3px rgba(37,99,235,.15)!important;}
.stRadio label:has(input:checked) p,.stRadio label:has(input:checked) div,.stRadio label:has(input:checked) span{color:#000000!important;font-weight:800!important;}

/* ════════════════════════════════════════════════════════════════
   TEXT INPUT (ô nhập chữ)
════════════════════════════════════════════════════════════════ */
.stTextInput>div>div>input{background:var(--bg-surface)!important;border:1.5px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;font-family:'Plus Jakarta Sans',sans-serif!important;}
.stTextInput>div>div>input:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(37,99,235,.12)!important;}

/* ════════════════════════════════════════════════════════════════
   CAPTION & TEXT NHỎ (st.caption, chú thích bên dưới biểu đồ...)
════════════════════════════════════════════════════════════════ */
[data-testid="stCaptionContainer"] p,.stCaptionContainer p{color:var(--text-secondary)!important;font-size:12px!important;font-weight:600!important;}

/* ════════════════════════════════════════════════════════════════
   METRIC (st.metric — số liệu Streamlit built-in)
════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] label{color:var(--text-secondary)!important;font-weight:700!important;}
[data-testid="stMetricValue"]{color:var(--text-primary)!important;font-weight:800!important;}

/* ════════════════════════════════════════════════════════════════
   DATAFRAME / BẢNG DỮ LIỆU
   → Header bảng: màu chữ và nền
════════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] th{color:var(--accent)!important;font-weight:700!important;background:var(--accent-light)!important;}

/* ── Toggle ── */
[data-testid="stToggle"] p{color:var(--text-primary)!important;font-weight:700!important;}

/* ── Number input ── */
.stNumberInput label p{color:var(--text-primary)!important;font-weight:700!important;}

/* ════════════════════════════════════════════════════════════════
   API USAGE BOXES (tab Control — ô hiển thị API key, usage bar)
════════════════════════════════════════════════════════════════ */
.api-usage-box{background:var(--bg-subtle);border:1px solid var(--border);border-radius:var(--radius-md);padding:14px 16px;margin:12px 0;}
.usage-bar-wrap{background:var(--border);border-radius:4px;height:8px;overflow:hidden;margin:6px 0;}
.usage-bar-fill{height:8px;border-radius:4px;transition:width .4s ease;}
/* Badge trạng thái: OK=xanh lá, WARN=vàng, DANGER=đỏ */
.api-badge{padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;display:inline-block;}
.api-badge.ok{background:var(--green-light);border:1px solid #BBF7D0;color:var(--green);}
.api-badge.warn{background:var(--amber-light);border:1px solid #FDE68A;color:var(--amber);}
.api-badge.danger{background:var(--red-light);border:1px solid #FECACA;color:var(--red);}
.api-key-box{background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:14px 16px;margin-bottom:12px;}

/* ════════════════════════════════════════════════════════════════
   RESPONSIVE (màn hình nhỏ)
════════════════════════════════════════════════════════════════ */
@media(max-width:768px){.stTabs [data-baseweb="tab"]{padding:7px 10px!important;font-size:11px!important;}.metric-value{font-size:22px!important;}.news-title{font-size:15px!important;}.news-card{padding:14px!important;}}
@media(max-width:480px){.stTabs [data-baseweb="tab"]{padding:6px 8px!important;font-size:10px!important;}.hero-title{font-size:20px!important;}}
</style>""", unsafe_allow_html=True)

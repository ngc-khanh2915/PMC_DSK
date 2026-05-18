import os

import streamlit as st

from utils import BASE_DIR, save_password_to_env


def render():
    st.markdown("""
    <div style='background:var(--accent-light);border:1.5px solid #BFDBFE;
         border-radius:var(--radius-md);padding:14px 18px;margin-bottom:18px;'>
      <div style='font-size:14px;font-weight:700;color:var(--accent);margin-bottom:4px;'>
        👤 Tài khoản &amp; Bảo mật</div>
      <div style='font-size:12px;color:var(--text-secondary);'>
        Đổi mật khẩu đăng nhập và cấu hình mã quên mật khẩu.</div>
    </div>""", unsafe_allow_html=True)

    _AUTH_USER = os.getenv("DASHBOARD_USER", "admin")
    _AUTH_PASS = os.getenv("DASHBOARD_PASS", "admin123")

    # ── Thông tin tài khoản ──────────────────────────────────────────
    st.markdown("<div class='chart-title'>ℹ️ Thông tin tài khoản</div>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div class='api-key-box'>"
        f"<div style='font-size:13px;color:var(--text-secondary);margin-bottom:6px;'>"
        f"👤 Tên đăng nhập: <b style='color:var(--text-primary);'>{_AUTH_USER}</b></div>"
        f"<div style='font-size:12px;color:var(--text-muted);'>"
        f"Mật khẩu: {'•' * len(_AUTH_PASS)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Đổi mật khẩu ────────────────────────────────────────────────
    st.markdown("<div class='chart-title'>🔒 Đổi mật khẩu</div>",
                unsafe_allow_html=True)

    with st.form("change_pass_form", clear_on_submit=True):
        cp1, cp2 = st.columns(2)
        with cp1:
            old_pass     = st.text_input("Mật khẩu hiện tại", type="password",
                                         placeholder="••••••••")
            new_pass     = st.text_input("Mật khẩu mới", type="password",
                                         placeholder="Tối thiểu 6 ký tự")
        with cp2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password",
                                         placeholder="Nhập lại mật khẩu mới")

        if st.form_submit_button("💾 Đổi mật khẩu", type="primary",
                                  use_container_width=True):
            if not old_pass:
                st.error("Vui lòng nhập mật khẩu hiện tại.")
            elif old_pass != _AUTH_PASS:
                st.error("Mật khẩu hiện tại không đúng.")
            elif not new_pass:
                st.error("Vui lòng nhập mật khẩu mới.")
            elif len(new_pass) < 6:
                st.error("Mật khẩu mới phải có ít nhất 6 ký tự.")
            elif new_pass != confirm_pass:
                st.error("Mật khẩu xác nhận không khớp.")
            elif new_pass == old_pass:
                st.warning("Mật khẩu mới phải khác mật khẩu hiện tại.")
            else:
                if save_password_to_env(new_pass):
                    st.success("Đổi mật khẩu thành công! Dùng mật khẩu mới cho lần đăng nhập tiếp theo.")
                else:
                    st.error("Không lưu được. Kiểm tra quyền ghi file .env")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Trạng thái quên mật khẩu qua email ──────────────────────────
    st.markdown("<div class='chart-title'>📧 Quên mật khẩu qua Email (OTP)</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:12px;color:var(--text-muted);margin-bottom:10px;'>"
        "Khi nhấn 'Quên mật khẩu?' ở trang đăng nhập, hệ thống tự sinh mã OTP "
        "6 số và gửi đến email bên dưới. Mã có hiệu lực 10 phút.</div>",
        unsafe_allow_html=True,
    )

    _notify = os.getenv("NOTIFY_EMAIL", "")
    _smtp_user = os.getenv("SMTP_USER", "")
    _smtp_pass = os.getenv("SMTP_PASS", "")
    _smtp_ok = bool(_smtp_user and _smtp_pass and _notify)

    if _smtp_ok:
        _parts  = _notify.split("@")
        _masked = (_parts[0][:2] + "***@" + _parts[1]) if len(_parts) == 2 else _notify
        st.markdown(
            f"<div class='api-key-box'>"
            f"<span class='api-badge ok'>🟢 Đã cấu hình</span>"
            f"<span style='font-size:12px;color:var(--text-muted);margin-left:10px;'>"
            f"OTP sẽ gửi đến: <b>{_masked}</b></span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        missing = []
        if not _smtp_user:
            missing.append("SMTP_USER")
        if not _smtp_pass:
            missing.append("SMTP_PASS")
        if not _notify:
            missing.append("NOTIFY_EMAIL")
        st.markdown(
            f"<div class='api-key-box'>"
            f"<span class='api-badge warn'>🟡 Chưa cấu hình</span>"
            f"<span style='font-size:12px;color:var(--text-muted);margin-left:10px;'>"
            f"Thiếu: {', '.join(missing)} trong .env</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.info("Thêm các biến trên vào file .env (xem .env.example) để bật tính năng quên mật khẩu.")

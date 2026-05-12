import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from streamlit_drawable_canvas import st_canvas
import holidays
import smtplib
from email.mime.text import MIMEText

# --- 1. Page Configuration ---
st.set_page_config(page_title="캐나다 본한인교회 사역자 및 직원 휴가 시스템", layout="wide")

# --- ⚙️ EMAIL CONFIGURATION ---
SMTP_SERVER = "gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-church-email@gmail.com"      
SENDER_PASSWORD = "xxxx-xxxx-xxxx-xxxx"           
ADMIN_NOTIFY_EMAIL = "admin-records@gmail.com"     

if 'admin_password' not in st.session_state:
    st.session_state.admin_password = "1234"

# --- 2. Automated Email Sender Logic ---
def send_confirmation_email(recipient_email, subject, body_text):
    try:
        msg = MIMEText(body_text)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"⚠️ 이메일 발송 실패: {e}")
        return False

# --- 3. Dynamic Ontario Holidays Loader ---
def get_ontario_holidays(year):
    ca_on_holidays = holidays.Canada(subdiv='ON', years=year)
    holiday_dict = {}
    for date, name in sorted(ca_on_holidays.items()):
        if name in ["Easter Sunday", "Heritage Day"]: continue
        if "Civic Holiday" in name: name = "Civic Holiday"
        holiday_dict[date.strftime("%Y-%m-%d")] = name
    return holiday_dict

# --- 4. Custom CSS Styles ---
st.markdown("""
<style>
    .app-title { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px; }
    .stButton>button { border-radius: 12px !important; border: 1px solid #ddd !important; font-weight: 500 !important; }
    .card-box { background-color: #F8F9FA; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
    .card-label { font-size: 14px; color: #666; }
    .card-value { font-size: 28px; font-weight: bold; }
    .list-container { border: 1px solid #EAEAEA; border-radius: 16px; padding: 25px; background-color: white; }
    .profile-circle {
        width: 42px; height: 42px; border-radius: 50%; color: white;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 15px;
    }
    .bg-pastor { background-color: #2E5B88; }
    .bg-sub-pastor { background-color: #4A76A8; }
    .bg-helper { background-color: #549A74; }
    .bg-staff { background-color: #A370A8; }
</style>
""", unsafe_allow_html=True)

# --- 5. Initialize Staff Data ---
if 'staff' not in st.session_state or st.session_state.staff.empty:
    st.session_state.staff = pd.DataFrame([
        {'Name': '고영민', 'Position': '목사', 'Total_Leave': 20, 'Email': ''},
        {'Name': '강진숙', 'Position': '부목사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '이중석', 'Position': '부목사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '최민수', 'Position': '부목사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '김제훈', 'Position': '부목사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '이병학', 'Position': '전도사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '권영미', 'Position': '전도사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '안휘수', 'Position': '전도사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '김현주', 'Position': '전도사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '이혜빈', 'Position': '간사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '김혜진', 'Position': '간사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '신근수', 'Position': '간사', 'Total_Leave': 15, 'Email': ''},
        {'Name': '임주현', 'Position': '사무', 'Total_Leave': 15, 'Email': ''},
        {'Name': '원재엽', 'Position': '관리', 'Total_Leave': 15, 'Email': ''},
        {'Name': '정주현', 'Position': '미디어', 'Total_Leave': 15, 'Email': ''},
        {'Name': '한난희', 'Position': '미디어', 'Total_Leave': 15, 'Email': ''},
        {'Name': '박은국', 'Position': '미디어', 'Total_Leave': 15, 'Email': ''},
        {'Name': '민옥화', 'Position': '재정부', 'Total_Leave': 15, 'Email': ''}
    ])

if 'leaves' not in st.session_state:
    st.session_state.leaves = pd.DataFrame(columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])

if 'menu_sel' not in st.session_state:
    st.session_state.menu_sel = "현황"

def calculate_church_days(start_date, end_date, l_type):
    if l_type == "Half": return 0.5
    days = 0
    curr = start_date
    while curr <= end_date:
        yearly_holidays = get_ontario_holidays(curr.year)
        if curr.weekday() < 5 and curr.strftime("%Y-%m-%d") not in yearly_holidays:
            days += 1
        curr += timedelta(days=1)
    return days

# --- 6. Navigation (Fixed Indexing) ---
st.markdown('<p class="app-title">🇨🇦 캐나다 본한인교회 사역자 및 직원 휴가 시스템</p>', unsafe_allow_html=True)
m_cols = st.columns(5)
if m_cols[0].button("📊 현황", use_container_width=True): st.session_state.menu_sel = "현황"
if m_cols[1].button("📅 달력", use_container_width=True): st.session_state.menu_sel = "달력"
if m_cols[2].button("🔒 직원", use_container_width=True): st.session_state.menu_sel = "직원"
if m_cols[3].button("📝 신청", use_container_width=True): st.session_state.menu_sel = "신청"
if m_cols[4].button("📋 내역", use_container_width=True): st.session_state.menu_sel = "내역"

# --- 7. Menu Views ---
if st.session_state.menu_sel == "현황":
    # Stats
    total_approved = st.session_state.leaves[st.session_state.leaves['Status'] == 'Approved']['Days'].sum() if not st.session_state.leaves.empty else 0
    total_pending = len(st.session_state.leaves[st.session_state.leaves['Status'] == 'Pending']) if not st.session_state.leaves.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-box"><div class="card-label">전체 직원</div><div class="card-value">{len(st.session_state.staff)}명</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-box"><div class="card-label">총사용 휴가</div><div class="card-value">{int(total_approved)}일</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-box"><div class="card-label">대기 중</div><div class="card-value">{total_pending}건</div></div>', unsafe_allow_html=True)
    
    for idx, row in st.session_state.staff.iterrows():
        # Safe float conversion for metrics
        try: total_limit = float(row['Total_Leave'])
        except: total_limit = 0.0
        
        person_leaves = st.session_state.leaves[(st.session_state.leaves['Name'] == row['Name']) & (st.session_state.leaves['Status'] == 'Approved')]
        used = person_leaves['Days'].sum() if not person_leaves.empty else 0
        rem = total_limit - used
        percent = (used / total_limit) if total_limit > 0 else 0
        
        st.write(f"**{row['Name']}** ({row['Position']})")
        st.progress(min(percent, 1.0))
        st.write(f"사용: {used}일 / 잔여: {rem}일")
        st.divider()

elif st.session_state.menu_sel == "직원":
    st.title("👤 사역자 명단 관리")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == st.session_state.admin_password:
        edited_staff = st.data_editor(st.session_state.staff, num_rows="dynamic", use_container_width=True)
        if st.button("💾 변경사항 최종 저장"):
            # SAFE CONVERSION: Handles empty or invalid leave numbers
            edited_staff['Total_Leave'] = pd.to_numeric(edited_staff['Total_Leave'], errors='coerce').fillna(0).astype(int)
            st.session_state.staff = edited_staff
            st.success("🎉 저장되었습니다!")
            st.rerun()
    else:
        st.warning("비밀번호를 입력하세요.")
        st.dataframe(st.session_state.staff, use_container_width=True)

elif st.session_state.menu_sel == "신청":
    st.title("📝 휴가 신청서")
    with st.form("leave_form"):
        name = st.selectbox("신청자", st.session_state.staff['Name'])
        l_type = st.selectbox("종류", ["Vacation", "Half", "Sick", "Unpaid"])
        start = st.date_input("시작일")
        end = st.date_input("종료일")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#F5F5F5", height=120, width=400, key="sig")
        if st.form_submit_button("제출"):
            days = calculate_church_days(start, end, l_type)
            new_entry = pd.DataFrame([[name, l_type, str(start), str(end), days, 'Pending', 'Yes', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], 
                                     columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])
            st.session_state.leaves = pd.concat([st.session_state.leaves, new_entry], ignore_index=True)
            st.success("신청되었습니다!")

elif st.session_state.menu_sel == "내역":
    st.title("📋 휴가 결재")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == st.session_state.admin_password:
        edited = st.data_editor(st.session_state.leaves, num_rows="dynamic", use_container_width=True,
                               column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Approved", "Rejected"])})
        if st.button("결재 저장"):
            st.session_state.leaves = edited
            st.rerun()
    else:
        st.table(st.session_state.leaves)

elif st.session_state.menu_sel == "달력":
    st.title("📅 월별 달력")
    yy = st.selectbox("연도", list(range(2026, 2037)))
    mm = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    # Basic calendar display
    st.write(calendar.month(yy, mm))
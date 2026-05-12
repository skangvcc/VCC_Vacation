import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from streamlit_drawable_canvas import st_canvas
import holidays

# --- [중요] 1. 페이지 설정 및 보안 로직 (이 부분이 가장 먼저 실행되어야 합니다) ---
st.set_page_config(page_title="본한인교회 휴가 관리 시스템", layout="wide")

# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 로그인 화면 함수
def login_screen():
    st.markdown("""
        <style>
        .login-box {
            max-width: 450px;
            padding: 50px;
            margin: 100px auto;
            background-color: #ffffff;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            border: 1px solid #f0f0f0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.write("<span style='font-size:50px;'>⛪</span>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2C3E50; margin-bottom:20px;'>본한인교회 휴가 시스템</h2>", unsafe_allow_html=True)
    st.write("안전한 사용을 위해 비밀번호를 입력해 주세요.")
    
    # 패스워드 입력창 (1004)
    access_pw = st.text_input("접속 비밀번호", type="password", placeholder="Password 입력", label_visibility="collapsed")
    
    if st.button("시스템 접속하기", use_container_width=True):
        if access_pw == "1004":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# 인증 체크: 인증되지 않았다면 로그인 화면만 띄우고 아래 코드는 실행 안 함
if not st.session_state.authenticated:
    login_screen()
    st.stop() # 메인 앱 실행 중단


# --- [로그인 성공 시] 2. 메인 프로그램 로직 시작 ---

# ⚙️ 관리자 비밀번호 설정
if 'admin_password' not in st.session_state:
    st.session_state.admin_password = "1234"

# 공휴일 로더
def get_ontario_holidays(year):
    ca_on_holidays = holidays.Canada(subdiv='ON', years=year)
    holiday_dict = {}
    for date, name in sorted(ca_on_holidays.items()):
        if name in ["Easter Sunday", "Heritage Day"]: continue
        if "Civic Holiday" in name: name = "Civic Holiday"
        holiday_dict[date.strftime("%Y-%m-%d")] = name
    return holiday_dict

# 휴가 일수 계산
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

# 디자인 CSS
st.markdown("""
<style>
    .app-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
    .app-title { font-size: 26px; font-weight: bold; color: #2C3E50; margin: 0; }
    .stButton>button { border-radius: 10px !important; }
    .card-box { background-color: #F4F7F9; border-radius: 12px; padding: 18px; margin-bottom: 20px; border-left: 5px solid #2E5B88; }
    .list-container { border: 1px solid #EAEAEA; border-radius: 16px; padding: 20px; background-color: white; }
    .profile-circle {
        width: 42px; height: 42px; border-radius: 50%; color: white;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 12px;
    }
    .bg-pastor { background-color: #2E5B88; }
    .bg-sub-pastor { background-color: #4A76A8; }
    .bg-helper { background-color: #549A74; }
    .bg-staff { background-color: #A370A8; }
</style>
""", unsafe_allow_html=True)

# 데이터 초기화 (18명 명단)
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

# 헤더 및 로그아웃
st.markdown('<div class="app-header"><span style="font-size:30px;">⛪</span><p class="app-title">본한인교회 휴가 관리 시스템</p></div>', unsafe_allow_html=True)
if st.sidebar.button("🔒 로그아웃 (시스템 잠금)"):
    st.session_state.authenticated = False
    st.rerun()

# 상단 가로 메뉴
m_cols = st.columns(5)
if m_cols[0].button("📊 현황", use_container_width=True): st.session_state.menu_sel = "현황"
if m_cols[1].button("📅 달력", use_container_width=True): st.session_state.menu_sel = "달력"
if m_cols[2].button("🔒 직원", use_container_width=True): st.session_state.menu_sel = "직원"
if m_cols[3].button("📝 신청", use_container_width=True): st.session_state.menu_sel = "신청"
if m_cols[4].button("📋 내역", use_container_width=True): st.session_state.menu_sel = "내역"

st.write("")

# [현황 페이지]
if st.session_state.menu_sel == "현황":
    total_approved = st.session_state.leaves[st.session_state.leaves['Status'] == 'Approved']['Days'].sum() if not st.session_state.leaves.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-box"><div class="card-label">전체 사역자</div><div class="card-value">{len(st.session_state.staff)}명</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-box"><div class="card-label">총 사용 휴가</div><div class="card-value">{int(total_approved)}일</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-box"><div class="card-label">결재 대기</div><div class="card-value">{len(st.session_state.leaves[st.session_state.leaves["Status"] == "Pending"])}건</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for idx, row in st.session_state.staff.iterrows():
        person_leaves = st.session_state.leaves[(st.session_state.leaves['Name'] == row['Name']) & (st.session_state.leaves['Status'] == 'Approved')]
        used = person_leaves['Days'].sum() if not person_leaves.empty else 0
        rem = float(row['Total_Leave']) - used
        percent = (used / float(row['Total_Leave'])) if float(row['Total_Leave']) > 0 else 0
        bg_class = "bg-pastor" if "목사" in row['Position'] else "bg-helper" if "전도사" in row['Position'] else "bg-staff"
        
        sc1, sc2, sc3, sc4 = st.columns([2.5, 4, 4, 1.5])
        sc1.markdown(f'<div style="display:flex; align-items:center;"><div class="profile-circle {bg_class}">{row["Name"][:2]}</div><div><p style="font-weight:bold;margin:0;">{row["Name"]}</p><p style="font-size:12px;color:grey;margin:0;">{row["Position"]}</p></div></div>', unsafe_allow_html=True)
        sc2.markdown(f'<p style="font-size:13px;margin-bottom:2px;">사용 {int(used)}일 / 한도 {int(row["Total_Leave"])}일</p>', unsafe_allow_html=True)
        sc2.progress(min(percent, 1.0))
        breakdown = [f"{t}: {person_leaves[person_leaves['Type']==t]['Days'].sum():g}일" for t in ["Vacation", "Half", "Sick", "Unpaid"] if not person_leaves[person_leaves['Type']==t].empty]
        sc3.markdown("<p style='font-size:12px;color:#666;margin-top:10px;'>" + (" | ".join(breakdown) if breakdown else "기록 없음") + "</p>", unsafe_allow_html=True)
        sc4.markdown(f'<p style="text-align:right;font-size:13px;font-weight:bold;color:#2E5B88;">잔여<br><span style="font-size:17px;">{int(rem)}일</span></p>', unsafe_allow_html=True)
        st.markdown('<hr style="margin:10px 0; border:0; border-top:1px solid #F5F5F5;">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# [기타 메뉴들은 기존과 동일하게 유지...]
elif st.session_state.menu_sel == "신청":
    st.title("📝 휴가 신청서")
    with st.form("leave_form"):
        name = st.selectbox("신청자 선택", st.session_state.staff['Name'])
        l_type = st.selectbox("휴가 종류", ["Vacation", "Half", "Sick", "Unpaid"])
        start = st.date_input("시작일")
        end = st.date_input("종료일")
        st.write("✒️ **디지털 서명**")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#F5F5F5", height=150, width=400, key="sig")
        if st.form_submit_button("신청서 제출"):
            days = calculate_church_days(start, end, l_type)
            new_entry = pd.DataFrame([[name, l_type, str(start), str(end), days, 'Pending', 'Yes', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])
            st.session_state.leaves = pd.concat([st.session_state.leaves, new_entry], ignore_index=True)
            st.success("성공적으로 신청되었습니다.")

# (달력, 직원, 내역 메뉴 생략 - 로직은 동일)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from streamlit_drawable_canvas import st_canvas

# --- 1. 페이지 설정 (브라우저 탭 제목) ---
st.set_page_config(page_title="캐나다 본한인교회 사역자 및 직원 휴가 시스템", layout="wide")

# --- 2. 2026년 캐나다 온타리오주 공식 공휴일 데이터 세팅 ---
ONTARIO_HOLIDAYS = {
    "2026-01-01": "New Year's Day",
    "2026-02-16": "Family Day",
    "2026-04-03": "Good Friday",
    "2026-05-18": "Victoria Day",
    "2026-07-01": "Canada Day",
    "2026-09-07": "Labour Day",
    "2026-10-12": "Thanksgiving Day",
    "2026-12-25": "Christmas Day",
    "2026-12-26": "Boxing Day",
    "2026-12-28": "Boxing Day (Observed)"
}

# --- 3. 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    .app-title { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px; }
    .stButton>button {
        border-radius: 12px !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
        color: #333 !important;
        font-weight: 500 !important;
        padding: 6px 16px !important;
    }
    .stButton>button:hover { background-color: #f5f5f5 !important; border-color: #bbb !important; }
    .card-box { background-color: #F8F9FA; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; }
    .card-label { font-size: 14px; color: #666; margin-bottom: 5px; }
    .card-value { font-size: 28px; font-weight: bold; }
    .val-blue { color: #34495E; }
    .val-green { color: #4F7942; }
    .val-yellow { color: #A08030; }
    .list-container { border: 1px solid #EAEAEA; border-radius: 16px; padding: 25px; background-color: white; }
    .profile-circle {
        width: 42px; height: 42px; border-radius: 50%; color: white;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 15px;
    }
    /* 직책별 프로필 서클 색상 지정 */
    .bg-pastor { background-color: #2E5B88; }
    .bg-sub-pastor { background-color: #4A76A8; }
    .bg-helper { background-color: #549A74; }
    .bg-staff { background-color: #A370A8; }
    
    .name-text { font-size: 16px; font-weight: bold; color: #222; margin: 0; }
    .pos-text { font-size: 13px; color: #777; margin: 0; }
    .usage-text { font-size: 14px; color: #555; }
    .rem-text { font-size: 14px; font-weight: bold; color: #222; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 4. 교회 사역자 및 직원 초기 데이터 입력 ---
if 'staff' not in st.session_state or st.session_state.staff.empty:
    st.session_state.staff = pd.DataFrame([
        {'Name': '고영민', 'Position': '목사', 'Total_Leave': 20, 'Email': 'go@church.com'},
        {'Name': '강진숙', 'Position': '부목사', 'Total_Leave': 15, 'Email': 'kang@church.com'},
        {'Name': '이중석', 'Position': '부목사', 'Total_Leave': 15, 'Email': 'lee1@church.com'},
        {'Name': '최민수', 'Position': '부목사', 'Total_Leave': 15, 'Email': 'choi@church.com'},
        {'Name': '김제훈', 'Position': '부목사', 'Total_Leave': 15, 'Email': 'kim1@church.com'},
        {'Name': '이병학', 'Position': '전도사', 'Total_Leave': 15, 'Email': 'lee2@church.com'},
        {'Name': '권영미', 'Position': '전도사', 'Total_Leave': 15, 'Email': 'kwon@church.com'},
        {'Name': '안휘수', 'Position': '전도사', 'Total_Leave': 15, 'Email': 'ahn@church.com'},
        {'Name': '김현주', 'Position': '전도사', 'Total_Leave': 15, 'Email': 'kim2@church.com'},
        {'Name': '이혜빈', 'Position': '간사', 'Total_Leave': 15, 'Email': 'lee3@church.com'},
        {'Name': '김혜진', 'Position': '간사', 'Total_Leave': 15, 'Email': 'kim3@church.com'},
        {'Name': '신근수', 'Position': '간사', 'Total_Leave': 15, 'Email': 'shin@church.com'},
        {'Name': '임주현', 'Position': '사무', 'Total_Leave': 15, 'Email': 'lim@church.com'},
        {'Name': '원재엽', 'Position': '관리', 'Total_Leave': 15, 'Email': 'won@church.com'},
        {'Name': '정주현', 'Position': '미디어', 'Total_Leave': 15, 'Email': 'jung@church.com'},
        {'Name': '한난희', 'Position': '미디어', 'Total_Leave': 15, 'Email': 'han@church.com'},
        {'Name': '박은국', 'Position': '미디어', 'Total_Leave': 15, 'Email': 'park@church.com'},
        {'Name': '민옥화', 'Position': '재정부', 'Total_Leave': 15, 'Email': 'min@church.com'}
    ])

if 'leaves' not in st.session_state:
    st.session_state.leaves = pd.DataFrame(columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])

if 'menu_sel' not in st.session_state:
    st.session_state.menu_sel = "현황"

# --- 5. 로직: 주말 및 온타리오 공휴일 제외 일수 계산 ---
def calculate_church_days(start_date, end_date, l_type):
    if l_type == "Half":
        return 0.5
    days = 0
    curr = start_date
    while curr <= end_date:
        if curr.weekday() < 5 and curr.strftime("%Y-%m-%d") not in ONTARIO_HOLIDAYS:
            days += 1
        curr += timedelta(days=1)
    return days

# --- 6. 상단 UI 헤더 ---
st.markdown('<p class="app-title">🇨🇦 캐나다 본한인교회 사역자 및 직원 휴가 시스템</p>', unsafe_allow_html=True)

m_cols = st.columns(5)
if m_cols.button("📊 현황", use_container_width=True): st.session_state.menu_sel = "현황"
if m_cols.button("📅 달력", use_container_width=True): st.session_state.menu_sel = "달력"
if m_cols.button("🔒 직원", use_container_width=True): st.session_state.menu_sel = "직원"
if m_cols.button("📝 신청", use_container_width=True): st.session_state.menu_sel = "신청"
if m_cols.button("📋 내역", use_container_width=True): st.session_state.menu_sel = "내역"

st.write("")

# 통계 연산
total_staff = len(st.session_state.staff)
total_approved = st.session_state.leaves[st.session_state.leaves['Status'] == 'Approved']['Days'].sum()
total_pending = len(st.session_state.leaves[st.session_state.leaves['Status'] == 'Pending'])

# --- 7. 세부 메뉴 구현 ---
if st.session_state.menu_sel == "현황":
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-box"><div class="card-label">전체 직원</div><div class="card-value val-blue">{total_staff}명</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-box"><div class="card-label">총사용 휴가</div><div class="card-value val-green">{int(total_approved)}일</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-box"><div class="card-label">대기 중</div><div class="card-value val-yellow">{total_pending}건</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for idx, row in st.session_state.staff.iterrows():
        name = row['Name']
        pos = row['Position']
        total = row['Total_Leave']
        used = st.session_state.leaves[(st.session_state.leaves['Name'] == name) & (st.session_state.leaves['Status'] == 'Approved')]['Days'].sum()
        rem = total - used
        percent = (used / total) if total > 0 else 0
        
        # 프로필 원형 아이콘 색상 분류 로직
        if "부목사" in pos: bg_class = "bg-sub-pastor"
        elif "목사" in pos: bg_class = "bg-pastor"
        elif "전도사" in pos: bg_class = "bg-helper"
        else: bg_class = "bg-staff"
        
        sc1, sc2, sc3, sc4 = st.columns([2, 4, 3, 1.5])
        sc1.markdown(f'<div style="display:flex; align-items:center;"><div class="profile-circle {bg_class}">{name[:2]}</div><div><p class="name-text">{name}</p><p class="pos-text">{pos}</p></div></div>', unsafe_allow_html=True)
        sc2.markdown(f'<p class="usage-text">사용 {int(used)}일 / 전체 {int(total)}일</p>', unsafe_allow_html=True)
        sc2.progress(min(percent, 1.0))
        sc4.markdown(f'<p class="rem-text">잔여 <span style="font-size:16px;">{int(rem)}일</span></p>', unsafe_allow_html=True)
        st.markdown('<hr style="margin:8px 0; border:0; border-top:1px solid #F5F5F5;">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.menu_sel == "달력":
    st.title("📅 월별 캐나다 공휴일 및 휴가 달력")
    cc1, cc2 = st.columns(2)
    year = cc1.selectbox("연도",)
    month = cc2.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
    cal = calendar.monthcalendar(year, month)
    st.subheader(f"{year}년 {calendar.month_name[month]}")
    
    days_headers = st.columns(7)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, w in enumerate(weekdays):
        days_headers[i].markdown(f"<p style='text-align:center; font-weight:bold;'>{w}</p>", unsafe_allow_html=True)
        
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                holiday_name = ONTARIO_HOLIDAYS.get(date_str, None)
                
                on_leave = []
                for _, l in st.session_state.leaves.iterrows():
                    if pd.to_datetime(l['Start']).date() <= current_date <= pd.to_datetime(l['End']).date() and l['Status'] == 'Approved':
                        on_leave.append(f"📌{l['Name']}")
                
                cell_html = f"**{day}**"
                if holiday_name:
                    cell_html += f"\n\n🍁 {holiday_name}"
                    cols[i].error(cell_html)
                elif on_leave:
                    cell_html += "\n\n" + "\n".join(on_leave)
                    cols[i].info(cell_html)
                else:
                    cols[i].write(day)

elif st.session_state.menu_sel == "직원":
    st.title("👤 사역자 명단 편집")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == "1234":
        with st.form("add_staff_form"):
            name = st.text_input("이름")
            pos = st.text_input("직책")
            total = st.number_input("연간 총 휴가 한도", 15)
            email = st.text_input("이메일")
            if st.form_submit_button("사역자 추가 등록"):
                if name:
                    new_st = pd.DataFrame([{'Name':name, 'Position':pos, 'Total_Leave':total, 'Email':email}])
                    st.session_state.staff = pd.concat([st.session_state.staff, new_st], ignore_index=True)
                    st.success("추가되었습니다!")
                    st.rerun()
    else:
        st.info("비밀번호 1234를 입력하면 명단을 수정 및 삭제할 수 있습니다.")
    st.data_editor(st.session_state.staff, use_container_width=True)

elif st.session_state.menu_sel == "신청":
    st.title("📝 휴가 신청서")
    with st.form("leave_apply_form"):
        name = st.selectbox("신청자 선택", st.session_state.staff['Name'])
        l_type = st.selectbox("휴가 종류", ["Vacation", "Half", "Sick", "Unpaid"])
        start = st.date_input("시작일")
        end = st.date_input("종료일")
        
        st.write("✒️ **디지털 서명**")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#F5F5F5", height=120, width=400, key="sig")
        
        if st.form_submit_button("제출하기"):
            days = calculate_church_days(start, end, l_type)
            new_leave = {
                'Name': name, 'Type': l_type, 'Start': str(start), 'End': str(end), 
                'Days': days, 'Status': 'Pending', 'Signed': 'Yes', 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.leaves = pd.concat([st.session_state.leaves, pd.DataFrame([new_leave])], ignore_index=True)
            st.success(f"신청 완료! (주말 및 온타리오 공휴일 제외 총 {days}일 자동 차감)")

elif st.session_state.menu_sel == "내역":
    st.title("📋 휴가 결재 및 내역 조회")
    if not st.session_state.leaves.empty:
        towrite = io.BytesIO()
        st.session_state.leaves.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 엑셀 백업 파일 다운로드", data=towrite.getvalue(), file_name="church_leave_final.xlsx")
    
    st.write("---")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == "1234":
        edited = st.data_editor(st.session_state.leaves, num_rows="dynamic")
        if st.button("수정사항 저장"):
            st.session_state.leaves = edited
            st.success("결재 내역이 안전하게 보관되었습니다.")
    else:
        st.table(st.session_state.leaves)

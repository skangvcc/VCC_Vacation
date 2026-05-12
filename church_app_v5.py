import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from streamlit_drawable_canvas import st_canvas
import holidays

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="본한인교회 사역자 및 직원 휴가 시스템", layout="wide")

# --- ⚙️ 설정: 비밀번호 ---
if 'admin_password' not in st.session_state:
    st.session_state.admin_password = "1234"

# --- 2. 캐나다 온타리오주 공휴일 자동 로더 ---
def get_ontario_holidays(year):
    ca_on_holidays = holidays.Canada(subdiv='ON', years=year)
    holiday_dict = {}
    for date, name in sorted(ca_on_holidays.items()):
        if name in ["Easter Sunday", "Heritage Day"]: continue
        if "Civic Holiday" in name: name = "Civic Holiday"
        holiday_dict[date.strftime("%Y-%m-%d")] = name
    return holiday_dict

# --- 3. 커스텀 CSS (정갈한 교회 대시보드 UI) ---
st.markdown("""
<style>
    /* 제목 및 레이아웃 */
    .app-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; }
    .app-title { font-size: 28px; font-weight: bold; color: #2C3E50; margin: 0; }
    .church-icon { font-size: 40px; }
    
    .stButton>button { border-radius: 12px !important; border: 1px solid #ddd !important; font-weight: 500 !important; }
    
    /* 요약 카드 */
    .card-box { background-color: #F4F7F9; border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; border-left: 5px solid #2E5B88; }
    .card-label { font-size: 14px; color: #666; }
    .card-value { font-size: 28px; font-weight: bold; color: #2E5B88; }
    
    /* 명단 리스트 */
    .list-container { border: 1px solid #EAEAEA; border-radius: 16px; padding: 25px; background-color: white; }
    .profile-circle {
        width: 42px; height: 42px; border-radius: 50%; color: white;
        display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-right: 15px;
    }
    .bg-pastor { background-color: #2E5B88; }
    .bg-sub-pastor { background-color: #4A76A8; }
    .bg-helper { background-color: #549A74; }
    .bg-staff { background-color: #A370A8; }
    
    .name-text { font-size: 16px; font-weight: bold; color: #222; margin: 0; }
    .pos-text { font-size: 13px; color: #777; margin: 0; }
    .usage-text { font-size: 14px; color: #555; }
    .rem-text { font-size: 14px; font-weight: bold; color: #2E5B88; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 4. 데이터 초기화 (18명 명단) ---
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

# 휴가 일수 계산 로직
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

# --- 5. 상단 UI: 교회 아이콘 및 제목 ---
st.markdown("""
<div class="app-header">
    <span class="church-icon">⛪</span>
    <p class="app-title">본한인교회 사역자 및 직원 휴가 시스템</p>
</div>
""", unsafe_allow_html=True)

# 네비게이션 메뉴 (가로 정렬 고정)
m_cols = st.columns(5)
if m_cols[0].button("📊 현황", use_container_width=True): st.session_state.menu_sel = "현황"
if m_cols[1].button("📅 달력", use_container_width=True): st.session_state.menu_sel = "달력"
if m_cols[2].button("🔒 직원", use_container_width=True): st.session_state.menu_sel = "직원"
if m_cols[3].button("📝 신청", use_container_width=True): st.session_state.menu_sel = "신청"
if m_cols[4].button("📋 내역", use_container_width=True): st.session_state.menu_sel = "내역"

st.write("")

# --- 6. 메뉴별 화면 구현 ---
if st.session_state.menu_sel == "현황":
    total_approved = st.session_state.leaves[st.session_state.leaves['Status'] == 'Approved']['Days'].sum() if not st.session_state.leaves.empty else 0
    total_pending = len(st.session_state.leaves[st.session_state.leaves['Status'] == 'Pending']) if not st.session_state.leaves.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-box"><div class="card-label">전체 사역자 및 직원</div><div class="card-value">{len(st.session_state.staff)}명</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-box"><div class="card-label">총사용 휴가 일수</div><div class="card-value">{int(total_approved)}일</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-box"><div class="card-label">결재 대기 중</div><div class="card-value">{total_pending}건</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for idx, row in st.session_state.staff.iterrows():
        total_limit = pd.to_numeric(row['Total_Leave'], errors='coerce') or 0.0
        person_leaves = st.session_state.leaves[(st.session_state.leaves['Name'] == row['Name']) & (st.session_state.leaves['Status'] == 'Approved')]
        used = person_leaves['Days'].sum() if not person_leaves.empty else 0
        rem = total_limit - used
        percent = (used / total_limit) if total_limit > 0 else 0
        
        bg_class = "bg-pastor" if "목사" in row['Position'] else "bg-helper" if "전도사" in row['Position'] else "bg-staff"
        
        sc1, sc2, sc3, sc4 = st.columns([2.5, 4, 4, 1.5])
        sc1.markdown(f'<div style="display:flex; align-items:center;"><div class="profile-circle {bg_class}">{row["Name"][:2]}</div><div><p class="name-text">{row["Name"]}</p><p class="pos-text">{row["Position"]}</p></div></div>', unsafe_allow_html=True)
        sc2.markdown(f'<p class="usage-text">사용 {int(used)}일 / 연간 한도 {int(total_limit)}일</p>', unsafe_allow_html=True)
        sc2.progress(min(percent, 1.0))
        
        types = ["Vacation", "Half", "Sick", "Unpaid"]
        breakdown = [f"<b>{t}</b>: {person_leaves[person_leaves['Type']==t]['Days'].sum():g}일" for t in types if not person_leaves[person_leaves['Type']==t].empty]
        sc3.markdown("<p style='font-size:12px; color:#555; margin-top:8px;'>🍁 <b>상세 내역:</b> " + (" | ".join(breakdown) if breakdown else "기록 없음") + "</p>", unsafe_allow_html=True)
        
        sc4.markdown(f'<p class="rem-text">잔여<br><span style="font-size:18px;">{int(rem)}일</span></p>', unsafe_allow_html=True)
        st.markdown('<hr style="margin:10px 0; border:0; border-top:1px solid #F5F5F5;">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.menu_sel == "달력":
    st.title("📅 월별 휴가 현황")
    yy = st.selectbox("연도", list(range(2026, 2037)))
    mm = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
    cal = calendar.monthcalendar(yy, mm)
    st.subheader(f"{yy}년 {mm}월")
    
    cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]): cols[i].markdown(f"**{d}**")

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: cols[i].write("")
            else:
                date_str = f"{yy}-{mm:02d}-{day:02d}"
                holiday = get_ontario_holidays(yy).get(date_str, None)
                on_leave = st.session_state.leaves[(st.session_state.leaves['Start'] <= date_str) & 
                                                  (st.session_state.leaves['End'] >= date_str) & 
                                                  (st.session_state.leaves['Status'] == 'Approved')]
                content = f"**{day}**"
                if holiday: content += f"\n\n🍁 {holiday}"
                if not on_leave.empty: content += "\n\n" + "\n".join([f"📌{n}" for n in on_leave['Name']])
                
                if holiday: cols[i].error(content)
                elif not on_leave.empty: cols[i].info(content)
                else: cols[i].write(content)

elif st.session_state.menu_sel == "직원":
    st.title("👤 사역자 명단 관리")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == st.session_state.admin_password:
        edited = st.data_editor(st.session_state.staff, num_rows="dynamic", use_container_width=True)
        if st.button("💾 변경사항 저장"):
            edited['Total_Leave'] = pd.to_numeric(edited['Total_Leave'], errors='coerce').fillna(0).astype(int)
            st.session_state.staff = edited
            st.success("🎉 명단이 안전하게 저장되었습니다!")
            st.rerun()
    else: st.warning("사무처 비밀번호를 입력해 주세요.")

elif st.session_state.menu_sel == "신청":
    st.title("📝 휴가 신청서")
    with st.form("leave_form"):
        name = st.selectbox("사역자 성함", st.session_state.staff['Name'])
        l_type = st.selectbox("휴가 종류", ["Vacation", "Half", "Sick", "Unpaid"])
        start = st.date_input("시작일")
        end = st.date_input("종료일")
        st.write("✒️ **디지털 서명**")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#F5F5F5", height=150, width=400, key="sig")
        if st.form_submit_button("신청 완료"):
            days = calculate_church_days(start, end, l_type)
            new_entry = pd.DataFrame([[name, l_type, str(start), str(end), days, 'Pending', 'Yes', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], 
                                     columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])
            st.session_state.leaves = pd.concat([st.session_state.leaves, new_entry], ignore_index=True)
            st.success(f"신청되었습니다! (총 {days}일)")

elif st.session_state.menu_sel == "내역":
    st.title("📋 결재 관리 및 내역")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == st.session_state.admin_password:
        edited = st.data_editor(st.session_state.leaves, num_rows="dynamic", use_container_width=True,
                               column_config={"Status": st.column_config.SelectboxColumn("상태", options=["Pending", "Approved", "Rejected"])})
        if st.button("✅ 최종 결재 저장"):
            st.session_state.leaves = edited
            st.success("결재 사항이 업데이트되었습니다.")
            st.rerun()
    else: st.table(st.session_state.leaves)
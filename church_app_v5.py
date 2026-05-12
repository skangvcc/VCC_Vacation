import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import io
from streamlit_drawable_canvas import st_canvas
import holidays
import gspread

# --- 1. 페이지 설정 (브라우저 탭 제목) ---
st.set_page_config(page_title="캐나다 본한인교회 사역자 및 직원 휴가 시스템", layout="wide")

# --- 2. 구글 시트 실시간 연결 함수 ---
@st.cache_resource
def init_google_sheets():
    """Streamlit Secrets의 보안 키를 이용해 구글 시트 계정과 동기화합니다."""
    try:
        creds = dict(st.secrets["gspread_credentials"])
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds)
        # 구글 드라이브에 생성한 시트 파일명과 정확히 일치해야 합니다.
        sh = gc.open("본한인교회_휴가데이터")
        return sh
    except Exception as e:
        st.error(f"구글 시트 연결 실패: {e}")
        return None

sheet_file = init_google_sheets()

# --- 3. 캐나다 온타리오주 공휴일 자동 생성 함수 ---
def get_ontario_holidays(year):
    """지정된 연도의 온타리오주 법정 공휴일 딕셔너리를 반환합니다."""
    ca_on_holidays = holidays.Canada(subdiv='ON', years=year)
    holiday_dict = {}
    for date, name in sorted(ca_on_holidays.items()):
        if name in ["Easter Sunday", "Heritage Day"]:
            continue
        if "Civic Holiday" in name:
            name = "Civic Holiday"
        holiday_dict[date.strftime("%Y-%m-%d")] = name
    return holiday_dict

# --- 4. 커스텀 CSS 스타일 (이미지 대시보드 UI 구현) ---
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

# --- 5. 초기 사역자 명단 (구글 시트가 비어있을 때 채워지는 데이터) ---
DEFAULT_STAFF = [
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
]

# --- 6. 구글 시트 실시간 데이터 로드 및 연동 ---
if sheet_file:
    staff_sheet = sheet_file.worksheet("Staff")
    staff_data = staff_sheet.get_all_records()
    if not staff_data:
        staff_sheet.append_rows([list(x.values()) for x in DEFAULT_STAFF])
        staff_data = DEFAULT_STAFF
    df_staff = pd.DataFrame(staff_data)
    
    leaves_sheet = sheet_file.worksheet("Leaves")
    leaves_data = leaves_sheet.get_all_records()
    df_leaves = pd.DataFrame(leaves_data) if leaves_data else pd.DataFrame(columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])
else:
    df_staff = pd.DataFrame(DEFAULT_STAFF)
    df_leaves = pd.DataFrame(columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])

if 'menu_sel' not in st.session_state:
    st.session_state.menu_sel = "현황"

# 주말 및 공휴일 제외 일수 계산 로직
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

# --- 7. 상단 UI 헤더 및 수정 완료된 가로 버튼 메뉴 ---
st.markdown('<p class="app-title">🇨🇦 캐나다 본한인교회 사역자 및 직원 휴가 시스템</p>', unsafe_allow_html=True)

m_cols = st.columns(5)
if m_cols[0].button("📊 현황", use_container_width=True): st.session_state.menu_sel = "현황"
if m_cols[1].button("📅 달력", use_container_width=True): st.session_state.menu_sel = "달력"
if m_cols[2].button("🔒 직원", use_container_width=True): st.session_state.menu_sel = "직원"
if m_cols[3].button("📝 신청", use_container_width=True): st.session_state.menu_sel = "신청"
if m_cols[4].button("📋 내역", use_container_width=True): st.session_state.menu_sel = "내역"

st.write("")

# 통계 연산
total_staff = len(df_staff)
total_approved = df_leaves[df_leaves['Status'] == 'Approved']['Days'].astype(float).sum() if not df_leaves.empty else 0
total_pending = len(df_leaves[df_leaves['Status'] == 'Pending']) if not df_leaves.empty else 0

# --- 8. 메뉴별 세부 화면 제어 ---
if st.session_state.menu_sel == "현황":
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-box"><div class="card-label">전체 직원</div><div class="card-value val-blue">{total_staff}명</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-box"><div class="card-label">총사용 휴가</div><div class="card-value val-green">{int(total_approved)}일</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-box"><div class="card-label">대기 중</div><div class="card-value val-yellow">{total_pending}건</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    for idx, row in df_staff.iterrows():
        name = row['Name']
        pos = row['Position']
        total = int(row['Total_Leave'])
        used = df_leaves[(df_leaves['Name'] == name) & (df_leaves['Status'] == 'Approved')]['Days'].astype(float).sum() if not df_leaves.empty else 0
        rem = total - used
        percent = (used / total) if total > 0 else 0
        
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
    years_list = list(range(2026, 2037))
    year = cc1.selectbox("연도", years_list, index=0)
    month = cc2.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
    current_yearly_holidays = get_ontario_holidays(year)
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
                holiday_name = current_yearly_holidays.get(date_str, None)
                
                on_leave = []
                if not df_leaves.empty:
                    for _, l in df_leaves.iterrows():
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

# --- 🔒 직원 관리 및 수정 패널 (구글 시트 즉시 저장 버그 수정 반영) ---
elif st.session_state.menu_sel == "직원":
    st.title("👤 사역자 명단 관리 및 편집")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    
    if pw == "1234":
        st.info("💡 아래 테이블에서 내용을 직접 수정한 후 반드시 하단의 저장 버튼을 눌러주세요. 수정 후 대시보드가 자동으로 최신화됩니다.")
        
        # 자유로운 행 추가/수정/삭제를 지원하는 데이터 에디터
        edited_staff = st.data_editor(df_staff, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 변경사항 구글 시트에 최종 저장"):
            if sheet_file:
                with st.spinner("구글 클라우드 동기화 및 캐시 갱신 중..."):
                    staff_sheet = sheet_file.worksheet("Staff")
                    staff_sheet.clear()
                    # 헤더라인 다시 작성 후 수정된 데이터 일괄 전송
                    staff_sheet.append_row(['Name', 'Position', 'Total_Leave', 'Email'])
                    if not edited_staff.empty:
                        edited_staff['Total_Leave'] = edited_staff['Total_Leave'].astype(int)
                        staff_sheet.append_rows(edited_staff.values.tolist())
                    
                    st.success("🎉 사역자 명단이 구글 시트에 성공적으로 동기화되었습니다!")
                    
                    # [버그 해결 핵심] 데이터 불러오기 함수 캐시를 지우고 시스템을 강제 새로고침(Rerun)합니다.
                    st.cache_resource.clear()
                    st.rerun()
    else:
        st.warning("사역자 명단을 수정하려면 사이드바에 올바른 관리자 비밀번호(1234)를 입력하십시오.")
        st.data_editor(df_staff, use_container_width=True, disabled=True)

elif st.session_state.menu_sel == "신청":
    st.title("📝 휴가 신청서")
    with st.form("leave_apply_form"):
        name = st.selectbox("신청자 선택", df_staff['Name'])
        l_type = st.selectbox("휴가 종류", ["Vacation", "Half", "Sick", "Unpaid"])
        start = st.date_input("시작일")
        end = st.date_input("종료일")
        
        st.write("✒️ **디지털 서명**")
        canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#F5F5F5", height=120, width=400, key="sig")
        
        if st.form_submit_button("제출하기"):
            if sheet_file:
                days = calculate_church_days(start, end, l_type)
                leaves_sheet = sheet_file.worksheet("Leaves")
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                leaves_sheet.append_row([name, l_type, str(start), str(end), days, 'Pending', 'Yes', timestamp_str])
                st.success(f"신청서가 구글 시트로 전송되었습니다! (총 {days}일 차감 대기)")

elif st.session_state.menu_sel == "내역":
    st.title("📋 휴가 결재 및 내역 조회")
    if not df_leaves.empty:
        towrite = io.BytesIO()
        df_leaves.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 엑셀 백업 파일 다운로드", data=towrite.getvalue(), file_name="church_leave_final.xlsx")
    
    st.write("---")
    pw = st.sidebar.text_input("관리자 비밀번호", type="password")
    if pw == "1234" and sheet_file:
        st.subheader("실시간 결재 승인 패널")
        edited = st.data_editor(df_leaves, num_rows="dynamic")
        if st.button("수정사항 구글 시트에 최종 저장"):
            leaves_sheet = sheet_file.worksheet("Leaves")
            leaves_sheet.clear()
            leaves_sheet.append_row(['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])
            if not edited.empty:
                leaves_sheet.append_rows(edited.values.tolist())
            st.success("구글 클라우드 시트 업데이트 완료!")
            st.cache_resource.clear()
            st.rerun()
    else:
        st.table(df_leaves)
import streamlit as st
import pandas as pd
from datetime import datetime
import io
from streamlit_drawable_canvas import st_canvas

# --- Setup ---
st.set_page_config(page_title="Church Staff Leave System", layout="wide")

# Initialize Session State
if 'staff' not in st.session_state:
    st.session_state.staff = pd.DataFrame(columns=['Name', 'Position', 'Total_Leave', 'Email'])
if 'leaves' not in st.session_state:
    st.session_state.leaves = pd.DataFrame(columns=['Name', 'Type', 'Start', 'End', 'Days', 'Status', 'Signed', 'Timestamp'])

# --- Sidebar Menu ---
menu = st.sidebar.radio("Navigation", ["Dashboard", "Staff Management", "Apply Leave", "Admin Tracking"])

# --- 1. Dashboard (Gauges) ---
if menu == "Dashboard":
    st.title("📊 Leave Usage Overview")
    if st.session_state.staff.empty:
        st.info("Please register staff in 'Staff Management' first.")
    else:
        for _, row in st.session_state.staff.iterrows():
            used = st.session_state.leaves[(st.session_state.leaves['Name'] == row['Name']) & (st.session_state.leaves['Status'] == 'Approved')]['Days'].sum()
            percent = (used / row['Total_Leave']) if row['Total_Leave'] > 0 else 0
            
            color = "red" if percent >= 0.9 else "orange" if percent >= 0.7 else "green"
            st.subheader(f"{row['Name']} ({row['Position']})")
            st.progress(min(percent, 1.0))
            st.write(f"Used: {used} / Total: {row['Total_Leave']} days")
            if percent >= 0.9: st.error("Critical: Over 90% used")
            elif percent >= 0.7: st.warning("Warning: Over 70% used")

# --- 2. Staff Management ---
elif menu == "Staff Management":
    st.title("👥 Staff Directory")
    pw = st.sidebar.text_input("Admin Password", type="password")
    if pw == "1234":
        with st.form("add_staff"):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("Name")
            pos = c2.text_input("Position")
            total = c3.number_input("Annual Days", 15)
            email = c4.text_input("Email")
            if st.form_submit_button("Add Staff"):
                if name:
                    new_staff = pd.DataFrame([{'Name':name, 'Position':pos, 'Total_Leave':total, 'Email':email}])
                    st.session_state.staff = pd.concat([st.session_state.staff, new_staff], ignore_index=True)
                    st.success("Registered!")
        st.dataframe(st.session_state.staff)
    else:
        st.info("Enter admin password (1234) in the sidebar to manage staff.")

# --- 3. Apply Leave (Signature Included) ---
elif menu == "Apply Leave":
    st.title("📝 Leave Application")
    if st.session_state.staff.empty:
        st.warning("No staff registered yet.")
    else:
        with st.form("leave_form"):
            name = st.selectbox("Staff Name", st.session_state.staff['Name'])
            l_type = st.selectbox("Type", ["Vacation", "Half", "Sick", "Unpaid"])
            start = st.date_input("Start Date")
            end = st.date_input("End Date")
            
            st.write("✒️ **Digital Signature**")
            canvas = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=150, width=400, key="sig")
            
            if st.form_submit_button("Submit"):
                if canvas.image_data is not None:
                    days = len(pd.bdate_range(start, end)) if l_type != "Half" else 0.5
                    new_entry = {
                        'Name': name, 'Type': l_type, 'Start': start, 'End': end, 
                        'Days': days, 'Status': 'Pending', 'Signed': 'Yes', 'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.leaves = pd.concat([st.session_state.leaves, pd.DataFrame([new_entry])], ignore_index=True)
                    st.success("Application Sent to Admin!")
                else:
                    st.error("Please sign before submitting.")

# --- 4. Admin Tracking & Excel Export ---
elif menu == "Admin Tracking":
    st.title("📋 Church Audit Trail")
    if not st.session_state.leaves.empty:
        towrite = io.BytesIO()
        st.session_state.leaves.to_excel(towrite, index=False, engine='xlsxwriter')
        st.download_button(label="📥 Download Excel for Records", data=towrite.getvalue(), file_name="church_leave_records.xlsx")
    
    st.write("---")
    pw = st.sidebar.text_input("Admin Password", type="password")
    if pw == "1234":
        st.subheader("Edit/Approve Records")
        edited_df = st.data_editor(st.session_state.leaves, num_rows="dynamic")
        if st.button("Save Changes"):
            st.session_state.leaves = edited_df
            st.success("Database Updated!")
    else:
        st.table(st.session_state.leaves)

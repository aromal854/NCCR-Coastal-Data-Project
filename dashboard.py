# dashboard.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import database as db
import utils
import config
import prediction # <--- IMPORT THE NEW FILE

def main_app():
    # --- SIDEBAR ---
    st.sidebar.title("Navigation")
    # Show Name and Unique ID
    st.sidebar.markdown(f"👤 **{st.session_state['user_name']}**")
    st.sidebar.caption(f"ID: {st.session_state['user_id']}")
    st.sidebar.badge(st.session_state['user_role'])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.rerun()
        
    st.title("🌊 NCCR Marine Data Portal")

    # --- DEFINE MENUS BASED ON ROLE ---
    # Added "🔮 AI Prediction Tools" to both menus
    if st.session_state['user_role'] == 'Admin':
        options = ["📥 Contribute Data", "🔮 AI Prediction Tools", "🗺️ Global Data Map", "📰 Research & News", "👮 Data Requests (Approval)", "📂 Master Data Repository", "🗑️ Manage & Delete Data"]
    else:
        options = ["📥 Contribute Data", "🔮 AI Prediction Tools", "🗺️ Global Data Map", "📰 Research & News", "📊 Request & Download Data"]
        
    menu = st.sidebar.radio("Go to:", options)

    # -----------------------------------------------------
    # OPTION: AI PREDICTION TOOLS (NEW)
    # -----------------------------------------------------
    if menu == "🔮 AI Prediction Tools":
        prediction.run_prediction_page() # <--- CALL THE FUNCTION

    # -----------------------------------------------------
    # OPTION: GLOBAL MAP VIEW (NEW)
    # -----------------------------------------------------
    elif menu == "🗺️ Global Data Map":
        st.header("🌍 Global Marine Data Map")
        st.info("Visualizing all contributed data points.")
        
        df = db.fetch_all_data()
        
        if not df.empty:
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                # Filter valid coordinates
                map_df = df.dropna(subset=['Latitude', 'Longitude'])
                
                if not map_df.empty:
                    # Basic Map
                    st.map(map_df, latitude='Latitude', longitude='Longitude')
                    
                    # Optional: Stats
                    st.success(f"Displaying **{len(map_df)}** locations.")
                else:
                    st.warning("No data points with valid coordinates found.")
            else:
                st.warning("Dataset missing Latitude/Longitude columns.")
        else:
            st.info("Database is empty.")

    # -----------------------------------------------------
    # OPTION A: CONTRIBUTE DATA
    # -----------------------------------------------------
    elif menu == "📥 Contribute Data":
        st.header("Submit Marine Field Data")
        st.info("Choose 'Single Entry' for manual input or 'Bulk Upload' for large datasets (Prediction Training).")

        # Initialize State Variables
        certificate_ready = False
        pdf_bytes = None
        contributor_name = ""

        # --- MODE SELECTION TABS ---
        tab_single, tab_bulk = st.tabs(["📝 Single Entry (Manual)", "📂 Bulk Upload (CSV/Excel)"])

        # ==========================================
        # 🟢 TAB 1: SINGLE ENTRY (Manual)
        # ==========================================
        with tab_single:
            st.subheader("1. Location & Profile")
            st.write(f"**Contributor:** {st.session_state['user_name']}")
            
            lc1, lc2, lc3 = st.columns(3)
            # Use Global COASTAL_DATA from config
            selected_state = lc1.selectbox("Select State / UT", list(config.COASTAL_DATA.keys()), key="s_state")
            available_coasts = config.COASTAL_DATA[selected_state]
            selected_coast = lc2.selectbox("Select Coastal Region", available_coasts, key="s_coast")
            
            if selected_coast == "Other" or selected_state == "Other State/Region":
                custom_coast = lc3.text_input("✍️ Type Region Name", placeholder="Enter specific region name", key="s_custom")
                final_main_loc = f"{selected_state} - {custom_coast}" if custom_coast else f"{selected_state} - Unknown"
            else:
                final_main_loc = selected_coast

            c1, c2, c3 = st.columns(3)
            latitude = c1.number_input("Latitude", format="%.6f", value=13.0827, key="s_lat")
            longitude = c2.number_input("Longitude", format="%.6f", value=80.2707, key="s_lon")
            specific_loc = c3.text_input("Specific Spot Name", key="s_spot")
            
            c4, c5, c6, c7 = st.columns(4)
            prof_role = c4.selectbox("Profession", ["Student", "Researcher", "Official", "Fisherman", "Other"], key="s_role")
            designation = c5.text_input("Designation", key="s_desig")
            date_col = c6.date_input("Date of Collection", date.today(), key="s_date")
            time_col = c7.time_input("Time of Collection", datetime.now().time(), key="s_time")

            st.markdown("---")

            # DATA ENTRY FORM
            with st.form("nccr_form", clear_on_submit=False):
                st.subheader("2. Field Parameters")
                tab_phy, tab_chem, tab_bio, tab_soc, tab_geo = st.tabs([
                    "🧪 Physical", "⚗️ Chemical", "🦠 Biological", "👥 Social", "🗺️ Geographical"
                ])

                with tab_phy:
                    p1, p2, p3 = st.columns(3)
                    temp = p1.number_input("Water Temp (°C)", format="%.2f")
                    salinity = p2.number_input("Salinity (psu)", format="%.2f")
                    ph = p3.number_input("pH Level", format="%.2f")
                    p4, p5, p6 = st.columns(3)
                    turbidity = p4.number_input("Turbidity (NTU)", format="%.2f")
                    transparency = p5.number_input("Transparency (cm)", format="%.2f")
                    tss = p6.number_input("TSS (mg/L)", format="%.2f")
                    p7, p8 = st.columns(2)
                    color = p7.text_input("Water Color")
                    odour = p8.text_input("Odour")

                with tab_chem:
                    ch1, ch2, ch3 = st.columns(3)
                    do = ch1.number_input("Dissolved Oxygen (DO)", format="%.2f")
                    bod = ch2.number_input("BOD (mg/L)", format="%.2f")
                    cod = ch3.number_input("COD (mg/L)", format="%.2f")
                    ch4, ch5, ch6 = st.columns(3)
                    nh4 = ch4.number_input("NH4-N", format="%.3f")
                    no3 = ch5.number_input("NO3-N", format="%.3f")
                    no2 = ch6.number_input("NO2-N", format="%.3f")
                    ch7, ch8 = st.columns(2)
                    po4 = ch7.number_input("PO4 (Phosphate)", format="%.3f")
                    so4 = ch8.number_input("SO4 (Sulphate)", format="%.3f")
                    m1, m2 = st.columns(2)
                    fecal = m1.number_input("Fecal Coliform", step=1)
                    total_col = m2.number_input("Total Coliform", step=1)

                with tab_bio:
                    b1, b2 = st.columns(2)
                    phyto = b1.text_area("Phytoplankton Species")
                    zoo = b2.text_area("Zooplankton Species")
                    prod = st.number_input("Primary Productivity", format="%.2f")

                with tab_soc:
                    s1, s2, s3 = st.columns(3)
                    villages = s1.number_input("Coastal Villages", step=1)
                    panchayats = s2.number_input("Panchayats", step=1)
                    pop = s3.number_input("Population", step=100)
                    s4, s5, s6 = st.columns(3)
                    fishermen = s4.number_input("Fishermen", step=10)
                    landing = s5.number_input("Landing Centers", step=1)
                    fish = s6.text_input("Fish Catch")

                with tab_geo:
                    g1, g2, g3 = st.columns(3)
                    shore = g1.selectbox("Shoreline", ["Stable", "Eroding", "Accreting"])
                    water_bodies = g2.number_input("Nearby Water Bodies", step=1)
                    indus = g3.number_input("Industrial Est", step=1)
                    g4, g5, g6 = st.columns(3)
                    tourism = g4.selectbox("Tourism", ["Active", "Inactive"])
                    tourist_inflow = g5.number_input("Tourist Inflow", step=100)
                    season = g6.text_input("Optimum Season")

                submitted = st.form_submit_button("🚀 Submit Single Entry")

                if submitted:
                    data_packet = {
                        "Contributor": st.session_state['user_name'], "Email": st.session_state['user_email'],
                        "Profession": prof_role, "Designation": designation,
                        "Date": str(date_col), "Time": str(time_col),
                        "Main_Location": final_main_loc, "Location": specific_loc,
                        "Latitude": latitude, "Longitude": longitude,
                        "Water_Temp": temp, "Salinity": salinity, "Transparency": transparency,
                        "Color": color, "Odour": odour, "Turbidity": turbidity, "TSS": tss, "pH": ph,
                        "DO": do, "BOD": bod, "COD": cod, "NH4_N": nh4, "NO3_N": no3, "NO2_N": no2,
                        "PO4": po4, "SO4": so4, "Fecal_Coliform": fecal, "Total_Coliform": total_col,
                        "Phytoplankton": phyto, "Zooplankton": zoo, "Productivity": prod,
                        "Coastal_Villages": villages, "Panchayats": panchayats, "Population": pop,
                        "Fishermen": fishermen, "Fish_Catch": fish, "Landing_Centers": landing,
                        "Shoreline_Status": shore, "Water_Bodies": water_bodies,
                        "Industrial_Est": indus, "Tourism_Status": tourism,
                        "Tourist_Inflow": tourist_inflow, "Optimum_Season": season,
                        "created_at": str(datetime.now())
                    }
                    
                    if db.save_marine_data(data_packet):
                        st.success(f"✅ Data Saved under Region: **{final_main_loc}**")
                        count = db.get_contribution_count(st.session_state['user_email'])
                        st.toast(f"Total Contributions: {count}")
                        if count >= config.CERTIFICATE_THRESHOLD:
                            certificate_ready = True
                            contributor_name = st.session_state['user_name']
                            pdf_bytes = utils.create_certificate(contributor_name, count)
                    else:
                        st.error("Failed to save data.")

        # ==========================================
        # 🔵 TAB 2: BULK UPLOAD (NCCR Format)
        # ==========================================
        with tab_bulk:
            st.subheader("Bulk Data Upload (NCCR Format)")
            st.write("Upload historical data (CSV or Excel) to train the prediction model.")
            st.info("💡 **Format:** The system expects official NCCR headers like `WQ Temp (°C)`, `Sal (psu)`, `Dissolved Oxygen (mg/L)`, etc.")
            
            # 1. Location Selection
            bc1, bc2 = st.columns(2)
            # Use Global COASTAL_DATA from config
            b_state = bc1.selectbox("Select State / UT", list(config.COASTAL_DATA.keys()), key="b_state")
            b_coast = bc2.selectbox("Select Coastal Region", config.COASTAL_DATA[b_state], key="b_coast")
            
            if b_coast == "Other" or b_state == "Other State/Region":
                b_custom = st.text_input("✍️ Type Region Name", key="b_custom")
                final_bulk_loc = f"{b_state} - {b_custom}" if b_custom else f"{b_state} - Unknown"
                b_def_lat, b_def_lon = 13.0827, 80.2707
            else:
                final_bulk_loc = b_coast
                b_def_lat, b_def_lon = config.REGION_COORDS.get(b_coast, (13.0827, 80.2707))

            # --- Details for Bulk Upload ---
            st.write("**Location & Contributor Details for this Batch:**")
            
            b1, b2, b3 = st.columns(3)
            # Update key to force refresh
            b_lat = b1.number_input("Latitude", format="%.6f", value=b_def_lat, key=f"b_lat_{b_coast}")
            b_lon = b2.number_input("Longitude", format="%.6f", value=b_def_lon, key=f"b_lon_{b_coast}")
            b_spot = b3.text_input("Specific Spot Name", key="b_spot")
            
            b4, b5 = st.columns(2)
            b_prof = b4.selectbox("Profession", ["Student", "Researcher", "Official", "Fisherman", "Other"], key="b_prof")
            b_desig = b5.text_input("Designation", key="b_desig")

            st.info(f"📍 Data will be saved under: **{final_bulk_loc}** ({b_spot})")

            # 2. File Uploader
            uploaded_file = st.file_uploader("Upload Data File", type=["csv", "xlsx", "xls"])
            
            if uploaded_file is not None:
                try:
                    # SMART READ LOGIC
                    if uploaded_file.name.endswith('.csv'):
                        bulk_df = pd.read_csv(uploaded_file)
                    else:
                        bulk_df = pd.read_excel(uploaded_file)

                    st.write("📊 **Data Preview:**")
                    st.dataframe(bulk_df.head(), use_container_width=True) # FIXED WIDTH ERROR HERE
                    
                    if st.button("🚀 Upload Bulk Data"):
                        data_list = []
                        # Progress bar for large files
                        my_bar = st.progress(0)
                        total_rows = len(bulk_df)

                        for index, row in bulk_df.iterrows():
                            # --- DATE & TIME HANDLING ---
                            try:
                                if "Date and Time" in row:
                                    dt_val = row["Date and Time"]
                                    if pd.notnull(dt_val):
                                        dt_obj = pd.to_datetime(dt_val)
                                        row_date = str(dt_obj.date())
                                        row_time = str(dt_obj.time())
                                    else:
                                        row_date = str(date.today())
                                        row_time = str(datetime.now().time())
                                else:
                                    row_date = str(date.today())
                                    row_time = str(datetime.now().time())
                            except:
                                row_date = str(date.today())
                                row_time = "00:00:00"
                            
                            packet = {
                                "Contributor": st.session_state['user_name'],
                                "Email": st.session_state['user_email'],
                                
                                "Main_Location": final_bulk_loc,
                                "Location": b_spot,
                                "Latitude": b_lat,
                                "Longitude": b_lon,
                                "Profession": b_prof,
                                "Designation": b_desig,
                                
                                "Date": row_date,
                                "Time": row_time,
                                
                                # --- MAPPING EXACT EXCEL HEADERS TO DB COLUMNS ---
                                "Water_Temp": row.get("WQ Temp (°C)"),
                                "Salinity": row.get("Sal (psu)"),
                                "DO": row.get("Dissolved Oxygen (mg/L)"),
                                "pH": row.get("pH"),
                                "Turbidity": row.get("Turbidity (NTU)") or row.get("Turbididt y (NTU)"), # Handle Typos
                                "TSS": row.get("TSS (mg/L)"),
                                "TDS": row.get("TDS (g/L)"),
                                
                                "Chlorophyll": row.get("Chl(ug/l)") or row.get("Chlorophy (mg/L)") or row.get("Chlorophy_RFU (ug/L)"),
                                "BGA": row.get("BGA (mg/l)"),
                                
                                "Wind_Speed": row.get("Wind Speed (m/s)"),
                                "Wind_Direction": row.get("Wind Dir (Deg)"),
                                "Precipitation": row.get("Total Precipitation (mm)"),
                                "Humidity": row.get("Rel.Hum (%)"),
                                "Air_Temp": row.get("Air Temp (°C)"),
                                
                                "created_at": str(datetime.now())
                            }
                            
                            # Clean up NaNs
                            for k, v in packet.items():
                                if pd.isna(v) or v == "None": packet[k] = None
                                    
                            data_list.append(packet)
                            
                            if index % 50 == 0:
                                my_bar.progress(min(index / total_rows, 1.0))
                        
                        success, msg = db.save_bulk_data(data_list)
                        my_bar.progress(1.0)

                        if success:
                            st.success(f"✅ Successfully uploaded {len(data_list)} records from {uploaded_file.name}!")
                            st.balloons()
                        else:
                            st.error(f"Failed: {msg}")
                            
                except Exception as e:
                    st.error(f"❌ Error reading file: {e}")

        # DOWNLOAD CERTIFICATE
        if certificate_ready and pdf_bytes:
            st.balloons()
            st.success("🏆 Certificate Unlocked!")
            st.download_button(label="📥 Download Certificate", data=pdf_bytes, file_name=f"NCCR_Cert.pdf", mime="application/pdf")

    # -----------------------------------------------------
    # 📰 NEW: RESEARCH & NEWS
    # -----------------------------------------------------
    elif menu == "📰 Research & News":
        st.header("📰 Marine Research & Official News")
        st.write("Share findings, official updates, and research papers here.")
        
        # --- UPLOAD SECTION ---
        with st.expander("📤 Upload New Paper / News"):
            with st.form("upload_paper"):
                p_title = st.text_input("Title / Headline")
                p_summary = st.text_area("Summary / Abstract")
                p_file = st.file_uploader("Attach File (PDF/Doc)", type=['pdf','docx','txt'])
                
                submitted = st.form_submit_button("Publish")
                if submitted and p_title:
                    role = st.session_state['user_role']
                    ok, msg = db.save_paper(p_title, p_summary, st.session_state['user_name'], role, p_file)
                    if ok: st.success("Published Successfully!"); st.rerun()
                    else: st.error(msg)

        st.divider()
        st.subheader("📚 Latest Updates")
        
        # --- DISPLAY SECTION ---
        papers = db.fetch_papers()
        if papers:
            for p in papers:
                # Highlight Admin Posts
                if p['role'] == 'Admin':
                    with st.container():
                        st.markdown(f"""
                        <div style="padding:15px; border-left:5px solid #FF4B4B; background-color:#f0f2f6; border-radius:5px;">
                            <h3>📢 {p['title']} <span style="font-size:12px; background-color:#FF4B4B; color:white; padding:2px 6px; border-radius:4px;">OFFICIAL</span></h3>
                            <p><b>By:</b> {p['author']} (Admin) | 📅 {p['created_at'][:10]}</p>
                            <p>{p['summary']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if p['file_data']:
                            b64 = p['file_data']
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{p["file_name"]}">📎 Download Attached File</a>'
                            st.markdown(href, unsafe_allow_html=True)
                else:
                    # User Posts
                    with st.container():
                        st.markdown(f"### 📄 {p['title']}")
                        st.caption(f"By: {p['author']} | 📅 {p['created_at'][:10]}")
                        st.write(p['summary'])
                        if p['file_data']:
                            b64 = p['file_data']
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{p["file_name"]}">📎 Download File</a>'
                            st.markdown(href, unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No papers or news uploaded yet.")

    # -----------------------------------------------------
    # OPTION B: ADMIN (WITH EMAIL NOTIFICATION)
    # -----------------------------------------------------
    elif menu == "👮 Data Requests (Approval)":
        st.header("Admin Approval Panel")
        req_df = db.fetch_pending_requests()
        if not req_df.empty:
            for index, row in req_df.iterrows():
                with st.expander(f"Request from: {row['user_email']}", expanded=True):
                    st.write(f"**Purpose:** {row['purpose']}")
                    st.write(f"**Date:** {row['request_date']}")
                    c1, c2 = st.columns([1, 4])
                    
                    if c1.button("✅ Approve", key=f"app_{row['id']}"):
                        db.update_request_status(row['id'], "Approved")
                        
                        # --- NEW: SEND APPROVAL EMAIL ---
                        msg_body = "Hello,\n\nYour request to access NCCR Marine Data has been APPROVED by the Admin.\nYou can now login and download the data.\n\nRegards,\nNCCR Admin Team"
                        sent = utils.send_email_notification(row['user_email'], "Data Access Request Approved ✅", msg_body)
                        
                        if sent: st.toast("📧 Email notification sent to user!")
                        else: st.toast("⚠️ Data approved, but email failed.")
                        
                        st.rerun()
                        
                    if c2.button("❌ Reject", key=f"rej_{row['id']}"):
                        db.update_request_status(row['id'], "Rejected")
                        st.rerun()
        else:
            st.info("No pending requests found.")

    # -----------------------------------------------------
    # OPTION C: MASTER DATA (UPDATED WITH CASCADING FILTER)
    # -----------------------------------------------------
    elif menu == "📂 Master Data Repository":
        st.header("NCCR Master Database")
        df = db.fetch_all_data()
        
        if not df.empty and 'Main_Location' in df.columns:
            st.subheader("📍 View Data by Region")
            view_mode = st.radio("Select View Mode:", ["🌍 Specific Region", "📚 View All Data"], horizontal=True)
            
            if view_mode == "🌍 Specific Region":
                # 1. Select State First
                state_list = list(config.COASTAL_DATA.keys())
                selected_state = st.selectbox("Select State / UT", state_list)
                
                # 2. Get standard regions from Config
                valid_regions_config = config.COASTAL_DATA.get(selected_state, [])
                
                # 3. Get actual regions existing in Database
                db_locations = df['Main_Location'].dropna().unique().tolist()
                
                filtered_options = [
                    loc for loc in db_locations 
                    if loc in valid_regions_config or loc.startswith(f"{selected_state} -")
                ]
                
                # 4. If data exists for this state, show Region Dropdown
                if filtered_options:
                    selected_region = st.selectbox("Select Coastal Region", filtered_options)
                    
                    # 5. Show Data
                    filtered_df = df[df['Main_Location'] == selected_region]
                    st.info(f"📂 Found **{len(filtered_df)}** records under **{selected_region}**")
                    st.dataframe(filtered_df, use_container_width=True) # FIXED WIDTH ERROR
                else:
                    st.warning(f"No data found for any region in {selected_state}")
            else:
                # View All Data
                st.write(f"Total Records: **{len(df)}**")
                st.dataframe(df, use_container_width=True) # FIXED WIDTH ERROR
        else:
            st.warning("Database is empty or missing 'Main_Location' data.")

    # -----------------------------------------------------
    # OPTION D: DOWNLOAD CENTER (UPDATED)
    # -----------------------------------------------------
    elif menu == "📊 Request & Download Data":
        st.header("📂 Advanced Data Download Center")
        status = db.check_request_status(st.session_state['user_email'])
        
        if status == "Approved":
            st.success("✅ Access Granted: You can download data.")
            raw_df = db.fetch_all_data()
            if not raw_df.empty and 'Main_Location' in raw_df.columns:
                st.divider()
                st.subheader("🛠️ Step 1: Select Region")
                
                # --- UPDATED: STATE -> REGION FILTER ---
                available_locs = raw_df['Main_Location'].dropna().unique().tolist()
                
                d1, d2 = st.columns(2)
                
                # 1. State Selector
                dl_state = d1.selectbox("Select State / UT", list(config.COASTAL_DATA.keys()))
                
                # 2. Filter Regions based on State
                valid_state_regions = config.COASTAL_DATA.get(dl_state, [])
                
                filtered_regions = [
                    loc for loc in available_locs 
                    if loc in valid_state_regions or loc.startswith(f"{dl_state} -")
                ]
                
                if not filtered_regions:
                    d2.warning(f"No data found for {dl_state}")
                    selected_loc = None
                else:
                    selected_loc = d2.selectbox("Select Specific Region", filtered_regions)

                if selected_loc:
                    filtered_df = raw_df[raw_df['Main_Location'] == selected_loc].copy()
                    st.info(f"Found {len(filtered_df)} records for {selected_loc}.")
                    
                    st.divider()
                    st.subheader("🛠️ Step 2: Select Parameter Categories")
                    cat_options = {
                        "Physical Parameters": ["Water_Temp", "Salinity", "pH", "Turbidity", "Transparency", "TSS", "TDS", "Color", "Odour"],
                        "Chemical Parameters": ["DO", "BOD", "COD", "NH4_N", "NO3_N", "NO2_N", "PO4", "SO4"],
                        "Biological Parameters": ["Chlorophyll", "BGA", "Fecal_Coliform", "Total_Coliform", "Productivity", "Phytoplankton", "Zooplankton"],
                        "Meteorological & Geo": ["Wind_Speed", "Wind_Direction", "Air_Temp", "Humidity", "Precipitation", "Shoreline_Status", "Population"]
                    }
                    selected_cats = st.multiselect("Choose Data Categories to Download", list(cat_options.keys()))
                    
                    final_cols = ["created_at", "Date", "Time", "Main_Location", "Location", "Latitude", "Longitude"]
                    for cat in selected_cats:
                        final_cols.extend(cat_options[cat])
                    
                    # Ensure columns exist in dataframe
                    final_cols = [c for c in final_cols if c in filtered_df.columns]
                    
                    if st.button("Generate CSV"):
                        export_df = filtered_df[final_cols].copy()
                        export_df.rename(columns=config.COLUMN_CONFIG, inplace=True)
                        csv = export_df.to_csv(index=False).encode('utf-8')
                        st.download_button(label=f"📥 Download {selected_loc} Data (CSV)", data=csv, file_name=f"NCCR_{selected_loc}_Data.csv", mime="text/csv")
            else:
                st.warning("Database is empty or missing 'Main_Location' data.")
        elif status == "Pending":
            st.warning("⏳ Your request is currently PENDING Admin approval.")
        else:
            if status == "Rejected":
                st.error("❌ Your previous request was REJECTED.")
            else:
                st.info("Please submit a request stating your purpose to access data.")
            with st.form("access_req"):
                purpose = st.text_area("Purpose of Data Use")
                if st.form_submit_button("Submit Request"):
                    if len(purpose) > 5:
                        ok, msg = db.submit_access_request(st.session_state['user_email'], purpose)
                        if ok: 
                            st.success(msg)
                            # Notify Admin
                            admin_msg = f"User {st.session_state['user_email']} requested data access.\nPurpose: {purpose}"
                            utils.send_email_notification(config.SENDER_EMAIL, "New Data Access Request", admin_msg)
                            st.rerun()
                        else: st.error(msg)
                    else:
                        st.error("Purpose is too short.")

    # -----------------------------------------------------
    # OPTION E: MANAGE & DELETE DATA (ADMIN ONLY)
    # -----------------------------------------------------
    elif menu == "🗑️ Manage & Delete Data" and st.session_state['user_role'] == 'Admin':
        st.header("🗑️ Data Management Console")
        st.warning("⚠️ Warning: Deleted data cannot be recovered.")
        
        # Fetch Data
        df = db.fetch_all_data()
        
        if not df.empty:
            # Optional: Filter by Location to make finding rows easier
            if 'Main_Location' in df.columns:
                all_locs = df['Main_Location'].unique().tolist()
                filter_loc = st.selectbox("Filter by Region (Optional)", ["All Regions"] + all_locs)
                
                if filter_loc != "All Regions":
                    df_view = df[df['Main_Location'] == filter_loc]
                else:
                    df_view = df
            else:
                df_view = df
            
            # Show Data with Checkbox Selection
            st.subheader(f"Select Records to Delete ({len(df_view)} rows found)")
            
            # Method: Multiselect by ID (Safest & Simplest)
            date_col = 'Date' if 'Date' in df_view.columns else 'created_at'
            loc_col = 'Main_Location' if 'Main_Location' in df_view.columns else 'id'
            
            df_view['display_label'] = df_view.apply(lambda x: f"ID {x['id']} | {x.get(date_col, 'N/A')} | {x.get(loc_col, 'N/A')}", axis=1)
            
            selected_ids = st.multiselect(
                "Search and Select Records to Delete:",
                options=df_view['id'],
                format_func=lambda x: df_view[df_view['id'] == x]['display_label'].values[0] if x in df_view['id'].values else f"ID {x}"
            )
            
            # Preview Selected
            if selected_ids:
                st.error(f"You have selected {len(selected_ids)} records for DELETION.")
                st.dataframe(df[df['id'].isin(selected_ids)], use_container_width=True) # FIXED WIDTH ERROR
                
                if st.button("🚨 CONFIRM PERMANENT DELETE"):
                    success = db.delete_data(selected_ids)
                    if success:
                        st.success("✅ Records deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Deletion failed. Check console for details.")
        else:
            st.info("No data available to delete.")
import streamlit as st
import pandas as pd
from datetime import date, datetime
from fpdf import FPDF
import database as db

# --- CONFIGURATION ---
st.set_page_config(page_title="NCCR Marine Portal", page_icon="🌊", layout="wide")
CERTIFICATE_THRESHOLD = 5 

# --- UNIT MAPPING FOR CSV EXPORT ---
COLUMN_CONFIG = {
    # Meta Data
    "created_at": "Upload Timestamp",
    "Date": "Collection Date",
    "Time": "Collection Time",
    "Main_Location": "Region",
    "Location": "Specific Spot",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    
    # Physical
    "Water_Temp": "Water Temperature (°C)",
    "Salinity": "Salinity (ppt)",
    "pH": "pH Level",
    "Turbidity": "Turbidity (NTU)",
    "Transparency": "Transparency (cm)",
    "TSS": "Total Suspended Solids (mg/L)",
    "Color": "Water Color",
    "Odour": "Odour",
    
    # Chemical
    "DO": "Dissolved Oxygen (mg/L)",
    "BOD": "Biochemical Oxygen Demand (mg/L)",
    "COD": "Chemical Oxygen Demand (mg/L)",
    "NH4_N": "Ammonium Nitrogen (µmol/L)",
    "NO3_N": "Nitrate Nitrogen (µmol/L)",
    "NO2_N": "Nitrite Nitrogen (µmol/L)",
    "PO4": "Phosphate (µmol/L)",
    "SO4": "Sulphate (mg/L)",
    
    # Biological
    "Fecal_Coliform": "Fecal Coliform (MPN/100ml)",
    "Total_Coliform": "Total Coliform (MPN/100ml)",
    "Productivity": "Primary Productivity (mgC/m3/hr)",
    "Phytoplankton": "Phytoplankton Species",
    "Zooplankton": "Zooplankton Species",
    
    # Social & Geo
    "Population": "Coastal Population",
    "Tourist_Inflow": "Annual Tourist Inflow",
    "Shoreline_Status": "Shoreline Status"
}

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None

# --- HELPER: GENERATE PDF CERTIFICATE ---
def create_certificate(name, contributions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(200, 40, txt="Certificate of Contribution", ln=True, align='C')
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 20, txt="Presented to", ln=True, align='C')
    pdf.set_font("Arial", 'B', 30)
    pdf.set_text_color(0, 0, 128) # Navy Blue
    pdf.cell(200, 20, txt=name, ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 20, txt=f"For contributing {contributions} valuable data points", ln=True, align='C')
    pdf.cell(200, 10, txt="to the NCCR Marine Water Quality Project.", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(200, 30, txt=f"Issued on: {date.today()}", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 🔐 1. LOGIN & REGISTER PAGE
# =========================================================
def login_page():
    st.title("🔐 NCCR Portal Login")
    st.markdown("Please log in to access the National Centre for Coastal Research Portal.")
    
    tab1, tab2 = st.tabs(["Login", "New User Registration"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            user, msg = db.login_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = user['role']
                st.session_state['user_email'] = user['email']
                st.session_state['user_name'] = user['name']
                st.rerun()
            else:
                st.error(msg)
                
    with tab2:
        st.subheader("Create an Account")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email Address")
        new_pass = st.text_input("Create Password", type="password")
        role_choice = st.selectbox("Request Role", ["User", "Admin"]) 
        
        if st.button("Register"):
            if new_email and new_pass and new_name:
                success, msg = db.register_user(new_email, new_name, new_pass, role_choice)
                if success:
                    st.success("✅ Registration Successful! Please switch to the Login tab.")
                else:
                    st.error(msg)
            else:
                st.warning("Please fill all fields.")

# =========================================================
# 🏠 2. MAIN APP (AFTER LOGIN)
# =========================================================
def main_app():
    # --- SIDEBAR ---
    st.sidebar.title("Navigation")
    st.sidebar.write(f"👤 **{st.session_state['user_name']}**")
    st.sidebar.badge(st.session_state['user_role'])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.rerun()
        
    st.title("🌊 NCCR Marine Data Portal")

    # --- DEFINE MENUS BASED ON ROLE ---
    if st.session_state['user_role'] == 'Admin':
        options = ["📥 Contribute Data", "👮 Data Requests (Approval)", "📂 Master Data Repository"]
    else:
        options = ["📥 Contribute Data", "📊 Request & Download Data"]
        
    menu = st.sidebar.radio("Go to:", options)

    # -----------------------------------------------------
    # OPTION A: CONTRIBUTE DATA (Single Entry + Bulk Upload)
    # -----------------------------------------------------
    if menu == "📥 Contribute Data":
        st.header("Submit Marine Field Data")
        st.info("Choose 'Single Entry' for manual input or 'Bulk Upload' for large datasets (Prediction Training).")

        # Initialize State Variables
        certificate_ready = False
        pdf_bytes = None
        contributor_name = ""

        # --- CENTRALIZED LOCATION DATA ---
        coastal_data = {
            "Kerala": ["Thiruvananthapuram Coast", "Kollam Coast", "Alappuzha Coast", "Kochi (Ernakulam) Coast", "Thrissur Coast", "Malappuram Coast", "Kozhikode Coast", "Kannur Coast", "Kasargod Coast", "Other"],
            "Tamil Nadu": ["Chennai Coast", "Thiruvallur Coast", "Kancheepuram Coast", "Villupuram Coast", "Cuddalore Coast", "Nagapattinam Coast", "Thiruvarur Coast", "Thanjavur Coast", "Pudukottai Coast", "Ramanathapuram Coast", "Thoothukudi Coast", "Tirunelveli Coast", "Kanyakumari Coast", "Other"],
            "Karnataka": ["Dakshina Kannada Coast", "Udupi Coast", "Uttara Kannada Coast", "Other"],
            "Maharashtra": ["Mumbai City Coast", "Mumbai Suburban Coast", "Thane Coast", "Palghar Coast", "Raigad Coast", "Ratnagiri Coast", "Sindhudurg Coast", "Other"],
            "Goa": ["North Goa Coast", "South Goa Coast", "Other"],
            "Gujarat": ["Kutch Coast", "Jamnagar Coast", "Porbandar Coast", "Junagadh Coast", "Amreli Coast", "Bhavnagar Coast", "Ahmedabad Coast", "Anand Coast", "Bharuch Coast", "Surat Coast", "Navsari Coast", "Valsad Coast", "Other"],
            "Andhra Pradesh": ["Srikakulam Coast", "Vizianagaram Coast", "Visakhapatnam Coast", "East Godavari Coast", "West Godavari Coast", "Krishna Coast", "Guntur Coast", "Prakasam Coast", "Nellore Coast", "Other"],
            "Odisha": ["Balasore Coast", "Bhadrak Coast", "Kendrapara Coast", "Jagatsinghpur Coast", "Puri Coast", "Ganjam Coast", "Other"],
            "West Bengal": ["Purba Medinipur Coast", "South 24 Parganas Coast", "North 24 Parganas Coast", "Other"],
            "Puducherry (UT)": ["Puducherry Region Coast", "Karaikal Coast", "Mahe Coast", "Yanam Coast", "Other"],
            "Daman & Diu (UT)": ["Daman Coast", "Diu Coast", "Other"],
            "Lakshadweep (UT)": ["Kavaratti", "Agatti", "Minicoy", "Amini", "Andrott", "Other"],
            "Andaman & Nicobar (UT)": ["Port Blair", "Havelock Island", "Neil Island", "Little Andaman", "Great Nicobar", "Other"],
            "Other State/Region": ["Other"]
        }

        # --- MODE SELECTION TABS ---
        tab_single, tab_bulk = st.tabs(["📝 Single Entry (Manual)", "📂 Bulk Upload (CSV)"])

        # ==========================================
        # 🟢 TAB 1: SINGLE ENTRY (Manual)
        # ==========================================
        with tab_single:
            st.subheader("1. Location & Profile")
            st.write(f"**Contributor:** {st.session_state['user_name']}")
            
            lc1, lc2, lc3 = st.columns(3)
            selected_state = lc1.selectbox("Select State / UT", list(coastal_data.keys()), key="s_state")
            available_coasts = coastal_data[selected_state]
            selected_coast = lc2.selectbox("Select Coastal Region", available_coasts, key="s_coast")
            
            if selected_coast == "Other" or selected_state == "Other State/Region":
                custom_coast = lc3.text_input("✍️ Type Region Name", placeholder="Enter specific region name", key="s_custom")
                final_main_loc = f"{selected_state} - {custom_coast}" if custom_coast else f"{selected_state} - Unknown" if selected_state == "Other State/Region" else f"{selected_state} - {custom_coast}" if custom_coast else "Unknown"
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
                    salinity = p2.number_input("Salinity (ppt)", format="%.2f")
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
                    st.markdown("**Microbial Analysis:**")
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
                        "Tourist_Inflow": tourist_inflow, "Optimum_Season": season
                    }
                    
                    if db.save_marine_data(data_packet):
                        st.success(f"✅ Data Saved under Region: **{final_main_loc}**")
                        count = db.get_contribution_count(st.session_state['user_email'])
                        st.toast(f"Total Contributions: {count}")
                        if count >= CERTIFICATE_THRESHOLD:
                            certificate_ready = True
                            contributor_name = st.session_state['user_name']
                            pdf_bytes = create_certificate(contributor_name, count)
                    else:
                        st.error("Failed to save data.")

        # ==========================================
        # 🔵 TAB 2: BULK UPLOAD (For Prediction)
        # ==========================================
        with tab_bulk:
            st.subheader("Bulk Data Upload for Prediction")
            st.write("Upload historical data (CSV) to train the prediction model.")
            
            # 1. Location Selection
            bc1, bc2 = st.columns(2)
            b_state = bc1.selectbox("Select State / UT", list(coastal_data.keys()), key="b_state")
            b_coast = bc2.selectbox("Select Coastal Region", coastal_data[b_state], key="b_coast")
            
            if b_coast == "Other" or b_state == "Other State/Region":
                b_custom = st.text_input("✍️ Type Region Name", key="b_custom")
                final_bulk_loc = f"{b_state} - {b_custom}" if b_custom else f"{b_state} - Unknown"
            else:
                final_bulk_loc = b_coast

            # --- NEW ADDITIONS: Details for Bulk Upload ---
            st.write("**Location & Contributor Details for this Batch:**")
            
            b1, b2, b3 = st.columns(3)
            b_lat = b1.number_input("Latitude", format="%.6f", value=13.0827, key="b_lat")
            b_lon = b2.number_input("Longitude", format="%.6f", value=80.2707, key="b_lon")
            b_spot = b3.text_input("Specific Spot Name", key="b_spot")
            
            b4, b5 = st.columns(2)
            b_prof = b4.selectbox("Profession", ["Student", "Researcher", "Official", "Fisherman", "Other"], key="b_prof")
            b_desig = b5.text_input("Designation", key="b_desig")

            st.info(f"📍 All data in the CSV will be saved under: **{final_bulk_loc}** ({b_spot})")

            # 2. Template
            st.markdown("---")
            st.write("⚠️ **Format Requirement:** CSV with columns: Date, Time, Water_Temp, Salinity, DO, pH, etc.")
            template_cols = ["Date", "Time", "Water_Temp", "Salinity", "DO", "pH", "Turbidity", "TSS", "BOD", "COD"]
            template_data = pd.DataFrame(columns=template_cols)
            csv_template = template_data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV Template", data=csv_template, file_name="nccr_template.csv", mime="text/csv")

            # 3. File Uploader
            uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
            
            if uploaded_file is not None:
                try:
                    bulk_df = pd.read_csv(uploaded_file)
                    st.write("📊 **Data Preview:**")
                    st.dataframe(bulk_df.head(), width="stretch")
                    
                    if st.button("🚀 Upload Bulk Data"):
                        data_list = []
                        for index, row in bulk_df.iterrows():
                            # Handle Date & Time
                            row_date = str(row.get("Date", date.today()))
                            row_time = str(row.get("Time", datetime.now().time()))
                            
                            packet = {
                                "Contributor": st.session_state['user_name'],
                                "Email": st.session_state['user_email'],
                                
                                # New Bulk Details applied to all rows
                                "Main_Location": final_bulk_loc,
                                "Location": b_spot,
                                "Latitude": b_lat,
                                "Longitude": b_lon,
                                "Profession": b_prof,
                                "Designation": b_desig,
                                
                                "Date": row_date,
                                "Time": row_time,
                                
                                "Water_Temp": row.get("Water_Temp", None),
                                "Salinity": row.get("Salinity", None),
                                "DO": row.get("DO", None),
                                "pH": row.get("pH", None),
                                "Turbidity": row.get("Turbidity", None),
                                "TSS": row.get("TSS", None),
                                "BOD": row.get("BOD", None),
                                "COD": row.get("COD", None),
                                
                                "created_at": str(datetime.now())
                            }
                            data_list.append(packet)
                        
                        success, msg = db.save_bulk_data(data_list)
                        if success:
                            st.success(f"✅ Successfully uploaded {len(data_list)} records!")
                            st.balloons()
                        else:
                            st.error(f"Failed: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        # DOWNLOAD CERTIFICATE
        if certificate_ready and pdf_bytes:
            st.balloons()
            st.success("🏆 Certificate Unlocked!")
            st.download_button(label="📥 Download Certificate", data=pdf_bytes, file_name=f"NCCR_Cert.pdf", mime="application/pdf")

    # -----------------------------------------------------
    # OPTION B: ADMIN
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
                        st.rerun()
                    if c2.button("❌ Reject", key=f"rej_{row['id']}"):
                        db.update_request_status(row['id'], "Rejected")
                        st.rerun()
        else:
            st.info("No pending requests found.")

    # -----------------------------------------------------
    # OPTION C: MASTER DATA
    # -----------------------------------------------------
    elif menu == "📂 Master Data Repository":
        st.header("NCCR Master Database")
        df = db.fetch_all_data()
        st.dataframe(df, use_container_width=True)

    # -----------------------------------------------------
    # OPTION D: DOWNLOAD CENTER
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
                available_locs = raw_df['Main_Location'].unique().tolist()
                selected_loc = st.selectbox("Select Coastal Region", available_locs)
                filtered_df = raw_df[raw_df['Main_Location'] == selected_loc].copy()
                st.info(f"Found {len(filtered_df)} records for {selected_loc}.")
                
                st.divider()
                st.subheader("🛠️ Step 2: Select Parameter Categories")
                cat_options = {
                    "Physical Parameters": ["Water_Temp", "Salinity", "pH", "Turbidity", "Transparency", "TSS", "Color", "Odour"],
                    "Chemical Parameters": ["DO", "BOD", "COD", "NH4_N", "NO3_N", "NO2_N", "PO4", "SO4"],
                    "Biological Parameters": ["Fecal_Coliform", "Total_Coliform", "Productivity", "Phytoplankton", "Zooplankton"],
                    "Geographical & Social": ["Shoreline_Status", "Population", "Tourism_Status", "Tourist_Inflow"]
                }
                selected_cats = st.multiselect("Choose Data Categories to Download", list(cat_options.keys()))
                final_cols = ["created_at", "Date", "Time", "Main_Location", "Location", "Latitude", "Longitude"]
                for cat in selected_cats:
                    final_cols.extend(cat_options[cat])
                final_cols = [c for c in final_cols if c in filtered_df.columns]
                
                if st.button("Generate CSV"):
                    export_df = filtered_df[final_cols].copy()
                    export_df.rename(columns=COLUMN_CONFIG, inplace=True)
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
                        if ok: st.success(msg); st.rerun()
                        else: st.error(msg)
                    else:
                        st.error("Purpose is too short.")

# --- APP FLOW CONTROL ---
if st.session_state['logged_in']:
    main_app()
else:
    login_page()
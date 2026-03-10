import streamlit as st
import pandas as pd
from datetime import date, datetime
import database as db
import utils
import config
import uuid
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

PENDING_CSV = "pending_verification.csv"

def send_verification_email(to_email, prof_name, request_id, user_name):
    # 1. Setup the Email Wrapper
    msg = MIMEMultipart('related')
    msg['Subject'] = "[Action Required] Verify Data Submission - NCCR Marine Data Portal"
    msg['From'] = config.SENDER_EMAIL
    msg['To'] = to_email

    # 2. Define the Image Path (Use relative path for deployment safety if possible)
    # Note: Ensure 'emblem.jpg' is in the project folder, or use the full path provided.
    img_path = r"pages\__pycache__\emblem.jpg" 
    
    # 3. Create the HTML Body
    import sys
    if sys.platform != "win32":
        # Assume production streamlit cloud (Linux)
        BASE_URL = "https://nccr-coastal-data-project-vcfp6ym9hfkvmzvydnqe3u.streamlit.app"
    else:
        # Local testing (Windows)
        BASE_URL = "http://localhost:8501"

    # We use cid:header_image to reference the attached image inside the HTML
    html_content = f"""
    <html>
      <body>
        <center>
          <img src="cid:header_image" alt="NCCR Emblem" style="width: 120px; height: auto;">
        </center>
        <p>Dear Prof. {prof_name},</p>
        <p>Good Day!</p>
        <p>It is for your information that <b>National Centre for Coastal Research</b>, an attached body of Ministry of Earth Sciences, Govt. of India has taken an initiative for strengthening coastal-ocean data repository for the welfare of Indian coastal Community and various government initiative and missions.</p>
        <p>As a part of this initiative data can be requested and shared by a Researcher/academician to the NCCR-Marine Data Portal for their advance research and understanding the coastal environment in face of changing nature-human landscape.</p>
        <p>Therefore, On behalf of above NCCR-Marine Data Portal, I may request to verify my attached data and kindly approve so that it will be placed at the above data portal. This data shall be treated as contributed and verified by <b>Shri. {user_name}</b> and <b>Prof./Dr. {prof_name}</b> jointly.</p>
        <p>As per the requirement of Data portal, Data has to be verified by the expert within 15 days from date of submission of the data.</p>
        <p>You may please suggest any other expert(s), in case you preoccupied/unavailable to verify the data.</p>
        
        <p>
            <a href="{BASE_URL}/?page=verify&id={request_id}" 
               style="background-color: #008CBA; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
               Click Here to Verify Data
            </a>
        </p>

        <p>Thank you Sir.</p>
        <p>With regards,<br><b>{user_name}</b></p>
      </body>
    </html>
    """
    
    # Attach HTML part
    msg.attach(MIMEText(html_content, 'html'))

    # 4. Embed the Image
    try:
        with open(img_path, 'rb') as f:
            img_data = f.read()
            
        # Initialize MIMEImage with the correct subtype
        image = MIMEImage(img_data, _subtype='jpeg', name=os.path.basename(img_path))
        
        # Explicitely set Content-ID with angle brackets
        image.add_header('Content-ID', '<header_image>')
        
        # Set Content-Disposition to inline so it displays in the body
        image.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
        
        msg.attach(image)
    except Exception as e:
        print(f"Warning: Could not attach emblem image. Error: {e}")

    # 5. Send Email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email failed to send: {e}")
        return False

def app():
    st.header("Submit Marine Field Data")
    st.info("Choose 'Single Entry' for manual input or 'Bulk Upload' for large datasets.")

    # Initialize State Variables
    certificate_ready = False
    pdf_bytes = None
    
    # Global User Name Input
    user_name = st.text_input("Your Name", value=st.session_state.get('user_name', 'Guest'))
    contributor_name = user_name

    # --- MODE SELECTION TABS ---
    tab_single, tab_bulk = st.tabs(["📝 Single Entry (Manual)", "📂 Bulk Upload (CSV/Excel)"])

    # ==========================================
    # 🟢 TAB 1: SINGLE ENTRY (Manual)
    # ==========================================
    with tab_single:
        st.subheader("1. Location & Profile")
        st.write(f"**Contributor:** {user_name}")
        
        lc1, lc2, lc3 = st.columns(3)
        # Use Global COASTAL_DATA from config
        selected_state = lc1.selectbox("Select State / UT", list(config.COASTAL_DATA.keys()), key="s_state")
        available_coasts = config.COASTAL_DATA[selected_state]
        selected_coast = lc2.selectbox("Select Coastal Region", available_coasts, key="s_coast")
        
        if selected_coast == "Other" or selected_state == "Other State/Region":
            custom_coast = lc3.text_input("✍️ Type Region Name", placeholder="Enter specific region name", key="s_custom")
            final_main_loc = f"{selected_state} - {custom_coast}" if custom_coast else f"{selected_state} - Unknown"
            def_lat, def_lon = 13.0827, 80.2707
        else:
            final_main_loc = selected_coast
            def_lat, def_lon = config.REGION_COORDS.get(selected_coast, (13.0827, 80.2707))

        c1, c2, c3 = st.columns(3)
        # Use dynamic key to force widget update
        latitude = c1.number_input("Latitude", format="%.6f", value=def_lat, key=f"s_lat_{selected_coast}")
        longitude = c2.number_input("Longitude", format="%.6f", value=def_lon, key=f"s_lon_{selected_coast}")
        specific_loc = c3.text_input("Specific Spot Name", key="s_spot")
        
        c4, c5, c6, c7 = st.columns(4)
        prof_role = c4.selectbox("Profession", ["Student", "Researcher", "Official", "Fisherman", "Other"], key="s_role")
        designation = c5.text_input("Designation", key="s_desig")
        date_col = c6.date_input("Date of Collection", date.today(), key="s_date")
        time_col = c7.time_input("Time of Collection", datetime.now().time(), key="s_time")

        st.markdown("---")
        st.subheader("🎓 Professor Verification (Required)")
        pv1, pv2, pv3 = st.columns(3)
        prof_name = pv1.text_input("Professor Name")
        prof_univ = pv2.text_input("University / Institution")
        prof_email = pv3.text_input("Professor Email")

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
                wb_type = g2.selectbox("Nearby Water Body Type", ["Estuary", "River", "Lake", "Lagoon", "Creek", "Backwater", "Other"])
                water_bodies = g3.number_input("Nearby Water Bodies (Count)", step=1)
                
                g4, g5, g6 = st.columns(3)
                indus = g4.number_input("Industrial Est", step=1)
                tourism = g5.selectbox("Tourism", ["Active", "Inactive"])
                tourist_inflow = g6.number_input("Tourist Inflow", step=100)
                
                season = st.text_input("Optimum Season")

            submitted = st.form_submit_button("🚀 Submit for Verification")

            if submitted:
                if not prof_email or not prof_name:
                    st.error("⚠️ Professor Details are required for verification.")
                else:
                    request_id = str(uuid.uuid4())
                    data_packet = {
                        "request_id": request_id,
                        "prof_email": prof_email,
                        "prof_name": prof_name,
                        "university": prof_univ,
                        "status": "pending",
                        # Data Fields
                        "Contributor": st.session_state.get('user_name', 'Guest'), "Email": st.session_state.get('user_email', ''),
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
                        "Shoreline_Status": shore, "Water_Body_Type": wb_type, 
                        "Water_Bodies": water_bodies,
                        "Industrial_Est": indus, "Tourism_Status": tourism,
                        "Tourist_Inflow": tourist_inflow, "Optimum_Season": season,
                        "created_at": str(datetime.now())
                    }
                    
                    # Save to CSV
                    try:
                        # Enforce Master Schema
                        for col in config.MASTER_COLUMNS:
                            if col not in data_packet:
                                data_packet[col] = None
                                
                        df_new = pd.DataFrame([data_packet], columns=config.MASTER_COLUMNS)
                        
                        if os.path.exists(PENDING_CSV):
                            df_new.to_csv(PENDING_CSV, mode='a', header=False, index=False)
                        else:
                            df_new.to_csv(PENDING_CSV, mode='w', header=True, index=False)
                            
                        # Send Email
                        if send_verification_email(prof_email, prof_name, request_id, user_name):
                            st.success(f"✅ Invitation sent to {prof_email}!")
                            st.info("Your data is pending verification. Once approved, it will be added to the database.")
                        else:
                            st.warning("Data saved, but failed to send email. Please contact Admin.")
                            
                    except Exception as e:
                        st.error(f"Error saving data: {e}")

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

        st.markdown("---")
        st.subheader("🎓 Professor Verification (Required)")
        bp1, bp2, bp3 = st.columns(3)
        b_prof_name = bp1.text_input("Professor Name", key="b_pname")
        b_univ = bp2.text_input("University / Institution", key="b_puniv")
        b_prof_email = bp3.text_input("Professor Email", key="b_pemail")

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
                st.dataframe(bulk_df.head(), width='stretch') 
                
                if st.button("🚀 Submit Bulk Data for Verification"):
                    if not b_prof_email or not b_prof_name:
                         st.error("⚠️ Professor Details are required for verification.")
                    else:
                        request_id = str(uuid.uuid4())
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
                                        dt_obj = pd.to_datetime(dt_val, dayfirst=True)
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
                                "request_id": request_id,
                                "prof_email": b_prof_email,
                                "prof_name": b_prof_name,
                                "university": b_univ,
                                "status": "pending",
                                
                                "Contributor": st.session_state.get('user_name', 'Guest'),
                                "Email": st.session_state.get('user_email', ''),
                                
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
                        
                        # Save to CSV (Pending Verification)
                        try:
                            # Enforce Master Schema
                            # 1. Fill missing columns in each packet
                            for packet in data_list:
                                for col in config.MASTER_COLUMNS:
                                    if col not in packet:
                                        packet[col] = None
                            
                            # 2. Create DataFrame with ordered columns
                            df_new = pd.DataFrame(data_list, columns=config.MASTER_COLUMNS)
                            
                            if os.path.exists(PENDING_CSV):
                                df_new.to_csv(PENDING_CSV, mode='a', header=False, index=False)
                            else:
                                df_new.to_csv(PENDING_CSV, mode='w', header=True, index=False)
                                
                            my_bar.progress(1.0)
                            
                            # Send Email
                            if send_verification_email(b_prof_email, b_prof_name, request_id, user_name):
                                st.success(f"✅ Bulk Data submitted! Verification link sent to Prof. {b_prof_name} ({b_prof_email}).")
                                st.balloons()
                            else:
                                st.warning("Data saved, but failed to send email. Please contact Admin.")
                                
                        except Exception as e:
                            st.error(f"Error saving bulk data: {e}")
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

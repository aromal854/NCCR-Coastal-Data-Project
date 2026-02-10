# dashboard.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import database as db
import utils
import config
import prediction # <--- IMPORT THE NEW FILE
import pages.contribute as contribute_page # NEW IMPORT

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

    # --- ADMIN SIDEBAR ANALYTICS (NEW) ---
    if st.session_state['user_role'] == 'Admin':
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Live Counters")
        
        # Quick Fetch for Stats
        stats_df = db.fetch_all_data()
        
        if not stats_df.empty:
            total_records = len(stats_df)
            
            # Calculate Monthly Growth
            try:
                current_month = datetime.now().strftime("%Y-%m")
                # Ensure string parsing is safe
                stats_df['temp_month'] = stats_df['created_at'].astype(str).str[:7]
                new_this_month = len(stats_df[stats_df['temp_month'] == current_month])
            except:
                new_this_month = 0
                
            # Top Region Logic
            top_loc = "N/A"
            if 'Main_Location' in stats_df.columns:
                try:
                    top_loc = stats_df['Main_Location'].value_counts().idxmax()
                    # Optional: Shorten if too long
                    if len(top_loc) > 15: top_loc = top_loc[:12] + "..."
                except:
                    top_loc = "N/A"

            # Count Verified
            verified_count = 0
            if 'Verified_By' in stats_df.columns:
                verified_count = len(stats_df.dropna(subset=['Verified_By']))

            # Display Metrics
            st.sidebar.metric("Total Data Points", total_records, delta=f"+{new_this_month} this month")
            st.sidebar.metric("✅ Verified Records", verified_count)
            st.sidebar.caption(f"🏆 Top Region: **{top_loc}**")
        else:
            st.sidebar.warning("No data found.")

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
        st.markdown("""
        **Data Visualization Console**  
        🔴 Each point represents a verified field data report.  
        👇 **Hover over points** to see details like Water Temperature, Salinity, and Contributor.
        """)
        
        df = db.fetch_all_data()
        import pydeck as pdk # Import locally to avoid global clutter if unused elsewhere
        
        if not df.empty:
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                # Filter valid coordinates
                map_df = df.dropna(subset=['Latitude', 'Longitude']) # Ensure numeric?
                
                # Convert coords to numeric just in case
                map_df['latitude'] = pd.to_numeric(map_df['Latitude'], errors='coerce')
                map_df['longitude'] = pd.to_numeric(map_df['Longitude'], errors='coerce')
                map_df = map_df.dropna(subset=['latitude', 'longitude'])

                if not map_df.empty:
                    # --- INTERACTIVE MAP METRICS ---
                    m1, m2, m3 = st.columns(3)
                    m1.metric("📍 Active Locations", map_df['Main_Location'].nunique())
                    m2.metric("📝 Total Reports", len(map_df))
                    m3.metric("📅 Latest Entry", map_df['created_at'].max()[:10] if 'created_at' in map_df else "N/A")

                    st.divider()

                    # --- PYDECK LAYER ---
                    layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_df,
                        get_position='[longitude, latitude]',
                        get_color='[200, 30, 0, 160]', # Red with transparency
                        get_radius=2000, # Meters
                        pickable=True, # Enable Tooltip
                        radius_min_pixels=8,
                        radius_max_pixels=30,
                    )

                    # --- VIEW STATE ---
                    # Center map on India approx
                    view_state = pdk.ViewState(
                        latitude=20.5937,
                        longitude=78.9629,
                        zoom=4,
                        pitch=0,
                    )

                    # --- TOOLTIP CONFIG ---
                    tooltip = {
                        "html": "<b>Location:</b> {Main_Location} <br/>"
                                "<b>Date:</b> {Date} <br/>"
                                "<b>Temp:</b> {Water_Temp} °C <br/>"
                                "<b>Salinity:</b> {Salinity} psu <br/>"
                                "<b>Contributor:</b> {Contributor}",
                        "style": {
                            "backgroundColor": "steelblue",
                            "color": "white"
                        }
                    }

                    # Render
                    r = pdk.Deck(
                        layers=[layer],
                        initial_view_state=view_state,
                        tooltip=tooltip,
                        # map_style=None  # Let Streamlit use default (usually CARTO)
                    )
                    
                    st.pydeck_chart(r)
                    
                else:
                    st.warning("No data points with valid coordinates found after verification.")
            else:
                st.warning("Dataset missing Latitude/Longitude columns.")
        else:
            st.info("Database is empty.")

    # -----------------------------------------------------
    # OPTION A: CONTRIBUTE DATA (UPDATED)
    # -----------------------------------------------------
    elif menu == "📥 Contribute Data":
        contribute_page.app()

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
                
                # Check for Verified_By and highlight it
                if 'Verified_By' in df.columns:
                     st.info("💡 Note: Data verified by external professors includes a 'Verified_By' tag.")

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
                    st.dataframe(filtered_df, width='stretch') # FIXED WIDTH ERROR
                else:
                    st.warning(f"No data found for any region in {selected_state}")
            else:
                # View All Data
                st.write(f"Total Records: **{len(df)}**")
                st.dataframe(df, width='stretch') # FIXED WIDTH ERROR
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
                    
                    final_cols = ["created_at", "Date", "Time", "Main_Location", "Location", "Latitude", "Longitude", "Verified_By"] # Added Verified_By
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
                st.dataframe(df[df['id'].isin(selected_ids)], width='stretch') # FIXED WIDTH ERROR
                
                if st.button("🚨 CONFIRM PERMANENT DELETE"):
                    success = db.delete_data(selected_ids)
                    if success:
                        st.success("✅ Records deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Deletion failed. Check console for details.")
        else:
            st.info("No data available to delete.")
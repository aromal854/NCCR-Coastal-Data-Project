import streamlit as st
import pandas as pd
import database as db
import utils
import config
import os
import numpy as np
import math

PENDING_CSV = "pending_verification.csv"
MAIN_CSV = "nccr_data.csv"

def show(request_id_from_app=None):
    # Set page config only if not already set (though app.py sets it usually)
    # st.set_page_config(page_title="Data Verification", page_icon="✅", layout="wide")
    
    st.markdown(
        """
        <div class="nccr-hero" style="margin-top:14px;">
            <div class="nccr-section-label">Verification</div>
            <div style="display:flex; gap:12px; align-items:flex-start;">
                <span class="material-symbols-rounded nccr-icon">verified_user</span>
                <div>
                    <h2 style="margin:0;">External Professor Verification</h2>
                    <p class="nccr-card-subtitle" style="margin-top:6px;">
                        Review the submission batch and approve or discard it securely.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # If ID passed from app.py, use it. Otherwise try to get from query params (fallback)
    request_id = request_id_from_app
    
    if not request_id:
        # Helper to get query params safely if needed
        if hasattr(st, "query_params"):
            request_id = st.query_params.get("id")
        else:
            params = st.experimental_get_query_params()
            request_id = params.get("id", [None])[0]

    if not request_id:
        st.error("Invalid or missing Request ID.")
        st.info("Please use the full link provided in the verification email.")
        return

    if not os.path.exists(PENDING_CSV):
        st.error("No pending verification records found.")
        return

    try:
        df = pd.read_csv(PENDING_CSV)
        
        # Ensure requests are strings to match CSV
        if 'request_id' in df.columns:
            df['request_id'] = df['request_id'].astype(str)
            
        batch = df[df['request_id'] == str(request_id)]
        
        if batch.empty:
            st.warning("This verification link is invalid or has already been processed.")
            st.info("You can close this window.")
            return
            
        # Get Professor Details from the first row
        first_row = batch.iloc[0].to_dict()
        prof_name = first_row.get('prof_name', 'Professor')
        university = first_row.get('university', 'Institution')
        
        st.markdown(
            f"""
            <div class="nccr-card" style="padding:14px 14px;">
                <div class="nccr-section-label">Welcome</div>
                <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
                    <div style="font-weight:800; color:var(--nccr-ink-2); font-size:1.02rem;">
                        Prof. {prof_name}
                    </div>
                    <div class="nccr-pill">{university}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        count = len(batch)
        if count > 1:
            st.info(f"You have a **Bulk Upload Batch** of **{count} records** to verify.")
        else:
            st.write("Please review the following marine data submission.")
        
        # Display Data (Exclude metadata for cleaner view)
        st.subheader("Submitted Data")
        
        display_cols = [c for c in batch.columns if c not in ['request_id', 'prof_email', 'prof_name', 'university', 'status']]
        st.dataframe(batch[display_cols], width='stretch')
        
        st.markdown("---")
        st.subheader("Decision")
        
        c1, c2, c3 = st.columns(3, gap="small")
        
        if c1.button("Verify & Approve Batch", type="primary"):
            # 1. Prepare Data
            prof_tag = f"{prof_name} ({university})"
            
            # Add Verified_By to ALL rows in the batch
            batch_to_save = batch.copy()
            batch_to_save['verified_by'] = prof_tag
            
            # Convert to list of dicts first
            raw_data_list = batch_to_save.to_dict(orient='records')
            
            # MANUAL CLEANUP: Iterate through every field to catch NaN/Inf
            # Bypassing Pandas to ensure 100% JSON compliance
            clean_data_list = []
            for row in raw_data_list:
                clean_row = {}
                for k, v in row.items():
                    # EXCLUDE TEMP COLUMNS not in DB
                    if k in ['prof_email', 'prof_name', 'university', 'status', 'request_id']:
                        continue
                        
                    # Check for float NaN or Infinity
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        clean_row[k] = None
                    # Check for pandas/numpy NaN objects
                    elif pd.isna(v): 
                        clean_row[k] = None
                    else:
                        clean_row[k] = v
                clean_data_list.append(clean_row)
            
            # Save to Supabase (Bulk)
            success, msg = db.save_bulk_data(clean_data_list)
            
            if success:
                # Save to nccr_data.csv (Legacy Requirement) - Append Batch
                try:
                    if os.path.exists(MAIN_CSV):
                        batch_to_save.to_csv(MAIN_CSV, mode='a', header=False, index=False)
                    else:
                        batch_to_save.to_csv(MAIN_CSV, mode='w', header=True, index=False)
                except Exception as csv_e:
                    print(f"CSV Backup Error: {csv_e}")
                
                # Remove from Pending (Filter out this request_id)
                df_clean = df[df['request_id'] != str(request_id)]
                df_clean.to_csv(PENDING_CSV, index=False)
                
                st.balloons()
                st.success(f"{len(clean_data_list)} records verified and approved. Thank you for your contribution.")
                st.stop()
            else:
                st.error(f"Error saving to database: {msg}")

        if c2.button("Discard Batch"):
            # Remove from Pending
            df_clean = df[df['request_id'] != str(request_id)]
            df_clean.to_csv(PENDING_CSV, index=False)
            st.error("Data batch has been discarded.")
            st.stop()
            
        if c3.button("Busy / Later"):
            st.info("No action taken. You can come back later using the same link.")

        st.markdown("---")
        st.write("Are you a Professor/Researcher? [Register Here](http://localhost:8501) to join the NCCR Portal.")
        
    except Exception as e:
        st.error(f"Error processing verification: {e}")

import streamlit as st
import pandas as pd
import database as db
import utils
import config
import os

PENDING_CSV = "pending_verification.csv"
MAIN_CSV = "nccr_data.csv"

def show(request_id):
    st.set_page_config(page_title="Data Verification", page_icon="✅", layout="wide")
    st.title("🛡️ External Professor Verification")
    
    if not os.path.exists(PENDING_CSV):
        st.error("No pending verification records found.")
        return

    try:
        df = pd.read_csv(PENDING_CSV)
        # Ensure we look for the request_id as a string
        # Filter for ALL rows matching the request_id (Batch Support)
        batch = df[df['request_id'] == request_id]
        
        if batch.empty:
            st.warning("⚠️ This verification link is invalid or has already been processed.")
            st.info("You can close this window.")
            return
            
        # Get Professor Details from the first row
        first_row = batch.iloc[0].to_dict()
        prof_name = first_row.get('prof_name', 'Professor')
        university = first_row.get('university', 'Institution')
        
        st.success(f"Welcome, **Prof. {prof_name}** from **{university}**!")
        
        count = len(batch)
        if count > 1:
            st.info(f"You have a **Bulk Upload Batch** of **{count} records** to verify.")
        else:
            st.write("Please review the following marine data submission.")
        
        # Display Data (Exclude metadata for cleaner view)
        st.subheader("📊 Submitted Data")
        
        display_cols = [c for c in batch.columns if c not in ['request_id', 'prof_email', 'prof_name', 'university', 'status']]
        st.dataframe(batch[display_cols], use_container_width=True)
        
        st.markdown("---")
        st.subheader("Decision")
        
        c1, c2, c3 = st.columns(3)
        
        if c1.button("✅ Verify & Approve Batch", type="primary"):
            # 1. Prepare Data
            prof_tag = f"{prof_name} ({university})"
            
            # Add Verified_By to ALL rows in the batch
            batch_to_save = batch.copy()
            batch_to_save['Verified_By'] = prof_tag
            
            # Convert to list of dicts for DB
            data_list = batch_to_save.to_dict(orient='records')
            
            # Save to Supabase (Bulk)
            success, msg = db.save_bulk_data(data_list)
            
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
                df_clean = df[df['request_id'] != request_id]
                df_clean.to_csv(PENDING_CSV, index=False)
                
                st.balloons()
                st.success(f"✅ {len(data_list)} Records Verified and Approved! Thank you for your contribution.")
                st.stop()
            else:
                st.error(f"❌ Error saving to database: {msg}")

        if c2.button("❌ Discard Batch"):
            # Remove from Pending
            df_clean = df[df['request_id'] != request_id]
            df_clean.to_csv(PENDING_CSV, index=False)
            st.error("Data batch has been discarded.")
            st.stop()
            
        if c3.button("⏳ Busy / Later"):
            st.info("No action taken. You can come back later using the same link.")

        st.markdown("---")
        st.write("Are you a Professor/Researcher? [Register Here](http://localhost:8501) to join the NCCR Portal.")
        
    except Exception as e:
        st.error(f"Error processing verification: {e}")

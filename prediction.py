# prediction.py
import streamlit as st
import pandas as pd
import numpy as np

# --- 1. DATA UPLOADING & PROCESSING ---

def get_column_mapping(df_columns):
    """
    Identifies columns using Strict Dual-Keyword "Fingerprint" Rules.
    Returns: Dictionary { 'internal_key': 'actual_csv_header' }
    """
    mapping = {}
    
    for col in df_columns:
        c = col.lower()
        
        # Strict Rules
        if "temp" in c and ("water" in c or "wq" in c) and "water bodies" not in c:
            mapping['water_temp'] = col
        elif "temp" in c and "air" in c:
            mapping['air_temp'] = col
        elif "sal" in c:
            mapping['salinity'] = col
        elif "turb" in c:
            mapping['turbidity'] = col
        elif "ph" == c or "p.h." == c or "ph level" in c: # Exact or specific phrase, avoids 'Phytoplankton'
             mapping['ph'] = col
        elif ("oxygen" in c or "dissolved" in c) or c == "do":
            mapping['do'] = col
        elif "tds" in c:
             mapping['tds'] = col
        elif "tss" in c:
             mapping['tss'] = col
        elif "water" in c and "bodies" in c:
             mapping['water_bodies'] = col
        elif "precip" in c or "rain" in c:
             mapping['precipitation'] = col
             
    return mapping

def clean_marine_data(df):
    """
    Applies NCCR Standard Cleaning: Date Handle -> Dead Sensor -> Physics Filter -> Interpolation.
    Returns: df (cleaned), mapping (dict), report (dict of lists)
    """
    # Step A: Date Handling
    date_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)
    
    if not date_col:
        return None, None, None, None # Signal Error
    
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
    except Exception as e:
        st.error(f"❌ Error converting '{date_col}' to datetime: {e}")
        return None, None, None, None

    # Step B: Initialize Logs
    dropped_cols = []
    interpolated_cols = []
    untouched_cols = []
    
    # Identify Columns
    mapping = get_column_mapping(df.columns)
    
    # Step C: Dead Sensor Check (TDS/TSS)
    for key in ['tds', 'tss']:
        if key in mapping:
            col_name = mapping[key]
            # Check if all 0 or sum is 0 (assuming non-negative sensors)
            if df[col_name].sum() == 0:
                df = df.drop(columns=[col_name])
                dropped_cols.append(col_name)
                st.warning(f"⚠️ Dropped Dead Sensor (All 0.0): {col_name}")
                del mapping[key] # Remove from map so we don't process it further

    # Step D: Physics Quarantine (Masking)
    # Applied ONLY to mapped columns
    
    if 'water_temp' in mapping:
        c = mapping['water_temp']
        # Mask > 40
        df.loc[df[c] > 40, c] = np.nan
        
    if 'ph' in mapping:
        c = mapping['ph']
        # Mask < 6 or > 9
        df.loc[(df[c] < 6) | (df[c] > 9), c] = np.nan
        
    if 'turbidity' in mapping:
        c = mapping['turbidity']
        # Mask < 0
        df.loc[df[c] < 0, c] = np.nan
        
    if 'salinity' in mapping:
        c = mapping['salinity']
        # Mask < 0.5
        df.loc[df[c] < 0.5, c] = np.nan
        
    if 'do' in mapping:
        c = mapping['do']
        # Mask < 0
        df.loc[df[c] < 0, c] = np.nan

    # Step E: Temporal Imputation & Logging
    # Iterate ALL columns remaining in dataframe
    remaining_gaps_cols = []
    
    for col in df.columns:
        if df[col].isnull().any():
            # Apply time interpolation - SCENTIFIC LIMIT: 6 units (approx 6 hours if hourly)
            df[col] = df[col].interpolate(method='time', limit=6, limit_direction='both')
            
            # Check if gaps still exist after interpolation
            if df[col].isnull().any():
                remaining_gaps_cols.append(col)
                interpolated_cols.append(col) # It was partially interpolated
            else:
                 interpolated_cols.append(col) # Fully repaired
        else:
            untouched_cols.append(col)


    # --- STEP E: Seasonal Imputation (Extended) ---
    # Look back up to 4 days to find "Same Time, Previous Day" data.
    # This fixes medium gaps by copying the daily cycle.
    days_to_look_back = [1, 2, 3, 4] 
    for days in days_to_look_back:
        # Shift data so "Yesterday's" data aligns with "Today's" timestamp
        historical_fill = df.shift(periods=days, freq='D')

        # Fill ONLY the remaining NaNs (does not overwrite existing good data)
        df = df.fillna(historical_fill)

    # --- STEP F: Monthly-Hourly Fallback (Season-Smart) ---
    # If historical lookup failed (e.g. Day 1 data), fill with the average
    # of that specific hour within that specific month.
    
    for col in df.columns:
        if df[col].isnull().any():
            # Group by Month AND Hour to preserve seasonality
            # transform('mean') calculates the average for each (Month, Hour) bucket
            seasonal_means = df.groupby([df.index.month, df.index.hour])[col].transform('mean')
            
            df[col] = df[col].fillna(seasonal_means)
        
    # Re-evaluate remaining gaps for the report
    remaining_gaps_cols = [c for c in df.columns if df[c].isnull().any()]

    # Reset Index
    df = df.reset_index()
    
    # Step F: Standardization (Renaming)
    # Invert mapping to rename columns: {'water_temp': 'WQ Temp'} -> Rename 'WQ Temp' to 'water_temp'
    rename_map = {v: k for k, v in mapping.items()}
    df = df.rename(columns=rename_map)
    
    report = {
        "dropped": dropped_cols,
        "interpolated": interpolated_cols,
        "untouched": untouched_cols,
        "incomplete": remaining_gaps_cols
    }
    
    return df, mapping, report, date_col

def load_data():
    """
    Handles the file upload and basic preprocessing for prediction.
    """
    uploaded_file = st.file_uploader("Upload Your Dataset (CSV/Excel) for Prediction", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # --- STEP 0: Sanitize Text Codes ---
            # Scientific Correction: "BTL" (Below Trace Limit) means the value is ~0.
            # It is NOT a missing value. We must convert it to 0.0.
            
            # Replace known text codes with 0
            df = df.replace(['BTL', 'BDL', 'btl', 'bdl'], 0.0)
            
            # Identify date column temporarily to exclude it from coercion
            date_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()), None)

            # NOW convert columns to numeric (coercing any *other* garbage to NaN)
            for col in df.columns:
                if col != date_col:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # --- APPLY CLEANING PIPELINE ---
             
            # Capture Raw Data (Step A)
            raw_df = df.copy()
            
            cleaned_df, mapping, report, date_col_name = clean_marine_data(df)
            
            if cleaned_df is None:
                st.error("❌ Scientific Error: No Date/Time column found. Cannot perform Time-Series Interpolation.")
                return None
            
            # Align Raw Data (Step B)
            if date_col_name:
                raw_df[date_col_name] = pd.to_datetime(raw_df[date_col_name])
                raw_df = raw_df.set_index(date_col_name).sort_index()

            st.success("✅ File Uploaded & Cleaned using NCCR Standard (Filter-First Pipeline)")
            
            # --- REPORTS (Step D: Tabs) ---
            tab1, tab2 = st.tabs(["📊 Visual Comparison", "📝 Transparency Report"])
            
            # TAB 1: Visual Comparison
            with tab1:
                
                if mapping:
                    # SMART AUTO-SELECTION
                    best_col = None
                    max_repairs = -1
                    
                    # Find the column with the most changes (repairs)
                    for param in mapping.keys():
                        orig_col = mapping[param]
                        clean_col = param
                        
                        if orig_col in raw_df.columns and clean_col in cleaned_df.columns:
                            # Count repairs (difference in NaNs or value changes)
                            # Using isna() count diff is a good proxy for repairs
                            missing_orig = raw_df[orig_col].isna().sum()
                            missing_clean = cleaned_df[clean_col].isna().sum()
                            repairs = missing_orig - missing_clean
                            
                            if repairs > max_repairs:
                                max_repairs = repairs
                                best_col = param

                    if best_col:
                        st.subheader(f"⚡ Instant Insight: Repairing {best_col}")
                        
                        orig_col = mapping[best_col]
                        clean_col = best_col
                        
                        # Combine for chart
                        viz_df = pd.DataFrame({
                            '❌ Original Raw': raw_df[orig_col],
                            '✅ Cleaned Result': cleaned_df[clean_col]
                        })
                        
                        # PERFORMANCE FIX: Downsampling (10% of data)
                        viz_df = viz_df.iloc[::10, :]
                        
                        st.line_chart(viz_df, color=["#FF4B4B", "#00CC96"])
                        st.caption("Showing the most significant repair. (Data downsampled for speed).")
                        
                        # Insight Metric
                        st.metric(
                            label=f"Missing Values Fixed ({best_col})", 
                            value=f"{max_repairs}", 
                            delta="Automated Repair",
                            delta_color="normal"
                        )
                    else:
                         st.info("No significant repairs found to visualize.")
                else:
                    st.info("No sensor columns identified for visualization.")

            # TAB 2: Transparency Report
            with tab2:
                # 1. Identification Report
                st.write("### 🔍 Column Identification Report")
                st.json(mapping)
                
                # 2. Transparency Report
                with st.expander("📝 Transparency Report (Cleaning Actions)", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        st.write("🔴 **Dropped (Dead Sensors)**")
                        if report['dropped']:
                            for c in report['dropped']:
                                st.write(f"- {c}")
                        else:
                            st.write("_None_")
                            
                    with c2:
                        st.write("🟡 **Interpolated (Repaired)**")
                        if report['interpolated']:
                            for c in report['interpolated']:
                                st.write(f"- {c}")
                        else:
                            st.write("_None_")
    
                    with c3:
                        st.write("⚫ **Incomplete (>6h Gaps)**")
                        if report['incomplete']:
                            for c in report['incomplete']:
                                st.write(f"- {c}")
                            st.caption("Gaps filled using: Linear Interpolation (<6h) -> 4-Day History -> Monthly-Hourly Seasonality.")
                        else:
                            st.write("_None_")
                            
                    with c4:
                        st.write("🟢 **Clean (Untouched)**")
                        if report['untouched']:
                            for c in report['untouched']:
                                st.write(f"- {c}")
                        else:
                            st.write("_None_")
    
                # 3. Statistical Summary
                st.write("### 📉 Post-Cleaning Statistics")
                st.dataframe(cleaned_df.describe())
            
            return cleaned_df
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            return None
    return None

# --- 2. PREDICTION LOGIC ---
# --- 2. PREDICTION LOGIC ---
def run_prediction_page():
    st.header("🔮 Marine Data Cleaning Tool")
    st.info("Upload your field data below to clean and standardize it using the NCCR Protocol.")

    # A. Load & Clean Data
    df = load_data()

    if df is not None:
        st.divider()
        st.success("✅ Data Successfully Processed! Standardized and ready for Analysis.")
        
        # B. Download Option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Cleaned Data (CSV)",
            data=csv,
            file_name="nccr_cleaned_marine_data.csv",
            mime="text/csv",
            type="primary"
        )
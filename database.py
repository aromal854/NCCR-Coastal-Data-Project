import streamlit as st
from supabase import create_client
import pandas as pd
import bcrypt
import base64
from datetime import datetime

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase Connect Error: {e}")
        return None

supabase = init_connection()

# --- HELPER: MAP KEYS TO DB (LOWERCASE) ---
def map_keys_to_db(data_dict):
    """
    Maps Dashboard keys (TitleCase) to Database columns (lowercase).
    This matches the renamed columns in your Supabase SQL.
    """
    mapping = {
        # Meta Data
        'Main_Location': 'main_location', 
        'Location': 'location', 
        'Latitude': 'latitude', 
        'Longitude': 'longitude',
        'Date': 'date', 
        'Time': 'time', 
        'created_at': 'created_at',
        
        # Physical
        'Water_Temp': 'water_temp', 
        'Salinity': 'salinity', 
        'pH': 'ph', 
        'Turbidity': 'turbidity', 
        'Transparency': 'transparency', 
        'TSS': 'tss', 
        'TDS': 'tds', 
        'Color': 'color', 
        'Odour': 'odour',
        'Depth': 'depth',
        
        # Chemical
        'DO': 'do', 
        'BOD': 'bod', 
        'COD': 'cod', 
        'NH4_N': 'nh4_n', 
        'NO3_N': 'no3_n', 
        'NO2_N': 'no2_n', 
        'PO4': 'po4', 
        'SO4': 'so4',
        
        # Biological
        'Chlorophyll': 'chlorophyll', 
        'BGA': 'bga', 
        'Fecal_Coliform': 'fecal_coliform', 
        'Total_Coliform': 'total_coliform', 
        'Productivity': 'productivity', 
        'Phytoplankton': 'phytoplankton', 
        'Zooplankton': 'zooplankton',
        
        # Meteorological & Geo
        'Wind_Speed': 'wind_speed', 
        'Wind_Direction': 'wind_direction', 
        'Air_Temp': 'air_temp', 
        'Humidity': 'humidity', 
        'Precipitation': 'precipitation',
        'Shoreline_Status': 'shoreline_status', 
        'Population': 'population', 
        'Tourist_Inflow': 'tourist_inflow', 
        'Optimum_Season': 'optimum_season',
        'Coastal_Villages': 'coastal_villages', 
        'Panchayats': 'panchayats', 
        'Fishermen': 'fishermen', 
        'Landing_Centers': 'landing_centers', 
        'Fish_Catch': 'fish_catch', 
        'Water_Bodies': 'water_bodies', 
        'Industrial_Est': 'industrial_est', 
        'Tourism_Status': 'tourism_status',
        
        # Contributors
        'Contributor': 'contributor', 
        'Email': 'email', 
        'Profession': 'profession', 
        'Designation': 'designation'
    }
    
    new_data = {}
    for key, value in data_dict.items():
        if key in mapping:
            new_data[mapping[key]] = value
        else:
            # Fallback: lowercase everything else just in case
            new_data[key.lower()] = value
            
    return new_data

# ==========================================
# 🔐 AUTHENTICATION FUNCTIONS
# ==========================================

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(email, name, password, role="User"):
    try:
        if not supabase: return False, "DB Connection Failed"
        exists = supabase.table("users").select("email").eq("email", email).execute()
        if exists.data:
            return False, "Email already exists."
        
        hashed = hash_password(password)
        user_data = {"email": email, "name": name, "password": hashed, "role": role}
        supabase.table("users").insert(user_data).execute()
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_user(email, password):
    try:
        if not supabase: return None, "DB Connection Failed"
        response = supabase.table("users").select("*").eq("email", email).execute()
        if not response.data: return None, "User not found."
        
        user = response.data[0]
        if check_password(password, user['password']):
            return user, "Success"
        else:
            return None, "Incorrect password."
    except Exception as e:
        return None, f"Login Error: {str(e)}"

# ==========================================
# 📥 DATA ENTRY FUNCTIONS
# ==========================================

def save_marine_data(data_dict):
    try:
        if supabase:
            # MAP KEYS TO LOWERCASE BEFORE SAVING
            clean_data = map_keys_to_db(data_dict)
            supabase.table("marine_data").insert(clean_data).execute()
            return True
        return False
    except Exception as e:
        print(f"Save Error: {e}")
        return False

def save_bulk_data(data_list):
    try:
        if supabase:
            # MAP KEYS FOR ALL ROWS
            clean_list = [map_keys_to_db(row) for row in data_list]
            
            # CHUNKING: Insert in batches of 1000 to prevent timeouts
            batch_size = 1000
            for i in range(0, len(clean_list), batch_size):
                batch = clean_list[i : i + batch_size]
                supabase.table("marine_data").insert(batch).execute()
            
            return True, "Success"
        return False, "No Connection"
    except Exception as e:
        return False, str(e)

def fetch_all_data():
    try:
        if supabase:
            # Fetch up to 100,000 rows (default is 100)
            response = supabase.table("marine_data").select("*").range(0, 99999).execute()
            df = pd.DataFrame(response.data)
            
            if not df.empty:
                # REVERSE MAPPING (Database lowercase -> Dashboard TitleCase)
                # This ensures your Download button and Dashboard filters work correctly
                reverse_mapping = {
                    'main_location': 'Main_Location', 'location': 'Location', 
                    'latitude': 'Latitude', 'longitude': 'Longitude',
                    'water_temp': 'Water_Temp', 'salinity': 'Salinity', 'ph': 'pH', 
                    'turbidity': 'Turbidity', 'transparency': 'Transparency', 
                    'tss': 'TSS', 'tds': 'TDS', 'color': 'Color', 'odour': 'Odour',
                    'do': 'DO', 'bod': 'BOD', 'cod': 'COD', 
                    'nh4_n': 'NH4_N', 'no3_n': 'NO3_N', 'no2_n': 'NO2_N', 
                    'po4': 'PO4', 'so4': 'SO4',
                    'chlorophyll': 'Chlorophyll', 'bga': 'BGA', 
                    'fecal_coliform': 'Fecal_Coliform', 'total_coliform': 'Total_Coliform', 
                    'productivity': 'Productivity', 'phytoplankton': 'Phytoplankton', 
                    'zooplankton': 'Zooplankton',
                    'wind_speed': 'Wind_Speed', 'wind_direction': 'Wind_Direction', 
                    'air_temp': 'Air_Temp', 'humidity': 'Humidity', 'precipitation': 'Precipitation',
                    'shoreline_status': 'Shoreline_Status', 'population': 'Population', 
                    'tourist_inflow': 'Tourist_Inflow', 'optimum_season': 'Optimum_Season',
                    'coastal_villages': 'Coastal_Villages', 'panchayats': 'Panchayats', 
                    'fishermen': 'Fishermen', 'landing_centers': 'Landing_Centers', 
                    'fish_catch': 'Fish_Catch', 'water_bodies': 'Water_Bodies', 
                    'industrial_est': 'Industrial_Est', 'tourism_status': 'Tourism_Status',
                    'contributor': 'Contributor', 'email': 'Email', 
                    'profession': 'Profession', 'designation': 'Designation',
                    'date': 'Date', 'time': 'Time', 'created_at': 'created_at'
                }
                df.rename(columns=reverse_mapping, inplace=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Fetch Error: {e}")
        return pd.DataFrame()

def get_contribution_count(email):
    try:
        if supabase:
            # Use lowercase 'email' because that's what the DB has now
            response = supabase.table("marine_data").select("email", count="exact").eq("email", email).execute()
            return response.count
        return 0
    except:
        return 0

# ==========================================
# 👮 ADMIN & REQUESTS
# ==========================================

def submit_access_request(email, purpose):
    try:
        if not supabase: return False, "Connection Error"
        existing = supabase.table("access_requests").select("*").eq("user_email", email).eq("status", "Pending").execute()
        if existing.data: return False, "Pending request already exists."
            
        data = {"user_email": email, "purpose": purpose, "status": "Pending", "request_date": str(datetime.now())}
        supabase.table("access_requests").insert(data).execute()
        return True, "Request submitted."
    except Exception as e:
        return False, str(e)

def check_request_status(email):
    try:
        if not supabase: return "None"
        res = supabase.table("access_requests").select("status").eq("user_email", email).order("id", desc=True).limit(1).execute()
        if res.data: return res.data[0]['status']
        return "None"
    except:
        return "None"

def fetch_pending_requests():
    try:
        if supabase:
            res = supabase.table("access_requests").select("*").eq("status", "Pending").execute()
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def update_request_status(request_id, new_status):
    try:
        if supabase:
            supabase.table("access_requests").update({"status": new_status}).eq("id", request_id).execute()
            return True
        return False
    except:
        return False

def delete_data(record_ids):
    """Deletes records from marine_data based on ID list."""
    try:
        if supabase:
            supabase.table("marine_data").delete().in_("id", record_ids).execute()
            return True
        return False
    except Exception as e:
        print(f"Delete Error: {e}")
        return False

# ==========================================
# 📰 RESEARCH PAPERS
# ==========================================

def save_paper(title, summary, author, role, file_obj):
    try:
        if file_obj:
            file_bytes = file_obj.read()
            base64_file = base64.b64encode(file_bytes).decode('utf-8')
            file_name = file_obj.name
        else:
            base64_file = None; file_name = None

        data = {
            "title": title, "summary": summary, "author": author, "role": role, 
            "file_name": file_name, "file_data": base64_file, "created_at": str(datetime.now())
        }
        if supabase:
            supabase.table("research_papers").insert(data).execute()
            return True, "Published!"
        return False, "Database Error"
    except Exception as e:
        return False, str(e)

def fetch_papers():
    try:
        if supabase:
            response = supabase.table("research_papers").select("*").order("created_at", desc=True).execute()
            data = response.data
            sorted_data = sorted(data, key=lambda x: 0 if x.get('role') == 'Admin' else 1)
            return sorted_data
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []
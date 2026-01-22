import streamlit as st
from supabase import create_client
import pandas as pd
import bcrypt

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Secrets not found! Please check .streamlit/secrets.toml. Error: {e}")
        return None

supabase = init_connection()

# ==========================================
# 🔐 AUTHENTICATION FUNCTIONS (Login/Register)
# ==========================================

def hash_password(password):
    """Converts plain password to secure hash using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    """Checks if entered password matches the stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(email, name, password, role="User"):
    """Registers a new user into the 'users' table."""
    try:
        if not supabase:
            return False, "Database connection failed."

        # 1. Check if email already exists
        exists = supabase.table("users").select("email").eq("email", email).execute()
        if exists.data:
            return False, "Email already exists. Please login."
        
        # 2. Hash the password
        hashed = hash_password(password)
        
        # 3. Insert new user
        user_data = {
            "email": email,
            "name": name,
            "password": hashed,
            "role": role
        }
        supabase.table("users").insert(user_data).execute()
        return True, "Registration successful! You can now login."
        
    except Exception as e:
        return False, f"Registration Error: {str(e)}"

def login_user(email, password):
    """Verifies login credentials."""
    try:
        if not supabase:
            return None, "Database connection failed."

        # 1. Fetch user by email
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if not response.data:
            return None, "User not found. Please register first."
        
        user = response.data[0]
        
        # 2. Verify Password
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
    """Inserts marine data into 'marine_data' table."""
    try:
        if supabase:
            supabase.table("marine_data").insert(data_dict).execute()
            return True
        return False
    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        return False

def fetch_all_data():
    """Fetches all marine data for Admin/Export."""
    try:
        if supabase:
            response = supabase.table("marine_data").select("*").execute()
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_contribution_count(email):
    """Counts contributions for certificate eligibility."""
    try:
        if supabase:
            # Note: Ensure column name matches your table ("Email" or "email")
            response = supabase.table("marine_data").select("Email", count="exact").eq("Email", email).execute()
            return response.count
        return 0
    except:
        return 0

# ==========================================
# 👮 ADMIN APPROVAL SYSTEM (Request Access)
# ==========================================

def submit_access_request(email, purpose):
    """User submits a request to download data."""
    try:
        if not supabase: return False, "Connection Error"

        # Check if a pending request already exists
        existing = supabase.table("access_requests").select("*").eq("user_email", email).eq("status", "Pending").execute()
        if existing.data:
            return False, "You already have a PENDING request. Please wait for Admin approval."
            
        # Insert new request
        data = {
            "user_email": email,
            "purpose": purpose,
            "status": "Pending"
        }
        supabase.table("access_requests").insert(data).execute()
        return True, "Request submitted successfully to Admin."
        
    except Exception as e:
        return False, f"Request Error: {str(e)}"

def check_request_status(email):
    """Checks the latest status of a user's request."""
    try:
        if not supabase: return "None"

        # Get the most recent request for this user
        res = supabase.table("access_requests") \
            .select("status") \
            .eq("user_email", email) \
            .order("request_date", desc=True) \
            .limit(1) \
            .execute()
            
        if res.data:
            return res.data[0]['status'] # Returns 'Approved', 'Pending', or 'Rejected'
        return "None"
    except:
        return "None"

def fetch_pending_requests():
    """Fetches all requests with status 'Pending' for Admin view."""
    try:
        if supabase:
            res = supabase.table("access_requests").select("*").eq("status", "Pending").execute()
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def update_request_status(request_id, new_status):
    """Admin updates status to 'Approved' or 'Rejected'."""
    try:
        if supabase:
            supabase.table("access_requests").update({"status": new_status}).eq("id", request_id).execute()
            return True
        return False
    except:
        return False
    
# --- BULK SAVE FUNCTION (Add this to database.py) ---
def save_bulk_data(data_list):
    """Inserts a list of dictionaries (Bulk Data) into Supabase."""
    try:
        if supabase:
            # Supabase allows inserting a list of rows at once
            data, count = supabase.table("marine_data").insert(data_list).execute()
            return True, "Success"
        return False, "No Connection"
    except Exception as e:
        return False, str(e)




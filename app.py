# app.py
import streamlit as st
import auth
import dashboard

import streamlit as st
import auth
import dashboard
import pages.verify as verify_page # Import the verify page

# --- QUERY PARAM CHECK FOR VERIFICATION ---
if st.query_params.get("page") == "verify" and st.query_params.get("id"):
    request_id = st.query_params.get("id")
    verify_page.show(request_id)
    st.stop()
    
# --- CONFIGURATION ---
st.set_page_config(
    page_title="NCCR Marine Portal", 
    page_icon="🌊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
# TEMPORARILY BYPASSED FOR TESTING
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True # Force Login
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "User" # Mock Role
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = "test@nccr.gov.in"
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = "Test User"
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = "TEST_001"

# --- OTP SESSION VARIABLES (For Registration) ---
if 'otp_generated' not in st.session_state:
    st.session_state['otp_generated'] = None
if 'otp_email' not in st.session_state:
    st.session_state['otp_email'] = None

# --- APP FLOW CONTROL ---
if st.session_state['logged_in']:
    # If logged in, load the Dashboard (which now contains the Prediction Page)
    dashboard.main_app()
else:
    # If not logged in, show the Login/Register Page
    auth.login_page()
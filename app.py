# app.py
import streamlit as st
import auth
import dashboard

# --- CONFIGURATION ---
st.set_page_config(
    page_title="NCCR Marine Portal", 
    page_icon="🌊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
# We initialize these upfront to prevent errors when switching between files
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

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
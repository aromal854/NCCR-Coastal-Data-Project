# app.py
import streamlit as st
import auth
import dashboard

# --- CONFIGURATION ---
st.set_page_config(page_title="NCCR Marine Portal", page_icon="🌊", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None
    st.session_state['user_id'] = None

# --- OTP SESSION VARIABLES ---
if 'otp_generated' not in st.session_state:
    st.session_state['otp_generated'] = None
if 'otp_email' not in st.session_state:
    st.session_state['otp_email'] = None

# --- APP FLOW CONTROL ---
if st.session_state['logged_in']:
    # If logged in, show the Dashboard
    dashboard.main_app()
else:
    # If not logged in, show the Login/Register Page
    auth.login_page()
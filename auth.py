# auth.py
import streamlit as st
import random
import database as db
import utils
import config

def login_page():
    # --- SESSION STATE FOR AUTH MODE ---
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = None # None, 'Admin', 'User'

    # --- CUSTOM CSS (Updated for Split Flow) ---
    st.markdown("""
    <style>
        /* Global Background */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            background-attachment: fixed;
        }
        
        /* Headers & Text */
        h1, h2, h3, h4, h5, h6, .stMarkdown, p, label {
            color: #0f2027 !important;
        }

        /* Role Selection Cards */
        .role-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
            border: 1px solid #d1d5db;
        }
        .role-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        }
        
        /* Buttons */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            height: 50px;
            border: none;
            color: white;
            transition: all 0.3s ease;
        }
        
        /* Primary Action Button (Blue) */
        .primary-btn div.stButton > button {
            background: linear-gradient(90deg, #0077b6, #00b4d8);
        }
        .primary-btn div.stButton > button:hover {
            box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
        }

        /* Admin Action Button (Dark/Red tint) */
        .admin-btn div.stButton > button {
            background: linear-gradient(90deg, #1f2937, #374151);
        }
        .admin-btn div.stButton > button:hover {
            background: linear-gradient(90deg, #374151, #4b5563);
            box-shadow: 0 4px 12px rgba(31, 41, 55, 0.4);
        }
        
        /* Back Button (Simple) */
        .back-btn div.stButton > button {
            background: transparent;
            color: #4b5563;
            border: 1px solid #9ca3af;
            height: 35px;
        }
        .back-btn div.stButton > button:hover {
            background: #e5e7eb;
            color: #1f2937;
        }
        
        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff;
            color: #1f2937;
            border: 1px solid #9ca3af;
            border-radius: 8px;
        }

    </style>
    """, unsafe_allow_html=True)

    # =========================================================
    # 1. LANDING SCREEN (ROLE SELECTION)
    # =========================================================
    if st.session_state['auth_mode'] is None:
        st.markdown("<br><br>", unsafe_allow_html=True) # Top Spacer
        
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2:
            st.title("🌊 NCCR Marine Data Portal")
            st.subheader("Welcome! Please select your role to continue.")
            st.markdown("---")
            
            rc1, rc2 = st.columns(2)
            
            with rc1:
                st.markdown('<div class="role-card"><h3>👨‍🔬 Public / Researcher</h3><p>Access data, contribute field reports, and view news.</p></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                if st.button("Enter as User / Researcher"):
                    st.session_state['auth_mode'] = 'User'
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with rc2:
                st.markdown('<div class="role-card"><h3>👮 Administrator</h3><p>Manage data, approve requests, and oversee system.</p></div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="admin-btn">', unsafe_allow_html=True)
                if st.button("Admin Portal Access"):
                    st.session_state['auth_mode'] = 'Admin'
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================
    # 2. SPECIFIC LOGIN FLOWS
    # =========================================================
    else:
        # Layout: Center Column
        c_left, c_center, c_right = st.columns([1, 4, 1])
        
        with c_center:
            # Back Button
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← Back to Role Selection"):
                st.session_state['auth_mode'] = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("") # Spacer

            # -------------------------------------------------
            # FLOW A: ADMIN LOGIN (STRICT, NO REGISTER)
            # -------------------------------------------------
            if st.session_state['auth_mode'] == 'Admin':
                st.markdown("""
                <div style="text-align: center; padding: 20px; background: #e5e7eb; border-radius: 10px; margin-bottom: 20px;">
                    <h2>👮 Admin Login</h2>
                    <p>Restricted Access Only</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.container():
                    email = st.text_input("Admin Email", key="admin_email")
                    password = st.text_input("Password", type="password", key="admin_pass")
                    
                    st.markdown('<br><div class="admin-btn">', unsafe_allow_html=True)
                    if st.button("Authenticate Admin"):
                        user, msg = db.login_user(email, password)
                        if user and user['role'] == 'Admin':
                            # Success
                            st.session_state['logged_in'] = True
                            st.session_state['user_role'] = 'Admin'
                            st.session_state['user_email'] = user['email']
                            st.session_state['user_name'] = user['name']
                            st.session_state['user_id'] = utils.generate_user_id(user['email'])
                            st.rerun()
                        elif user and user['role'] != 'Admin':
                            st.error("⛔ Access Denied: You are not an Admin.")
                        else:
                            st.error(msg)
                    st.markdown('</div>', unsafe_allow_html=True)

            # -------------------------------------------------
            # FLOW B: USER LOGIN & REGISTER
            # -------------------------------------------------
            elif st.session_state['auth_mode'] == 'User':
                st.title("👨‍🔬 Researcher / User Access")
                
                tab1, tab2 = st.tabs(["🔑 Existing User Login", "📝 New Registration"])
                
                # --- LOGIN ---
                with tab1:
                    email = st.text_input("Email", key="u_email")
                    password = st.text_input("Password", type="password", key="u_pass")
                    
                    st.markdown('<br><div class="primary-btn">', unsafe_allow_html=True)
                    if st.button("Login"):
                        user, msg = db.login_user(email, password)
                        if user:
                            # Allow any role to login here? Or strictly non-admins?
                            # Usually better to allow anyone, but redirect Admins if they login here?
                            # For now, simple login.
                            st.session_state['logged_in'] = True
                            st.session_state['user_role'] = user['role']
                            st.session_state['user_email'] = user['email']
                            st.session_state['user_name'] = user['name']
                            st.session_state['user_id'] = utils.generate_user_id(user['email'])
                            st.rerun()
                        else:
                            st.error(msg)
                    st.markdown('</div>', unsafe_allow_html=True)

                # --- REGISTER ---
                with tab2:
                    st.info("ℹ️ Create an account to contribute and download data.")
                    new_name = st.text_input("Full Name", placeholder="Dr. Oceanus")
                    new_email = st.text_input("Email Address", placeholder="email@institute.edu")
                    new_phone = st.text_input("Phone Number", placeholder="+91 9876543210")
                    
                    c_p1, c_p2 = st.columns(2)
                    new_pass = c_p1.text_input("Create Password", type="password")
                    confirm_pass = c_p2.text_input("Confirm Password", type="password")
                    
                    role_choice = st.selectbox("Role Request", ["User", "Admin"]) 
                    
                    st.write("")
                    # Button: Send OTP
                    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                    if st.button("📩 Send Verification OTP"):
                         if new_email and new_name and new_pass and confirm_pass and new_phone:
                            if new_pass != confirm_pass:
                                st.error("❌ Passwords do not match!")
                            else:
                                otp_code = random.randint(100000, 999999)
                                st.session_state['otp_generated'] = str(otp_code)
                                st.session_state['otp_email'] = new_email
                                msg_body = f"Hello {new_name},\n\nYour OTP is: {otp_code}"
                                if utils.send_email_notification(new_email, "NCCR OTP", msg_body):
                                    st.toast(f"✅ OTP sent to {new_email}")
                                else:
                                    st.error("Email failed.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Verify
                    if st.session_state.get('otp_generated'):
                        st.divider()
                        otp_input = st.text_input("Enter OTP", max_chars=6)
                        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                        if st.button("✅ Complete Registration"):
                            if otp_input == st.session_state['otp_generated']:
                                success, msg = db.register_user(new_email, new_name, new_pass, role_choice)
                                if success:
                                    st.success("Registration Successful! Please Login.")
                                    st.session_state['otp_generated'] = None # Clear OTP
                                    utils.send_email_notification(config.SENDER_EMAIL, "New User", f"New user: {new_email}")
                                else:
                                    st.error(msg)
                            else:
                                st.error("Invalid OTP")
                        st.markdown('</div>', unsafe_allow_html=True)
# auth.py
import streamlit as st
import random
import database as db
import utils
import config

def login_page():
    st.title("🔐 NCCR Portal Login")
    st.markdown("Please log in to access the National Centre for Coastal Research Portal.")
    
    tab1, tab2 = st.tabs(["Login", "New User Registration"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            user, msg = db.login_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = user['role']
                st.session_state['user_email'] = user['email']
                st.session_state['user_name'] = user['name']
                # Generate Display ID
                st.session_state['user_id'] = utils.generate_user_id(user['email'])
                st.rerun()
            else:
                st.error(msg)
                
    with tab2:
        st.subheader("Create an Account")
        st.info("Registration requires Email OTP Verification.")
        
        # --- INPUT FIELDS ---
        new_name = st.text_input("Full Name")
        new_phone = st.text_input("Phone Number") 
        new_email = st.text_input("Email Address")
        new_pass = st.text_input("Create Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        role_choice = st.selectbox("Request Role", ["User", "Admin"]) 
        
        st.markdown("---")
        
        # --- SPLIT LOGIC: SEND OTP vs VERIFY OTP ---
        c1, c2 = st.columns([1, 2])
        
        # BUTTON 1: SEND OTP
        if c1.button("📩 Send Verification OTP"):
            if new_email and new_name and new_pass and confirm_pass and new_phone:
                if new_pass != confirm_pass:
                    st.error("❌ Passwords do not match!")
                else:
                    # Generate OTP
                    otp_code = random.randint(100000, 999999)
                    
                    # Store in Session
                    st.session_state['otp_generated'] = str(otp_code)
                    st.session_state['otp_email'] = new_email
                    
                    # Send Email
                    msg_body = f"Hello {new_name},\n\nUse this OTP to complete your NCCR Registration: {otp_code}\n\nDo not share this code."
                    if utils.send_email_notification(new_email, "NCCR Registration OTP", msg_body):
                        st.toast(f"✅ OTP sent to {new_email}!")
                        st.info("Please check your email and enter the OTP below.")
                    else:
                        st.error("Failed to send email. Check internet or credentials.")
            else:
                st.warning("Please fill all fields first.")

        # BUTTON 2: VERIFY & REGISTER
        otp_input = c2.text_input("Enter OTP from Email", placeholder="123456", max_chars=6)
        
        if c2.button("✅ Verify & Register"):
            # Check if OTP was generated
            if st.session_state['otp_generated']:
                # Check if Email wasn't changed after sending OTP
                if new_email == st.session_state['otp_email']:
                    # Check OTP Match
                    if otp_input == st.session_state['otp_generated']:
                        # --- DATABASE REGISTRATION ---
                        success, msg = db.register_user(new_email, new_name, new_pass, role_choice)
                        if success:
                            st.success("🎉 Registration Successful! You can now login.")
                            st.session_state['otp_generated'] = None # Clear OTP
                            
                            # Notify Admin
                            admin_msg = f"New User Registered:\nName: {new_name}\nID: {utils.generate_user_id(new_email)}\nEmail: {new_email}\nPhone: {new_phone}\nRole: {role_choice}"
                            utils.send_email_notification(config.SENDER_EMAIL, "New User Alert", admin_msg)
                        else:
                            st.error(msg)
                    else:
                        st.error("❌ Invalid OTP. Please try again.")
                else:
                    st.error("⚠️ Email changed. Please request a new OTP.")
            else:
                st.error("⚠️ Please click 'Send Verification OTP' first.")
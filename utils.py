# utils.py
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from datetime import date
import uuid
import config # Import the config file

# --- HELPER: GENERATE USER ID ---
def generate_user_id(email):
    """Generates a pseudo-unique ID from email (e.g. NCCR-A1B2)"""
    hash_object = hashlib.md5(email.encode())
    hex_dig = hash_object.hexdigest()
    return f"NCCR-{hex_dig[:4].upper()}"

# --- HELPER: SEND EMAIL FUNCTION ---
def send_email_notification(to_email, subject, message_body):
    """Sends an email using free Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(config.SENDER_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# --- HELPER: SEND VERIFICATION EMAIL ---
def send_verification_email(prof_email, prof_name, data_id):
    """Sends a verification email to the professor."""
    try:
        # Use deployed URL from secrets if available, else fallback to localhost for local dev
        try:
            import streamlit as st
            base_url = st.secrets.get("APP_URL", "http://localhost:8501")
        except Exception:
            base_url = "http://localhost:8501"
        link = f"{base_url}/?page=verify&id={data_id}"
        
        subject = f"Action Required: Verify Marine Data Contribution"
        
        body = f"""
        Dear Prof. {prof_name},
        
        A new marine data contribution requires your expert verification.
        
        Please click the link below to review and verify the data:
        {link}
        
        If you did not request this, please ignore this email.
        
        Regards,
        NCCR Coastal-Marine Data Portal
        """

        msg = MIMEMultipart()
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = prof_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(config.SENDER_EMAIL, prof_email, text)
        server.quit()
        return True
    except Exception as e:
        if "11001" in str(e) or "getaddrinfo failed" in str(e):
            print("⚠️ Email Error: No Internet Connection or DNS Failure.")
            return False
        print(f"Verification Email Error: {e}")
        return False

# --- HELPER: GENERATE PDF CERTIFICATE ---
def create_certificate(name, contributions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(200, 40, txt="Certificate of Contribution", ln=True, align='C')
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 20, txt="Presented to", ln=True, align='C')
    pdf.set_font("Arial", 'B', 30)
    pdf.set_text_color(0, 0, 128) # Navy Blue
    pdf.cell(200, 20, txt=name, ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 20, txt=f"For contributing {contributions} valuable data points", ln=True, align='C')
    pdf.cell(200, 10, txt="to the NCCR Marine Water Quality Project.", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(200, 30, txt=f"Issued on: {date.today()}", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')
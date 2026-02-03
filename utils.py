# utils.py
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from datetime import date
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
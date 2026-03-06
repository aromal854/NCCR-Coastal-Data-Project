# app.py
import streamlit as st
import auth
import dashboard
import verify_page # Import the verify logic (hidden from sidebar)

def apply_nccr_branding():
    """
    Injects custom CSS for the NCCR Coastal Monitoring Platform.
    Design system: Inter font, deep ocean blue + muted teal palette,
    light mist-grey background, soft coastal blue-grey sidebar.
    """
    st.markdown(
        """
        <style>
        /* ── 0. HIDE STREAMLIT CHROME ──────────────────────── */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        [data-testid="stToolbar"] {
            display: none !important;
        }
        /* Hide the keyboard_double material icon text in top bar */
        .st-emotion-cache-czk5ss {
            display: none !important;
        }
        /* Ensure sidebar collapse/expand arrow is always visible */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        #MainMenu, footer, header {
            visibility: hidden !important;
            height: 0 !important;
        }


        /* ── 1. TYPOGRAPHY ─────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        *, *::before, *::after {
            font-family: 'Inter', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: #1A3A5C !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        p, span, div, label, li,
        [data-testid="stMarkdownContainer"] p {
            color: #334E68 !important;
        }

        /* ── 2. BACKGROUND ──────────────────────────────────── */
        [data-testid="stAppViewContainer"] {
            background: #F4F7FB !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
            backdrop-filter: blur(6px) !important;
        }


        /* ── 3. SIDEBAR — always visible, never collapsible ─── */
        [data-testid="stSidebar"] {
            transform: none !important;
            margin-left: 0 !important;
            min-width: 244px !important;
            visibility: visible !important;
            display: flex !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #E8EFF8 0%, #D6E2F0 100%) !important;
            border-right: 1px solid rgba(26, 58, 92, 0.10) !important;
        }
        /* Hide collapse/expand buttons since sidebar is always open */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        [data-testid="stSidebar"] span {
            color: #1A3A5C !important;
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        /* Radio nav items */
        div[class*="stRadio"] > div > label {
            border-radius: 8px !important;
            padding: 4px 8px !important;
            transition: background 0.2s !important;
        }
        div[class*="stRadio"] > div > label:hover {
            background: rgba(42, 138, 122, 0.10) !important;
        }
        div[class*="stRadio"] > div > label[data-selected="true"] {
            background: rgba(42, 138, 122, 0.16) !important;
            border-left: 3px solid #2A8A7A !important;
        }
        div[class*="stRadio"] > div > label > div[data-testid="stMarkdownContainer"] > p {
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }

        /* ── 4. KPI METRIC CARDS ────────────────────────────── */
        div[data-testid="stMetric"],
        div[data-testid="stMetric"] > div,
        .nccr-card {
            background: #FFFFFF !important;
            border: 1px solid rgba(26, 58, 92, 0.08) !important;
            border-radius: 10px !important;
            padding: 14px 18px !important;
            box-shadow: 0 2px 8px rgba(26, 58, 92, 0.06) !important;
            transition: box-shadow 0.25s ease, transform 0.25s ease !important;
        }
        div[data-testid="stMetric"]:hover,
        .nccr-card:hover {
            box-shadow: 0 6px 20px rgba(26, 58, 92, 0.11) !important;
            border-color: rgba(42, 138, 122, 0.30) !important;
            transform: translateY(-2px) !important;
        }
        div[data-testid="stMetricLabel"] label,
        div[data-testid="stMetricLabel"] div,
        div[data-testid="stMetricLabel"] p {
            color: #627D98 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.07em !important;
        }
        div[data-testid="stMetricValue"] div {
            color: #1A3A5C !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.82rem !important;
            font-weight: 500 !important;
        }

        /* ── 5. BUTTONS ─────────────────────────────────────── */
        [data-testid="baseButton-primary"],
        [data-testid="baseButton-secondary"] {
            background-color: #2A8A7A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
            box-shadow: 0 2px 6px rgba(42, 138, 122, 0.25) !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="baseButton-primary"]:hover,
        [data-testid="baseButton-secondary"]:hover {
            background-color: #22756A !important;
            box-shadow: 0 4px 12px rgba(42, 138, 122, 0.35) !important;
            transform: translateY(-1px) !important;
        }

        /* ── 6. INPUTS ──────────────────────────────────────── */
        div[data-baseweb="input"],
        div[data-baseweb="select"] > div:first-child {
            background: #FFFFFF !important;
            border: 1px solid rgba(26, 58, 92, 0.16) !important;
            border-radius: 8px !important;
            color: #1A3A5C !important;
        }
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"]:focus-within > div:first-child {
            border-color: #2A8A7A !important;
            box-shadow: 0 0 0 2px rgba(42, 138, 122, 0.18) !important;
        }

        /* ── 7. CONTAINERS / TABLES ─────────────────────────── */
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: #FFFFFF !important;
            border: 1px solid rgba(26, 58, 92, 0.09) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }
        div[data-testid="stExpander"] details {
            border: 1px solid rgba(26, 58, 92, 0.09) !important;
            border-radius: 10px !important;
            background: #F8FAFD !important;
        }
        div[data-testid="stExpander"] summary {
            background: transparent !important;
            color: #1A3A5C !important;
            font-weight: 600 !important;
        }
        hr {
            border-color: rgba(26, 58, 92, 0.09) !important;
            margin: 1.8rem 0 !important;
        }

        /* ── 8. ALERT HELPER CLASSES ────────────────────────── */
        .nccr-alert-critical {
            background: rgba(220, 38, 38, 0.07);
            border-left: 4px solid #DC2626;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .nccr-alert-warning {
            background: rgba(245, 158, 11, 0.08);
            border-left: 4px solid #F59E0B;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .nccr-alert-ok {
            background: rgba(22, 163, 74, 0.07);
            border-left: 4px solid #16A34A;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .nccr-alert-info {
            background: rgba(26, 58, 92, 0.06);
            border-left: 4px solid #1A3A5C;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .nccr-alert-title {
            font-weight: 700;
            font-size: 0.88rem;
            margin-bottom: 2px;
            color: #1A3A5C;
        }
        .nccr-alert-body {
            font-size: 0.82rem;
            color: #4A6280;
            margin: 0;
        }

        /* ── 9. SECTION HEADER CLASS ────────────────────────── */
        .nccr-section-label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #8DA4B8 !important;
            margin-bottom: 4px;
        }

        /* ── 10. FORECAST TABLE ─────────────────────────────── */
        .nccr-forecast-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            background: #FFFFFF;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(26, 58, 92, 0.06);
        }
        .nccr-forecast-table th {
            background: #1A3A5C;
            color: #FFFFFF;
            font-weight: 600;
            padding: 10px 14px;
            text-align: center;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .nccr-forecast-table td {
            padding: 9px 14px;
            text-align: center;
            color: #334E68 !important;
            border-bottom: 1px solid rgba(26, 58, 92, 0.07);
        }
        .nccr-forecast-table tr:nth-child(even) td {
            background: #F4F8FD;
        }
        .nccr-forecast-table tr:last-child td {
            border-bottom: none;
        }
        .nccr-forecast-table .day-label {
            font-weight: 700;
            color: #1A3A5C !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

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

# Apply global branding right after setting page config
apply_nccr_branding()

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
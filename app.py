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
        /* ── DESIGN TOKENS (Ocean theme) ───────────────────── */
        :root {
            --nccr-bg0: #F4F8FC;
            --nccr-bg1: #EEF6FB;
            --nccr-surface: #FFFFFF;
            --nccr-ink: #0F2D3D;
            --nccr-ink-2: #1A3A5C;
            --nccr-muted: #627D98;
            --nccr-muted-2: #8DA4B8;
            --nccr-border: rgba(26, 58, 92, 0.10);
            --nccr-shadow: 0 10px 30px rgba(10, 38, 64, 0.08);
            --nccr-shadow-soft: 0 2px 10px rgba(10, 38, 64, 0.06);
            --nccr-primary: #1A4A6E;   /* deep ocean */
            --nccr-accent: #2A8A7A;    /* seafoam */
            --nccr-warn: #B07D3A;      /* sand */
            --nccr-danger: #DC2626;
            --nccr-radius: 14px;
        }

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
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..700,0..1,-25..200');

        /* Exclude material icon classes from the global font override to avoid text overlaps in dataframes */
        *:not(i):not([class*="material"]):not([data-testid="stIconMaterial"])::before, 
        *:not(i):not([class*="material"]):not([data-testid="stIconMaterial"])::after,
        *:not(i):not([class*="material"]):not([data-testid="stIconMaterial"]) {
            font-family: 'Inter', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: var(--nccr-ink-2) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        p, span, div, label, li,
        [data-testid="stMarkdownContainer"] p {
            color: #334E68 !important;
        }

        /* ── 2. BACKGROUND ──────────────────────────────────── */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(1400px 800px at 18% 0%, var(--nccr-bg1) 0%, var(--nccr-bg0) 55%, #F7FBFF 100%) !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
            backdrop-filter: blur(6px) !important;
        }

        /* Content width + spacing */
        section.main > div.block-container {
            padding-top: 1.4rem !important;
            padding-bottom: 2.2rem !important;
            max-width: 1280px !important;
        }


        /* ── 3. SIDEBAR — always visible on desktop, toggleable on mobile ─── */
        @media (min-width: 769px) {
            [data-testid="stSidebar"] {
                transform: none !important;
                margin-left: 0 !important;
                min-width: 244px !important;
                visibility: visible !important;
                display: flex !important;
            }
            /* Hide collapse/expand buttons on desktop */
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
        }
        
        @media (max-width: 768px) {
            /* On mobile, ONLY hide the top header space, but keep the collapse button visible */
            header[data-testid="stHeader"] {
                display: block !important;
                background: transparent !important;
                height: 3rem !important;
            }
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapseButton"] {
                display: flex !important;
            }
        }

        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #EAF3FB 0%, #D7E8F5 55%, #D4E2F0 100%) !important;
            border-right: 1px solid var(--nccr-border) !important;
        }
        
        /* Hide Default Streamlit Page Navigation */
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Radio nav items */
        div[class*="stRadio"] > div > label {
            border-radius: 12px !important;
            padding: 6px 10px !important;
            transition: background 0.2s !important;
        }
        div[class*="stRadio"] > div > label:hover {
            background: rgba(42, 138, 122, 0.10) !important;
        }
        div[class*="stRadio"] > div > label[data-selected="true"] {
            background: rgba(42, 138, 122, 0.16) !important;
            border-left: 3px solid var(--nccr-accent) !important;
        }
        div[class*="stRadio"] > div > label > div[data-testid="stMarkdownContainer"] > p {
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }

        /* ── 4. KPI METRIC CARDS ────────────────────────────── */
        div[data-testid="stMetric"],
        div[data-testid="stMetric"] > div,
        .nccr-card {
            background: var(--nccr-surface) !important;
            border: 1px solid rgba(26, 58, 92, 0.09) !important;
            border-radius: var(--nccr-radius) !important;
            padding: 14px 18px !important;
            box-shadow: var(--nccr-shadow-soft) !important;
            transition: box-shadow 0.25s ease, transform 0.25s ease !important;
        }
        div[data-testid="stMetric"]:hover,
        .nccr-card:hover {
            box-shadow: var(--nccr-shadow) !important;
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
            color: var(--nccr-ink-2) !important;
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
            background-color: var(--nccr-accent) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
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
            background: var(--nccr-surface) !important;
            border: 1px solid rgba(26, 58, 92, 0.09) !important;
            border-radius: var(--nccr-radius) !important;
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

        /* ── 11. REUSABLE LAYOUT HELPERS ───────────────────── */
        .nccr-hero {
            border-radius: calc(var(--nccr-radius) + 4px);
            border: 1px solid rgba(26, 58, 92, 0.10);
            background:
                radial-gradient(900px 340px at 20% 0%, rgba(42, 138, 122, 0.18) 0%, rgba(42, 138, 122, 0.00) 55%),
                radial-gradient(900px 380px at 85% 0%, rgba(26, 74, 110, 0.18) 0%, rgba(26, 74, 110, 0.00) 60%),
                linear-gradient(180deg, rgba(255,255,255,0.86) 0%, rgba(255,255,255,0.96) 100%);
            box-shadow: var(--nccr-shadow-soft);
            padding: 18px 18px;
        }
        .nccr-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(26, 58, 92, 0.10);
            background: rgba(255, 255, 255, 0.72);
            color: var(--nccr-muted);
            font-size: 0.82rem;
            font-weight: 600;
        }
        .nccr-card-title {
            font-weight: 700;
            color: var(--nccr-ink-2);
            margin: 0 0 4px 0;
        }
        .nccr-card-subtitle {
            margin: 0;
            color: var(--nccr-muted);
            font-size: 0.88rem;
        }

        /* Material icons (formal) */
        .material-symbols-rounded {
            font-family: 'Material Symbols Rounded' !important;
            font-weight: 600;
            font-style: normal;
            font-size: 22px;
            line-height: 1;
            display: inline-block;
            vertical-align: -0.25em;
            letter-spacing: normal;
            text-transform: none;
            white-space: nowrap;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
        .nccr-icon {
            color: var(--nccr-primary);
            background: rgba(26, 74, 110, 0.08);
            border: 1px solid rgba(26, 74, 110, 0.12);
            border-radius: 12px;
            padding: 8px;
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
    
# --- LOGOUT HANDLER ---
if st.query_params.get("logout") == "true":
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = None
    if hasattr(st, "query_params") and hasattr(st.query_params, "clear"):
        st.query_params.clear()
        

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
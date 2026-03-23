import streamlit as st
import pandas as pd
import database as db
import utils
import config
import os
import numpy as np
import math
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import certificate as cert_module

PENDING_CSV = "pending_verification.csv"
MAIN_CSV = "nccr_data.csv"


# ─────────────────────────────────────────────────────────────────────────────
# Email helper: send certificate to contributor
# ─────────────────────────────────────────────────────────────────────────────

def _send_certificate_email(
    to_email: str,
    contributor_name: str,
    location: str,
    prof_name: str,
    cert_bytes: bytes,
):
    """Email the generated PNG certificate to the contributor."""
    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = "🎓 Your NCCR Certificate of Contribution"
        msg["From"] = config.SENDER_EMAIL
        msg["To"] = to_email

        html = f"""
        <html><body>
          <p>Dear {contributor_name},</p>
          <p>Congratulations! Your marine data submission for <b>{location}</b> has been
          reviewed and <b>verified</b> by <b>Prof./Dr. {prof_name}</b>.</p>
          <p>Please find your <b>NCCR Certificate of Contribution</b> attached to this email.</p>
          <p>Thank you for contributing to India's coastal data ecosystem.</p>
          <p>With regards,<br>
          <b>NCCR Marine Data Portal</b><br>
          National Centre for Coastal Research, Ministry of Earth Sciences</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        # Attach the certificate PNG
        cert_img = MIMEImage(cert_bytes, _subtype="png", name="NCCR_Certificate_of_Contribution.png")
        cert_img.add_header("Content-Disposition", "attachment",
                            filename="NCCR_Certificate_of_Contribution.png")
        msg.attach(cert_img)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Certificate email error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Main verification page
# ─────────────────────────────────────────────────────────────────────────────

def show(request_id_from_app=None):
    st.markdown(
        """
        <div class="nccr-hero" style="margin-top:14px;">
            <div class="nccr-section-label">Verification</div>
            <div style="display:flex; gap:12px; align-items:flex-start;">
                <span class="material-symbols-rounded nccr-icon">verified_user</span>
                <div>
                    <h2 style="margin:0;">External Professor Verification</h2>
                    <p class="nccr-card-subtitle" style="margin-top:6px;">
                        Review the submission batch and approve or discard it securely.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Resolve request_id
    request_id = request_id_from_app

    if not request_id:
        if hasattr(st, "query_params"):
            request_id = st.query_params.get("id")
        else:
            params = st.experimental_get_query_params()
            request_id = params.get("id", [None])[0]

    if not request_id:
        st.error("Invalid or missing Request ID.")
        st.info("Please use the full link provided in the verification email.")
        return

    if not os.path.exists(PENDING_CSV):
        st.error("No pending verification records found.")
        return

    try:
        df = pd.read_csv(PENDING_CSV)

        if "request_id" in df.columns:
            df["request_id"] = df["request_id"].astype(str)

        batch = df[df["request_id"] == str(request_id)]

        if batch.empty:
            st.warning("This verification link is invalid or has already been processed.")
            st.info("You can close this window.")
            return

        # Professor & contributor details from first row
        first_row = batch.iloc[0].to_dict()
        prof_name       = first_row.get("prof_name", "Professor")
        university      = first_row.get("university", "Institution")
        contributor_name = str(first_row.get("Contributor", "Contributor"))
        contributor_email = str(first_row.get("Email", ""))
        location        = str(first_row.get("Main_Location", "Coastal Region"))

        st.markdown(
            f"""
            <div class="nccr-card" style="padding:14px 14px;">
                <div class="nccr-section-label">Welcome</div>
                <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
                    <div style="font-weight:800; color:var(--nccr-ink-2); font-size:1.02rem;">
                        Prof. {prof_name}
                    </div>
                    <div class="nccr-pill">{university}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        count = len(batch)
        if count > 1:
            st.info(f"You have a **Bulk Upload Batch** of **{count} records** to verify.")
        else:
            st.write("Please review the following marine data submission.")

        st.subheader("Submitted Data")
        display_cols = [
            c for c in batch.columns
            if c not in ["request_id", "prof_email", "prof_name", "university", "status"]
        ]
        st.dataframe(batch[display_cols], width="stretch")

        st.markdown("---")
        st.subheader("Decision")

        c1, c2, c3 = st.columns(3, gap="small")

        # ─── APPROVE ──────────────────────────────────────────────────────
        if c1.button("Verify & Approve Batch", type="primary"):
            prof_tag = f"{prof_name} ({university})"

            batch_to_save = batch.copy()
            batch_to_save["verified_by"] = prof_tag

            raw_data_list = batch_to_save.to_dict(orient="records")

            # Columns that map to numeric (DOUBLE PRECISION / INTEGER) in Supabase
            NUMERIC_COLS = {
                "Water_Temp", "Salinity", "pH", "Turbidity", "Transparency",
                "TSS", "TDS", "DO", "BOD", "COD", "NH4_N", "NO3_N", "NO2_N",
                "PO4", "SO4", "Fecal_Coliform", "Total_Coliform", "Productivity",
                "Chlorophyll", "BGA", "Wind_Speed", "Wind_Direction", "Air_Temp",
                "Humidity", "Precipitation", "Depth",
                "Coastal_Villages", "Panchayats", "Population",
                "Fishermen", "Landing_Centers", "Water_Bodies",
                "Industrial_Est", "Tourist_Inflow",
                "Latitude", "Longitude",
            }

            clean_data_list = []
            for row in raw_data_list:
                clean_row = {}
                for k, v in row.items():
                    if k in ["prof_email", "prof_name", "university", "status", "request_id"]:
                        continue
                    # Drop NaN / Inf floats
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        clean_row[k] = None
                    elif isinstance(v, float):
                        clean_row[k] = v
                    else:
                        try:
                            if pd.isna(v):
                                clean_row[k] = None
                                continue
                        except Exception:
                            pass
                        # Coerce non-numeric strings in numeric columns to None
                        # (handles "BTL", "<LOQ", "N/D", "ND", "---", etc.)
                        if k in NUMERIC_COLS and isinstance(v, str):
                            try:
                                clean_row[k] = float(v)
                            except (ValueError, TypeError):
                                clean_row[k] = None  # discard non-parseable strings
                        else:
                            clean_row[k] = v
                clean_data_list.append(clean_row)

            success, msg = db.save_bulk_data(clean_data_list)

            if success:
                # Save to nccr_data.csv (legacy backup)
                try:
                    if os.path.exists(MAIN_CSV):
                        batch_to_save.to_csv(MAIN_CSV, mode="a", header=False, index=False)
                    else:
                        batch_to_save.to_csv(MAIN_CSV, mode="w", header=True, index=False)
                except Exception as csv_e:
                    print(f"CSV Backup Error: {csv_e}")

                # Remove from Pending
                df_clean = df[df["request_id"] != str(request_id)]
                df_clean.to_csv(PENDING_CSV, index=False)

                # ── Generate Certificate ───────────────────────────────────
                cert_bytes = cert_module.create_certificate(
                    contributor_name=contributor_name,
                    location=location,
                    verified_by=prof_tag,
                    contributor_email=contributor_email,
                    num_records=len(clean_data_list),
                )

                st.balloons()
                st.success(
                    f"✅ {len(clean_data_list)} records verified and approved. "
                    "Thank you for your contribution."
                )

                # ── Send certificate email to contributor ──────────────────
                if contributor_email and "@" in contributor_email:
                    sent = _send_certificate_email(
                        to_email=contributor_email,
                        contributor_name=contributor_name,
                        location=location,
                        prof_name=prof_name,
                        cert_bytes=cert_bytes,
                    )
                    if sent:
                        st.info(
                            f"🎓 A **Certificate of Contribution** has been sent to "
                            f"**{contributor_email}**."
                        )
                    else:
                        st.warning(
                            "Data approved, but the certificate email could not be sent. "
                            "The contributor can download it below."
                        )

                # ── Download button (professor/verify page) ────────────────
                st.markdown("### 🏅 Certificate of Contribution")
                st.markdown(
                    "The certificate below is issued to the contributor upon successful "
                    "professor-verification of their data."
                )
                st.download_button(
                    label="⬇️ Download Certificate (PNG)",
                    data=cert_bytes,
                    file_name=f"NCCR_Certificate_{contributor_name.replace(' ', '_')}.png",
                    mime="image/png",
                )
                st.image(cert_bytes, caption="NCCR Certificate of Contribution", use_container_width=True)

                st.stop()
            else:
                st.error(f"Error saving to database: {msg}")

        # ─── DISCARD ──────────────────────────────────────────────────────
        if c2.button("Discard Batch"):
            df_clean = df[df["request_id"] != str(request_id)]
            df_clean.to_csv(PENDING_CSV, index=False)
            st.error("Data batch has been discarded.")
            st.stop()

        # ─── LATER ────────────────────────────────────────────────────────
        if c3.button("Busy / Later"):
            st.info("No action taken. You can come back later using the same link.")

        st.markdown("---")
        st.write(
            "Are you a Professor/Researcher? "
            "[Register Here](http://localhost:8501) to join the NCCR Portal."
        )

    except Exception as e:
        st.error(f"Error processing verification: {e}")

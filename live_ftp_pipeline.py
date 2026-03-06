# live_ftp_pipeline.py
# ============================================================
# NCCR Live RTMS Buoy Data Pipeline
# ============================================================
# Sequence:
#   1. FTP  → Download today's CSV from the buoy server
#   2. Append to master_raw_data.csv  (no data loss)
#   3. Clean via prediction.clean_marine_data()
#   4. Save cleaned output as nccr_data.csv
#   5. BiGRU 3-day forecast via model_prep + Keras model
# ============================================================

import os
import io
from typing import cast
import logging
from datetime import date, timedelta
from ftplib import FTP, error_perm


import pandas as pd
import numpy as np

# ── Tensorflow / Keras ────────────────────────────────────────
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"          # suppress TF C++ logs
import tensorflow as tf
from tensorflow.keras.models import load_model

# ── Local NCCR modules ────────────────────────────────────────
from prediction import clean_marine_data           # Returns: cleaned_df, mapping, report, date_col
from model_prep import prep_data_for_dl            # Returns: X, y, scaler, available_features

# ─────────────────────────────────────────────────────────────
# CONFIGURATION  (replace placeholders with real values)
# ─────────────────────────────────────────────────────────────

# FTP connection — replace all placeholder values before running
FTP_HOST:       str = "ftp.rtms-buoy.example.gov.in"   # ← replace
FTP_PORT:       int = 21
FTP_USER:       str = "nccr_user"                       # ← replace
FTP_PASSWORD:   str = "your_password_here"              # ← replace
FTP_REMOTE_DIR: str = "/daily_exports/"                 # ← replace
FTP_PREFIX:     str = "RTMS_"
FTP_EXT:        str = ".csv"

MASTER_CSV:    str      = "master_raw_data.csv"          # Historical database
CLEANED_CSV:  str      = "nccr_data.csv"                  # Output of cleaning step
MODEL_PATH:   str      = "water_quality_bigru.h5"         # Trained BiGRU model
LOOKBACK:     int      = 28                                 # Must match model_prep.py
FORECAST_SLOTS: int    = 12                                 # Must match model training
FEATURES: list[str]    = ["Water_Temp", "pH", "DO", "Salinity", "Chl(ug/l)"]

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("NCCR_Pipeline")


# ═════════════════════════════════════════════════════════════
# STEP 1 — FTP INGESTION
# ═════════════════════════════════════════════════════════════

def build_remote_filename(for_date: date) -> str:
    """Constructs the expected remote filename for a given date."""
    return f"{FTP_PREFIX}{for_date.isoformat()}{FTP_EXT}"


def download_todays_csv(for_date: date | None = None) -> pd.DataFrame | None:
    """
    Connects to the FTP server and downloads today's buoy CSV.

    Parameters
    ----------
    for_date : date, optional
        Target date (defaults to today).

    Returns
    -------
    pd.DataFrame | None
        Parsed DataFrame from the downloaded file, or None on failure.
    """
    target_date   = for_date or date.today()
    remote_file   = build_remote_filename(target_date)
    remote_path   = FTP_REMOTE_DIR.rstrip("/") + "/" + remote_file

    log.info(f"Connecting to FTP: {FTP_HOST}:{FTP_PORT}")
    try:
        with FTP() as ftp:
            ftp.connect(host=FTP_HOST, port=FTP_PORT, timeout=30)
            ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
            log.info(f"Authenticated. Downloading: {remote_path}")

            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {remote_path}", buffer.write)
            buffer.seek(0)

            df = pd.read_csv(buffer)
            log.info(f"Downloaded {len(df)} rows from FTP ({remote_file})")
            return df

    except error_perm as e:
        log.error(f"FTP permission error — file may not exist yet: {e}")
        return None
    except Exception as e:
        log.error(f"FTP connection/download failed: {e}")
        return None


# ═════════════════════════════════════════════════════════════
# STEP 2 — APPEND TO MASTER & CLEAN
# ═════════════════════════════════════════════════════════════

def append_to_master(new_df: pd.DataFrame, master_path: str) -> pd.DataFrame:
    """
    Safely appends new_df to the master CSV without dropping any
    existing historical rows.

    Parameters
    ----------
    new_df      : pd.DataFrame   Freshly downloaded rows.
    master_path : str            Path to master_raw_data.csv.

    Returns
    -------
    pd.DataFrame   The combined (existing + new) DataFrame.
    """
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)
        log.info(f"Master CSV loaded: {len(master_df)} existing rows.")
        combined  = pd.concat([master_df, new_df], ignore_index=True)
    else:
        log.warning(f"Master CSV not found at '{master_path}'. Creating new file.")
        combined = new_df.copy()

    combined.to_csv(master_path, index=False)
    log.info(f"Master CSV updated: {len(combined)} total rows → '{master_path}'")
    return combined  # type: ignore[return-value]


def run_impurification(combined_df: pd.DataFrame, cleaned_path: str) -> pd.DataFrame | None:
    """
    Passes the raw combined DataFrame through the NCCR cleaning pipeline
    (prediction.clean_marine_data) and saves the result.

    Parameters
    ----------
    combined_df  : pd.DataFrame   Raw combined master data.
    cleaned_path : str            Destination path for the cleaned CSV.

    Returns
    -------
    pd.DataFrame | None   The cleaned DataFrame, or None if cleaning failed.
    """
    log.info("Running NCCR impurification pipeline (clean_marine_data)…")

    # Sanitize BTL/BDL codes before cleaning (mirrors prediction.load_data logic)
    combined_df = combined_df.replace(["BTL", "BDL", "btl", "bdl"], 0.0)

    # Identify date column to exclude from numeric coercion
    date_col_raw = next(
        (c for c in combined_df.columns if any(k in c.lower() for k in ["date", "time", "timestamp"])),
        None,
    )
    for col in combined_df.columns:
        if col != date_col_raw:
            combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce")

    try:
        cleaned_df, mapping, report, date_col = clean_marine_data(combined_df)
    except Exception as e:
        # clean_marine_data contains Streamlit calls (st.error / st.warning) that crash
        # when executed outside a Streamlit context.  Catch and surface the real cause.
        log.error(f"clean_marine_data raised an exception (likely Streamlit UI call "
                  f"outside app context): {e}")
        return None

    if not isinstance(cleaned_df, pd.DataFrame):
        log.error("Cleaning failed — no Date/Time column found in master data "
                  "(clean_marine_data returned None).")
        return None

    cleaned_df = cast(pd.DataFrame, cleaned_df)   # narrow type for static analysis

    # ── Cleaning Report ───────────────────────────────────────
    log.info("── Cleaning Report ──────────────────────────────")
    log.info(f"  Dropped (dead sensors) : {report.get('dropped', [])}")
    log.info(f"  Interpolated (repaired): {report.get('interpolated', [])}")
    log.info(f"  Incomplete (>6h gaps)  : {report.get('incomplete', [])}")
    log.info(f"  Untouched (clean)      : {report.get('untouched', [])}")
    log.info("─────────────────────────────────────────────────")

    cleaned_df.to_csv(cleaned_path, index=False)
    log.info(f"Cleaned data saved: {len(cleaned_df)} rows → '{cleaned_path}'")
    return cleaned_df


# ═════════════════════════════════════════════════════════════
# STEP 3 — BiGRU 3-DAY FORECAST
# ═════════════════════════════════════════════════════════════

def run_bigru_forecast(cleaned_csv: str, model_path: str) -> pd.DataFrame | None:
    """
    Loads the trained BiGRU model and generates a 3-day forecast.

    Parameters
    ----------
    cleaned_csv : str   Path to the cleaned nccr_data.csv.
    model_path  : str   Path to the trained .h5 / .keras model file.

    Returns
    -------
    pd.DataFrame | None   3-day forecast with real-world values, or None on error.
    """

    # ── 3a. Prepare data ──────────────────────────────────────
    log.info("Preparing data for BiGRU via model_prep.prep_data_for_dl…")
    try:
        X, y, scaler, available_features = prep_data_for_dl(cleaned_csv)
    except Exception as e:
        log.error(f"prep_data_for_dl failed: {e}")
        return None

    if X is None or len(X) == 0:
        log.error("prep_data_for_dl returned empty arrays. Not enough data.")
        return None

    log.info(f"  X shape          : {X.shape}")
    log.info(f"  Available features: {available_features}")

    # ── 3b. Load model ────────────────────────────────────────
    if not os.path.exists(model_path):
        log.error(f"Model file not found: '{model_path}'")
        return None

    log.info(f"Loading BiGRU model from '{model_path}'…")
    try:
        # compile=False skips deserializing saved metrics/optimizer config,
        # which fixes "Could not deserialize 'keras.metrics.mae'" on Keras 3+.
        # Recompile immediately so predict() works correctly.
        model = load_model(model_path, compile=False)
        model.compile(optimizer="adam", loss="mae")
        log.info("Model loaded successfully.")
        model.summary(print_fn=log.debug)
    except Exception as e:
        log.error(f"Failed to load model: {e}")
        return None

    # ── 3c. Extract the most recent 7-day window ──────────────
    latest_sequence = X[-1:]           # shape: (1, lookback, n_features)
    log.info(f"Latest sequence shape: {latest_sequence.shape}")

    # ── 3d. Predict ───────────────────────────────────────────
    log.info("Running model.predict on latest window…")
    raw_prediction = model.predict(latest_sequence, verbose=0)
    # raw_prediction shape depends on model output:
    #   Flat Dense output  → (1, forecast_days * n_features)
    #   Sequence output    → (1, forecast_days, n_features)

    n_features    = len(available_features)
    forecast_slots = FORECAST_SLOTS

    if raw_prediction.ndim == 2:
        # Flat output → reshape to (forecast_slots, n_features)
        forecast_scaled = raw_prediction.reshape(forecast_slots, n_features)
    elif raw_prediction.ndim == 3:
        # Already (1, forecast_slots, n_features)
        forecast_scaled = raw_prediction[0]
    else:
        log.error(f"Unexpected prediction shape: {raw_prediction.shape}")
        return None

    # ── 3e. Inverse-transform to real-world values ────────────
    forecast_real = scaler.inverse_transform(forecast_scaled)   # (forecast_slots, n_features)

    # ── 3f. Build a readable DataFrame ───────────────────────
    from datetime import datetime
    base_dttm      = datetime.combine(date.today(), datetime.min.time())
    forecast_dates = [base_dttm + timedelta(hours=6 * (i + 1)) for i in range(int(forecast_slots))]

    forecast_df = pd.DataFrame(
        forecast_real,
        index=[d.strftime("%Y-%m-%d %H:%M") for d in forecast_dates],
        columns=available_features,
    )
    forecast_df.index.name = "Date"

    return forecast_df


# ═════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═════════════════════════════════════════════════════════════

def run_pipeline(skip_ftp: bool = False):
    """
    Runs the full pipeline end-to-end.

    Parameters
    ----------
    skip_ftp : bool
        If True, skip the FTP download step and work with the existing
        master_raw_data.csv (useful for testing / offline runs).
    """
    log.info("=" * 60)
    log.info("  NCCR Live RTMS Pipeline — START")
    log.info("=" * 60)

    # ── STEP 1: FTP Ingestion ─────────────────────────────────
    if not skip_ftp:
        today_df = download_todays_csv()
        if today_df is None:
            log.error("FTP download failed. Aborting pipeline.")
            return
        combined_df = append_to_master(today_df, MASTER_CSV)
    else:
        log.info("--skip-ftp flag set. Loading existing master CSV directly.")
        if not os.path.exists(MASTER_CSV):
            log.error(f"Master CSV not found: '{MASTER_CSV}'. Cannot proceed.")
            return
        combined_df = pd.read_csv(MASTER_CSV)
        log.info(f"Loaded {len(combined_df)} rows from '{MASTER_CSV}'")

    # ── STEP 2: Impurification (NCCR Cleaning) ───────────────
    cleaned_df = run_impurification(combined_df, CLEANED_CSV)
    if cleaned_df is None:
        log.error("Cleaning step failed. Aborting pipeline.")
        return

    # ── STEP 3: BiGRU Forecast ────────────────────────────────
    forecast_df = run_bigru_forecast(CLEANED_CSV, MODEL_PATH)

    if forecast_df is None:
        log.error("BiGRU forecast failed.")
        return

    # ── RESULT ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🌊 NCCR BiGRU — 3-Day Marine Quality Forecast")
    print("=" * 60)
    print(forecast_df.to_string(float_format=lambda x: f"{x:.3f}"))
    print("=" * 60 + "\n")

    log.info("Pipeline completed successfully.")
    return forecast_df


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NCCR Live FTP → Clean → BiGRU Pipeline")
    parser.add_argument(
        "--skip-ftp",
        action="store_true",
        help="Skip the FTP download step and work from the existing master_raw_data.csv",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override today's date for the FTP filename (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    if args.date:
        override_date = date.fromisoformat(args.date)
        log.info(f"Date override: {override_date}")
        if not args.skip_ftp:
            today_df = download_todays_csv(for_date=override_date)
            if today_df is None:
                log.error("FTP download failed. Exiting.")
                raise SystemExit(1)
            append_to_master(today_df, MASTER_CSV)
            run_pipeline(skip_ftp=True)   # cleaning + forecast only, master already updated
    else:
        run_pipeline(skip_ftp=args.skip_ftp)

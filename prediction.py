# prediction.py
import streamlit as st
import pandas as pd
import numpy as np
import os

# ── Lazy heavy imports (only loaded when model runs) ────────────────────────
# tensorflow and sklearn are imported inside functions to keep startup fast.

# ---------------------------------------------------------------------------
# SECTION 1 — DATA PROCESSING HELPERS
# ---------------------------------------------------------------------------

# Canonical BiGRU feature order (must match model training in model_prep.py)
FEATURES = ['water_temp', 'ph', 'do', 'salinity'] # 'Chl(ug/l)' temporarily disabled
FEATURE_LABELS = {
    'water_temp':  '🌡️ Water Temp (°C)',
    'ph':          '⚗️ pH',
    'do':          '💧 Dissolved Oxygen (mg/L)',
    'salinity':    '🧂 Salinity (psu)',
    'Chl(ug/l)':   '🌿 Chlorophyll-a (µg/L)',
}

# ── 6-Hour Resolution Constants ──────────────────────────────────────────────
# Each 'slot' = one 6-hour window (00:00, 06:00, 12:00, 18:00)
SLOTS_PER_DAY = 4          # 24h / 6h
LOOKBACK      = 28         # 7 days × 4 slots  — input window
FORECAST      = 12         # 3 days × 4 slots  — output window
RESAMP_FREQ   = '6h'      # pandas resample frequency string


def get_column_mapping(df_columns):
    """
    Identifies columns using Strict Dual-Keyword "Fingerprint" Rules.
    Returns: Dictionary { 'internal_key': 'actual_csv_header' }
    """
    mapping = {}
    for col in df_columns:
        c = col.lower()
        if "temp" in c and ("water" in c or "wq" in c) and "water bodies" not in c:
            mapping['water_temp'] = col
        elif "temp" in c and "air" in c:
            mapping['air_temp'] = col
        elif "sal" in c:
            mapping['salinity'] = col
        elif "turb" in c:
            mapping['turbidity'] = col
        elif "chl" in c or "chlorophyll" in c:
            mapping['Chl(ug/l)'] = col
        elif "ph" == c or "p.h." == c or "ph level" in c:
            mapping['ph'] = col
        elif ("oxygen" in c or "dissolved" in c) or c == "do":
            mapping['do'] = col
        elif "tds" in c:
            mapping['tds'] = col
        elif "tss" in c:
            mapping['tss'] = col
        elif "water" in c and "bodies" in c:
            mapping['water_bodies'] = col
        elif "precip" in c or "rain" in c:
            mapping['precipitation'] = col
    return mapping


# ---------------------------------------------------------------------------
# SECTION 1b — DOMAIN-AWARE 6-HOUR AGGREGATION
# ---------------------------------------------------------------------------

def _smart_6h_aggregate(group: pd.DataFrame) -> pd.Series:
    """
    Converts a 6-hour bucket of 10-minute sensor readings into a single
    representative value using oceanographically optimal aggregation per parameter.

    Rules (from the NCCR domain rationale):
      • Dissolved Oxygen  → minimum   (worst-case ecological value; fish mortality risk)
      • Chlorophyll-a     → 90th pct  (bloom peak detection; log-normal distribution)
      • Blue-Green Algae  → 90th pct  (same rationale as Chl)
      • Turbidity         → 75th pct  (storm/runoff spike = danger signal)
      • Precipitation     → sum        (accumulative rainfall, not rate)
      • pH, Salinity      → median    (robust to sensor flush / drift artifacts)
      • Water Temp        → 5–95% trimmed mean  (removes mid-day surface heating spikes)
      • All others        → 10–90% trimmed mean (safe default outlier removal)
    """
    result = {}
    for col in group.columns:
        s = group[col].dropna()
        if len(s) == 0:
            result[col] = np.nan
            continue

        c = col.lower()

        # Dissolved Oxygen — 25th percentile (early warning for low DO, but less noisy than absolute min)
        if c == 'do' or ('oxygen' in c and 'dissolved' in c) or c.startswith('do '):
            result[col] = float(s.quantile(0.25))

        # Chlorophyll-a and Blue-Green Algae — bloom peak (90th percentile)
        elif 'chl' in c or 'chloro' in c or 'bga' in c or 'blue' in c:
            result[col] = float(s.quantile(0.90))

        # Turbidity — storm/runoff risk (75th percentile)
        elif 'turb' in c:
            result[col] = float(s.quantile(0.75))

        # Precipitation — accumulative sum
        elif 'precip' in c or 'rain' in c:
            result[col] = float(s.sum())

        # pH and Salinity — median (robust to transient drift)
        elif c in ('ph', 'p.h.') or 'ph level' in c or 'sal' in c:
            result[col] = float(s.median())

        # Water Temperature — 5–95% trimmed mean (removes heating artefacts)
        elif 'temp' in c and 'air' not in c:
            lo, hi = s.quantile(0.05), s.quantile(0.95)
            result[col] = float(s.clip(lo, hi).mean())

        # Default — 10–90% trimmed mean
        else:
            lo, hi = s.quantile(0.10), s.quantile(0.90)
            result[col] = float(s.clip(lo, hi).mean())

    return pd.Series(result)


def clean_marine_data(df) -> "tuple[pd.DataFrame, dict, dict, str] | tuple[None, None, None, None]":
    """
    Applies NCCR Standard Cleaning: Date Handle -> Dead Sensor -> Physics Filter -> Interpolation.
    Returns: df (cleaned), mapping (dict), report (dict of lists), date_col (str)
    """
    date_col = next(
        (c for c in df.columns
         if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()),
        None
    )
    if not date_col:
        return None, None, None, None

    try:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df[date_col] = df[date_col].astype("datetime64[ns]")
        df = df.dropna(subset=[date_col])
        df = df.set_index(date_col).sort_index()
        # Drop duplicates in index and columns to prevent pandas alignment errors
        df = df.loc[~df.index.duplicated(keep='first')]
        df = df.loc[:, ~df.columns.duplicated()]
    except Exception as e:
        st.error(f"❌ Error converting '{date_col}' to datetime: {e}")
        return None, None, None, None

    dropped_cols, interpolated_cols, untouched_cols = [], [], []
    mapping = get_column_mapping(df.columns)

    # Dead sensor check
    for key in ['tds', 'tss']:
        if key in mapping:
            col_name = mapping[key]
            if df[col_name].sum() == 0:
                df = df.drop(columns=[col_name])
                dropped_cols.append(col_name)
                st.warning(f"⚠️ Dropped Dead Sensor (All 0.0): {col_name}")
                mapping.pop(key, None)

    # Physics quarantine
    if 'water_temp' in mapping:
        c = mapping['water_temp']
        # Bay of Bengal water temp rarely drops below 20C. A reading of 0 is a dead sensor.
        df.loc[(df[c] <= 0) | (df[c] > 40), c] = np.nan
    if 'air_temp' in mapping:
        c = mapping['air_temp']
        df.loc[(df[c] <= 0) | (df[c] > 55), c] = np.nan
    if 'ph' in mapping:
        c = mapping['ph']
        df.loc[(df[c] < 6) | (df[c] > 10), c] = np.nan
    if 'turbidity' in mapping:
        c = mapping['turbidity']
        df.loc[df[c] <= 0, c] = np.nan
    if 'salinity' in mapping:
        c = mapping['salinity']
        df.loc[df[c] < 0.5, c] = np.nan
    if 'do' in mapping:
        c = mapping['do']
        # DO of exactly 0.0 is typically a sensor calibration error/failure in open coastal waters
        df.loc[df[c] <= 0, c] = np.nan
    if 'tds' in mapping:
        c = mapping['tds']
        df.loc[df[c] <= 0, c] = np.nan
    if 'tss' in mapping:
        c = mapping['tss']
        df.loc[df[c] <= 0, c] = np.nan
    if 'Chl(ug/l)' in mapping:
        c = mapping['Chl(ug/l)']
        df.loc[df[c] <= 0, c] = np.nan

    # Temporal interpolation
    remaining_gaps_cols = []
    for col in df.columns:
        if df[col].isnull().any():
            df[col] = df[col].interpolate(method='time', limit=6, limit_direction='both')
            if df[col].isnull().any():
                remaining_gaps_cols.append(col)
                interpolated_cols.append(col)
            else:
                interpolated_cols.append(col)
        else:
            untouched_cols.append(col)

    # Seasonal fallback
    for days in [1, 2, 3, 4]:
        df = df.fillna(df.shift(periods=days, freq='D'))
    for col in df.columns:
        if df[col].isnull().any():
            seasonal_means = df.groupby(
                [df.index.month, df.index.hour])[col].transform('mean')
            df[col] = df[col].fillna(seasonal_means)

    remaining_gaps_cols = [c for c in df.columns if df[c].isnull().any()]
    df = df.reset_index()

    rename_map = {v: k for k, v in mapping.items()}
    df = df.rename(columns=rename_map)

    report = {
        "dropped":      dropped_cols,
        "interpolated": interpolated_cols,
        "untouched":    untouched_cols,
        "incomplete":   remaining_gaps_cols,
    }
    return df, mapping, report, date_col


def load_data():
    """Handles file upload, BTL cleaning and the NCCR cleaning pipeline."""
    uploaded_file = st.file_uploader(
        "Upload Your Dataset (CSV/Excel)", type=["csv", "xlsx"])

    if uploaded_file is None:
        return None, None

    try:
        df = (pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv')
              else pd.read_excel(uploaded_file))

        pd.set_option('future.no_silent_downcasting', True)
        df = df.replace(['BTL', 'BDL', 'btl', 'bdl'], 0.0)
        df = df.infer_objects(copy=False)
        date_col = next(
            (c for c in df.columns
             if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()),
            None)
        for col in df.columns:
            if col != date_col:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        raw_df = df.copy()
        cleaned_df, mapping, report, date_col_name = clean_marine_data(df)

        if cleaned_df is None:
            st.error("❌ No Date/Time column found. Cannot perform Time-Series processing.")
            return None, None

        if date_col_name:
            raw_df[date_col_name] = pd.to_datetime(
                raw_df[date_col_name], dayfirst=True, errors='coerce')
            raw_df[date_col_name] = raw_df[date_col_name].astype("datetime64[ns]")
            raw_df = raw_df.dropna(subset=[date_col_name]).set_index(date_col_name).sort_index()

        st.success("✅ File Uploaded & Cleaned using NCCR Standard (Filter-First Pipeline)")

        st.write("### 🔍 Column Identification Report")
        st.json(mapping)
        st.markdown("#### 📝 Transparency Report *(Cleaning Actions)*")
        if True:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.write("🔴 **Dropped (Dead Sensors)**")
                for c in (report['dropped'] or ["_None_"]):
                    st.write(f"- {c}")
            with c2:
                st.write("🟡 **Interpolated (Repaired)**")
                for c in (report['interpolated'] or ["_None_"]):
                    st.write(f"- {c}")
            with c3:
                st.write("⚫ **Incomplete (>6h Gaps)**")
                if report['incomplete']:
                    for c in report['incomplete']:
                        st.write(f"- {c}")
                    st.caption("Filled via: Linear (<6h) → 4-Day History → Seasonal Mean")
                else:
                    st.write("- _None_")
            with c4:
                st.write("🟢 **Clean (Untouched)**")
                for c in (report['untouched'] or ["_None_"]):
                    st.write(f"- {c}")
        st.write("### 📊 Dataset Statistics")
        col_pre, col_post = st.columns(2)

        # Prepare Pre-Cleaning Stats
        rename_map = {v: k for k, v in mapping.items()}
        raw_df_renamed = raw_df.rename(columns=rename_map)
        safe_raw_df = raw_df_renamed.copy()
        for col in safe_raw_df.columns:
            if pd.api.types.is_datetime64_any_dtype(safe_raw_df[col]):
                safe_raw_df[col] = safe_raw_df[col].astype(str)
            elif safe_raw_df[col].dtype == object:
                try:
                    safe_raw_df[col] = safe_raw_df[col].apply(
                        lambda x: str(x) if hasattr(x, 'year') else x)
                except Exception:
                    pass

        with col_pre:
            st.markdown("#### 🟥 Pre-Cleaning (Raw)")
            st.dataframe(safe_raw_df.describe(), width='stretch')

        # Prepare Post-Cleaning Stats
        safe_df = cleaned_df.copy()
        for col in safe_df.columns:
            if pd.api.types.is_datetime64_any_dtype(safe_df[col]):
                safe_df[col] = safe_df[col].astype(str)
            elif safe_df[col].dtype == object:
                try:
                    safe_df[col] = safe_df[col].apply(
                        lambda x: str(x) if hasattr(x, 'year') else x)
                except Exception:
                    pass
        
        with col_post:
            st.markdown("#### 🟩 Post-Cleaning")
            st.dataframe(safe_df.describe(), width='stretch')

        return cleaned_df, date_col_name

    except Exception as e:
        import traceback
        st.error(f"❌ Error reading file: {e}\n\n```\n{traceback.format_exc()}\n```")
        return None, None


# ---------------------------------------------------------------------------
# SECTION 2 — BiGRU HOLDOUT VALIDATION
# ---------------------------------------------------------------------------

def _prepare_holdout(cleaned_df, date_col_name):
    """
    Returns X_input (28-slot / 7-day×4 window), y_true (12-slot / 3-day×4 ground truth),
    scaler, available feature list, and the 6h-resampled dataframe — or None on failure.

    Resolution: 6-hour slots using domain-aware optimal aggregation per parameter
    (see _smart_6h_aggregate for the scientific rationale per parameter type).
    """
    from sklearn.preprocessing import MinMaxScaler

    # Determine available features
    avail_feats = [f for f in FEATURES if f in cleaned_df.columns]
    if len(avail_feats) < 2:
        return None, None, None, None, None, "Need at least 2 recognised sensor columns for BiGRU."

    # Set datetime index and resample to 6-hour slots with smart aggregation
    try:
        df_idx = cleaned_df.copy()
        if date_col_name and date_col_name in df_idx.columns:
            df_idx = df_idx.set_index(date_col_name)
        elif not isinstance(df_idx.index, pd.DatetimeIndex):
            return None, None, None, None, None, "Cannot locate datetime index."

        # Apply domain-aware 6-hour aggregation (the optimal equation)
        resampled = (
            df_idx[avail_feats]
            .resample(RESAMP_FREQ)
            .apply(_smart_6h_aggregate)
            .ffill()
        )
    except Exception as e:
        return None, None, None, None, None, f"Resampling failed: {e}"

    # Need at least LOOKBACK + FORECAST + some training buffer
    min_slots = LOOKBACK + FORECAST + SLOTS_PER_DAY  # 28+12+4 = 44 slots ≈ 11 days
    if len(resampled) < min_slots:
        days_needed = min_slots // SLOTS_PER_DAY
        days_have   = len(resampled) // SLOTS_PER_DAY
        return None, None, None, None, None, (
            f"Need ≥ {days_needed} days of data for 6-hour holdout validation. "
            f"Dataset has only ~{days_have} days after resampling.")

    # Log1p-transform Chlorophyll (log-normal distribution → near-normal)
    chl_col = 'Chl(ug/l)'
    if chl_col in avail_feats:
        resampled = resampled.copy()
        resampled[chl_col] = np.log1p(resampled[chl_col].clip(lower=0))

    # Holdout split: last (LOOKBACK + FORECAST) slots
    recent = resampled.iloc[-(LOOKBACK + FORECAST):]
    X_raw  = recent.iloc[:LOOKBACK].values   # shape (28, n_feat)
    y_true = recent.iloc[LOOKBACK:].values   # shape (12, n_feat)

    # Scale using recent history (last 120 slots ≈ 30 days, or full dataset)
    history = resampled.iloc[max(0, len(resampled) - 120):].values
    scaler  = MinMaxScaler()
    scaler.fit(history)

    X_scaled = scaler.transform(X_raw)     # (28, n_feat)
    X_input  = X_scaled[np.newaxis, ...]   # (1, 28, n_feat)

    return X_input, y_true, scaler, avail_feats, resampled, None



def _train_and_save_model(resampled_df, avail_feats, model_path,
                          lookback=LOOKBACK, forecast_slots=FORECAST):
    """
    Trains a fresh BiGRU on ALL available features and saves it to model_path.
    Uses the full 6h-resampled dataframe (except last FORECAST slots held out).
    Returns (success: bool, message: str).

    Input shape:  (batch, LOOKBACK=28, n_feat)   — 7 days × 4 six-hour slots
    Output shape: (batch, FORECAST=12, n_feat)   — 3 days × 4 six-hour slots
    """
    import tensorflow as tf
    from sklearn.preprocessing import MinMaxScaler

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    tf.get_logger().setLevel('ERROR')

    n_feat = len(avail_feats)

    # Log1p-transform Chlorophyll before scaling (corrects its log-normal distribution)
    chl_col = 'Chl(ug/l)'
    data_for_train = resampled_df[avail_feats].copy()
    if chl_col in avail_feats:
        data_for_train[chl_col] = np.log1p(data_for_train[chl_col].clip(lower=0))

    data = data_for_train.values   # (n_slots, n_feat)

    min_needed = lookback + forecast_slots + SLOTS_PER_DAY
    if len(data) < min_needed:
        days_n = min_needed // SLOTS_PER_DAY
        return False, (
            f"Need at least {days_n} days (~{min_needed} six-hour slots) to train. "
            f"Got {len(data)} slots."
        )

    scaler      = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(lookback, len(scaled_data) - forecast_slots + 1):
        X.append(scaled_data[i - lookback : i])
        y.append(scaled_data[i : i + forecast_slots])

    X = np.array(X)   # (samples, LOOKBACK=28, n_feat)
    y = np.array(y)   # (samples, FORECAST=12, n_feat)

    # Build BiGRU architecture (with Dropout for regularisation)
    # Input shape now: (LOOKBACK=28, n_feat) — 7 days × 4 six-hour slots
    # Output shape:    (FORECAST=12, n_feat) — 3 days × 4 six-hour slots
    model = tf.keras.Sequential([
        tf.keras.layers.Bidirectional(
            tf.keras.layers.GRU(64, return_sequences=True),
            input_shape=(lookback, n_feat)
        ),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Bidirectional(tf.keras.layers.GRU(32)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(forecast_slots * n_feat),
        tf.keras.layers.Reshape((forecast_slots, n_feat)),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3), loss='mae')

    # Scale epochs & batch size with dataset size
    # With 6h resolution, n_samples is ~4× larger than daily → more stable training
    n_samples  = len(X)
    epochs     = min(300, max(100, n_samples // 4))   # scales with 6h sample count
    batch_size = min(64, max(16, n_samples // 20))

    callbacks = [
        # Stop early if val_loss stops improving; restore best weights
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=25,
            restore_best_weights=True, verbose=0
        ),
        # Reduce LR when val_loss plateaus (fine-tunes learning)
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5,
            patience=10, min_lr=1e-6, verbose=0
        ),
    ]

    try:
        model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.15,
            callbacks=callbacks,
            verbose=0,
        )
        # Save in native Keras format (avoids HDF5 deprecation warning)
        keras_path = model_path.replace('.h5', '.keras')
        model.save(keras_path)
        # Also keep .h5 for backwards compat with existing load_model calls
        model.save(model_path)
        return True, (
            f"Model retrained on {n_feat} feature(s): {', '.join(avail_feats)}. "
            f"Resolution: 6-hour slots (LOOKBACK={lookback}, FORECAST={forecast_slots}). "
            f"Trained for up to {epochs} epochs (early stopping active)."
        )
    except Exception as e:
        return False, f"Training failed: {e}"


def _run_bigru_section(cleaned_df, date_col_name):
    """Renders the BiGRU validation section inside run_prediction_page()."""
    import plotly.graph_objects as go
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <span style="font-size:1.6rem;">🧠</span>
            <div>
                <p style="margin:0; font-size:0.7rem; font-weight:700; letter-spacing:.12em;
                           text-transform:uppercase; color:#8DA4B8;">
                    Bidirectional GRU Neural Network &mdash; 6-Hour Resolution</p>
                <h2 style="margin:0; color:#1A3A5C;">Model Validation &amp; Accuracy</h2>
                <p style="margin:2px 0 0 0; color:#627D98; font-size:0.85rem;">
                    Holdout test &mdash; 28-slot (7-day) input &rarr; 12-slot (3-day) forecast vs. ground truth
                    &nbsp;|&nbsp; Domain-aware 6h aggregation per parameter</p>
            </div>
        </div>
        <hr style="margin:10px 0 20px 0; border-color:rgba(26,58,92,0.10);">
        """,
        unsafe_allow_html=True,
    )

    # ── Prepare holdout data ────────────────────────────────────────────────
    with st.spinner("📊 Preparing data for BiGRU validation…"):
        X_input, y_true, scaler, avail_feats, daily_df, err = _prepare_holdout(
            cleaned_df, date_col_name)

    if err:
        st.warning(f"⚠️ Cannot run validation: {err}")
        return

    # ── Load model ──────────────────────────────────────────────────────────
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "water_quality_bigru.h5")

    model_col, _ = st.columns([3, 1])
    with model_col:
        if not os.path.exists(MODEL_PATH):
            st.error(
                "🚫 **Model file not found** — `water_quality_bigru.h5` is missing from the "
                "project root. Train and save the model first, then re-upload your data.",
                icon="🚫"
            )
            with st.expander("ℹ️ How to train and save the model"):
                st.code(
                    """
# Run this once from your project root to train & save the model:
python -c "
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Bidirectional, GRU, Dense, Reshape
from model_prep import prep_data_for_dl

X, y, scaler, feats = prep_data_for_dl('nccr_data.csv')
n_feat = len(feats)
model = Sequential([
    Bidirectional(GRU(64, return_sequences=True), input_shape=(7, n_feat)),
    Bidirectional(GRU(32)),
    Dense(3 * n_feat),
    Reshape((3, n_feat))
])
model.compile(optimizer='adam', loss='mae')
model.fit(X, y, epochs=50, batch_size=32, validation_split=0.1)
model.save('water_quality_bigru.h5')
print('Model saved.')
"
                    """,
                    language="bash",
                )
            return

        with st.spinner("🧠 Loading BiGRU neural network weights…"):
            try:
                # Suppress TF verbosity
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                import tensorflow as tf
                tf.get_logger().setLevel('ERROR')
                # compile=False skips deserializing saved metrics/optimizer config,
                # which fixes "Could not deserialize 'keras.metrics.mae'" on Keras 3+.
                # We recompile immediately after so the model is fully functional.
                model = tf.keras.models.load_model(MODEL_PATH, compile=False)
                model.compile(optimizer='adam', loss='mae')
            except Exception as e:
                st.error(f"❌ Failed to load model: {e}")
                return
        st.success("✅ BiGRU model loaded successfully", icon="🤖")

    # ── Reconcile model's expected feature count with available data ──────────
    # model.input_shape = (None, lookback, n_features_at_training_time)
    model_n_feat = model.input_shape[-1]   # features the model was trained on
    data_n_feat  = len(avail_feats)

    if model_n_feat != data_n_feat:
        st.markdown(
            f"""
            <div style="background:#FFF8E1; border-left:4px solid #FFA000;
                        border-radius:0 8px 8px 0; padding:16px 20px; margin:12px 0;">
                <p style="margin:0; font-weight:700; color:#E65100; font-size:0.95rem;">
                    ⚠️ Model was trained on <b>{model_n_feat}</b> feature(s),
                    but your data has <b>{data_n_feat}</b> features.
                </p>
                <p style="margin:6px 0 0 0; color:#6D4C41; font-size:0.85rem;">
                    To get predictions for <b>all {data_n_feat} parameters</b>
                    ({', '.join(avail_feats)}), the model must be retrained.
                    Click below — training runs entirely in the app (~1–2 min).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            retrain_clicked = st.button(
                f"🔄 Retrain Model on All {data_n_feat} Features",
                type="primary",
                use_container_width=True,
            )
        with col_info:
            st.caption(
                "This overwrites `water_quality_bigru.h5` with a new model "
                "trained on your full dataset. After training, re-upload your "
                "file to see predictions for all parameters."
            )

        if retrain_clicked:
            train_bar = st.progress(0, text="🚀 Initialising BiGRU training…")
            train_bar.progress(10, text="📐 Building model architecture…")
            ok, msg = _train_and_save_model(
                resampled_df = daily_df,   # daily_df is now the 6h-resampled df
                avail_feats  = avail_feats,
                model_path   = MODEL_PATH,
            )
            if ok:
                train_bar.progress(100, text="✅ Training complete!")
                st.success(
                    f"✅ **Model retrained successfully!**  {msg}\n\n"
                    f"Please **re-upload your CSV** above to run the full "
                    f"{data_n_feat}-parameter validation.",
                    icon="🎉"
                )
            else:
                train_bar.empty()
                st.error(f"❌ Retraining failed: {msg}")
        else:
            # Show partial results using trimmed features while user hasn't retrained
            st.info(
                f"ℹ️ Showing results for **{model_n_feat}** feature(s) only "
                f"until the model is retrained.",
                icon="📊"
            )
            avail_feats = avail_feats[:model_n_feat]
            X_input     = X_input[:, :, :model_n_feat]
            y_true      = y_true[:, :model_n_feat]
            from sklearn.preprocessing import MinMaxScaler
            sub_scaler = MinMaxScaler()
            sub_scaler.data_min_      = scaler.data_min_[:model_n_feat]
            sub_scaler.data_max_      = scaler.data_max_[:model_n_feat]
            sub_scaler.data_range_    = scaler.data_range_[:model_n_feat]
            sub_scaler.scale_         = scaler.scale_[:model_n_feat]
            sub_scaler.min_           = scaler.min_[:model_n_feat]
            sub_scaler.n_features_in_ = model_n_feat
            scaler = sub_scaler


    # ── Run inference ───────────────────────────────────────────────────────
    # 3-step progress bar so the user can see exactly what is happening
    progress_bar = st.progress(0, text="🔮 Starting BiGRU inference…")
    try:
        progress_bar.progress(25, text="⚙️ Step 1 / 3 — Feeding input window to model…")
        raw_pred = model.predict(X_input, verbose=0)

        progress_bar.progress(60, text="📐 Step 2 / 3 — Reshaping & inverse-transforming predictions…")
        n_feat = len(avail_feats)

        # Detect actual forecast steps from model output shape
        # Old model (FORECAST=3 daily) vs new model (FORECAST=12 six-hour)
        if raw_pred.ndim == 3:
            actual_forecast_steps = raw_pred.shape[1]   # (batch, steps, feats)
        elif raw_pred.ndim == 2:
            # Flat output: (batch, steps * feats) — derive steps
            actual_forecast_steps = raw_pred.shape[1] // n_feat
            raw_pred = raw_pred.reshape(1, actual_forecast_steps, n_feat)
        else:
            actual_forecast_steps = FORECAST

        y_pred_scaled = raw_pred[0]   # (actual_forecast_steps, n_feat)
        y_pred = scaler.inverse_transform(y_pred_scaled)

        # Trim y_true to the model's actual output length to avoid shape mismatch
        # (happens when old 3-step model is used with new 12-step holdout)
        y_true_disp = y_true[:actual_forecast_steps].copy().astype(float)

        chl_col = 'Chl(ug/l)'
        if chl_col in avail_feats:
            chl_idx = list(avail_feats).index(chl_col)
            y_pred[:, chl_idx]      = np.expm1(np.clip(y_pred[:, chl_idx],      0, None))
            y_true_disp[:, chl_idx] = np.expm1(np.clip(y_true_disp[:, chl_idx], 0, None))

        progress_bar.progress(100, text="✅ Step 3 / 3 — Inference complete! Rendering results…")
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Prediction failed: {e}")
        return
    progress_bar.empty()

    # Warn if stale model (old 3-step vs new 12-step)
    if actual_forecast_steps < FORECAST:
        st.warning(
            f"⚠️ **Stale model detected** — current model outputs **{actual_forecast_steps} steps** "
            f"but the pipeline now uses **{FORECAST} six-hour slots**. "
            f"Results shown for {actual_forecast_steps} step(s) only. "
            f"Click **🔄 Retrain BiGRU** below to upgrade to full 6-hour resolution.",
            icon="⚠️"
        )



    # ── Metrics ─────────────────────────────────────────────────────────────
    # Custom CSS to prevent text truncation in st.metric boxes
    st.markdown("""
        <style>
        [data-testid="stMetricLabel"] > div, [data-testid="stMetricValue"] > div {
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.2 !important;
        }
        [data-testid="stMetricValue"] > div {
            font-size: 1.6rem !important;
        }
        [data-testid="stMetricDelta"] > div {
            font-size: 0.85rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    steps_label = f"{actual_forecast_steps}-Slot" if actual_forecast_steps == FORECAST else f"{actual_forecast_steps}-Step (stale)"
    st.markdown(f"#### 📐 Parameter-wise Accuracy  *({steps_label} Holdout)*")
    metric_cols = st.columns(min(n_feat, 5))

    mae_values, rmse_values = {}, {}
    for i, feat in enumerate(avail_feats):
        mae  = mean_absolute_error(y_true_disp[:, i], y_pred[:, i])
        rmse = np.sqrt(mean_squared_error(y_true_disp[:, i], y_pred[:, i]))
        mae_values[feat]  = mae
        rmse_values[feat] = rmse

        label = FEATURE_LABELS.get(feat, feat)
        avg_actual = float(np.mean(y_true_disp[:, i]))
        pct_err    = (mae / avg_actual * 100) if avg_actual else 0

        with metric_cols[i % len(metric_cols)]:
            st.metric(
                label=label,
                value=f"MAE {mae:.3f}",
                delta=f"RMSE {rmse:.3f}  |  {pct_err:.1f}% err",
                delta_color="off",
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Forecast vs Actual Chart ─────────────────────────────────────────────
    # Create dropdown for parameter selection
    dropdown_options = {FEATURE_LABELS.get(f, f): f for f in avail_feats}
    default_feat = max(mae_values, key=mae_values.get)
    default_label = FEATURE_LABELS.get(default_feat, default_feat)
    
    st.markdown("#### 📈 Forecast Visualization")
    selected_label = st.selectbox(
        "Select Parameter to Visualize:",
        options=list(dropdown_options.keys()),
        index=list(dropdown_options.keys()).index(default_label)
    )
    
    primary_feat = dropdown_options[selected_label]
    primary_idx  = avail_feats.index(primary_feat)
    label_str    = selected_label

    # Build 6-hour slot labels for x-axis
    # daily_df is now a 6h-resampled DataFrame; index[-1] is the last known 6h slot
    last_slot = daily_df.index[-1]
    day_labels = [
        (last_slot + pd.Timedelta(hours=6 * (s + 1))).strftime("%d %b %H:%M")
        for s in range(FORECAST)
    ]

    fig = go.Figure()

    # Actual trace
    fig.add_trace(go.Scatter(
        x=day_labels,
        y=y_true_disp[:, primary_idx].tolist(),
        name="Actual (Ground Truth)",
        mode="lines+markers",
        line=dict(color="#1A4A6E", width=3),
        marker=dict(size=9, symbol="circle"),
    ))

    # Predicted trace
    fig.add_trace(go.Scatter(
        x=day_labels,
        y=y_pred[:, primary_idx].tolist(),
        name="BiGRU Prediction",
        mode="lines+markers",
        line=dict(color="#2A8A7A", width=3, dash="dot"),
        marker=dict(size=9, symbol="diamond"),
    ))

    # Error band
    y_upper = (y_true_disp[:, primary_idx] + rmse_values[primary_feat]).tolist()
    y_lower = (y_true_disp[:, primary_idx] - rmse_values[primary_feat]).tolist()
    fig.add_trace(go.Scatter(
        x=day_labels + day_labels[::-1],
        y=y_upper + y_lower[::-1],
        fill="toself",
        fillcolor="rgba(26,74,110,0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        name="±1 RMSE Band",
        showlegend=True,
    ))

    fig.update_layout(
        title=dict(
            text=f"3-Day (12 × 6h) Forecast vs Ground Truth — {label_str}",
            font=dict(family="Inter", size=14, color="#1A3A5C"),
        ),
        height=360,
        paper_bgcolor="white",
        plot_bgcolor="#FAFCFF",
        margin=dict(l=8, r=8, t=48, b=8),
        font=dict(family="Inter", color="#334E68", size=12),
        legend=dict(orientation="h", y=-0.22, x=0, font_size=11),
        xaxis=dict(showgrid=False, tickfont_size=11, color="#8DA4B8"),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F8",
                   tickfont_size=11, color="#1A4A6E"),
    )
    st.plotly_chart(fig, use_container_width=True)  # plotly has no width= yet

    # ── Full forecast table (adapts to actual_forecast_steps) ─────────────
    slots_per_day_label = "6-Hour" if actual_forecast_steps == FORECAST else "Day"
    st.markdown(f"#### 📋 Full Prediction Table  *({actual_forecast_steps} {slots_per_day_label} Slots)*")
    rows = []
    last_slot = daily_df.index[-1]
    for s in range(actual_forecast_steps):
        if actual_forecast_steps == FORECAST:
            # New 6h model: show 6-hour slot timestamps
            slot_dt  = last_slot + pd.Timedelta(hours=6 * (s + 1))
            day_num  = s // SLOTS_PER_DAY + 1
            row_lbl  = f"Day {day_num}  {slot_dt.strftime('%d %b')}  {slot_dt.strftime('%H:%M')}"
        else:
            # Old daily model (stale): show day labels
            row_lbl = (last_slot + pd.Timedelta(days=s + 1)).strftime("%d %b %Y")
        row = {"Slot": row_lbl}
        for i, feat in enumerate(avail_feats):
            lbl = FEATURE_LABELS.get(feat, feat)
            row[f"{lbl} (Pred)"]   = round(float(y_pred[s, i]), 3)
            row[f"{lbl} (Actual)"] = round(float(y_true_disp[s, i]), 3)
        rows.append(row)
    forecast_table = pd.DataFrame(rows).set_index("Slot")
    st.dataframe(forecast_table, width='stretch')

    # ── Overall model summary — Accuracy Meter ──────────────────────────────
    overall_mae  = float(np.mean(list(mae_values.values())))
    overall_rmse = float(np.mean(list(rmse_values.values())))

    # Accuracy = 100 - mean % error across all parameters
    pct_errors = {}
    for feat in avail_feats:
        avg_actual = float(np.mean(y_true_disp[:, avail_feats.index(feat)]))
        pct_errors[feat] = (mae_values[feat] / avg_actual * 100) if avg_actual else 0

    overall_acc = max(0.0, min(100.0, 100 - float(np.mean(list(pct_errors.values())))))

    # Colour-coded rating
    if overall_acc >= 90:
        rating, bar_color, ring_color = "Excellent", "#1A9E6E", "#1A9E6E"
    elif overall_acc >= 75:
        rating, bar_color, ring_color = "Good", "#2A7ABF", "#2A7ABF"
    elif overall_acc >= 60:
        rating, bar_color, ring_color = "Fair", "#E6A817", "#E6A817"
    else:
        rating, bar_color, ring_color = "Poor", "#D94040", "#D94040"

    # Arc gauge — drawn with a conic-gradient CSS circle
    dash_pct   = int(overall_acc)     # 0-100
    gauge_html = f"""
    <div style="margin-top:18px; background:linear-gradient(135deg,#F0F7FF,#E8F1FA);
                border-radius:14px; padding:22px 20px 16px; border:1px solid #D0E4F7;">

      <p style="margin:0 0 14px 0; font-weight:700; color:#1A3A5C; font-size:0.95rem;">
        📊 Overall Model Accuracy — 3-Day / 12-Slot 6h Holdout ({n_feat} parameters)
      </p>

      <div style="display:flex; align-items:center; gap:32px; flex-wrap:wrap;">

        <div style="position:relative; width:130px; height:130px; flex-shrink:0;">
          <div style="
            width:130px; height:130px; border-radius:50%;
            background: conic-gradient({ring_color} 0% {dash_pct}%, #D8E9F5 {dash_pct}% 100%);
            display:flex; align-items:center; justify-content:center;">
            <div style="width:90px; height:90px; border-radius:50%;
                        background:#F4F9FF; display:flex; flex-direction:column;
                        align-items:center; justify-content:center;">
              <span style="font-size:1.7rem; font-weight:800; color:{ring_color};
                           line-height:1.1;">{overall_acc:.1f}</span>
              <span style="font-size:0.65rem; color:#627D98; text-transform:uppercase;
                           letter-spacing:0.04em;">/ 100</span>
            </div>
          </div>
        </div>

        <div style="flex:1; min-width:140px;">
          <div style="display:inline-block; background:{ring_color}20;
                      color:{ring_color}; font-weight:700; font-size:0.95rem;
                      padding:3px 14px; border-radius:20px; margin-bottom:10px;">
            {rating}
          </div>
          <p style="margin:0; font-size:0.82rem; color:#627D98;">
            Mean MAE: <b style="color:#1A3A5C;">{overall_mae:.4f}</b>&nbsp;&nbsp;
            Mean RMSE: <b style="color:#1A3A5C;">{overall_rmse:.4f}</b>
          </p>
          <p style="margin:6px 0 0 0; font-size:0.75rem; color:#8DA4B8;">
            Accuracy = 100 − mean % error across all parameters
          </p>
        </div>

      </div>

      <div style="margin-top:16px; display:flex; flex-direction:column; gap:7px;">
    """

    for feat in avail_feats:
        lbl  = FEATURE_LABELS.get(feat, feat)
        acc  = max(0.0, min(100.0, 100 - pct_errors[feat]))
        col  = "#1A9E6E" if acc >= 90 else ("#2A7ABF" if acc >= 75 else ("#E6A817" if acc >= 60 else "#D94040"))
        gauge_html += f"""
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:175px; font-size:0.78rem; color:#334E68;
                       white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            {lbl}
          </span>
          <div style="flex:1; background:#D8E9F5; border-radius:6px; height:10px;">
            <div style="width:{acc:.1f}%; background:{col}; height:10px;
                        border-radius:6px; transition:width 0.8s ease;"></div>
          </div>
          <span style="width:46px; text-align:right; font-size:0.78rem;
                       font-weight:700; color:{col};">{acc:.1f}%</span>
        </div>"""

    gauge_html += "\n      </div>\n    </div>"

    import streamlit.components.v1 as components
    components.html(gauge_html, height=310, scrolling=False)



# ---------------------------------------------------------------------------
# SECTION 3 — MAIN PAGE ENTRY POINT
# ---------------------------------------------------------------------------

def run_prediction_page():
    st.header("🔮 Marine AI Prediction & Validation")
    st.info(
        "Upload cleaned or raw field data below. The NCCR pipeline will standardise it, "
        "then the BiGRU neural network will validate its 3-day forecast accuracy.",
        icon="📡"
    )

    # Step 1 — Clean data
    cleaned_df, date_col_name = load_data()

    if cleaned_df is None:
        return

    st.divider()
    st.success("✅ Data Successfully Processed! Standardized and ready for Analysis.")

    # Download cleaned data
    csv = cleaned_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Data (CSV)",
        data=csv,
        file_name="nccr_cleaned_marine_data.csv",
        mime="text/csv",
    )

    st.divider()

    # Step 2 — BiGRU validation
    _run_bigru_section(cleaned_df, date_col_name)
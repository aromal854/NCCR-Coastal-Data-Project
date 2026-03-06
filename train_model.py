# train_model.py
# Run once: python train_model.py
# Trains the BiGRU model and saves water_quality_bigru.h5

import os
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH     = os.path.join(os.path.dirname(__file__), "water_quality_bigru.h5")
FEATURES       = ['water_temp', 'ph', 'do', 'salinity', 'Chl(ug/l)']
LOOKBACK_SLOTS = 28
FORECAST_SLOTS = 12
MIN_SLOTS      = LOOKBACK_SLOTS + FORECAST_SLOTS + 120   # minimum needed (approx 40 days)

from prediction import _smart_6h_aggregate

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# ── 1. Try to load a real CSV first ───────────────────────────────────────────
def try_load_real(csv_path):
    try:
        df = pd.read_csv(csv_path)
        date_col = next(
            (c for c in df.columns
             if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()),
            None)
        if not date_col:
            return None
        df['_dt'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['_dt']).set_index('_dt').sort_index()
        avail = [f for f in FEATURES if f in df.columns]
        if not avail:
            return None
        resampled = df[avail].resample('6h').apply(_smart_6h_aggregate).ffill().dropna()
        if len(resampled) < MIN_SLOTS:
            return None
        return resampled, avail
    except Exception:
        return None

real = None
# Priority order: cleaned pipeline output first (has correct column names),
# then raw data files, then small fallbacks last.
for csv_name in [
    'nccr_data.csv',               # cleaned pipeline output (correct col names)
    'nccr_cleaned_marine_data.csv',# user-uploaded cleaned file
    'marine_data_cloud.csv',
    'Chennai_Small_Data.csv',      # last resort — short + different column names
]:
    result = try_load_real(csv_name)
    if result:
        real = result
        print(f"[OK] Using real data from: {csv_name}  ({len(real[0])} days)")
        break

# ── 2. Fallback: generate synthetic coastal time-series ───────────────────────
if real is None:
    print("[INFO] No real CSV has enough records.")
    print("[INFO] Generating 3 years of synthetic Chennai coastal data for training (6h resolution)...")

    np.random.seed(42)
    n_slots = 365 * 3 * 4   # 3 years × 4 slots per day
    dates   = pd.date_range("2021-01-01", periods=n_slots, freq="6h")
    t       = np.linspace(0, 2 * np.pi * 3, n_slots)   # 3 full annual cycles

    # Realistic coastal parameter distributions with seasonal & noise components
    water_temp = (28 + 3 * np.sin(t - 0.5)
                  + np.random.normal(0, 0.6, n_slots))              # 25–31 °C

    ph         = (8.0 + 0.3 * np.sin(t + 1.0)
                  + np.random.normal(0, 0.08, n_slots))             # 7.6–8.3

    do         = (6.5 - 0.8 * np.sin(t - 0.5)
                  + np.random.normal(0, 0.3, n_slots))              # 5.2–7.8 mg/L

    salinity   = (32.5 + 1.5 * np.sin(t + 0.8)
                  + np.random.normal(0, 0.4, n_slots))              # 30–35 psu

    chl_a      = np.abs(5 + 10 * np.sin(t + 2.0)
                        + np.random.normal(0, 3, n_slots))          # 0–50 µg/L

    # Clip to physically valid ranges
    water_temp = np.clip(water_temp, 24, 35)
    ph         = np.clip(ph, 7.4, 9.0)
    do         = np.clip(do, 4.5, 10.0)
    salinity   = np.clip(salinity, 28, 37)
    chl_a      = np.clip(chl_a, 0.1, 80)

    daily_data = pd.DataFrame({
        'Water_Temp': water_temp,
        'pH':         ph,
        'DO':         do,
        'Salinity':   salinity,
        'Chl(ug/l)':  chl_a,
    }, index=dates)

    avail_feats = FEATURES
    resampled   = daily_data
    print(f"[OK] Synthetic dataset: {len(resampled)} slots, {len(avail_feats)} features")
else:
    resampled, avail_feats = real

n_feat = len(avail_feats)
print(f"[INFO] Features ({n_feat}): {avail_feats}")

# ── 3. Scale ──────────────────────────────────────────────────────────────────
scaler      = MinMaxScaler()
scaled_data = scaler.fit_transform(resampled.values)

# ── 4. Sliding window ─────────────────────────────────────────────────────────
X, y = [], []
for i in range(LOOKBACK_SLOTS, len(scaled_data) - FORECAST_SLOTS + 1):
    X.append(scaled_data[i - LOOKBACK_SLOTS : i])
    y.append(scaled_data[i : i + FORECAST_SLOTS])

X = np.array(X)
y = np.array(y)
print(f"🧮 X: {X.shape}  |  y: {y.shape}")

# ── 5. Build BiGRU ────────────────────────────────────────────────────────────
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Bidirectional, GRU, Dense, Dropout, Reshape, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

tf.get_logger().setLevel('ERROR')

model = Sequential([
    Input(shape=(LOOKBACK_SLOTS, n_feat)),
    Bidirectional(GRU(64, return_sequences=True)),
    Dropout(0.2),
    Bidirectional(GRU(32)),
    Dropout(0.2),
    Dense(FORECAST_SLOTS * n_feat, activation='linear'),
    Reshape((FORECAST_SLOTS, n_feat)),
])
model.compile(optimizer='adam', loss='mae', metrics=['mse'])
model.summary()

# ── 6. Train ──────────────────────────────────────────────────────────────────
callbacks = [
    EarlyStopping(monitor='val_loss', patience=12, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-5, verbose=1),
]

print("\n[START] Training BiGRU...")
history = model.fit(
    X, y,
    epochs=100,
    batch_size=32,
    validation_split=0.15,
    callbacks=callbacks,
    verbose=1,
)

# ── 7. Save ───────────────────────────────────────────────────────────────────
model.save(MODEL_PATH)
val_loss = min(history.history['val_loss'])
print(f"\n[OK] Model saved -> {MODEL_PATH}")
print(f"[LOSS] Best validation MAE: {val_loss:.5f}")
print("[DONE] Refresh the Streamlit app and upload a CSV to test prediction.")

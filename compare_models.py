"""
compare_models.py  (v2 - UTF-8 safe, writes output directly to file)
"""
import sys, os, io, time, warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

OUT_PATH = r"c:\Users\arjun\Desktop\Marine_Project\compare_results.txt"
_log = open(OUT_PATH, "w", encoding="utf-8")

def p(*args, **kw):
    msg = " ".join(str(a) for a in args)
    _log.write(msg + "\n")
    _log.flush()

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ── 1. LOAD DATA ──────────────────────────────────────────────────────────────
p("=" * 65)
p("NCCR Marine Portal -- Model Comparison Study")
p("Dataset: Chennai_2019-2024.xlsx")
p("=" * 65)

DATA_PATH = r"c:\Users\arjun\Desktop\Marine_Project\Chennai_2019-2024.xlsx"
df_raw = pd.read_excel(DATA_PATH)

p(f"\n[DATA] Raw shape: {df_raw.shape}")
p(f"[DATA] Columns:")
for c in df_raw.columns:
    nn = df_raw[c].notna().sum()
    p(f"       {str(c)!r:50s}  dtype={str(df_raw[c].dtype):10s}  {nn}/{len(df_raw)} non-null")

# ── 2. NCCR PREPROCESSING PIPELINE ───────────────────────────────────────────
df = df_raw.copy()
df = df.replace(['BTL', 'BDL', 'btl', 'bdl', '<1', '-'], np.nan)

# Identify date column
date_col = next((c for c in df.columns
                 if any(k in str(c).lower() for k in ['date', 'time', 'timestamp'])), None)
p(f"\n[PREP] Date column: {date_col!r}")

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Physics quarantine
ph_col   = next((c for c in df.columns if str(c).lower() in ['ph', 'p.h.', 'ph level'] or str(c).lower() == 'ph'), None)
if not ph_col:
    ph_col = next((c for c in df.columns if 'ph' in str(c).lower() and len(str(c)) < 6), None)
if ph_col:
    df.loc[(df[ph_col] < 6) | (df[ph_col] > 10), ph_col] = np.nan

temp_col = next((c for c in df.columns if 'water' in str(c).lower() and 'temp' in str(c).lower()), None)
if not temp_col:
    temp_col = next((c for c in df.columns if 'temp' in str(c).lower() and 'air' not in str(c).lower()), None)
if temp_col:
    df.loc[df[temp_col] > 40, temp_col] = np.nan

sal_col  = next((c for c in df.columns if 'sal' in str(c).lower()), None)
if sal_col:
    df.loc[df[sal_col] < 0.5, sal_col] = np.nan

do_col   = next((c for c in df.columns
                 if str(c).lower() == 'do'
                 or ('oxygen' in str(c).lower() and 'dissolved' in str(c).lower())
                 or (str(c).lower().startswith('do') and len(str(c)) < 5)), None)
if do_col:
    df.loc[df[do_col] < 0, do_col] = np.nan

chl_col  = next((c for c in df.columns
                 if 'chl' in str(c).lower() or 'chlorophyll' in str(c).lower()), None)

# Feature selection: use detected columns + others with >50% coverage
core = [c for c in [temp_col, ph_col, sal_col, do_col, chl_col] if c is not None and c in df.columns]
extra = [c for c in df.columns
         if c not in core
         and df[c].dtype in [np.float64, np.int64, 'float32', 'int32']
         and df[c].notna().mean() > 0.5]

FEATURES = core + extra[:max(0, 8 - len(core))]   # cap at 8 total
p(f"\n[PREP] Features ({len(FEATURES)}): {FEATURES}")

# Daily resample + 3-tier imputation
daily = df[FEATURES].resample('D').mean()
daily = daily.interpolate(method='time', limit=6)
for days in [1, 2, 3, 4]:
    daily = daily.fillna(daily.shift(periods=days, freq='D'))
for col in daily.columns:
    if daily[col].isnull().any():
        sm = daily.groupby([daily.index.month, daily.index.hour])[col].transform('mean')
        daily[col] = daily[col].fillna(sm)
daily = daily.ffill().bfill().dropna()

p(f"[PREP] Daily records after pipeline: {len(daily)} days  ({daily.index.min().date()} to {daily.index.max().date()})")

# log1p transform for Chlorophyll
if chl_col and chl_col in daily.columns:
    daily[chl_col] = np.log1p(daily[chl_col].clip(lower=0))
    p(f"[PREP] log1p applied to Chlorophyll: {chl_col!r}")

# ── 3. SEQUENCE BUILDER ───────────────────────────────────────────────────────
LOOKBACK = 7
FORECAST = 3
n_feat   = len(FEATURES)

scaler = MinMaxScaler()
scaled = scaler.fit_transform(daily.values)

X_all, y_all = [], []
for i in range(LOOKBACK, len(scaled) - FORECAST + 1):
    X_all.append(scaled[i - LOOKBACK : i])
    y_all.append(scaled[i : i + FORECAST].flatten())

X_all = np.array(X_all)
y_all = np.array(y_all)

split = int(len(X_all) * 0.80)
X_train, X_test = X_all[:split], X_all[split:]
y_train, y_test = y_all[:split], y_all[split:]

p(f"\n[SPLIT] Train: {len(X_train)} samples | Test: {len(X_test)} samples")

X_train_flat = X_train.reshape(len(X_train), -1)
X_test_flat  = X_test.reshape(len(X_test),  -1)

# ── 4. SCORING FUNCTION ───────────────────────────────────────────────────────
def score(y_true_s, y_pred_s, label, elapsed):
    yt = y_true_s.reshape(-1, FORECAST, n_feat)
    yp = y_pred_s.reshape(-1, FORECAST, n_feat)

    yt_inv = np.stack([scaler.inverse_transform(yt[:, d, :]) for d in range(FORECAST)], axis=1)
    yp_inv = np.stack([scaler.inverse_transform(yp[:, d, :]) for d in range(FORECAST)], axis=1)

    if chl_col and chl_col in FEATURES:
        ci = FEATURES.index(chl_col)
        yt_inv[:, :, ci] = np.expm1(np.clip(yt_inv[:, :, ci], 0, None))
        yp_inv[:, :, ci] = np.expm1(np.clip(yp_inv[:, :, ci], 0, None))

    ft = yt_inv.reshape(-1, n_feat)
    fp = yp_inv.reshape(-1, n_feat)

    mae_p  = [mean_absolute_error(ft[:, i], fp[:, i]) for i in range(n_feat)]
    rmse_p = [np.sqrt(mean_squared_error(ft[:, i], fp[:, i])) for i in range(n_feat)]
    denom  = np.abs(ft); denom[denom < 1e-6] = 1e-6
    mape_p = [np.mean(np.abs((ft[:, i]-fp[:, i])/denom[:, i]))*100 for i in range(n_feat)]

    avg_mae  = float(np.mean(mae_p))
    avg_rmse = float(np.mean(rmse_p))
    avg_mape = float(np.mean(mape_p))
    avg_acc  = max(0.0, 100.0 - avg_mape)

    p(f"\n  [{label}]")
    p(f"  Train time  : {elapsed:.1f}s")
    p(f"  Avg MAE     : {avg_mae:.4f}")
    p(f"  Avg RMSE    : {avg_rmse:.4f}")
    p(f"  Avg MAPE    : {avg_mape:.2f}%")
    p(f"  Accuracy    : {avg_acc:.1f}%")
    p(f"  Per-parameter:")
    for i, feat in enumerate(FEATURES):
        p(f"    {str(feat):40s}  MAE={mae_p[i]:.4f}  RMSE={rmse_p[i]:.4f}  MAPE={mape_p[i]:.2f}%")

    return {"Model": label,
            "Avg MAE": round(avg_mae,4),
            "Avg RMSE": round(avg_rmse,4),
            "Avg MAPE (%)": round(avg_mape,2),
            "Accuracy (%)": round(avg_acc,1),
            "Train Time (s)": round(elapsed,1)}

results = []

# ── 5. LINEAR REGRESSION ─────────────────────────────────────────────────────
p("\n" + "-"*65 + "\nMODEL 1/5: Linear Regression")
t0 = time.time()
lr = LinearRegression()
lr.fit(X_train_flat, y_train)
pred_lr = lr.predict(X_test_flat)
results.append(score(y_test, pred_lr, "Linear Regression", time.time()-t0))

# ── 6. RANDOM FOREST ─────────────────────────────────────────────────────────
p("\n" + "-"*65 + "\nMODEL 2/5: Random Forest (100 trees)")
t0 = time.time()
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train_flat, y_train)
pred_rf = rf.predict(X_test_flat)
results.append(score(y_test, pred_rf, "Random Forest", time.time()-t0))

# ── 7. DEEP LEARNING MODELS ───────────────────────────────────────────────────
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

y_train_dl = y_train.reshape(-1, FORECAST, n_feat)

n_samples = len(X_train)
EPOCHS    = 300
BATCH     = 32

p(f"\n[DL] epochs={EPOCHS}  batch={BATCH}  n_feat={n_feat}")

callbacks = [
    tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=40,
                                     restore_best_weights=True, verbose=0),
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                         patience=10, min_lr=1e-6, verbose=0),
]

def build_and_train(arch):
    inp = tf.keras.Input(shape=(LOOKBACK, n_feat))
    if arch == "LSTM":
        x = tf.keras.layers.LSTM(64, return_sequences=True)(inp)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.LSTM(32)(x)
        x = tf.keras.layers.Dropout(0.2)(x)
    elif arch == "GRU":
        x = tf.keras.layers.GRU(64, return_sequences=True)(inp)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.GRU(32)(x)
        x = tf.keras.layers.Dropout(0.2)(x)
    else:  # BiGRU
        x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(64, return_sequences=True, kernel_regularizer=tf.keras.regularizers.l2(1e-5)))(inp)
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(32, kernel_regularizer=tf.keras.regularizers.l2(1e-5)))(x)
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        
    out = tf.keras.layers.Dense(FORECAST * n_feat)(x)
    out = tf.keras.layers.Reshape((FORECAST, n_feat))(out)
    m = tf.keras.Model(inp, out)
    
    if arch == "BiGRU":
        m.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mae')
    else:
        m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mae')
    t0 = time.time()
    hist = m.fit(X_train, y_train_dl,
                 epochs=EPOCHS, batch_size=BATCH,
                 validation_split=0.15,
                 callbacks=callbacks, verbose=0)
    elapsed = time.time() - t0
    p(f"  Epochs run: {len(hist.history['loss'])}  Final val_loss: {hist.history['val_loss'][-1]:.6f}")
    pred = m.predict(X_test, verbose=0).reshape(len(X_test), -1)
    return pred, elapsed

for arch_name in ["LSTM", "GRU", "BiGRU"]:
    idx = {"LSTM":3,"GRU":4,"BiGRU":5}[arch_name]
    p(f"\n{'-'*65}\nMODEL {idx}/5: {arch_name}")
    pred_dl, elapsed = build_and_train(arch_name)
    results.append(score(y_test, pred_dl, arch_name, elapsed))

# ── 8. SUMMARY TABLE ─────────────────────────────────────────────────────────
p("\n" + "="*65)
p("FINAL COMPARISON TABLE")
p("="*65)
res_df = pd.DataFrame(results).sort_values("Avg RMSE")
p(res_df.to_string(index=False))

# RMSE reduction vs LR
lr_rmse = float(res_df[res_df["Model"]=="Linear Regression"]["Avg RMSE"].iloc[0])
p("\nRMSE Improvement over Linear Regression baseline:")
for _, row in res_df.iterrows():
    if row["Model"] != "Linear Regression":
        pct = (lr_rmse - row["Avg RMSE"]) / lr_rmse * 100
        p(f"  {str(row['Model']):20s}  {pct:+.1f}%")

p(f"\n[DONE] Results saved to {OUT_PATH}")
_log.close()
print("DONE - check compare_results.txt")

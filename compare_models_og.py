"""
compare_models_og.py  — runs on Chennai_2019-2024(OG).xlsx (5-year full dataset)
All output written to compare_results_og.txt (UTF-8 safe)
"""
import sys, os, io, time, warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

OUT = r"C:\Users\arjun\Desktop\Marine_Project\compare_results_og.txt"
_f  = open(OUT, "w", encoding="utf-8")
def p(*a): _f.write(" ".join(str(x) for x in a) + "\n"); _f.flush()

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ── 1. LOAD ───────────────────────────────────────────────────────────────────
DATA = r"C:\Users\arjun\Desktop\Marine_Project\Chennai_2019-2024(OG).xlsx"
p("=" * 65)
p("NCCR Marine Portal -- Model Comparison (OG Dataset)")
p(f"File: Chennai_2019-2024(OG).xlsx")
p("=" * 65)

df = pd.read_excel(DATA)
p(f"\n[DATA] Raw shape: {df.shape}")
p(f"[DATA] Date range: {df.iloc[0,0]} to {df.iloc[-1,0]}")
for c in df.columns:
    p(f"  {str(c)!r:50s}  {str(df[c].dtype):12s}  {df[c].notna().sum()}/{len(df)}")

# ── 2. NCCR PIPELINE ──────────────────────────────────────────────────────────
# Replace text flags
df = df.replace(['BTL','BDL','btl','bdl','<1','-'], np.nan)

# Date index
date_col = 'Date and Time'
df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()

# Numeric coercion
for c in df.columns:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# Physics quarantine
if 'pH' in df.columns:
    df.loc[(df['pH'] < 6) | (df['pH'] > 10), 'pH'] = np.nan

wq_temp = 'WQ Temp (°C)'
if wq_temp in df.columns:
    df.loc[df[wq_temp] > 40, wq_temp] = np.nan

sal = 'Sal (psu)'
if sal in df.columns:
    df.loc[df[sal] < 0.5, sal] = np.nan

do_c = 'Dissolved Oxygen (mg/L)'
if do_c in df.columns:
    df.loc[df[do_c] < 0, do_c] = np.nan

chl = 'Chl(ug/l)'

# Drop dead-sensor columns (all zero)
for c in list(df.columns):
    if df[c].notna().sum() > 0 and (df[c].dropna() == 0).all():
        p(f"[PREP] Dropped dead sensor: {c!r}")
        df.drop(columns=[c], inplace=True)

# Core WQ features only (keeps model focused on oceanographic params)
CORE_FEATS = [wq_temp, 'pH', sal, do_c, chl]
FEATURES   = [f for f in CORE_FEATS if f in df.columns]
p(f"\n[PREP] Core WQ features used: {FEATURES}")

# Daily resample
daily = df[FEATURES].resample('D').mean()

# 3-tier imputation
daily = daily.interpolate(method='time', limit=6)
for d in [1,2,3,4]:
    daily = daily.fillna(daily.shift(periods=d, freq='D'))
for c in daily.columns:
    if daily[c].isnull().any():
        sm = daily.groupby([daily.index.month, daily.index.hour])[c].transform('mean')
        daily[c] = daily[c].fillna(sm)
daily = daily.ffill().bfill().dropna()

p(f"[PREP] Daily records: {len(daily)} ({daily.index.min().date()} to {daily.index.max().date()})")

# log1p for Chlorophyll
if chl in daily.columns:
    daily[chl] = np.log1p(daily[chl].clip(lower=0))
    p(f"[PREP] log1p applied to Chlorophyll")

# ── 3. SEQUENCES ──────────────────────────────────────────────────────────────
LOOKBACK = 7
FORECAST = 3
n_feat   = len(FEATURES)

scaler = MinMaxScaler()
scaled = scaler.fit_transform(daily.values)

X_all, y_all = [], []
for i in range(LOOKBACK, len(scaled) - FORECAST + 1):
    X_all.append(scaled[i-LOOKBACK:i])
    y_all.append(scaled[i:i+FORECAST].flatten())

X_all = np.array(X_all)
y_all = np.array(y_all)

split = int(len(X_all) * 0.80)
X_tr, X_te = X_all[:split], X_all[split:]
y_tr, y_te = y_all[:split], y_all[split:]

p(f"\n[SPLIT] Train: {len(X_tr)} | Test: {len(X_te)}")

X_tr_f = X_tr.reshape(len(X_tr), -1)
X_te_f = X_te.reshape(len(X_te), -1)

# ── 4. SCORING ────────────────────────────────────────────────────────────────
def score(yt_s, yp_s, label, elapsed):
    yt = yt_s.reshape(-1, FORECAST, n_feat)
    yp = yp_s.reshape(-1, FORECAST, n_feat)
    yt_inv = np.stack([scaler.inverse_transform(yt[:,d,:]) for d in range(FORECAST)], 1)
    yp_inv = np.stack([scaler.inverse_transform(yp[:,d,:]) for d in range(FORECAST)], 1)
    if chl in FEATURES:
        ci = FEATURES.index(chl)
        yt_inv[:,:,ci] = np.expm1(np.clip(yt_inv[:,:,ci], 0, None))
        yp_inv[:,:,ci] = np.expm1(np.clip(yp_inv[:,:,ci], 0, None))
    ft = yt_inv.reshape(-1, n_feat)
    fp = yp_inv.reshape(-1, n_feat)

    mae_p  = [mean_absolute_error(ft[:,i], fp[:,i]) for i in range(n_feat)]
    rmse_p = [np.sqrt(mean_squared_error(ft[:,i], fp[:,i])) for i in range(n_feat)]
    denom  = np.abs(ft); denom[denom<1e-6] = 1e-6
    mape_p = [np.mean(np.abs((ft[:,i]-fp[:,i])/denom[:,i]))*100 for i in range(n_feat)]

    avg_mae  = float(np.mean(mae_p))
    avg_rmse = float(np.mean(rmse_p))
    avg_mape = float(np.mean(mape_p))
    # Only core WQ mape for accuracy (exclude mete params)
    wq_mape  = float(np.mean(mape_p))
    avg_acc  = max(0.0, 100.0 - wq_mape)

    p(f"\n  [{label}]  train_time={elapsed:.1f}s")
    p(f"  Avg MAE={avg_mae:.4f}  RMSE={avg_rmse:.4f}  MAPE={avg_mape:.2f}%  Acc={avg_acc:.1f}%")
    for i, feat in enumerate(FEATURES):
        p(f"    {str(feat):40s}  MAE={mae_p[i]:.4f}  RMSE={rmse_p[i]:.4f}  MAPE={mape_p[i]:.2f}%")

    return {"Model":label,
            "Avg_MAE":round(avg_mae,4),
            "Avg_RMSE":round(avg_rmse,4),
            "Avg_MAPE":round(avg_mape,2),
            "Accuracy":round(avg_acc,1),
            "Train_s":round(elapsed,1),
            **{f"MAE_{f.split('(')[0].strip()}":round(mae_p[i],4) for i,f in enumerate(FEATURES)},
            **{f"RMSE_{f.split('(')[0].strip()}":round(rmse_p[i],4) for i,f in enumerate(FEATURES)},
            **{f"MAPE_{f.split('(')[0].strip()}":round(mape_p[i],2) for i,f in enumerate(FEATURES)}}

results = []

# ── 5. LR ─────────────────────────────────────────────────────────────────────
p("\n" + "-"*65 + "\nMODEL 1/5: Linear Regression (Baseline)")
t0 = time.time()
lr = LinearRegression(); lr.fit(X_tr_f, y_tr)
results.append(score(y_te, lr.predict(X_te_f), "Linear Regression", time.time()-t0))

# ── 6. RF ─────────────────────────────────────────────────────────────────────
p("\n" + "-"*65 + "\nMODEL 2/5: Random Forest (100 trees)")
t0 = time.time()
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_tr_f, y_tr)
results.append(score(y_te, rf.predict(X_te_f), "Random Forest", time.time()-t0))

# ── 7. DL MODELS ──────────────────────────────────────────────────────────────
import tensorflow as tf; tf.get_logger().setLevel('ERROR')
y_tr_dl = y_tr.reshape(-1, FORECAST, n_feat)

n_s    = len(X_tr)
EPOCHS = min(300, max(100, n_s // 4))
BATCH  = min(64, max(16, n_s // 20))
p(f"\n[DL] epochs_max={EPOCHS}  batch={BATCH}  n_feat={n_feat}  train_samples={n_s}")

cbs = [tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=25,
                                         restore_best_weights=True, verbose=0),
       tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                             patience=10, min_lr=1e-6, verbose=0)]

def make_model(arch):
    inp = tf.keras.Input(shape=(LOOKBACK, n_feat))
    if arch == "LSTM":
        x = tf.keras.layers.LSTM(64, return_sequences=True)(inp)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.LSTM(32)(x)
    elif arch == "GRU":
        x = tf.keras.layers.GRU(64, return_sequences=True)(inp)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.GRU(32)(x)
    else:
        x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(64, return_sequences=True))(inp)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(32))(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    x = tf.keras.layers.Dense(FORECAST * n_feat)(x)
    out = tf.keras.layers.Reshape((FORECAST, n_feat))(x)
    m = tf.keras.Model(inp, out)
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mae')
    return m

for arch, idx in [("LSTM",3), ("GRU",4), ("BiGRU",5)]:
    p(f"\n{'-'*65}\nMODEL {idx}/5: {arch}")
    tf.keras.backend.clear_session()
    m = make_model(arch)
    t0 = time.time()
    hist = m.fit(X_tr, y_tr_dl, epochs=EPOCHS, batch_size=BATCH,
                 validation_split=0.15, callbacks=cbs, verbose=0)
    elapsed = time.time()-t0
    ep_ran = len(hist.history['loss'])
    p(f"  Epochs: {ep_ran}  val_loss: {hist.history['val_loss'][-1]:.6f}")
    results.append(score(y_te, m.predict(X_te, verbose=0).reshape(len(X_te),-1), arch, elapsed))

# ── 8. SUMMARY ────────────────────────────────────────────────────────────────
p("\n" + "="*65)
p("FINAL COMPARISON TABLE")
p("="*65)
rdf = pd.DataFrame(results)
p(rdf[["Model","Avg_MAE","Avg_RMSE","Avg_MAPE","Accuracy","Train_s"]].to_string(index=False))

p("\nPer-parameter MAE:")
cols_mae = [c for c in rdf.columns if c.startswith("MAE_")]
p(rdf[["Model"]+cols_mae].to_string(index=False))

p("\nPer-parameter RMSE:")
cols_rmse = [c for c in rdf.columns if c.startswith("RMSE_")]
p(rdf[["Model"]+cols_rmse].to_string(index=False))

p("\nPer-parameter MAPE (%):")
cols_mape = [c for c in rdf.columns if c.startswith("MAPE_")]
p(rdf[["Model"]+cols_mape].to_string(index=False))

lr_rmse = float(rdf[rdf["Model"]=="Linear Regression"]["Avg_RMSE"].iloc[0])
p("\nRMSE change vs Linear Regression:")
for _, r in rdf.iterrows():
    if r["Model"] != "Linear Regression":
        pct = (lr_rmse - r["Avg_RMSE"]) / lr_rmse * 100
        p(f"  {str(r['Model']):20s}  {pct:+.1f}%")

p(f"\n[DONE] Saved to {OUT}")
_f.close()
print("DONE")

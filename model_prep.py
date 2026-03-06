import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

from prediction import _smart_6h_aggregate

def prep_data_for_dl(csv_path):
    # 1. Load the cleaned data
    df = pd.read_csv(csv_path)
    
    # Ensure Date and Time are properly formatted as datetime index
    df['date_time'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.set_index('date_time')

    # 2. RESAMPLE: Convert high-frequency data into 6-Hour Windows
    # Select numeric features relevant for prediction
    features = ['Water_Temp', 'pH', 'DO', 'Salinity', 'Turbidity']
    
    # Filter only columns that exist in the CSV to avoid KeyError
    available_features = [f for f in features if f in df.columns]
    
    # Resample to 6-hour frequency and apply smart domain aggregation
    resampled_df = df[available_features].resample('6h').apply(_smart_6h_aggregate)
    
    # Forward-fill any empty slots (e.g., if sensors were down)
    resampled_df = resampled_df.ffill().dropna()

    # 3. SCALE: Normalize values between 0 and 1
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(resampled_df)

    # 4. TRANSFORM: Create the 3D Sliding Window
    X, y = [], []
    lookback_slots = 28
    forecast_slots = 12

    for i in range(lookback_slots, len(scaled_data) - forecast_slots + 1):
        X.append(scaled_data[i - lookback_slots : i])      # Past 28 slots (7 days)
        y.append(scaled_data[i : i + forecast_slots])      # Next 12 slots (3 days)

    X = np.array(X)
    y = np.array(y)

    return X, y, scaler, available_features

# Add a test execution block
if __name__ == "__main__":
    if os.path.exists("nccr_data.csv"):
        X, y, scaler, cols = prep_data_for_dl("nccr_data.csv")
        print(f"Data Prepped Successfully!")
        print(f"Using Features: {cols}")
        print(f"Input Shape (X): {X.shape}") 
        print(f"Target Shape (y): {y.shape}")
    else:
        print("❌ Waiting for nccr_data.csv to be generated... Please ensure the file exists.")

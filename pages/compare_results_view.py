import streamlit as st
import pandas as pd
import io

# Data loaded manually from compare_results_og.txt output
data = {
    "Model": ["Linear Regression", "Random Forest", "LSTM", "GRU", "BiGRU"],
    "Avg_MAE": [1.0399, 1.4996, 1.1086, 2.3547, 2.7460],
    "Avg_RMSE": [2.4241, 2.9721, 2.5701, 3.9405, 4.3696],
    "Avg_MAPE": [13.12, 17.69, 13.71, 23.16, 26.98],
    "Accuracy": [86.9, 82.3, 86.3, 76.8, 73.0],
    "Train_s": [0.0, 0.4, 33.9, 10.2, 14.8]
}

df_results = pd.DataFrame(data)

st.set_page_config(page_title="Model Comparison Results", layout="wide")

st.markdown(
    """
    <div class="nccr-hero" style="margin-top:14px;">
        <div class="nccr-section-label">Models</div>
        <div style="display:flex; gap:12px; align-items:flex-start;">
            <span class="material-symbols-rounded nccr-icon">analytics</span>
            <div>
                <h2 style="margin:0;">Model Comparison Results (OG Dataset)</h2>
                <p class="nccr-card-subtitle" style="margin-top:6px;">
                    Results based on the 5-year full dataset <code>Chennai_2019-2024(OG).xlsx</code>.
                </p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 🏆 Final Comparison Table")
st.dataframe(df_results, use_container_width=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 📉 Per-parameter MAE")
    mae_data = {
        "Model": ["Linear Regression", "Random Forest", "LSTM", "GRU", "BiGRU"],
        "WQ Temp": [0.3121, 0.4431, 0.3309, 0.7547, 1.0505],
        "pH": [0.0623, 0.1129, 0.0757, 0.2398, 0.4205],
        "Salinity": [1.3602, 2.0624, 1.4550, 4.8569, 4.9069],
        "Dissolved Oxygen": [0.4852, 0.9782, 0.5272, 1.3152, 1.7534],
        "Chlorophyll": [2.9800, 3.9014, 3.1543, 4.6069, 5.5989]
    }
    st.dataframe(pd.DataFrame(mae_data), use_container_width=True)

with col2:
    st.markdown("### 📉 Per-parameter RMSE")
    rmse_data = {
        "Model": ["Linear Regression", "Random Forest", "LSTM", "GRU", "BiGRU"],
        "WQ Temp": [0.4704, 0.6249, 0.4887, 0.9739, 1.3062],
        "pH": [0.1243, 0.1676, 0.1444, 0.3092, 0.6168],
        "Salinity": [3.1612, 3.4715, 3.3821, 6.1012, 6.8082],
        "Dissolved Oxygen": [0.7506, 1.4822, 0.7862, 1.6360, 2.1936],
        "Chlorophyll": [7.6138, 9.1143, 8.0490, 10.6823, 10.9231]
    }
    st.dataframe(pd.DataFrame(rmse_data), use_container_width=True)


st.markdown("### 📊 RMSE Change vs Linear Regression")
rmse_change_data = {
    "Model": ["Random Forest", "LSTM", "GRU", "BiGRU"],
    "Change (%)": ["-22.6%", "-6.0%", "-62.6%", "-80.3%"]
}
st.table(pd.DataFrame(rmse_change_data))

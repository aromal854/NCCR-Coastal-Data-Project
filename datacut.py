import pandas as pd

# 1. വലിയ ഫയൽ ലോഡ് ചെയ്യുക
df = pd.read_excel("Chennai_2019-2024.xlsx")

# 2. പകുതി ഡേറ്റ മാത്രം എടുക്കുക (ആദ്യത്തെ 50%)
half_count = len(df) // 20
df_small = df.iloc[:half_count]

# 3. പുതിയ ഫയലായി സേവ് ചെയ്യുക (CSV ആണെങ്കിൽ കൂടുതൽ വേഗത്തിൽ ലോഡ് ആകും)
df_small.to_csv("Chennai_Small_Data.csv", index=False)

print("Done! Small file created.")
import sys
import os

# Add the project directory to path so we can import modules
sys.path.append(r"c:\Users\arjun\Desktop\Marine_Project")

import pandas as pd
import database as db
import math

PENDING_CSV = r"c:\Users\arjun\Desktop\Marine_Project\pending_verification.csv"

def test_verify():
    print("Testing verification pipeline...")
    if not os.path.exists(PENDING_CSV):
        print("No pending file found.")
        return
        
    df = pd.read_csv(PENDING_CSV)
    if df.empty:
        print("Pending CSV is empty.")
        return
        
    # Fake verification process
    batch = df.copy()
    prof_tag = "Prof. Test (Test University)"
    batch['verified_by'] = prof_tag
    
    raw_data_list = batch.to_dict(orient='records')
    clean_data_list = []
    
    print(f"Loaded {len(raw_data_list)} records.")
    
    # 1. Simulate exact cleanup loop from verify_page.py
    for row in raw_data_list:
        clean_row = {}
        for k, v in row.items():
            if k in ['prof_email', 'prof_name', 'university', 'status', 'request_id']:
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean_row[k] = None
            elif pd.isna(v): 
                clean_row[k] = None
            else:
                clean_row[k] = v
        clean_data_list.append(clean_row)
        
    print("Sample cleaned row before DB map:")
    sample = clean_data_list[0]
    for k, v in sample.items():
        if v is not None:
             print(f"  {k}: {v} ({type(v)})")
             
             
    # 2. Simulate save_bulk_data logic directly
    print("\nMapping keys...")
    mapped_list = [db.map_keys_to_db(row) for row in clean_data_list]
    
    print("\nAttempting Supabase Insert...")
    try:
        if db.supabase:
            print("Supabase connected.")
            # Trigger raw insert to catch exact error
            res = db.supabase.table("marine_data").insert(mapped_list[:2]).execute()
            print("Insert seemingly successful:")
            print(res)
        else:
            print("Supabase connection failed.")
    except Exception as e:
        print(f"\n+++ DETAILED SUPABASE EXCEPTION CAUGHT +++")
        print(e)
        
if __name__ == "__main__":
    test_verify()


import pandas as pd
import database as db
import config

print("🚀 Starting Data Coordinate Correction...")

# 1. Fetch All Data (Raw DB Column Names are lowercase)
df = db.fetch_all_data()

if df.empty:
    print("❌ No data found to update.")
    exit()

print(f"📊 Found {len(df)} records.")

# 2. Iterate and Update
updated_count = 0

for index, row in df.iterrows():
    record_id = row['id']
    
    # "Main_Location" comes from fetch_all_data's renaming logic.
    # It might be simple "Chennai Coast" or composite "Tamil Nadu - Chennai Coast" if logic varied.
    # Let's try to match it against config.REGION_COORDS keys.
    
    current_loc = row.get('Main_Location')
    
    if not current_loc:
        continue
        
    found_coords = None
    
    # Direct Match
    if current_loc in config.REGION_COORDS:
        found_coords = config.REGION_COORDS[current_loc]
    else:
        # Partial Match (e.g. "Tamil Nadu - Chennai Coast")
        for key in config.REGION_COORDS.keys():
            if key in current_loc:
                found_coords = config.REGION_COORDS[key]
                break
    
    if found_coords:
        lat, lon = found_coords
        
        # Only update if the current values are the Default Chennai values (approx)
        # 13.0827, 80.2707. Let's send updates regardless to be sure?
        # Better to update all to be consistent with the map view request.
        
        try:
            # Need to update using RAW DB column names (lowercase)
            data = {"latitude": lat, "longitude": lon}
            db.supabase.table("marine_data").update(data).eq("id", record_id).execute()
            updated_count += 1
            print(f"✅ Updated ID {record_id}: {current_loc} -> {lat}, {lon}")
        except Exception as e:
            print(f"❌ Failed to update ID {record_id}: {e}")

print(f"🎉 Process Complete. Updated {updated_count} records.")

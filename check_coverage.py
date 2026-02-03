
import config

print("🔍 Checking Coordinate Coverage...")

missing = []
total = 0
covered = 0

for state, regions in config.COASTAL_DATA.items():
    for region in regions:
        if region == "Other": continue
        total += 1
        # Check direct match or partial match
        if region in config.REGION_COORDS:
            covered += 1
        else:
            # Check if we have a coordinate entry that is a substring? 
            # (Dashboard logic uses direct lookup usually)
            missing.append(f"{state}: {region}")

print(f"✅ Covered: {covered}/{total}")
if missing:
    print("❌ Missing Coordinates for:")
    for m in missing:
        print(f" - {m}")
else:
    print("🌟 100% Coverage achieved.")

# config.py
# --- CONFIGURATION & CONSTANTS ---

# Email Credentials
SENDER_EMAIL = "aromalvasanth1038@gmail.com" 
SENDER_PASSWORD = "roou arbj jlmj jlye" 

# Certificate Settings
CERTIFICATE_THRESHOLD = 5 

# --- CENTRALIZED LOCATION DATA ---
COASTAL_DATA = {
    "Kerala": ["Thiruvananthapuram Coast", "Kollam Coast", "Alappuzha Coast", "Kochi (Ernakulam) Coast", "Thrissur Coast", "Malappuram Coast", "Kozhikode Coast", "Kannur Coast", "Kasargod Coast", "Other"],
    "Tamil Nadu": ["Chennai Coast", "Thiruvallur Coast", "Kancheepuram Coast", "Villupuram Coast", "Cuddalore Coast", "Nagapattinam Coast", "Thiruvarur Coast", "Thanjavur Coast", "Pudukottai Coast", "Ramanathapuram Coast", "Thoothukudi Coast", "Tirunelveli Coast", "Kanyakumari Coast", "Other"],
    "Karnataka": ["Dakshina Kannada Coast", "Udupi Coast", "Uttara Kannada Coast", "Other"],
    "Maharashtra": ["Mumbai City Coast", "Mumbai Suburban Coast", "Thane Coast", "Palghar Coast", "Raigad Coast", "Ratnagiri Coast", "Sindhudurg Coast", "Other"],
    "Goa": ["North Goa Coast", "South Goa Coast", "Other"],
    "Gujarat": ["Kutch Coast", "Jamnagar Coast", "Porbandar Coast", "Junagadh Coast", "Amreli Coast", "Bhavnagar Coast", "Ahmedabad Coast", "Anand Coast", "Bharuch Coast", "Surat Coast", "Navsari Coast", "Valsad Coast", "Other"],
    "Andhra Pradesh": ["Srikakulam Coast", "Vizianagaram Coast", "Visakhapatnam Coast", "East Godavari Coast", "West Godavari Coast", "Krishna Coast", "Guntur Coast", "Prakasam Coast", "Nellore Coast", "Other"],
    "Odisha": ["Balasore Coast", "Bhadrak Coast", "Kendrapara Coast", "Jagatsinghpur Coast", "Puri Coast", "Ganjam Coast", "Other"],
    "West Bengal": ["Purba Medinipur Coast", "South 24 Parganas Coast", "North 24 Parganas Coast", "Other"],
    "Puducherry (UT)": ["Puducherry Region Coast", "Karaikal Coast", "Mahe Coast", "Yanam Coast", "Other"],
    "Daman & Diu (UT)": ["Daman Coast", "Diu Coast", "Other"],
    "Lakshadweep (UT)": ["Kavaratti", "Agatti", "Minicoy", "Amini", "Andrott", "Other"],
    "Andaman & Nicobar (UT)": ["Port Blair", "Havelock Island", "Neil Island", "Little Andaman", "Great Nicobar", "Other"],
    "Other State/Region": ["Other"]
}

# --- APPROXIMATE COORDINATES (LAT, LON) ---
REGION_COORDS = {
    # Tamil Nadu
    "Chennai Coast": (13.0827, 80.2707), "Thiruvallur Coast": (13.15, 80.30), "Kancheepuram Coast": (12.50, 80.15),
    "Villupuram Coast": (12.00, 79.80), "Cuddalore Coast": (11.7480, 79.7714), "Nagapattinam Coast": (10.7672, 79.8437),
    "Thiruvarur Coast": (10.70, 79.60), "Thanjavur Coast": (10.30, 79.30), "Pudukottai Coast": (10.00, 79.00),
    "Ramanathapuram Coast": (9.3639, 78.8395), "Thoothukudi Coast": (8.7642, 78.1348), "Tirunelveli Coast": (8.7139, 77.7567),
    "Kanyakumari Coast": (8.0883, 77.5385),
    # Kerala
    "Thiruvananthapuram Coast": (8.5241, 76.9366), "Kollam Coast": (8.8932, 76.6141), "Alappuzha Coast": (9.4981, 76.3388),
    "Kochi (Ernakulam) Coast": (9.9312, 76.2673), "Thrissur Coast": (10.5276, 76.2144), "Malappuram Coast": (10.8505, 75.9265),
    "Kozhikode Coast": (11.2588, 75.7804), "Kannur Coast": (11.8745, 75.3704), "Kasargod Coast": (12.4996, 74.9869),
    # Karnataka (Added Missing)
    "Dakshina Kannada Coast": (12.91, 74.85), "Udupi Coast": (13.34, 74.74), "Uttara Kannada Coast": (14.80, 74.13),
    # Andhra Pradesh
    "Visakhapatnam Coast": (17.6868, 83.2185), "Srikakulam Coast": (18.30, 83.90), "Vizianagaram Coast": (18.11, 83.39),
    "East Godavari Coast": (16.90, 82.20), "West Godavari Coast": (16.50, 81.50), "Krishna Coast": (16.10, 81.10),
    "Guntur Coast": (15.80, 80.50), "Prakasam Coast": (15.50, 80.05), "Nellore Coast": (14.4426, 79.9865),
    # Odisha
    "Puri Coast": (19.8135, 85.8312), "Ganjam Coast": (19.35, 85.05), "Balasore Coast": (21.49, 87.00),
    "Bhadrak Coast": (20.90, 86.80), "Jagatsinghpur Coast": (20.00, 86.40), "Kendrapara Coast": (20.50, 86.60),
    # Maharashtra
    "Mumbai City Coast": (18.93, 72.82), "Mumbai Suburban Coast": (19.10, 72.85), "Thane Coast": (19.21, 72.97),
    "Palghar Coast": (19.69, 72.76), "Raigad Coast": (18.50, 72.90),
    "Ratnagiri Coast": (16.99, 73.31), "Sindhudurg Coast": (16.10, 73.50),
    # Goa
    "North Goa Coast": (15.60, 73.75), "South Goa Coast": (15.20, 73.95),
    # Gujarat
    "Kutch Coast": (23.00, 69.50), "Jamnagar Coast": (22.47, 70.05), "Porbandar Coast": (21.64, 69.62),
    "Junagadh Coast": (21.52, 70.45), "Amreli Coast": (21.60, 71.21), "Bhavnagar Coast": (21.76, 72.15),
    "Ahmedabad Coast": (22.25, 72.50), "Anand Coast": (22.56, 72.92), "Bharuch Coast": (21.70, 72.99),
    "Surat Coast": (21.17, 72.83), "Navsari Coast": (20.94, 72.90), "Valsad Coast": (20.60, 72.90),
    # West Bengal
    "Purba Medinipur Coast": (21.90, 87.70), "South 24 Parganas Coast": (21.70, 88.50), "North 24 Parganas Coast": (22.61, 88.40),
    # UTs
    "Puducherry Region Coast": (11.9416, 79.8083), "Karaikal Coast": (10.92, 79.83), "Mahe Coast": (11.70, 75.53), "Yanam Coast": (16.73, 82.21),
    "Port Blair": (11.6234, 92.7265), "Havelock Island": (11.97, 92.98), "Neil Island": (11.83, 93.05),
    "Little Andaman": (10.74, 92.51), "Great Nicobar": (7.00, 93.80),
    "Kavaratti": (10.56, 72.64), "Agatti": (10.85, 72.19), "Minicoy": (8.28, 73.02), "Amini": (11.12, 72.72), "Andrott": (10.82, 73.66),
    "Daman Coast": (20.42, 72.83), "Diu Coast": (20.71, 70.98),
    "Other": (20.59, 78.96) # Center of India
}

# --- UNIT MAPPING FOR CSV EXPORT ---
COLUMN_CONFIG = {
    # Meta Data
    "created_at": "Upload Timestamp",
    "Date": "Collection Date",
    "Time": "Collection Time",
    "Main_Location": "Region",
    "Location": "Specific Spot",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    
    # Physical
    "Water_Temp": "Water Temperature (°C)",
    "Salinity": "Salinity (psu)",
    "pH": "pH Level",
    "Turbidity": "Turbidity (NTU)",
    "Transparency": "Transparency (cm)",
    "TSS": "Total Suspended Solids (mg/L)",
    "TDS": "Total Dissolved Solids (g/L)",
    "Color": "Water Color",
    "Odour": "Odour",
    
    # Chemical
    "DO": "Dissolved Oxygen (mg/L)",
    "BOD": "Biochemical Oxygen Demand (mg/L)",
    "COD": "Chemical Oxygen Demand (mg/L)",
    "NH4_N": "Ammonium Nitrogen (µmol/L)",
    "NO3_N": "Nitrate Nitrogen (µmol/L)",
    "NO2_N": "Nitrite Nitrogen (µmol/L)",
    "PO4": "Phosphate (µmol/L)",
    "SO4": "Sulphate (mg/L)",
    
    # Biological
    "Chlorophyll": "Chlorophyll (ug/l)",
    "BGA": "Blue Green Algae (mg/l)",
    "Fecal_Coliform": "Fecal Coliform (MPN/100ml)",
    "Total_Coliform": "Total Coliform (MPN/100ml)",
    "Productivity": "Primary Productivity (mgC/m3/hr)",
    "Phytoplankton": "Phytoplankton Species",
    "Zooplankton": "Zooplankton Species",
    
    # Meteorological & Geo
    "Wind_Speed": "Wind Speed (m/s)",
    "Wind_Direction": "Wind Direction (Deg)",
    "Air_Temp": "Air Temperature (°C)",
    "Humidity": "Relative Humidity (%)",
    "Precipitation": "Total Precipitation (mm)",
    "Population": "Coastal Population",
    "Tourist_Inflow": "Annual Tourist Inflow",
    "Shoreline_Status": "Shoreline Status"
}
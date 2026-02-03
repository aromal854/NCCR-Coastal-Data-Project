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
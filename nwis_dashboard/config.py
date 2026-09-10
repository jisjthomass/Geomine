import os

# Data Mode: "local", "csv", or "postgres"
DATA_MODE = os.getenv("DATA_MODE", "local")

# Backend API Endpoints (Preserved)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/api/analyze_risk"
DASHBOARD_STATE_ENDPOINT = f"{BACKEND_URL}/api/dashboard/state"

# PostgreSQL Connection Configuration (Placeholders for backend integration)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DATABASE = os.getenv("PG_DATABASE", "nwis_wells_db")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

# Cache & Performance Settings
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Default Safe Operating Envelopes
TELEMETRY_THRESHOLDS = {
    "rop": {"min": 5.0, "normal_max": 25.0, "high_risk": 35.0, "unit": "m/hr"},
    "rpm": {"min": 60.0, "normal_max": 150.0, "high_risk": 180.0, "unit": "RPM"},
    "torque": {"min": 1000.0, "normal_max": 5000.0, "high_risk": 6500.0, "unit": "ft-lbs"},
    "wob": {"min": 4.0, "normal_max": 20.0, "high_risk": 28.0, "unit": "klbs"},
}

# GIS Basemap Providers & Tiles
ESRI_SATELLITE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
ESRI_ATTRIBUTION = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"

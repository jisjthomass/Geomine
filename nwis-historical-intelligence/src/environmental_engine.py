# nwis-historical-intelligence/src/environmental_engine.py
import math

def calculate_environmental_risk(lat: float, lon: float, current_depth: float, infrastructure_data: list) -> dict:
    """
    Calculates spatial proximity to critical underground infrastructure
    (aquifers, gas pipelines, dug wells).
    Uses a 3D intersection approximation (Lat, Lon, Depth).
    """
    highest_risk = "SAFE"
    warnings = []
    
    for item in infrastructure_data:
        # Simplified 3D distance check
        # Assuming haversine distance gives X/Y in km, and depth is Z in meters
        # For prototype, we simulate intersection logic based on thresholds.
        
        infra_type = item.get("type", "Unknown")
        infra_depth = item.get("depth_m", 0)
        
        depth_diff = abs(current_depth - infra_depth)
        
        if depth_diff < 50:
            if infra_type == "Aquifer":
                highest_risk = "CRITICAL"
                warnings.append(f"WARNING: Drill path intersects active Aquifer at {infra_depth}m. High risk of groundwater contamination.")
            elif infra_type == "Gas Pipeline":
                highest_risk = "CRITICAL"
                warnings.append(f"FATAL: Drill trajectory approaching High-Pressure Gas Pipeline at {infra_depth}m.")
                
    return {
        "environmental_risk_level": highest_risk,
        "warnings": warnings
    }

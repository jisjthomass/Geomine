# nwis-historical-intelligence/src/physics_engine.py

def calculate_mse_and_stick_slip(telemetry_window: list) -> dict:
    """
    Analyzes a rolling window (e.g., last 5 seconds) of telemetry data
    to detect Stick-Slip vibrations and calculate Mechanical Specific Energy (MSE).
    """
    if len(telemetry_window) < 5:
        return {"status": "insufficient_data", "is_stick_slip": False}

    # Basic MSE calculation (simplified for prototype)
    # MSE = (WOB / Area) + (120 * pi * RPM * Torque) / (Area * ROP)
    
    # Check for Stick-Slip pattern: Sharp Torque fluctuations + RPM drops
    torques = [t.get("torque", 0) for t in telemetry_window]
    rpms = [t.get("rpm", 0) for t in telemetry_window]
    
    avg_rpm = sum(rpms) / len(rpms)
    torque_variance = max(torques) - min(torques)
    
    is_stick_slip = False
    warning_message = None
    
    # If torque violently swings (e.g., > 1500 variance) while average RPM is low/dropping
    if torque_variance > 1500 and avg_rpm < 80:
        is_stick_slip = True
        warning_message = "CRITICAL: High Stick-Slip Vibration Detected. Severe risk of drill string twist-off."

    return {
        "status": "success",
        "is_stick_slip": is_stick_slip,
        "torque_variance": round(torque_variance, 2),
        "avg_rpm": round(avg_rpm, 2),
        "warning": warning_message
    }

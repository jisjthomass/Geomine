DRILLING_DAY_RATE = 20_00_000  # ₹20 Lakh/day assumption for prototype
HOURLY_RATE = DRILLING_DAY_RATE / 24

def calculate_npt_insights(current_npt_minutes: int, comparable_events: list) -> dict:
    """
    Takes the current well's NPT duration and compares it against historical offset wells.
    Calculates the financial cost and potential savings.
    """
    
    # 1. Current Well NPT
    current_npt_hours = current_npt_minutes / 60.0
    current_npt_cost = current_npt_hours * HOURLY_RATE
    
    # 2. Historical Comparison
    historical_npt_minutes_list = [
        e.get("npt_duration_minutes", 0) for e in comparable_events 
        if e.get("npt_duration_minutes", 0) > 0
    ]
    
    if not historical_npt_minutes_list:
        return {
            "current_npt_hours": round(current_npt_hours, 2),
            "current_npt_cost": round(current_npt_cost, 2),
            "historical_avg_npt_hours": 0.0,
            "potential_reduction_hours": 0.0,
            "potential_savings": 0.0,
            "message": "No comparable historical NPT data available for offset wells."
        }
        
    avg_historical_npt_minutes = sum(historical_npt_minutes_list) / len(historical_npt_minutes_list)
    avg_historical_npt_hours = avg_historical_npt_minutes / 60.0
    
    # 3. Calculate Reduction & Savings (Only if current is worse than history)
    potential_reduction_hours = max(0.0, current_npt_hours - avg_historical_npt_hours)
    potential_savings = potential_reduction_hours * HOURLY_RATE
    
    return {
        "current_npt_hours": round(current_npt_hours, 2),
        "current_npt_cost": round(current_npt_cost, 2),
        "historical_avg_npt_hours": round(avg_historical_npt_hours, 2),
        "potential_reduction_hours": round(potential_reduction_hours, 2),
        "potential_savings": round(potential_savings, 2),
        "message": f"NPT is {round(potential_reduction_hours, 2)} hours above historical average." if potential_reduction_hours > 0 else "NPT is within or below historical averages."
    }

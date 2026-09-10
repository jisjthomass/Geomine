import math

WELLS = [
    {'well_id': 'OIL-DLJ-99', 'name': 'OIL-DLJ-99', 'lat': 27.35, 'lon': 95.32, 'field': 'Duliajan', 'total_depth_m': 3200, 'formation_at_2780': 'Formation X', 'event_type': 'None', 'event_md': None, 'event_note': '', 'is_active': 1},
    {'well_id': 'A-17', 'name': 'Well A', 'lat': 27.361, 'lon': 95.328, 'field': 'Duliajan', 'total_depth_m': 3150, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2810, 'event_note': 'Pack-off after torque spike', 'is_active': 0},
    {'well_id': 'B-09', 'name': 'Well B', 'lat': 27.342, 'lon': 95.309, 'field': 'Duliajan', 'total_depth_m': 3050, 'formation_at_2780': 'Formation X', 'event_type': 'Torque Spike', 'event_md': 2790, 'event_note': 'High torque in shale', 'is_active': 0},
    {'well_id': 'C-04', 'name': 'Well C', 'lat': 27.3555, 'lon': 95.334, 'field': 'Duliajan', 'total_depth_m': 3300, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2810, 'event_note': 'Differential sticking', 'is_active': 0},
    {'well_id': 'D-12', 'name': 'Well D', 'lat': 27.338, 'lon': 95.341, 'field': 'Duliajan', 'total_depth_m': 2900, 'formation_at_2780': 'Formation Y', 'event_type': 'Mud Loss', 'event_md': 2400, 'event_note': 'Lost circulation in limestone', 'is_active': 0},
    {'well_id': 'E-21', 'name': 'Well E', 'lat': 27.366, 'lon': 95.312, 'field': 'Duliajan', 'total_depth_m': 3100, 'formation_at_2780': 'Formation X', 'event_type': 'Mud Loss', 'event_md': 2765, 'event_note': 'Partial losses while drilling', 'is_active': 0},
    {'well_id': 'F-08', 'name': 'Well F', 'lat': 27.3488, 'lon': 95.3015, 'field': 'Duliajan', 'total_depth_m': 2980, 'formation_at_2780': 'Formation Z', 'event_type': 'None', 'event_md': None, 'event_note': 'No major incident', 'is_active': 0},
    {'well_id': 'G-33', 'name': 'Well G', 'lat': 27.3712, 'lon': 95.3355, 'field': 'Duliajan', 'total_depth_m': 3400, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2825, 'event_note': 'Hole pack-off at shale interface', 'is_active': 0},
    {'well_id': 'H-14', 'name': 'Well H', 'lat': 27.3295, 'lon': 95.3188, 'field': 'Duliajan', 'total_depth_m': 2800, 'formation_at_2780': 'Formation Y', 'event_type': 'Torque Spike', 'event_md': 2210, 'event_note': 'Hard stringers', 'is_active': 0},
    {'well_id': 'I-05', 'name': 'Well I', 'lat': 27.357, 'lon': 95.305, 'field': 'Duliajan', 'total_depth_m': 3250, 'formation_at_2780': 'Formation X', 'event_type': 'None', 'event_md': None, 'event_note': 'Clean section', 'is_active': 0},
    {'well_id': 'J-19', 'name': 'Well J', 'lat': 27.344, 'lon': 95.3365, 'field': 'Duliajan', 'total_depth_m': 3180, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2775, 'event_note': 'Differential sticking after losses', 'is_active': 0},
    {'well_id': 'K-02', 'name': 'Well K', 'lat': 27.382, 'lon': 95.35, 'field': 'Duliajan', 'total_depth_m': 3000, 'formation_at_2780': 'Formation Z', 'event_type': 'Mud Loss', 'event_md': 1900, 'event_note': 'Severe losses', 'is_active': 0},
    {'well_id': 'L-27', 'name': 'Well L', 'lat': 27.3365, 'lon': 95.292, 'field': 'Duliajan', 'total_depth_m': 3120, 'formation_at_2780': 'Formation X', 'event_type': 'Torque Spike', 'event_md': 2805, 'event_note': 'Torque increase in Formation X', 'is_active': 0},
    {'well_id': 'M-11', 'name': 'Well M', 'lat': 27.353, 'lon': 95.348, 'field': 'Duliajan', 'total_depth_m': 2950, 'formation_at_2780': 'Formation Y', 'event_type': 'None', 'event_md': None, 'event_note': 'No event near 2780', 'is_active': 0},
    {'well_id': 'N-40', 'name': 'Well N', 'lat': 27.3608, 'lon': 95.3192, 'field': 'Duliajan', 'total_depth_m': 3280, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2798, 'event_note': 'Tight hole then stuck', 'is_active': 0},
    {'well_id': 'O-06', 'name': 'Well O', 'lat': 27.3412, 'lon': 95.3244, 'field': 'Duliajan', 'total_depth_m': 3080, 'formation_at_2780': 'Formation X', 'event_type': 'Mud Loss', 'event_md': 2788, 'event_note': 'Losses at 2788m', 'is_active': 0},
    {'well_id': 'P-18', 'name': 'Well P', 'lat': 27.325, 'lon': 95.3055, 'field': 'Duliajan', 'total_depth_m': 2700, 'formation_at_2780': 'Formation Z', 'event_type': 'None', 'event_md': None, 'event_note': 'Shallow well', 'is_active': 0},
    {'well_id': 'Q-22', 'name': 'Well Q', 'lat': 27.3688, 'lon': 95.326, 'field': 'Duliajan', 'total_depth_m': 3330, 'formation_at_2780': 'Formation X', 'event_type': 'Torque Spike', 'event_md': 2760, 'event_note': 'Erratic torque', 'is_active': 0},
    {'well_id': 'R-03', 'name': 'Well R', 'lat': 27.349, 'lon': 95.333, 'field': 'Duliajan', 'total_depth_m': 3190, 'formation_at_2780': 'Formation X', 'event_type': 'None', 'event_md': None, 'event_note': 'Uneventful', 'is_active': 0},
    {'well_id': 'S-15', 'name': 'Well S', 'lat': 27.355, 'lon': 95.3158, 'field': 'Duliajan', 'total_depth_m': 3220, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2832, 'event_note': 'Stuck after connection', 'is_active': 0},
    {'well_id': 'T-29', 'name': 'Well T', 'lat': 27.3725, 'lon': 95.3088, 'field': 'Duliajan', 'total_depth_m': 3010, 'formation_at_2780': 'Formation Y', 'event_type': 'Mud Loss', 'event_md': 2500, 'event_note': 'Minor losses', 'is_active': 0},
    {'well_id': 'U-07', 'name': 'Well U', 'lat': 27.3398, 'lon': 95.3275, 'field': 'Duliajan', 'total_depth_m': 3165, 'formation_at_2780': 'Formation X', 'event_type': 'None', 'event_md': None, 'event_note': 'Good analog lithology', 'is_active': 0},
    {'well_id': 'V-31', 'name': 'Well V', 'lat': 27.3466, 'lon': 95.3122, 'field': 'Duliajan', 'total_depth_m': 3095, 'formation_at_2780': 'Formation X', 'event_type': 'Torque Spike', 'event_md': 2782, 'event_note': 'Torque spike at 2782m', 'is_active': 0},
    {'well_id': 'W-10', 'name': 'Well W', 'lat': 27.3633, 'lon': 95.3411, 'field': 'Duliajan', 'total_depth_m': 2870, 'formation_at_2780': 'Formation Z', 'event_type': 'None', 'event_md': None, 'event_note': 'Different formation', 'is_active': 0},
    {'well_id': 'X-25', 'name': 'Well X', 'lat': 27.331, 'lon': 95.33, 'field': 'Duliajan', 'total_depth_m': 3275, 'formation_at_2780': 'Formation X', 'event_type': 'Mud Loss', 'event_md': 2740, 'event_note': 'Losses before target', 'is_active': 0},
    {'well_id': 'Y-16', 'name': 'Well Y', 'lat': 27.3588, 'lon': 95.3225, 'field': 'Duliajan', 'total_depth_m': 3210, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2800, 'event_note': 'Classic stuck-pipe analog', 'is_active': 0},
    {'well_id': 'Z-13', 'name': 'Well Z', 'lat': 27.374, 'lon': 95.318, 'field': 'Duliajan', 'total_depth_m': 2990, 'formation_at_2780': 'Formation Y', 'event_type': 'None', 'event_md': None, 'event_note': 'Offset but different zone', 'is_active': 0},
    {'well_id': 'AA-01', 'name': 'Well AA', 'lat': 27.3433, 'lon': 95.345, 'field': 'Duliajan', 'total_depth_m': 3140, 'formation_at_2780': 'Formation X', 'event_type': 'None', 'event_md': None, 'event_note': 'Nearby clean well', 'is_active': 0},
    {'well_id': 'AB-08', 'name': 'Well AB', 'lat': 27.3518, 'lon': 95.3077, 'field': 'Duliajan', 'total_depth_m': 3060, 'formation_at_2780': 'Formation X', 'event_type': 'Torque Spike', 'event_md': 2818, 'event_note': 'Overpull and torque', 'is_active': 0},
    {'well_id': 'AC-20', 'name': 'Well AC', 'lat': 27.3655, 'lon': 95.3298, 'field': 'Duliajan', 'total_depth_m': 3310, 'formation_at_2780': 'Formation X', 'event_type': 'Stuck Pipe', 'event_md': 2795, 'event_note': 'Stuck in Formation X', 'is_active': 0},
]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_nearby_wells(lat: float, lon: float, radius_km: float) -> list:
    """
    Finds historical wells within a specified radius.
    Strictly follows the Constitution's function signature.
    """
    nearby = []
    for w in WELLS:
        if w.get('is_active') == 1:
            continue
            
        dist = haversine_km(lat, lon, w['lat'], w['lon'])
        
        if dist <= radius_km:
            nearby.append({
                "well_id": w['well_id'],
                "distance_km": round(dist, 2),
                "latitude": w['lat'],
                "longitude": w['lon']
            })
            
    # Sort by closest first
    nearby = sorted(nearby, key=lambda x: x["distance_km"])
    return nearby

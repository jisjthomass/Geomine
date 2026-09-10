import re

with open("app.py", "r") as f:
    content = f.read()

# Make sure we add the import
if "from api_client import analyze_drilling_risk" not in content:
    content = content.replace("from map_component import create_offset_well_map", "from map_component import create_offset_well_map\nfrom api_client import analyze_drilling_risk")

old_block = """        st.session_state["dashboard_data"] = get_local_dashboard_data(
            current_depth=depth,
            radius_km=radius_km,
            formation=selected_formation,
            depth_window=depth_window,
        )"""

new_block = """        # Integrated with Thomas's FastAPI Backend
        payload = {
            "location_area": "Duliajan Sector 4",
            "lat": 27.35,
            "lon": 95.32,
            "target_formation": selected_formation,
            "depth": float(depth),
            "rop": float(rop),
            "rpm": float(rpm),
            "torque": float(torque),
            "wob": float(wob),
            "search_radius_km": float(radius_km)
        }
        st.session_state["dashboard_data"] = analyze_drilling_risk(payload)"""

content = content.replace(old_block, new_block)

with open("app.py", "w") as f:
    f.write(content)

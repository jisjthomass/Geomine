import folium
from folium import LayerControl
from folium.plugins import Fullscreen
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import pydeck as pdk

from config import ESRI_SATELLITE_URL, ESRI_ATTRIBUTION

def render_pydeck_map(
    active_well: dict,
    nearby_wells: list[dict],
    radius_km: float = 5.0,
    height: int = 500,
) -> None:
    """
    Renders a hardware-accelerated WebGL Deck.gl map directly inside Streamlit's canvas.
    Completely eliminates iframe destruction and blackout during parameter changes.
    """
    active_lat = active_well.get("lat", 27.35)
    active_lon = active_well.get("lon", 95.32)
    active_id = active_well.get("well_id", "OIL-DLJ-99")

    color_map = {
        "Stuck Pipe": [239, 68, 68, 230],
        "Mud Loss": [249, 115, 22, 230],
        "Torque Spike": [234, 179, 8, 230],
        "None": [34, 197, 94, 230],
    }

    offset_records = []
    for well in nearby_wells:
        if well.get("is_active") == 1 or well.get("well_id") == active_id:
            continue
        lat = well.get("lat")
        lon = well.get("lon")
        if lat is None or lon is None:
            continue

        event_type = well.get("event_type", "None")
        event_depth = well.get("event_md")
        rec = dict(well)
        rec["fill_color"] = color_map.get(event_type, [34, 197, 94, 230])
        rec["event_depth_str"] = f"{event_depth:.0f} m" if event_depth is not None else "N/A"
        rec["distance_str"] = f"{well.get('distance_km', 0):.2f}"
        rec["sim_str"] = f"{well.get('similarity', 0):.0f}"
        offset_records.append(rec)

    offset_df = pd.DataFrame(offset_records)
    active_df = pd.DataFrame([active_well])

    layers = []

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=active_df,
            get_position="[lon, lat]",
            get_radius=2000,
            get_fill_color=[56, 189, 248, 12],
            get_line_color=[56, 189, 248, 180],
            stroked=True,
            filled=True,
            line_width_min_pixels=1,
            pickable=False,
        )
    )

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=active_df,
            get_position="[lon, lat]",
            get_radius=radius_km * 1000,
            get_fill_color=[37, 99, 235, 18],
            get_line_color=[37, 99, 235, 220],
            stroked=True,
            filled=True,
            line_width_min_pixels=2,
            pickable=False,
        )
    )

    if not offset_df.empty:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=offset_df,
                get_position="[lon, lat]",
                get_radius=130,
                get_fill_color="fill_color",
                get_line_color=[255, 255, 255, 255],
                stroked=True,
                filled=True,
                line_width_min_pixels=1.5,
                pickable=True,
            )
        )

    import math as _math
    # DeckGL/WebMercator Zoom Calibration:
    # We want the circle to tightly fit the 500px container.
    # Base constant 14.9 perfectly frames the bounding box without clipping.
    _pdk_zoom = max(4.0, min(15.5, 14.9 - _math.log2(max(radius_km, 0.1))))
    
    view_state = pdk.ViewState(
        latitude=active_lat,
        longitude=active_lon,
        zoom=_pdk_zoom,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<div style='font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px; line-height: 1.5;'>"
            "<b style='color: #38bdf8; font-size: 13px;'>📍 {name}</b> ({well_id})<br/>"
            "<b>Distance:</b> {distance_str} km &nbsp;│&nbsp; <b>Match:</b> {sim_str}%<br/>"
            "<b>Zone:</b> {formation_at_2780}<br/>"
            "<b>Incident:</b> <b>{event_type}</b> @ {event_depth_str}<br/>"
            "</div>"
        ),
        "style": {
            "backgroundColor": "#0f172a",
            "color": "#f8fafc",
            "border": "1px solid #334155",
            "borderRadius": "8px",
            "padding": "8px 12px",
            "zIndex": "99999",
        },
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=pdk.map_styles.CARTO_DARK,
        tooltip=tooltip,
    )

    run_counter = st.session_state.get("run_count", 0)
    st.pydeck_chart(
        deck,
        use_container_width=True,
        height=height,
        key=f"pydeck_{radius_km}_{run_counter}"
    )

def render_folium_map(
    active_well: dict,
    nearby_wells: list[dict],
    radius_km: float = 5.0,
    height: int = 500,
    use_satellite: bool = False
) -> None:
    active_lat = active_well.get("lat", 27.35)
    active_lon = active_well.get("lon", 95.32)

    tiles = ESRI_SATELLITE_URL if use_satellite else "CartoDB dark_matter"
    attr = ESRI_ATTRIBUTION if use_satellite else "© CartoDB"
    
    well_map = folium.Map(
        location=[active_lat, active_lon],
        zoom_start=11,
        tiles=tiles,
        attr=attr,
        control_scale=True,
        prefer_canvas=True
    )
    
    Fullscreen().add_to(well_map)

    color_map = {
        "Stuck Pipe": "#ef4444",
        "Mud Loss": "#f97316",
        "Torque Spike": "#eab308",
        "None": "#22c55e",
    }
    
    bounds = [[active_lat, active_lon]]

    folium.Circle(
        location=[active_lat, active_lon],
        radius=radius_km * 1000,
        color="#2563eb",
        weight=2,
        fill=True,
        fill_color="#2563eb",
        fill_opacity=0.05,
        tooltip=f"Search Buffer ({radius_km} km)"
    ).add_to(well_map)

    bounds.append([active_lat + (radius_km / 111.0), active_lon])
    bounds.append([active_lat - (radius_km / 111.0), active_lon])
    bounds.append([active_lat, active_lon + (radius_km / (111.0 * 0.88))])
    bounds.append([active_lat, active_lon - (radius_km / (111.0 * 0.88))])

    folium.CircleMarker(
        location=[active_lat, active_lon],
        radius=8,
        color="#38bdf8",
        weight=2,
        fill=True,
        fill_color="#0ea5e9",
        fill_opacity=0.9,
        tooltip="<b>Active Rig</b><br>OIL-DLJ-99"
    ).add_to(well_map)

    # Sort and cap strictly at 50 wells to prevent DOM lag
    top_wells = sorted(nearby_wells, key=lambda x: x.get('similarity', 0), reverse=True)[:50]

    for well in top_wells:
        w_lat = well.get("lat")
        w_lon = well.get("lon")
        
        if not w_lat or not w_lon:
            continue
            
        event_type = well.get("event_type", "None")
        
        html_tooltip = f"""
        <div style='font-family: sans-serif; font-size: 12px; white-space: nowrap;'>
            <b style='color: #38bdf8;'>📍 {well.get('well_id')}</b><br/>
            <b>Match:</b> {well.get('similarity', 0):.0f}%<br/>
            <b>Distance:</b> {well.get('distance_km', 0):.2f} km<br/>
            <b>Incident:</b> <b style='color:{color_map.get(event_type, "#22c55e")}'>{event_type}</b>
        </div>
        """
        
        folium.CircleMarker(
            location=[w_lat, w_lon],
            radius=6,
            color="white",
            weight=1,
            fill=True,
            fill_color=color_map.get(event_type, "#22c55e"),
            fill_opacity=0.9,
            tooltip=folium.Tooltip(html_tooltip)
        ).add_to(well_map)
        
        bounds.append([w_lat, w_lon])

    well_map.fit_bounds(bounds)

    legend_html = """
    <div style="position: absolute; bottom: 15px; left: 15px; z-index: 1000; background: #0f172a; padding: 10px; border: 1px solid #1e293b; border-radius: 8px; font-size: 12px; font-family: sans-serif; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="margin-bottom: 5px;"><span style="color: #60a5fa; font-size: 14px;">●</span> Active Rig</div>
        <div style="margin-bottom: 5px;"><span style="color: #ef4444; font-size: 14px;">●</span> Stuck Pipe</div>
        <div style="margin-bottom: 5px;"><span style="color: #f97316; font-size: 14px;">●</span> Mud Loss</div>
        <div style="margin-bottom: 5px;"><span style="color: #eab308; font-size: 14px;">●</span> Torque Spike</div>
        <div><span style="color: #22c55e; font-size: 14px;">●</span> Normal</div>
    </div>
    """
    well_map.get_root().html.add_child(folium.Element(legend_html))

    LayerControl(position="topright").add_to(well_map)

    run_counter = st.session_state.get("run_count", 0)
    st_folium(
        well_map,
        width=None,
        height=height,
        use_container_width=True,
        returned_objects=[],
        key=f"gis_well_map_{radius_km}_{run_counter}",
    )

def create_offset_well_map(
    active_well: dict,
    nearby_wells: list[dict],
    radius_km: float = 5.0,
    height: int = 500,
) -> None:
    st.markdown("##### [GIS] Proximity Map")
    
    map_type = st.radio(
        "Map Engine",
        ["[MAP] Seamless Dark Map (Auto-Zoom)", "[SAT] Leaflet Satellite"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    try:
        if map_type == "[MAP] Seamless Dark Map (Auto-Zoom)":
            render_pydeck_map(active_well, nearby_wells, radius_km, height)
        else:
            render_folium_map(active_well, nearby_wells, radius_km, height, use_satellite=True)
    except Exception as e:
        st.error(f"Map Rendering Error: {e}")

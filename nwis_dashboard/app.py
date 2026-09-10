import streamlit as st
st.cache_data.clear()
import pandas as pd
import altair as alt

from config import DATA_MODE, TELEMETRY_THRESHOLDS, PG_HOST, PG_PORT, PG_DATABASE, PG_USER
from data_source import (
    get_local_dashboard_data,
    get_dataset_summary,
    load_all_wells_df,
    get_formation_risk_analytics,
    generate_handover_report_df,
)
from map_component import create_offset_well_map
from api_client import analyze_drilling_risk
import api_client



# =====================================================================
# 1. PAGE CONFIGURATION
# =====================================================================

st.set_page_config(
    page_title="NWIS | Drilling Risk & Spatial Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================================
# 2. HIGH-READABILITY INDUSTRIAL STYLING (SIH Presentation Standard)
# =====================================================================

st.markdown(
    """
    <style>
    /* Hide Streamlit Header, Deploy Button, and Footer */
    header { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    .stDeployButton { display: none !important; }

    /* Global Base & Typography */
    .stApp {
        background-color: #080c14;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Container Margin Reduction (Removes excessive empty padding) */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.8rem !important;
        padding-right: 1.8rem !important;
        max-width: 100% !important;
    }

    /* Top Mission Control Header */
    .nwis-brand-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }
    .nwis-main-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #f8fafc;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .nwis-main-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 500;
    }
    .status-badge-live {
        background-color: rgba(34, 197, 94, 0.15);
        border: 1px solid #22c55e;
        color: #4ade80;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #22c55e;
    }

    /* Section Headings */
    .section-header {
        font-size: 18px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 12px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Industrial SCADA Instrument Cards */
    .scada-panel-card {
        background-color: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 10px 14px;
        min-height: 102px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
    }
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2px;
    }
    .panel-tag {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }
    .panel-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 3px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        letter-spacing: 0.04em;
    }
    .panel-value-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin: 2px 0;
    }
    .panel-val-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 23px;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }
    .panel-unit {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .panel-footer-meta {
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.35;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        padding-top: 5px;
        margin-top: 3px;
    }

    /* Operational Directive Banners (Dynamic Alert Classes) */
    .action-banner-critical {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.20) 0%, rgba(15, 23, 42, 0.98) 100%);
        border-left: 5px solid #ef4444;
        border-top: 1px solid #450a0a;
        border-right: 1px solid #450a0a;
        border-bottom: 1px solid #450a0a;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0 16px 0;
    }
    .action-banner-high {
        background: linear-gradient(135deg, rgba(234, 88, 12, 0.20) 0%, rgba(15, 23, 42, 0.98) 100%);
        border-left: 5px solid #f97316;
        border-top: 1px solid #431407;
        border-right: 1px solid #431407;
        border-bottom: 1px solid #431407;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0 16px 0;
    }
    .action-banner-medium {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.16) 0%, rgba(15, 23, 42, 0.98) 100%);
        border-left: 5px solid #eab308;
        border-top: 1px solid #422006;
        border-right: 1px solid #422006;
        border-bottom: 1px solid #422006;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0 16px 0;
    }
    .action-banner-low {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(15, 23, 42, 0.98) 100%);
        border-left: 5px solid #22c55e;
        border-top: 1px solid #052e16;
        border-right: 1px solid #052e16;
        border-bottom: 1px solid #052e16;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0 16px 0;
    }
    .action-title-text {
        font-size: 16px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .action-body-text {
        font-size: 16px;
        line-height: 1.6;
        color: #e2e8f0;
    }
    .action-evidence-text {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 8px;
        line-height: 1.5;
    }

    /* Analog Well Mini-Cards */
    .analog-well-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: border-color 0.15s ease;
    }
    .analog-well-card:hover {
        border-color: #38bdf8;
    }
    .analog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .analog-name {
        font-size: 14px;
        font-weight: 800;
        color: #f8fafc;
    }
    .analog-sim-badge {
        font-size: 12px;
        font-weight: 800;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.12);
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .analog-detail {
        font-size: 12px;
        color: #cbd5e1;
        line-height: 1.4;
    }

    /* Operating Envelope Gauge Cards */
    .envelope-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .envelope-title {
        font-size: 14px;
        font-weight: 800;
        color: #38bdf8;
        margin-bottom: 4px;
    }

    /* Sidebar Clean Styling */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    [data-testid="stSidebar"] h3 {
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #f8fafc !important;
        margin-top: 10px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stSidebar"] label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #cbd5e1 !important;
    }

    /* Tab Header Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #0f172a;
        padding: 6px 10px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        margin-bottom: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        font-weight: 700;
        color: #94a3b8;
        border-radius: 5px;
        padding: 6px 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-size: 14px !important;
        font-weight: 800 !important;
        min-height: 40px;
        letter-spacing: 0.02em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# 3. DATA LOAD & REPOSITORY SUMMARY
# =====================================================================

dataset_summary = get_dataset_summary()
wells_df = load_all_wells_df()

if wells_df.empty or not dataset_summary.get("active_well"):
    st.error("[!] Dataset not available. Please check well repository configuration.")
    st.stop()

default_active_well = dataset_summary["active_well"]
available_formations = ["Kopili Shale", "Girujan Clay", "Barail Coal-Shale", "Lakadong-Therria"]


# =====================================================================
# 4. SIDEBAR CONFIGURATION (Well & Real-Time Operational Controls)
# =====================================================================

with st.sidebar.form("drilling_parameters_form"):
    st.markdown("###  Spatial & Geological Parameters")

    selected_formation = st.selectbox(
        "Target Formation Zone",
        ["All"] + available_formations,
        index=1 if "Formation X" in available_formations else 0,
        help="Filter offset wells penetrating the specified geological formation zone",
    )

    if "radius_km_slider" not in st.session_state:
        st.session_state["radius_km_slider"] = 5.0
        
    radius_km = st.slider(
        "Radial Search Buffer (km)",
        min_value=1.0,
        max_value=50.0,
        step=0.5,
        help="Radial geographic search perimeter around the active drilling rig",
        key="radius_km_slider"
    )

    depth_window = st.slider(
        "Historical Depth Corridor (± m)",
        min_value=30.0,
        max_value=150.0,
        value=80.0,
        step=10.0,
        help="Corridor window around current bit depth for identifying analog historical incidents",
    )

    st.markdown("###  Live Surface Sensors")

    depth = st.number_input(
        "Current Bit Depth (m)",
        min_value=1000.0,
        max_value=5000.0,
        value=2780.0,
        step=10.0,
    )

    c_sen1, c_sen2 = st.columns(2)
    with c_sen1:
        rop = st.number_input(
            "ROP (m/hr)",
            min_value=0.0,
            max_value=100.0,
            value=15.2,
            step=0.5,
            help="Rate of Penetration",
        )
        torque = st.number_input(
            "Torque (ft-lbs)",
            min_value=0.0,
            max_value=10000.0,
            value=4500.0,
            step=100.0,
            help="Surface Torque",
        )

    with c_sen2:
        rpm = st.number_input(
            "RPM",
            min_value=0.0,
            max_value=300.0,
            value=120.5,
            step=5.0,
            help="Rotary Table Speed",
        )
        wob = st.number_input(
            "WOB (klbs)",
            min_value=0.0,
            max_value=60.0,
            value=10.5,
            step=0.5,
            help="Weight on Bit",
        )

    st.markdown("###  Performance Controls")
    enable_ai = st.checkbox(
        " Generate AI Risk Summary (Adds ~5s latency)",
        value=False,
        help="Turn off to drastically reduce analysis speed by skipping the Gemini LLM step."
    )


    analyze_button = st.form_submit_button(
        " Run Drilling Risk Analysis",
        type="primary",
        use_container_width=True,
    )

with st.sidebar:
    # Live Rig Simulator
    st.markdown("---")
    st.markdown("####  Real-Time eRTMAC Simulator")
    
    def on_sim_toggle():
        if st.session_state.get("live_sim_toggle"):
            st.session_state["radius_km_slider"] = 45.0
            
    is_simulating = st.toggle(" Start Live Rig Simulation", key="live_sim_toggle", on_change=on_sim_toggle)
    
    if is_simulating:
        st.session_state["sim_depth"] = st.session_state.get("sim_depth", 2480.0)
        st.session_state["sim_torque"] = st.session_state.get("sim_torque", 3500.0)
        
        sim_depth = float(round(st.session_state["sim_depth"], 2))
        st.info(f"[SIMULATOR] Active... Depth: {sim_depth:.2f}m")


# =====================================================================
# 5. SESSION STATE — LAZY INIT (no auto API call on first visit)
# =====================================================================

# On first page load we do NOT hit the backend automatically.
# We populate session state with safe defaults so the page renders
# instantly. The backend is only called when the user explicitly
# clicks the "Run Drilling Risk Analysis" button.
_empty_dashboard = {
    "status": "idle",
    "active_well": default_active_well,
    "ml_prediction": {"risk_score": 0.0, "risk_level": "IDLE", "predicted_event": "Press Run to analyse"},
    "historical_context": {
        "nearby_wells_analyzed": 0,
        "historical_matches_found": 0,
        "evidence_string": "Click <b>Run Drilling Risk Analysis</b> to start.",
        "recommended_action": "Awaiting first analysis.",
        "offset_wells_map_data": [],
        "stuck_pipe_count": 0,
        "mud_loss_count": 0,
        "torque_spike_count": 0,
    },
}

if "dashboard_data" not in st.session_state:
    st.session_state["dashboard_data"] = _empty_dashboard
    st.session_state["active_radius_km"] = radius_km
    st.session_state["telemetry"] = {"depth": depth, "rop": rop, "rpm": rpm, "torque": torque, "wob": wob}
    st.session_state["_current_rig_id"] = default_active_well["well_id"]

# Detect rig switch and auto-reset
if st.session_state.get("_current_rig_id") != default_active_well["well_id"]:
    st.session_state["_current_rig_id"] = default_active_well["well_id"]
    st.session_state["dashboard_data"] = _empty_dashboard
    st.session_state["telemetry"] = {"depth": depth, "rop": rop, "rpm": rpm, "torque": torque, "wob": wob}

if analyze_button:
    # Increment run counter to force map remounts and clear camera cache
    st.session_state["run_count"] = st.session_state.get("run_count", 0) + 1
    with st.spinner(" Analysing offset well incidents and spatial risk corridor..."):
        payload = {
            "location_area": f"{default_active_well.get('field', 'Duliajan')} {'Sector 4'}",
            "lat": default_active_well.get("lat", 27.35),
            "lon": default_active_well.get("lon", 95.32),
            "target_formation": selected_formation,
            "depth": float(depth),
            "rop": float(rop),
            "rpm": float(rpm),
            "torque": float(torque),
            "wob": float(wob),
            "search_radius_km": float(radius_km),
            "depth_window": float(depth_window),
            "enable_ai": False  # Force false to get instant metrics
        }
        st.session_state["dashboard_data"] = analyze_drilling_risk(payload)
        # Save the real AI flag for the lazy loader
        st.session_state["pending_ai_payload"] = payload if enable_ai else None
        st.session_state["ai_summary"] = None
        st.session_state["active_radius_km"] = radius_km
        st.session_state["telemetry"] = {"depth": depth, "rop": rop, "rpm": rpm, "torque": torque, "wob": wob}

dashboard_data = st.session_state["dashboard_data"]
# Always use the CURRENTLY selected rig, never the stale cached one
active_well = default_active_well
nearby_wells = dashboard_data.get("historical_context", {}).get("offset_wells_map_data", [])
risk_assessment = dashboard_data.get("risk_assessment", dashboard_data.get("ml_prediction", {}))
historical_context = dashboard_data.get("historical_context", {})

current_telemetry = st.session_state["telemetry"]
risk_score = float(risk_assessment.get("risk_score", 0.0))
risk_level = str(risk_assessment.get("risk_level", "IDLE"))
predicted_event = str(risk_assessment.get("predicted_event", "Press Run to analyse"))
stuck_pipe_count = historical_context.get("stuck_pipe_count", 0)
mud_loss_count = historical_context.get("mud_loss_count", 0)
torque_spike_count = historical_context.get("torque_spike_count", 0)



# =====================================================================
# 6. MISSION CONTROL BRAND HEADER & REAL-TIME STATUS
# =====================================================================

st.markdown(
    f"""
    <div class="nwis-brand-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <div class="nwis-main-title">
                     GeoMine | NWIS Drilling Risk & Spatial Intelligence
                </div>
                <div class="nwis-main-subtitle">
                    Nearby Wells Intelligence System • Real-Time Rig Monitoring & Offset Hazard Mitigation
                </div>
            </div>
            <div style="text-align: right;">
                <span class="status-badge-live">
                    <span class="pulse-dot"></span>
                    LIVE OPERATIONAL MONITORING
                </span>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px; font-weight: 600;">
                    Rig: <b style="color:#f8fafc;">{active_well.get('name', 'OIL-DLJ-99')}</b> &nbsp;│&nbsp; Field: <b style="color:#f8fafc;">{active_well.get('field', 'Duliajan Basin')}</b> &nbsp;│&nbsp; Depth: <b style="color:#38bdf8;">{current_telemetry['depth']:.0f} m</b>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# 7. INDUSTRIAL SCADA INSTRUMENT PANELS (5 Uniform Cards)
# =====================================================================

planned_td = float(active_well.get("total_depth_m", 3200))
bit_depth = float(current_telemetry["depth"])
meters_remaining = max(0.0, planned_td - bit_depth)

risk_border = "#ef4444" if risk_level == "CRITICAL" else "#f97316" if risk_level == "HIGH" else "#eab308" if risk_level == "MEDIUM" else "#22c55e"
risk_bg = "rgba(239, 68, 68, 0.14)" if risk_level == "CRITICAL" else "rgba(249, 115, 22, 0.14)" if risk_level == "HIGH" else "rgba(234, 179, 8, 0.14)" if risk_level == "MEDIUM" else "rgba(34, 197, 94, 0.14)"

stuck_badge_color = "#ef4444" if stuck_pipe_count > 0 else "#22c55e"
stuck_badge_bg = "rgba(239, 68, 68, 0.14)" if stuck_pipe_count > 0 else "rgba(34, 197, 94, 0.14)"
stuck_badge_text = "ELEVATED" if stuck_pipe_count > 0 else "NORMAL"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(
        f"""
        <div class="scada-panel-card">
            <div class="panel-header">
                <span class="panel-tag">TAG: WELLBORE</span>
                <span class="panel-badge" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);">ACTIVE</span>
            </div>
            <div class="panel-value-row">
                <span class="panel-val-mono" style="color: #38bdf8;">{active_well.get('name', 'OIL-DLJ-99')}</span>
            </div>
            <div class="panel-footer-meta">
                Field: <b>{active_well.get('field', 'Duliajan')}</b> &bull; Assam Shelf
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="scada-panel-card">
            <div class="panel-header">
                <span class="panel-tag">MEASURED DEPTH</span>
                <span class="panel-badge" style="background: rgba(96, 165, 250, 0.12); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3);">BIT MD</span>
            </div>
            <div class="panel-value-row">
                <span class="panel-val-mono">{bit_depth:,.1f}</span>
                <span class="panel-unit">m</span>
            </div>
            <div class="panel-footer-meta">
                Target TD: <b>{planned_td:,.0f} m</b> &bull; Rem: <b>{meters_remaining:,.0f} m</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""
        <div class="scada-panel-card">
            <div class="panel-header">
                <span class="panel-tag">CORRIDOR HAZARD</span>
                <span class="panel-badge" style="background: {risk_bg}; color: {risk_border}; border: 1px solid {risk_border};">{risk_level}</span>
            </div>
            <div class="panel-value-row">
                <span class="panel-val-mono" style="color: {risk_border};">{risk_score:.0f}</span>
                <span class="panel-unit">/ 100</span>
            </div>
            <div class="panel-footer-meta">
                Predicted: <b>{predicted_event}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    analog_badge_style = "background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);" if len(nearby_wells) > 0 else "background: rgba(100, 116, 139, 0.12); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3);"
    st.markdown(
        f"""
        <div class="scada-panel-card">
            <div class="panel-header">
                <span class="panel-tag">OFFSET ANALOGS</span>
                <span class="panel-badge" style="{analog_badge_style}">r={radius_km:.1f}km</span>
            </div>
            <div class="panel-value-row">
                <span class="panel-val-mono">{len(nearby_wells)}</span>
                <span class="panel-unit">Wells</span>
            </div>
            <div class="panel-footer-meta">
                {"Window: <b>&plusmn;" + f"{depth_window:.0f} m</b> &bull; Zone: <b>{active_well.get('formation_at_2780', 'N/A')}</b>" if len(nearby_wells) > 0 else "No nearby wells found in corridor"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi5:
    st.markdown(
        f"""
        <div class="scada-panel-card">
            <div class="panel-header">
                <span class="panel-tag">{"STUCK-PIPE EVENTS" if len(nearby_wells) > 0 else "CORRIDOR HAZARDS"}</span>
                <span class="panel-badge" style="background: {stuck_badge_bg}; color: {stuck_badge_color}; border: 1px solid {stuck_badge_color};">{stuck_badge_text if len(nearby_wells) > 0 else "CLEAN"}</span>
            </div>
            <div class="panel-value-row">
                <span class="panel-val-mono" style="color: {stuck_badge_color};">{stuck_pipe_count if len(nearby_wells) > 0 else 0}</span>
                <span class="panel-unit">{"Incidents" if len(nearby_wells) > 0 else "Events"}</span>
            </div>
            <div class="panel-footer-meta">
                {"Mud Loss: <b>" + str(mud_loss_count) + "</b> &bull; Torque Spike: <b>" + str(torque_spike_count) + "</b>" if len(nearby_wells) > 0 else "Zero offset anomalies logged in this corridor"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 8. OPERATIONAL DIRECTIVE & EXPLAINABILITY BANNER (LAZY LOADED)
# =====================================================================

directive_placeholder = st.empty()

def render_directive(evidence_text):
    banner_class = "action-banner-critical" if risk_level == "CRITICAL" else "action-banner-high" if risk_level == "HIGH" else "action-banner-medium" if risk_level == "MEDIUM" else "action-banner-low"
    alert_icon = "" if risk_level in ["CRITICAL", "HIGH"] else "" if risk_level == "MEDIUM" else ""

    directive_placeholder.markdown(
        f'''
        <div class="{banner_class}">
            <div class="action-title-text">
                <span>{alert_icon} OPERATIONAL DIRECTIVE — {risk_level} HAZARD ({predicted_event.upper()})</span>
            </div>
            <div class="action-body-text">
                <b>Recommended Action:</b> {historical_context.get('recommended_action', 'Continue drilling under standard operational parameters.')}
            </div>
            <div class="action-evidence-text">
                <b>Explainability Factors:</b> {evidence_text} 
                &nbsp;•&nbsp; <b>Corridor Incidents:</b> {stuck_pipe_count} Stuck Pipe, {mud_loss_count} Mud Loss, {torque_spike_count} Torque Spike.
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

# Render initial state
current_evidence = st.session_state.get("ai_summary") or historical_context.get('evidence_string', 'No historical analog incidents identified.')
if st.session_state.get("pending_ai_payload"):
    # If there is a pending AI request, show a loading message in the evidence section
    render_directive(" <i>Gemini AI is analyzing offset wells...</i>")
else:
    render_directive(current_evidence)


# =====================================================================
# 9. STRUCTURED 5-TAB NAVIGATION
# =====================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " GIS Spatial Command",
    " Offset Records & Deep-Dive",
    " Offset Trends & Analytics",
    " Live Telemetry & Safe Envelopes",
    " Searchable Knowledge Repository",
])


# ---------------------------------------------------------------------
# TAB 1: GIS SPATIAL COMMAND
# ---------------------------------------------------------------------
with tab1:
    map_col, right_col = st.columns([1.7, 1.0], gap="medium")

    with map_col:
        create_offset_well_map(
            active_well=active_well,
            nearby_wells=nearby_wells,
            radius_km=radius_km,
            height=530,
        )

    with right_col:
        st.markdown('<div class="section-header"> Top Analog Offset Matches</div>', unsafe_allow_html=True)

        if nearby_wells:
            top_analogs = sorted(
                nearby_wells,
                key=lambda item: item.get("similarity", 0),
                reverse=True,
            )[:4]

            for well in top_analogs:
                event_type = well.get("event_type", "None")
                event_badge_color = "#ef4444" if event_type == "Stuck Pipe" else "#f97316" if event_type == "Mud Loss" else "#eab308" if event_type == "Torque Spike" else "#22c55e"
                
                st.markdown(
                    f"""
                    <div class="analog-well-card">
                        <div class="analog-header">
                            <span class="analog-name"> {well.get('name', 'Well')} ({well.get('well_id')})</span>
                            <span class="analog-sim-badge">{well.get('similarity', 0):.0f}% Match</span>
                        </div>
                        <div class="analog-detail">
                            <b>Distance:</b> {well.get('distance_km', '-')} km &nbsp;│&nbsp; <b>Zone:</b> {well.get('formation_at_2780', 'N/A')}
                        </div>
                        <div class="analog-detail" style="margin-top: 2px;">
                            <b>Historical Event:</b> <span style="color: {event_badge_color}; font-weight: 800;">{event_type}</span> @ {well.get('event_md', 'N/A')} m
                        </div>
                        <div style="font-size: 11px; color: #94a3b8; font-style: italic; margin-top: 4px;">
                            "{well.get('event_note', 'No notes logged.')}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("ℹ️ No offset wells found in this search radius and depth corridor. Try increasing the buffer radius.")


# ---------------------------------------------------------------------
# TAB 2: OFFSET RECORDS & DEEP-DIVE
# ---------------------------------------------------------------------
with tab2:
    if nearby_wells:
        sorted_wells = sorted(
            nearby_wells,
            key=lambda w: w.get("similarity", 0.0),
            reverse=True,
        )

        # 1. PULL UP: Offset Well Intelligence Records Table
        t_head_col, t_btn_col = st.columns([2.0, 1.0])
        with t_head_col:
            st.markdown('<div class="section-header"> Offset Well Intelligence Records</div>', unsafe_allow_html=True)
        with t_btn_col:
            handover_df = generate_handover_report_df(sorted_wells)
            csv_data = handover_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=" Export Well Records (CSV)",
                data=csv_data,
                file_name=f"nwis_offset_wells_{active_well.get('name', 'OIL-DLJ-99')}_{current_telemetry['depth']:.0f}m.csv",
                mime="text/csv",
                help="Download the prioritized offset well table as a CSV.",
                use_container_width=True,
            )

        table_df = pd.DataFrame(sorted_wells)
        display_cols = ["similarity", "name", "well_id", "distance_km", "formation_at_2780", "event_type", "event_md"]
        avail_cols = [c for c in display_cols if c in table_df.columns]

        event = st.dataframe(
            table_df[avail_cols],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "similarity": st.column_config.ProgressColumn(
                    "Analog Similarity",
                    min_value=0,
                    max_value=100,
                    format="%.0f%%",
                ),
                "name": st.column_config.TextColumn("Well Name", width="medium"),
                "well_id": st.column_config.TextColumn("Well ID", width="small"),
                "distance_km": st.column_config.NumberColumn("Distance", format="%.2f km"),
                "formation_at_2780": st.column_config.TextColumn("Formation Zone"),
                "event_type": st.column_config.TextColumn("Historical Incident"),
                "event_md": st.column_config.NumberColumn("Incident Depth", format="%.0f m"),
            },
        )

        # 2. MOVE DOWN: Offset Well Deep-Diver
        st.markdown('<div class="section-header" style="margin-top: 24px;"> Offset Well Deep-Diver</div>', unsafe_allow_html=True)

        selected_rows = event.selection.rows
        if selected_rows:
            selected_well = sorted_wells[selected_rows[0]]
        else:
            selected_well = sorted_wells[0]
            st.info(" Click on any well row in the table above to dynamically view its deep-dive details!")

        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Geographic Distance", f"{selected_well.get('distance_km', 0):.2f} km")
        d_col2.metric("Analog Match Score", f"{selected_well.get('similarity', 0):.0f}%")
        d_col3.metric("Incident Depth", f"{selected_well.get('event_md', 'N/A')} m" if selected_well.get('event_md') else "N/A")
        d_col4.metric("Incident Classification", selected_well.get("event_type", "None"))

        # --- NEW MITIGATION & VISUAL RADAR ---
        evt = selected_well.get('event_type', '')
        if "Stuck" in evt:
            mitigation = " <b>STANDARD MITIGATION:</b> Halt rotation and circulation immediately. Jar up/down based on overpull limits. Prepare pipe-freeing pill (LCM/Acid)."
            icon = ""
        elif "Loss" in evt:
            mitigation = " <b>STANDARD MITIGATION:</b> Reduce pump rates immediately. Monitor trip tank strictly. Prepare Loss Circulation Material (LCM) pills."
            icon = ""
        elif "Kick" in evt or "Gas" in evt:
            mitigation = " <b>STANDARD MITIGATION:</b> Hard shut-in the well. Record SIDPP/SICP. Prepare well control kill procedures (Driller's Method)."
            icon = ""
        elif "Torque" in evt:
            mitigation = " <b>STANDARD MITIGATION:</b> Pick up off bottom, check for drag. Circulate bottoms up. Re-evaluate mud lubricity."
            icon = ""
        elif "Shale" in evt:
            mitigation = " <b>STANDARD MITIGATION:</b> Increase mud weight for stabilization. Limit swabbing speeds on trips. Circulate well."
            icon = ""
        else:
            mitigation = " <b>STANDARD MITIGATION:</b> Maintain standard operational parameters. Proceed with normal drilling vigilance."
            icon = ""
            
        incident_depth = selected_well.get('event_md', 0)
        current_depth = current_telemetry['depth']
        
        if incident_depth:
            depth_diff = incident_depth - current_depth
            if depth_diff > 0:
                proximity_msg = f"[!] Incident is <b>{depth_diff:.0f} m below</b> current bit depth."
                prox_color = "#eab308" # yellow
            elif depth_diff < 0:
                proximity_msg = f" Incident is <b>{abs(depth_diff):.0f} m above</b> current bit depth."
                prox_color = "#22c55e" # green
            else:
                proximity_msg = f" <b>CURRENTLY AT INCIDENT DEPTH</b>"
                prox_color = "#ef4444" # red
                
            min_d = max(0, current_depth - 150)
            max_d = current_depth + 150
            vis_incident = max(min_d, min(max_d, incident_depth))
            curr_pct = ((current_depth - min_d) / (max_d - min_d)) * 100
            inc_pct = ((vis_incident - min_d) / (max_d - min_d)) * 100
            
            depth_visual_html = f'''
<div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:16px; height: 100%; text-align:center;">
<div style="color:#f8fafc; margin-top:0; font-size: 14px; font-weight:800;"> Depth Proximity Radar</div>
<div style="color:{prox_color}; font-size:12px; margin-bottom:12px;">{proximity_msg}</div>

<div style="position:relative; height:150px; width:40px; margin:0 auto; background:#1e293b; border-radius:20px; border:1px solid #334155;">
<!-- Incident marker -->
<div style="position:absolute; top:{100-inc_pct}%; left:-10px; width:60px; height:3px; background:#ef4444; z-index:2; box-shadow: 0 0 6px #ef4444;"></div>
<div style="position:absolute; top:calc({100-inc_pct}% - 7px); left:60px; color:#ef4444; font-size:10px; font-weight:bold; white-space:nowrap;">Event ({incident_depth}m)</div>

<!-- Current bit marker -->
<div style="position:absolute; top:{100-curr_pct}%; left:-5px; width:50px; height:3px; background:#38bdf8; z-index:3; box-shadow: 0 0 6px #38bdf8;"></div>
<div style="position:absolute; top:calc({100-curr_pct}% - 7px); right:55px; color:#38bdf8; font-size:10px; font-weight:bold; white-space:nowrap;">Bit ({current_depth}m)</div>

<!-- Drill string visual -->
<div style="position:absolute; top:0; left:16px; width:8px; height:{100-curr_pct}%; background:linear-gradient(#94a3b8, #cbd5e1); border-radius:4px 4px 0 0;"></div>
<!-- Drill bit visual -->
<div style="position:absolute; top:{100-curr_pct}%; left:12px; width:16px; height:12px; background:#f59e0b; clip-path: polygon(0 0, 100% 0, 50% 100%);"></div>
</div>
<div style="font-size:10px; color:#64748b; margin-top:10px;">Relative to ±150m corridor</div>
</div>
            '''
        else:
            depth_visual_html = f'''
<div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:16px; height: 100%; text-align:center;">
<div style="color:#f8fafc; margin-top:0; font-size: 14px; font-weight:800;"> Depth Proximity Radar</div>
<div style="color:#64748b; font-size:12px; margin-top:50px;">No incident depth available.</div>
</div>
            '''

        dd_col1, dd_col2 = st.columns([1.7, 1.0])
        with dd_col1:
            st.markdown(
                f'''
                <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:16px; height: 100%;">
                    <div style="border-bottom:1px solid #1e293b; padding-bottom:8px; margin-bottom:12px;">
                        <span style="font-size:16px; font-weight:800; color:#f8fafc;">{icon} {selected_well.get('name')} ({selected_well.get('well_id')})</span>
                        <span style="float:right; font-size:13px; color:#38bdf8; font-weight:700;">Field: {selected_well.get('field', 'Duliajan')}</span>
                    </div>
                    <div style="font-size:13px; color:#cbd5e1; margin-bottom: 12px; line-height: 1.6;">
                        <b>Target Formation:</b> {selected_well.get('formation_at_2780', 'N/A')}<br>
                        <b>Geological Hazard:</b> <span style="color:#ef4444; font-weight:bold;">{selected_well.get('event_type', 'None')}</span><br>
                        <b>Analog Match:</b> {selected_well.get('similarity', 0):.0f}% Similar Signature
                    </div>
                    <div style="padding:10px; background:#1e293b; border-left:4px solid #38bdf8; border-radius:4px; font-size:12.5px; color:#e2e8f0;">
                        <b>Engineering Remarks:</b><br> {selected_well.get('event_note') if selected_well.get('event_note') else 'No historical drilling anomalies logged.'}
                    </div>
                    <div style="margin-top:12px; padding:10px; background:#450a0a; border:1px solid #dc2626; border-radius:4px; font-size:12.5px; color:#fecaca;">
                        {mitigation}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            
        with dd_col2:
            st.markdown(depth_visual_html, unsafe_allow_html=True)

    else:
        st.info("ℹ️ No offset wells found in this search corridor.")


# ---------------------------------------------------------------------
# TAB 3: OFFSET TRENDS & ANALYTICS
# ---------------------------------------------------------------------
with tab3:
    st.markdown('<div class="section-header"> Offset Incident Patterns & Analog Rankings</div>', unsafe_allow_html=True)

    if nearby_wells:
        analytics_df = pd.DataFrame(nearby_wells)

        ch_col1, ch_col2 = st.columns([1.4, 1.0], gap="large")

        with ch_col1:
            st.markdown("###  Offset Wells Ranked by Analog Similarity")
            ranked_chart_df = analytics_df.sort_values("similarity", ascending=True)

            ranking_chart = (
                alt.Chart(ranked_chart_df)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                .encode(
                    y=alt.Y("name:N", title="Offset Well Name", sort=None),
                    x=alt.X("similarity:Q", title="Analog Match Similarity (%)", scale=alt.Scale(domain=[0, 100])),
                    color=alt.Color(
                        "event_type:N",
                        title="Incident Type",
                        scale=alt.Scale(
                            domain=["Stuck Pipe", "Mud Loss", "Torque Spike", "None"],
                            range=["#ef4444", "#f97316", "#eab308", "#22c55e"]
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("name:N", title="Well"),
                        alt.Tooltip("well_id:N", title="ID"),
                        alt.Tooltip("distance_km:Q", title="Distance (km)"),
                        alt.Tooltip("formation_at_2780:N", title="Formation"),
                        alt.Tooltip("event_type:N", title="Incident"),
                        alt.Tooltip("similarity:Q", title="Similarity (%)"),
                    ]
                )
                .properties(height=max(320, len(ranked_chart_df) * 20))
            )
            st.altair_chart(ranking_chart, use_container_width=True)

        with ch_col2:
            st.markdown("###  Corridor Incident Hazard Breakdown")
            incident_summary_df = (
                analytics_df["event_type"]
                .value_counts()
                .reset_index()
            )
            incident_summary_df.columns = ["Incident Type", "Well Count"]

            donut_chart = (
                alt.Chart(incident_summary_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Incident Type:N", title="Incident Classification"),
                    y=alt.Y("Well Count:Q", title="Number of Wells"),
                    color=alt.Color(
                        "Incident Type:N",
                        scale=alt.Scale(
                            domain=["Stuck Pipe", "Mud Loss", "Torque Spike", "None"],
                            range=["#ef4444", "#f97316", "#eab308", "#22c55e"]
                        ),
                        legend=None
                    ),
                    tooltip=["Incident Type:N", "Well Count:Q"]
                )
                .properties(height=320)
            )
            st.altair_chart(donut_chart, use_container_width=True)

            st.markdown(
                f"""
                <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:12px; font-size:13px; color:#cbd5e1; margin-top:8px;">
                    <b>Corridor Statistical Summary:</b><br>
                    • Total Offset Analogs Analyzed: <b>{len(analytics_df)}</b> wells<br>
                    • Critical Stuck-Pipe Incidents: <b style="color:#ef4444;">{stuck_pipe_count}</b><br>
                    • Mud Loss Incidents: <b style="color:#f97316;">{mud_loss_count}</b><br>
                    • Torque Spike Anomalies: <b style="color:#eab308;">{torque_spike_count}</b><br>
                    • Clean Uneventful Wells: <b style="color:#22c55e;">{len(analytics_df) - stuck_pipe_count - mud_loss_count - torque_spike_count}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ️ No offset wells in the current search corridor.")


# ---------------------------------------------------------------------
# TAB 4: LIVE TELEMETRY & SAFE OPERATING ENVELOPES
# ---------------------------------------------------------------------
with tab4:
    # Calculate MSE (Mechanical Specific Energy) - Teale's Formula
    bit_area = 56.75  # 8.5" hole = 56.75 sq.in.
    _rop_val = max(0.01, float(current_telemetry['rop']))
    _rpm_val = float(current_telemetry['rpm'])
    _torque_val = float(current_telemetry['torque'])
    _wob_val = float(current_telemetry['wob'])
    mse_val = (_wob_val * 1000 / bit_area) + (13.33 * _rpm_val * _torque_val) / (bit_area * _rop_val)
    mse_val = round(mse_val / 1000, 1)  # Convert to kpsi
    mse_color = "#ef4444" if mse_val > 160.0 else "#eab308" if mse_val > 90.0 else "#22c55e"
    mse_status = "Critical Pack-Off / Bit Balling" if mse_val > 160.0 else "Elevated Mechanical Drag" if mse_val > 90.0 else "Optimal Rock Cutting Efficiency"

    st.markdown('<div class="section-header"> Live Surface Telemetry & Mechanical Energy HUD</div>', unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        st.metric("ROP", f"{current_telemetry['rop']:.1f} m/h")
    with t2:
        st.metric("RPM", f"{current_telemetry['rpm']:.0f} RPM")
    with t3:
        torque_val = current_telemetry['torque']
        st.metric("Torque", f"{torque_val:.0f} ft-lb", delta="Elevated" if torque_val > 4500 else "Nominal", delta_color="inverse")
    with t4:
        st.metric("WOB", f"{current_telemetry['wob']:.1f} klb")
    with t5:
        st.metric("MSE (Teale)", f"{mse_val:.1f} kpsi", delta="High Inefficiency" if mse_val > 120 else "Nominal", delta_color="inverse")

    # Dedicated MSE Rock Mechanics Analyzer Card
    mse_pct = min(100, max(5, int((mse_val / 220.0) * 100)))
    st.markdown(
        f"""
        <div style="background: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 14px 18px; margin: 14px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 13px; font-weight: 800; color: #f8fafc; text-transform: uppercase; letter-spacing: 0.06em;">
                    Teale's Mechanical Specific Energy (MSE) Cutting Dynamics
                </span>
                <span style="font-size: 11px; font-weight: 800; color: {mse_color}; background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 4px; border: 1px solid {mse_color};">
                    {mse_status.upper()}
                </span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin: 6px 0;">
                <span style="font-family: ui-monospace, Consolas, monospace; font-size: 26px; font-weight: 800; color: {mse_color};">
                    {mse_val:.1f}
                </span>
                <span style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">kpsi</span>
                <span style="font-size: 12px; color: #94a3b8; margin-left: 12px;">
                    Rock Compressive Baseline: <b>~45.0 kpsi</b> &nbsp;│&nbsp; Energy Efficiency Factor: <b style="color: {mse_color};">{'Low (Severe Friction)' if mse_val > 120 else 'High (Pure Cutting)'}</b>
                </span>
            </div>
            <div style="background: rgba(255,255,255,0.08); height: 6px; border-radius: 3px; margin: 8px 0; overflow: hidden;">
                <div style="background: {mse_color}; height: 100%; width: {mse_pct}%; transition: width 0.3s ease;"></div>
            </div>
            <div style="font-size: 11px; color: #64748b; font-family: ui-monospace, Consolas, monospace;">
                Formula: MSE = (WOB / A<sub>bit</sub>) + (13.33 × RPM × Torque) / (A<sub>bit</sub> × ROP) &nbsp;│&nbsp; 8.5" Hole Area = 56.75 sq.in.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header" style="margin-top: 14px;"> Real-Time Telemetry vs. Safe Operating Envelopes</div>', unsafe_allow_html=True)
    
    e1, e2 = st.columns(2, gap="medium")
    
    with e1:
        # ROP Envelope
        rop_curr = current_telemetry["rop"]
        rop_cfg = TELEMETRY_THRESHOLDS["rop"]
        rop_status = "[!] High Penetration Rate" if rop_curr > rop_cfg["high_risk"] else "[!] Low ROP (Pack-off Risk)" if rop_curr < rop_cfg["min"] else " Operating in Safe Zone"
        rop_color = "#ef4444" if rop_curr > rop_cfg["high_risk"] else "#eab308" if rop_curr < rop_cfg["min"] else "#22c55e"
        
        st.markdown(
            f"""
            <div class="envelope-card">
                <div class="envelope-title">Rate of Penetration (ROP)</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span style="font-size:24px; font-weight:800; color:#f8fafc;">{rop_curr:.1f} m/hr</span>
                    <span style="color:{rop_color}; font-weight:800; font-size:13px; background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">{rop_status}</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin: 8px 0 6px 0; overflow: hidden;">
                    <div style="background: {rop_color}; height: 100%; width: {min(100, max(5, int((rop_curr / 45.0) * 100)))}%;"></div>
                </div>
                <div style="font-size:11px; color:#94a3b8;">
                    Safe Working Range: <b>{rop_cfg['min']} – {rop_cfg['normal_max']} m/hr</b> &nbsp;│&nbsp; High Risk Threshold: <b>> {rop_cfg['high_risk']} m/hr</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Torque Envelope
        torque_curr = current_telemetry["torque"]
        torque_cfg = TELEMETRY_THRESHOLDS["torque"]
        torque_status = " Critical Over-Torque" if torque_curr > torque_cfg["high_risk"] else "[!] Elevated Mechanical Drag" if torque_curr > torque_cfg["normal_max"] else "[!] Low Torque" if torque_curr < torque_cfg["min"] else " Safe Operational Torque"
        torque_color = "#ef4444" if torque_curr > torque_cfg["high_risk"] else "#eab308" if (torque_curr > torque_cfg["normal_max"] or torque_curr < torque_cfg["min"]) else "#22c55e"
        
        st.markdown(
            f"""
            <div class="envelope-card">
                <div class="envelope-title">Surface Torque</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span style="font-size:24px; font-weight:800; color:#f8fafc;">{torque_curr:.0f} ft-lbs</span>
                    <span style="color:{torque_color}; font-weight:800; font-size:13px; background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">{torque_status}</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin: 8px 0 6px 0; overflow: hidden;">
                    <div style="background: {torque_color}; height: 100%; width: {min(100, max(5, int((torque_curr / 8000.0) * 100)))}%;"></div>
                </div>
                <div style="font-size:11px; color:#94a3b8;">
                    Safe Working Range: <b>{torque_cfg['min']} – {torque_cfg['normal_max']} ft-lbs</b> &nbsp;│&nbsp; Critical Threshold: <b>> {torque_cfg['high_risk']} ft-lbs</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with e2:
        # RPM Envelope
        rpm_curr = current_telemetry["rpm"]
        rpm_cfg = TELEMETRY_THRESHOLDS["rpm"]
        rpm_status = "[!] Drill String Vibration Hazard" if rpm_curr > rpm_cfg["high_risk"] else "[!] Low RPM (Sticking Risk)" if rpm_curr < rpm_cfg["min"] else " Safe Rotary Range"
        rpm_color = "#ef4444" if rpm_curr > rpm_cfg["high_risk"] else "#eab308" if rpm_curr < rpm_cfg["min"] else "#22c55e"
        
        st.markdown(
            f"""
            <div class="envelope-card">
                <div class="envelope-title">Rotary Speed (RPM)</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span style="font-size:24px; font-weight:800; color:#f8fafc;">{rpm_curr:.0f} RPM</span>
                    <span style="color:{rpm_color}; font-weight:800; font-size:13px; background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">{rpm_status}</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin: 8px 0 6px 0; overflow: hidden;">
                    <div style="background: {rpm_color}; height: 100%; width: {min(100, max(5, int((rpm_curr / 220.0) * 100)))}%;"></div>
                </div>
                <div style="font-size:11px; color:#94a3b8;">
                    Safe Working Range: <b>{rpm_cfg['min']} – {rpm_cfg['normal_max']} RPM</b> &nbsp;│&nbsp; Harmonic Vibration Limit: <b>> {rpm_cfg['high_risk']} RPM</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # WOB Envelope
        wob_curr = current_telemetry["wob"]
        wob_cfg = TELEMETRY_THRESHOLDS["wob"]
        wob_status = " String Buckling Risk" if wob_curr > wob_cfg["high_risk"] else "[!] Low WOB (Poor Drilling)" if wob_curr < wob_cfg["min"] else " Safe Bit Loading"
        wob_color = "#ef4444" if wob_curr > wob_cfg["high_risk"] else "#eab308" if wob_curr < wob_cfg["min"] else "#22c55e"
        
        st.markdown(
            f"""
            <div class="envelope-card">
                <div class="envelope-title">Weight on Bit (WOB)</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span style="font-size:24px; font-weight:800; color:#f8fafc;">{wob_curr:.1f} klbs</span>
                    <span style="color:{wob_color}; font-weight:800; font-size:13px; background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">{wob_status}</span>
                </div>
                <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin: 8px 0 6px 0; overflow: hidden;">
                    <div style="background: {wob_color}; height: 100%; width: {min(100, max(5, int((wob_curr / 35.0) * 100)))}%;"></div>
                </div>
                <div style="font-size:11px; color:#94a3b8;">
                    Safe Working Range: <b>{wob_cfg['min']} – {wob_cfg['normal_max']} klbs</b> &nbsp;│&nbsp; Buckling Limit: <b>> {wob_cfg['high_risk']} klbs</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# TAB 5: SEARCHABLE KNOWLEDGE REPOSITORY
# ---------------------------------------------------------------------
with tab5:

    st.markdown('<div class="section-header"> Automated Document Ingestion (OCR/NLP)</div>', unsafe_allow_html=True)
    st.markdown("Upload unstructured Daily Drilling Reports (DDR) or Well Completion Reports. Gemini AI will automatically extract geological hazards and append them to the Postgres Knowledge Base.")
    
    with st.expander(" Upload & Ingest New Document", expanded=False):
        raw_report = st.text_area("Paste Raw Report Text (PDF/TXT content)", height=150, placeholder="e.g., On 12-Oct, Well OIL-ABC-99 experienced a severe stuck pipe at 2650m in the Barail Sandstone due to differential sticking. Spotted 50bbl of pipe laxative to free string...")
        if st.button("Extract & Structure Knowledge"):
            if raw_report:
                with st.spinner(" Gemini AI is extracting parameters..."):
                    import api_client
                    result = api_client.ingest_historical_report(raw_report)
                    if result.get("status") == "success":
                        st.success(" Document successfully structured and ingested into PostgreSQL!")
                        st.json(result["extracted_data"])
                    else:
                        st.error(f"Ingestion failed: {result.get('message')}")
            else:
                st.warning("Please paste some text first.")
    
    st.markdown("---")

    st.markdown('<div class="section-header"> Searchable Knowledge Repository</div>', unsafe_allow_html=True)
    st.markdown("Ask natural language questions about historical drilling events, lessons learned, and operational challenges.")
    st.markdown("**Examples:** *What Gas Kicks happened at 2800m in Kopili Shale?* · *Show stuck pipe incidents above 3000m*")

    search_query = st.text_input("Search Query", placeholder="e.g. What were the major incidents at 2800m in Kopili Shale?", key="nlp_search_input", label_visibility="collapsed")
    col_btn, col_hint = st.columns([1, 4])
    with col_btn:
        search_clicked = st.button(" Search", key="nlp_search_btn", use_container_width=True)
    with col_hint:
        st.caption("Powered by Gemini NLP · Queries your full historical drilling event database")

    if search_clicked:
        if search_query:
            with st.spinner(" AI parsing query and searching database..."):
                import requests
                from config import BACKEND_URL
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/api/search_knowledge",
                        json={
                            "question": search_query,
                            "lat": 27.35,
                            "lon": 95.32,
                            "radius_km": float(st.session_state.get("active_radius_km", 50.0))
                        },
                        timeout=60
                    )
                    res.raise_for_status()
                    data = res.json()

                    if "error" in data:
                        st.error(f"❌ {data['error']}")
                    else:
                        intel = data.get("historical_intelligence", {})
                        events = intel.get("historical_events", [])
                        pattern = intel.get("pattern_analysis", {})
                        parsed = data.get("parsed_query", {})

                        p_depth = parsed.get("current_depth", "?")
                        p_form = parsed.get("formation", "?")
                        p_evtype = parsed.get("event_type") or "All types"
                        p_tol = parsed.get("depth_tolerance", 100)
                        st.markdown(f"""
<div style="background:#0d2035;border:1px solid #00d4ff55;border-radius:8px;padding:12px 18px;margin:10px 0 16px 0;">
  <span style="color:#00d4ff;font-size:0.85rem;font-weight:700;letter-spacing:1px;"> AI PARSED YOUR QUERY</span><br>
  <span style="color:#cdd6f4;">Depth: </span><b style="color:#fadb14">{p_depth} m</b>&emsp;
  <span style="color:#cdd6f4;">Formation: </span><b style="color:#fadb14">{p_form}</b>&emsp;
  <span style="color:#cdd6f4;">Event Filter: </span><b style="color:#fadb14">{p_evtype}</b>&emsp;
  <span style="color:#cdd6f4;">Depth Window: </span><b style="color:#fadb14">±{p_tol} m</b>
</div>""", unsafe_allow_html=True)

                        if not events:
                            st.warning("[!] No historical events matched your query. Try widening the depth window or checking the formation name.")
                        else:
                            total = pattern.get("total_events", len(events))
                            unique_w = pattern.get("unique_wells", 0)
                            most_common = pattern.get("most_common_event", "N/A")
                            avg_depth = pattern.get("average_depth", 0)

                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric(" Incidents Found", total)
                            m2.metric(" Unique Wells", unique_w)
                            m3.metric("[!] Dominant Event", most_common)
                            m4.metric(" Avg Depth", f"{avg_depth} m")

                            st.markdown(f"---")
                            st.markdown(f"**{total} result(s) — sorted by relevance score:**")

                            EVENT_COLOR = {
                                "Stuck Pipe Incident": "#ff4b4b",
                                "Gas Kick": "#ff4b4b",
                                "Severe Mud Loss": "#f7a800",
                                "Shale Instability": "#f7a800",
                                "Torque Spike": "#f7a800",
                                "Normal Operation": "#00cc6a",
                            }
                            EVENT_ICON = {
                                "Stuck Pipe Incident": "",
                                "Gas Kick": "[GAS]",
                                "Severe Mud Loss": "[FLUID]",
                                "Shale Instability": "",
                                "Torque Spike": "",
                                "Normal Operation": "",
                            }

                            for ev in events:
                                ev_type = ev.get("event_type", "Unknown")
                                color = EVENT_COLOR.get(ev_type, "#888888")
                                icon = EVENT_ICON.get(ev_type, "")
                                well_id = ev.get("well_id", "?")
                                depth_m = ev.get("depth_m", "?")
                                form = ev.get("formation", "?")
                                score = ev.get("relevance_score", 0)
                                depth_diff = ev.get("depth_difference_m", 0)
                                cause = ev.get("cause", "Not recorded")
                                mitigation = ev.get("mitigation", "Not recorded")
                                outcome = ev.get("outcome", "Not recorded")

                                lbl = f"{icon}  **{well_id}** — {ev_type}  |  Depth: **{depth_m} m**  |  Relevance: **{score:.0f}%**  |  Δ{depth_diff:.0f} m from query depth"
                                with st.expander(lbl, expanded=False):
                                    ca, cb, cc = st.columns(3)
                                    ca.markdown("** Well**\n\n`" + str(well_id) + "`")
                                    cb.markdown("** Formation**\n\n`" + str(form) + "`")
                                    cc.markdown("** Depth**\n\n`" + str(depth_m) + " m`")
                                    st.markdown(f"""
<div style="border-left:4px solid {color};padding:10px 16px;background:#0a1929;border-radius:0 6px 6px 0;margin-top:10px;">
  <div style="margin-bottom:6px;"><span style="color:{color};font-weight:700;">{icon} Incident Type:</span> <span style="color:#e0e0e0;">{ev_type}</span></div>
  <div style="margin-bottom:6px;"><span style="color:#f7a800;font-weight:700;">[CAUSE] Root Cause:</span> <span style="color:#e0e0e0;">{cause}</span></div>
  <div style="margin-bottom:6px;"><span style="color:#00d4ff;font-weight:700;">[ACTION] Mitigation:</span> <span style="color:#e0e0e0;">{mitigation}</span></div>
  <div style="margin-bottom:6px;"><span style="color:#00cc6a;font-weight:700;">[RESULT] Outcome:</span> <span style="color:#e0e0e0;">{outcome}</span></div>
  <div style="margin-top:8px;padding-top:8px;border-top:1px solid #1e293b;"><span style="color:#a855f7;font-weight:700;">[INFO] Event Summary:</span> <span style="color:#cbd5e1;">Historical incident of {ev_type} recorded at {depth_m}m in {form}. Root cause analyzed as {cause}, addressed via {mitigation}, resulting in {outcome}.</span></div>
</div>""", unsafe_allow_html=True)


                            import streamlit.components.v1 as components
                            components.html(
                                '''
                                <script>
                                    var elements = window.parent.document.querySelectorAll('.stExpander');
                                    if (elements.length > 0) {
                                        elements[0].scrollIntoView({behavior: 'smooth', block: 'start'});
                                    }
                                </script>
                                ''', height=0
                            )

                except Exception as e:
                    st.error(f"Search failed: {e}")
        else:
            st.warning("Please enter a search query.")


# =====================================================================
# LAZY AI LOADING (Executes after the rest of the UI has rendered)
# =====================================================================
if st.session_state.get("pending_ai_payload"):
    payload = st.session_state["pending_ai_payload"]
    st.session_state["pending_ai_payload"] = None # Clear it so it doesn't run again on next interaction
    

    import importlib
    ai_result = api_client.generate_ai_summary(payload)
    
    # Update state and UI
    st.session_state["ai_summary"] = ai_result.get("explanation", "AI analysis unavailable.")
    render_directive(st.session_state["ai_summary"])

# =====================================================================
# REAL-TIME SIMULATOR LOOP
# =====================================================================
if st.session_state.get("live_sim_toggle"):
    import time
    time.sleep(1.0) # Slowed down to 1.0s (1 FPS) to prevent Map/WebGL crashing and blackouts
    
    import random
    
    # Base physics state from session or defaults
    current_depth = st.session_state.get("sim_depth", 2480.0)
    current_torque = st.session_state.get("sim_torque", 3500.0)
    current_rop = st.session_state.get("sim_rop", float(rop))
    current_rpm = st.session_state.get("sim_rpm", float(rpm))
    current_wob = st.session_state.get("sim_wob", float(wob))
    
    # 1. Depth increments dynamically based on ROP (meters/hr -> meters/sec approx)
    # Simulator runs 1 tick/sec. 36 m/hr = 0.01 m/sec. We speed it up 100x for the demo.
    depth_inc = max(1.0, current_rop * 0.15) + random.uniform(-0.5, 1.5)
    current_depth += depth_inc
    
    # Reset loop for demo purposes
    if current_depth > 2750.0:
        current_depth = 2480.0
        current_torque = 3200.0
        current_rop = 18.0
        current_rpm = 120.0
        current_wob = 8.0

    # 2. Physics Engine: Lithology-based Drilling Dynamics
    # We define geological "zones" that change the mechanical response
    if current_depth < 2550.0:
        # ZONE 1: Normal Shale (Smooth drilling)
        target_wob = 8.5
        target_rpm = 125.0
        target_torque = 3200.0 + (current_wob * 100.0)
        target_rop = 22.0
    elif current_depth < 2620.0:
        # ZONE 2: Hard Sandstone Stringers (Requires more WOB, generates high torque, drops ROP)
        target_wob = 16.5
        target_rpm = 90.0
        target_torque = 4800.0 + (current_wob * 150.0)
        target_rop = 8.5
    elif current_depth < 2680.0:
        # ZONE 3: Fractured Fault Zone (Erratic, Stick-Slip behavior)
        target_wob = 10.0 + random.uniform(-5.0, 5.0)
        target_rpm = 110.0 + random.uniform(-40.0, 40.0)
        # Torque spikes violently then releases (Stick-Slip)
        target_torque = random.choice([2500.0, 5700.0, 6200.0, 3800.0]) 
        target_rop = 14.0
    else:
        # ZONE 4: Washout / Cavings (Loss of bit contact)
        target_wob = 2.5
        target_rpm = 140.0
        target_torque = 1800.0
        target_rop = 28.0

    # 3. Apply Random Walk / Smoothing towards targets
    # This prevents instant snaps and creates realistic moving gauges
    current_wob += (target_wob - current_wob) * 0.3 + random.uniform(-1.2, 1.2)
    current_rpm += (target_rpm - current_rpm) * 0.2 + random.uniform(-5.0, 5.0)
    current_torque += (target_torque - current_torque) * 0.25 + random.uniform(-150.0, 150.0)
    current_rop += (target_rop - current_rop) * 0.15 + random.uniform(-2.0, 2.0)
    
    # Safety clamps
    current_wob = max(0.0, current_wob)
    current_rpm = max(10.0, current_rpm)
    current_rop = max(0.0, current_rop)
    
    # Store state
    st.session_state["sim_depth"] = current_depth
    st.session_state["sim_torque"] = current_torque
    st.session_state["sim_rop"] = current_rop
    st.session_state["sim_rpm"] = current_rpm
    st.session_state["sim_wob"] = current_wob
    
    # Format variables to map to existing logic payload names
    sim_rop = current_rop
    sim_rpm = current_rpm
    sim_wob = current_wob
    
    # Generate backend payload for the simulation tick
    sim_payload = {
        "location_area": f"{default_active_well.get('field', 'Duliajan')} {'Sector 4'}", "lat": default_active_well.get("lat", 27.35), "lon": default_active_well.get("lon", 95.32),
        "target_formation": selected_formation, "depth": float(current_depth),
        "rop": float(sim_rop), "rpm": float(sim_rpm), "torque": float(current_torque), "wob": float(sim_wob),
        "search_radius_km": float(radius_km), "depth_window": float(depth_window), "enable_ai": False
    }
    from api_client import analyze_drilling_risk
    st.session_state["dashboard_data"] = analyze_drilling_risk(sim_payload)
    st.session_state["telemetry"] = {"depth": current_depth, "rop": float(sim_rop), "rpm": float(sim_rpm), "torque": current_torque, "wob": float(sim_wob)}
    
    # We DO NOT trigger Gemini AI during live simulation to prevent rate limiting, 
    # the user can manually click 'Run' to generate the AI report once an anomaly is hit.
    st.rerun()

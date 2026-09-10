from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import pandas as pd
import streamlit as st

from wells_data import WELLS
from config import DATA_MODE, CACHE_TTL_SECONDS, PG_HOST, PG_PORT, PG_DATABASE, PG_USER
from gis_engine import get_nearby_wells, rank_wells

# =====================================================================
# DATA REPOSITORY INTERFACE & ADAPTERS (PostgreSQL / CSV / Local Ready)
# =====================================================================

class BaseWellRepository(ABC):
    """
    Abstract interface for well data access.
    Allows local in-memory records, CSV files, and future PostgreSQL
    database integrations to be swapped seamlessly without modifying
    business logic or Streamlit UI components.
    """

    @abstractmethod
    def get_all_wells(self) -> List[Dict[str, Any]]:
        """Retrieve all well records (active and offset wells)."""
        pass

    @abstractmethod
    def get_active_well(self) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active drilling well record."""
        pass


class LocalWellRepository(BaseWellRepository):
    """Local in-memory repository reading from wells_data.py."""

    def __init__(self, wells_data: Optional[List[Dict[str, Any]]] = None):
        self._wells = wells_data if wells_data is not None else WELLS

    def get_all_wells(self) -> List[Dict[str, Any]]:
        return [dict(w) for w in self._wells]

    def get_active_well(self) -> Optional[Dict[str, Any]]:
        for well in self._wells:
            if well.get("is_active") == 1:
                return dict(well)
        return None


class CSVWellRepository(BaseWellRepository):
    """CSV file repository for flexible flat-file dataset loading."""

    def __init__(self, csv_filepath: str):
        self.csv_filepath = csv_filepath

    def get_all_wells(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.csv_filepath):
            return [dict(w) for w in WELLS]
        df = pd.read_csv(self.csv_filepath)
        return df.to_dict(orient="records")

    def get_active_well(self) -> Optional[Dict[str, Any]]:
        wells = self.get_all_wells()
        for well in wells:
            if well.get("is_active") == 1:
                return well
        return None


class PostgresWellRepository(BaseWellRepository):
    """
    PostgreSQL repository stub.
    When database credentials and schema are finalized by backend team,
    integrate with psycopg2 / SQLAlchemy here.
    """

    def __init__(self, host: str = PG_HOST, port: int = PG_PORT,
                 database: str = PG_DATABASE, user: str = PG_USER):
        self.host = host
        self.port = port
        self.database = database
        self.user = user

    def get_all_wells(self) -> List[Dict[str, Any]]:
        return [dict(w) for w in WELLS]

    def get_active_well(self) -> Optional[Dict[str, Any]]:
        wells = self.get_all_wells()
        for well in wells:
            if well.get("is_active") == 1:
                return well
        return None


def get_well_repository(mode: str = DATA_MODE) -> BaseWellRepository:
    """Factory function returning the configured well repository."""
    if mode == "postgres":
        return PostgresWellRepository()
    elif mode == "csv" and os.path.exists("wells.csv"):
        return CSVWellRepository("wells.csv")
    else:
        return LocalWellRepository()


# =====================================================================
# CACHED DATA LOADERS & SUMMARY AGGREGATIONS
# =====================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_all_wells_df() -> pd.DataFrame:
    """Cached accessor for all wells as a Pandas DataFrame."""
    repo = get_well_repository()
    return pd.DataFrame(repo.get_all_wells())


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_dataset_summary() -> Dict[str, Any]:
    """
    Computes high-level overview statistics for instant dashboard loading.
    """
    df = load_all_wells_df()
    if df.empty:
        return {
            "total_wells": 0,
            "active_well": None,
            "formations": [],
            "incident_counts": {},
            "high_risk_count": 0,
            "fields": [],
        }

    active_rows = df[df["is_active"] == 1]
    active_well = active_rows.iloc[0].to_dict() if not active_rows.empty else None

    offset_df = df[df["is_active"] != 1]
    incident_counts = offset_df["event_type"].value_counts().to_dict()
    high_risk_count = int(incident_counts.get("Stuck Pipe", 0))

    formations = sorted(df["formation_at_2780"].dropna().unique().tolist())
    fields = sorted(df["field"].dropna().unique().tolist())

    return {
        "total_wells": len(df),
        "offset_wells_count": len(offset_df),
        "active_well": active_well,
        "formations": formations,
        "incident_counts": incident_counts,
        "high_risk_count": high_risk_count,
        "fields": fields,
    }


# =====================================================================
# CORE DASHBOARD DATA AGGREGATION
# =====================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _compute_dashboard_data(
    current_depth: float,
    radius_km: float,
    formation: str,
    depth_window: float,
) -> dict:
    """Internal cached calculation for offset well analysis."""
    repo = get_well_repository()
    all_wells = repo.get_all_wells()
    active_well = repo.get_active_well()

    if not active_well:
        return {
            "status": "error",
            "error": "No active well configured in the repository",
            "active_well": {},
            "nearby_wells": [],
            "historical_context": {},
            "ml_prediction": {},
        }

    # Find nearby wells using GIS engine (Haversine)
    nearby_wells = get_nearby_wells(
        lat=float(active_well["lat"]),
        lon=float(active_well["lon"]),
        radius_km=radius_km,
        wells=all_wells,
    )

    # Filter by formation
    if formation != "All":
        nearby_wells = [
            well
            for well in nearby_wells
            if well.get("formation_at_2780") == formation
        ]

    # Historical depth filter (± depth_window)
    depth_filtered_wells = []
    for well in nearby_wells:
        event_depth = well.get("event_md")
        if event_depth is None:
            continue

        try:
            event_depth = float(event_depth)
            depth_difference = abs(event_depth - current_depth)

            if depth_difference <= depth_window:
                well_copy = well.copy()
                well_copy["depth_difference"] = round(depth_difference, 1)
                depth_filtered_wells.append(well_copy)
        except (TypeError, ValueError):
            continue

    # Rank depth-filtered wells by similarity
    ranked_wells = rank_wells(
        nearby_wells=depth_filtered_wells,
        active_formation=active_well.get("formation_at_2780", "Formation X"),
        current_depth=current_depth,
        depth_window=depth_window,
    )

    # Count incidents
    stuck_pipe_count = sum(
        1
        for well in ranked_wells
        if well.get("event_type") == "Stuck Pipe"
    )
    mud_loss_count = sum(
        1
        for well in ranked_wells
        if well.get("event_type") == "Mud Loss"
    )
    torque_spike_count = sum(
        1
        for well in ranked_wells
        if well.get("event_type") == "Torque Spike"
    )

    # Risk level determination based on historical analog incident density
    if stuck_pipe_count >= 2:
        risk_score = 85.0
        risk_level = "CRITICAL"
        predicted_event = "Stuck Pipe"
        recommended_action = "Severe stuck-pipe analog cluster detected in this depth corridor. Increase circulation rate, monitor torque variance, and conduct a wiper trip before advancing bit depth."
    elif stuck_pipe_count == 1 or mud_loss_count >= 2:
        risk_score = 72.0
        risk_level = "HIGH"
        predicted_event = "Stuck Pipe / Mud Loss"
        recommended_action = "High historical incident density in offset corridor. Maintain steady drill string rotation, monitor cuttings return, and review mud weight."
    elif torque_spike_count >= 1 or mud_loss_count >= 1:
        risk_score = 48.0
        risk_level = "MEDIUM"
        predicted_event = "Torque Spike / Vibration"
        recommended_action = "Moderate mechanical risk detected. Adjust WOB to avoid stick-slip vibration and monitor surface torque closely."
    else:
        risk_score = 22.0
        risk_level = "LOW"
        predicted_event = "Normal Operations"
        recommended_action = "No high-severity offset incidents within current depth corridor. Continue drilling under standard operational parameters."

    historical_context = {
        "nearby_well_count": len(ranked_wells),
        "stuck_pipe_count": stuck_pipe_count,
        "mud_loss_count": mud_loss_count,
        "torque_spike_count": torque_spike_count,
        "evidence_string": (
            f"{len(ranked_wells)} historical offset wells identified "
            f"within ±{depth_window:.0f} m of the current depth ({current_depth:.0f} m)."
        ),
        "recommended_action": recommended_action,
    }

    risk_assessment = {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "predicted_event": predicted_event,
        "is_anomaly": risk_score >= 60.0,
    }

    return {
        "status": "success",
        "active_well": active_well,
        "nearby_wells": ranked_wells,
        "historical_context": historical_context,
        "risk_assessment": risk_assessment,
        "ml_prediction": risk_assessment,  # Backward compatible alias
    }


def get_local_dashboard_data(
    current_depth: float,
    radius_km: float,
    formation: str,
    depth_window: float,
) -> dict:
    """
    Public entry point for retrieving complete dashboard intelligence.
    Preserves exact API contract while using cached execution.
    """
    try:
        return _compute_dashboard_data(
            current_depth=float(current_depth),
            radius_km=float(radius_km),
            formation=str(formation),
            depth_window=float(depth_window),
        )
    except Exception as error:
        fallback_assessment = {
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "predicted_event": "Data unavailable",
            "is_anomaly": False,
        }
        return {
            "status": "error",
            "error": str(error),
            "active_well": {},
            "nearby_wells": [],
            "historical_context": {
                "nearby_well_count": 0,
                "stuck_pipe_count": 0,
                "mud_loss_count": 0,
                "torque_spike_count": 0,
                "evidence_string": "Data unavailable due to error",
                "recommended_action": "Unable to calculate recommendation",
            },
            "risk_assessment": fallback_assessment,
            "ml_prediction": fallback_assessment,
        }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_formation_risk_analytics() -> pd.DataFrame:
    """
    Computes aggregated incident risk metrics by formation across all offset wells.
    Used for geological lithology comparison charts.
    """
    df = load_all_wells_df()
    if df.empty:
        return pd.DataFrame()

    offset_df = df[df["is_active"] != 1].copy()
    
    records = []
    for formation, group in offset_df.groupby("formation_at_2780"):
        total = len(group)
        stuck_pipe = int(sum(group["event_type"] == "Stuck Pipe"))
        mud_loss = int(sum(group["event_type"] == "Mud Loss"))
        torque_spike = int(sum(group["event_type"] == "Torque Spike"))
        no_event = int(sum(group["event_type"] == "None"))
        
        incident_rate = round(((total - no_event) / total) * 100, 1) if total > 0 else 0.0
        stuck_rate = round((stuck_pipe / total) * 100, 1) if total > 0 else 0.0

        records.append({
            "Formation": formation,
            "Total Wells": total,
            "Stuck Pipe": stuck_pipe,
            "Mud Loss": mud_loss,
            "Torque Spike": torque_spike,
            "No Incident": no_event,
            "Incident Rate (%)": incident_rate,
            "Stuck-Pipe Rate (%)": stuck_rate,
        })

    return pd.DataFrame(records)


def generate_handover_report_df(nearby_wells: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Formats the corridor offset analog records into a structured
    Shift Handover & Toolpusher Risk Report DataFrame for CSV export.
    """
    if not nearby_wells:
        return pd.DataFrame()

    rows = []
    for w in nearby_wells:
        rows.append({
            "Well ID": w.get("well_id", ""),
            "Well Name": w.get("name", ""),
            "Field": w.get("field", ""),
            "Distance (km)": w.get("distance_km", 0.0),
            "Formation Zone": w.get("formation_at_2780", ""),
            "Historical Incident": w.get("event_type", "None"),
            "Incident Depth (m)": w.get("event_md", "N/A"),
            "Analog Match (%)": f"{w.get('similarity', 0.0):.0f}%",
            "Field Note / Remarks": w.get("event_note", ""),
        })

    return pd.DataFrame(rows)

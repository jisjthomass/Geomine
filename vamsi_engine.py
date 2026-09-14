import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVENTS_PATH = ROOT / "historical_drilling_events.sql"
INFRA_PATH = ROOT / "data" / "infrastructure.json"

EVENT_RULES = [
    ("Stuck Pipe Incident", ["stuck pipe", "stuck-pipe", "pack-off", "pack off", "packed off"]),
    ("Severe Mud Loss", ["severe mud loss", "mud loss", "lost circulation", "complete loss"]),
    ("Gas Kick", ["gas kick", "kick", "influx"]),
    ("High Torque", ["high torque", "torque spike", "erratic torque", "overpull"]),
    ("Shale Instability", ["shale instability", "wellbore instability", "sloughing"]),
    ("Normal Operation", ["normal operation", "standard drilling"]),
]

NPT_DEFAULT = {
    "Stuck Pipe Incident": ("StuckPipe", 360),
    "Severe Mud Loss": ("Losses", 180),
    "Gas Kick": ("Kick", 240),
    "High Torque": ("Other", 45),
    "Shale Instability": ("Other", 120),
    "Normal Operation": ("Other", 0),
}

EXTRACT_FALLBACK = {
    "well_id": None,
    "latitude": None,
    "longitude": None,
    "event_depth": None,
    "event_type": "Normal Operation",
    "formation": None,
    "summary_text": "",
    "npt_duration_minutes": 0,
    "npt_category": "Other",
    "raw_span": "",
    "error": None,
}

ENV_SAFE = {
    "environmental_risk_level": "SAFE",
    "infrastructure_type": "None",
    "infra_id": None,
    "distance_km": None,
    "infra_depth_m": None,
    "warning_message": "None",
    "error": None,
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _clean(text):
    return re.sub(r"\s+", " ", str(text or "").replace("\n", " ")).strip()


def extract_event(text: str) -> dict:
    """NLP fuel line. Thomas can pass OCR text or a DDR sentence."""
    out = dict(EXTRACT_FALLBACK)
    try:
        raw = _clean(text)
        if not raw:
            out["error"] = "empty_text"
            return out
        low = raw.lower()
        label, span = "Normal Operation", ""
        for name, keys in EVENT_RULES:
            if any(k in low for k in keys):
                label, span = name, keys[0]
                break
        depth = None
        m = re.search(r"(\d{3,5}(?:\.\d+)?)\s*m", raw, flags=re.I)
        if m:
            depth = float(m.group(1))
        well = None
        wm = re.search(r"\b(OIL-[A-Z]{2,4}-\d{2,4}|Well\s+[A-Z0-9-]+)\b", raw, flags=re.I)
        if wm:
            well = wm.group(1).upper().replace("WELL ", "OIL-")
        form = None
        fm = re.search(
            r"(Girujan Clay|Lakadong-Therria|Barail Coal-Shale|Tipam Sandstone|Kopili Shale|Formation\s+[A-Z0-9]+)",
            raw,
            flags=re.I,
        )
        if fm:
            form = fm.group(1)
        hours = None
        hm = re.search(r"(\d+(?:\.\d+)?)\s*(?:hrs|hours|hr)\b", raw, flags=re.I)
        if hm:
            hours = int(float(hm.group(1)) * 60)
        cat, mins = NPT_DEFAULT[label]
        out.update(
            {
                "well_id": well,
                "event_depth": depth,
                "event_type": label,
                "formation": form,
                "summary_text": raw,
                "npt_category": cat,
                "npt_duration_minutes": hours if hours is not None else mins,
                "raw_span": span,
                "error": None,
            }
        )
        return out
    except Exception:
        out["error"] = "timeout"
        return out


def load_events(path=None):
    """Load wells from historical_drilling_events.sql (COPY / tab rows)."""
    try:
        p = Path(path) if path else EVENTS_PATH
        if not p.exists():
            return []
        rows = []
        for raw in p.read_text(errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("--"):
                continue
            if not line[0].isdigit():
                continue
            if "OIL-" not in line:
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                parts = line.split(",", 8)
            if len(parts) < 8:
                continue
            try:
                rows.append(
                    {
                        "id": parts[0].strip(),
                        "well_id": parts[1].strip(),
                        "latitude": float(parts[2]),
                        "longitude": float(parts[3]),
                        "event_depth": float(parts[5]),
                        "event_type": parts[6].strip(),
                        "formation": parts[7].strip(),
                        "summary_text": parts[8].strip() if len(parts) > 8 else "",
                    }
                )
            except ValueError:
                continue
        return rows
    except Exception:
        return []


def get_nearby_wells(lat: float, lon: float, radius_km: float, events=None) -> list:
    """Offset-well engine. Uses Aaron table if present."""
    try:
        lat = float(lat)
        lon = float(lon)
        radius_km = float(radius_km)
        pool = events if events is not None else load_events()
        out = []
        for w in pool:
            dist = haversine_km(lat, lon, w["latitude"], w["longitude"])
            if dist <= radius_km:
                item = dict(w)
                item["distance_km"] = round(dist, 3)
                cat, mins = NPT_DEFAULT.get(w.get("event_type"), ("Other", 0))
                item["npt_category"] = cat
                item["npt_duration_minutes"] = mins
                out.append(item)
        out.sort(key=lambda r: r["distance_km"])
        return out
    except Exception:
        return []


def check_environmental_proximity(lat: float, lon: float, active_depth: float) -> dict:
    """Round-2 GIS contract. Never raises."""
    try:
        lat = float(lat)
        lon = float(lon)
        active_depth = float(active_depth)
    except (TypeError, ValueError):
        bad = dict(ENV_SAFE)
        bad.update(
            {
                "environmental_risk_level": "UNKNOWN",
                "warning_message": "Invalid coordinates or depth.",
                "error": "bad_input",
            }
        )
        return bad
    try:
        assets = json.loads(INFRA_PATH.read_text()) if INFRA_PATH.exists() else []
    except Exception:
        miss = dict(ENV_SAFE)
        miss.update({"error": "timeout", "warning_message": "Infrastructure table unavailable."})
        return miss
    hits = []
    for item in assets:
        try:
            dist = haversine_km(lat, lon, float(item["latitude"]), float(item["longitude"]))
            z_gap = abs(active_depth - float(item["depth_m"]))
            if dist <= float(item.get("safe_radius_km", 0.5)) and z_gap <= float(
                item.get("safe_depth_window_m", 100)
            ):
                hits.append((dist, z_gap, item))
        except (KeyError, TypeError, ValueError):
            continue
    if not hits:
        return dict(ENV_SAFE)
    hits.sort(key=lambda t: (t[0], t[1]))
    _, _, best = hits[0]
    kind = best.get("infra_type", "Unknown")
    level = "CRITICAL" if kind in ("Aquifer", "Pipeline") else "HIGH"
    return {
        "environmental_risk_level": level,
        "infrastructure_type": kind,
        "infra_id": best.get("infra_id"),
        "distance_km": round(hits[0][0], 3),
        "infra_depth_m": float(best["depth_m"]),
        "warning_message": (
            f"Drill path near {kind} '{best.get('name', '')}' "
            f"at asset depth {int(best['depth_m'])} m; bit at {int(active_depth)} m."
        ),
        "error": None,
    }

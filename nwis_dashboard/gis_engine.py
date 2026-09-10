import pandas as pd
from math import radians, sin, cos, sqrt, atan2


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    try:
        earth_radius_km = 6371.0

        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a_value = (
            sin(delta_lat / 2) ** 2
            + cos(radians(lat1))
            * cos(radians(lat2))
            * sin(delta_lon / 2) ** 2
        )

        return 2 * earth_radius_km * atan2(
            sqrt(a_value),
            sqrt(1 - a_value),
        )

    except Exception:
        return 0.0


def calculate_similarity(
    well: dict,
    active_formation: str,
    current_depth: float,
    depth_window: float,
) -> float:
    try:
        score = 0.0

        distance_km = well.get("distance_km", 999)

        if distance_km <= 2:
            score += 40
        elif distance_km <= 5:
            score += 25
        else:
            score += 10

        if well.get("formation_at_2780") == active_formation:
            score += 30

        event_depth = well.get("event_md")

        if (
            event_depth is not None
            and abs(float(event_depth) - current_depth) <= depth_window
        ):
            score += 30

        return min(score, 100.0)

    except Exception:
        return 0.0


def get_nearby_wells(
    lat: float,
    lon: float,
    radius_km: float,
    wells: list[dict],
) -> list[dict]:
    fallback_response = []

    try:
        nearby_wells = []

        for well in wells:
            if well.get("is_active") == 1:
                continue

            distance_km = haversine_km(
                lat,
                lon,
                float(well["lat"]),
                float(well["lon"]),
            )

            if distance_km <= radius_km:
                well_copy = well.copy()
                well_copy["distance_km"] = round(distance_km, 2)

                nearby_wells.append(well_copy)

        return nearby_wells

    except Exception:
        return fallback_response


def rank_wells(
    nearby_wells: list[dict],
    active_formation: str,
    current_depth: float,
    depth_window: float,
) -> list[dict]:
    fallback_response = []

    try:
        ranked_wells = []

        for well in nearby_wells:
            well_copy = well.copy()

            similarity = calculate_similarity(
                well_copy,
                active_formation,
                current_depth,
                depth_window,
            )

            well_copy["similarity"] = round(similarity, 1)

            ranked_wells.append(well_copy)

        ranked_wells.sort(
            key=lambda item: item.get("similarity", 0),
            reverse=True,
        )

        return ranked_wells

    except Exception:
        return fallback_response
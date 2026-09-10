from search import search_historical_events
from analyzer import analyze_historical_events
from evidence import generate_evidence


def analyze_well(
    events,
    nearby_well_ids,
    current_depth,
    formation,
    event_type=None,
    depth_tolerance=100
):
    """
    Main public entry point for the Historical Intelligence Engine.

    Coordinates search, statistical pattern analysis, and evidence generation
    on historical offset well data.

    Args:
        events (list): Loaded historical events dataset.
        nearby_well_ids (list): List of offset/nearby well IDs.
        current_depth (int or float): Current drilling depth in meters.
        formation (str): Geological formation name.
        event_type (str, optional): Filter by event type (case-insensitive). Defaults to None.
        depth_tolerance (int or float, optional): Depth window in meters (±). Defaults to 100.

    Returns:
        dict: A combined dictionary containing:
            - 'historical_events': List of filtered and ranked event dictionaries.
            - 'pattern_analysis': Aggregated frequency metrics and depth statistics.
            - 'evidence': List of deterministic evidence objects.
    """
    # 1. Search and score historical events
    matching_events = search_historical_events(
        events=events,
        nearby_well_ids=nearby_well_ids,
        current_depth=current_depth,
        formation=formation,
        depth_tolerance=depth_tolerance,
        event_type=event_type,
    )

    # 2. Perform pattern and frequency analysis
    pattern_analysis = analyze_historical_events(matching_events)

    # 3. Generate deterministic evidence objects
    evidence = generate_evidence(
        results=matching_events,
        current_depth=current_depth,
        formation=formation,
    )

    # 4. Return unified intelligence payload
    return {
        "historical_events": matching_events,
        "pattern_analysis": pattern_analysis,
        "evidence": evidence,
    }


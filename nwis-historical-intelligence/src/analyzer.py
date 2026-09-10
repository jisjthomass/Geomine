def analyze_historical_events(results):
    """
    Performs deterministic pattern analysis on a list of historical event results.

    Args:
        results (list): List of matching historical event dictionaries.

    Returns:
        dict: A dictionary containing aggregated statistics and frequency counts.
    """
    if not results:
        return {
            "total_events": 0,
            "unique_wells": 0,
            "event_frequency": {},
            "most_common_event": None,
            "depth_range": {
                "min_depth": None,
                "max_depth": None,
            },
            "average_depth": 0.0,
            "cause_frequency": {},
            "mitigation_frequency": {},
        }

    total_events = len(results)
    unique_wells = len({event["well_id"] for event in results if "well_id" in event})

    event_frequency = {}
    cause_frequency = {}
    mitigation_frequency = {}
    depths = []

    for event in results:
        # Event type frequency
        event_type = event.get("event_type")
        if event_type:
            event_frequency[event_type] = event_frequency.get(event_type, 0) + 1

        # Cause frequency
        cause = event.get("cause")
        if cause:
            cause_frequency[cause] = cause_frequency.get(cause, 0) + 1

        # Mitigation frequency
        mitigation = event.get("mitigation")
        if mitigation:
            mitigation_frequency[mitigation] = mitigation_frequency.get(mitigation, 0) + 1

        # Depths
        if "depth_m" in event and event["depth_m"] is not None:
            depths.append(event["depth_m"])

    # Most common event
    if event_frequency:
        most_common_event = max(event_frequency, key=event_frequency.get)
    else:
        most_common_event = None

    # Depth statistics
    if depths:
        min_depth = min(depths)
        max_depth = max(depths)
        average_depth = round(sum(depths) / len(depths), 2)
    else:
        min_depth = None
        max_depth = None
        average_depth = 0.0

    return {
        "total_events": total_events,
        "unique_wells": unique_wells,
        "event_frequency": event_frequency,
        "most_common_event": most_common_event,
        "depth_range": {
            "min_depth": min_depth,
            "max_depth": max_depth,
        },
        "average_depth": average_depth,
        "cause_frequency": cause_frequency,
        "mitigation_frequency": mitigation_frequency,
    }

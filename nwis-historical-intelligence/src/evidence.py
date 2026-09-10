def generate_evidence(results, current_depth, formation):
    """
    Generates deterministic evidence objects from historical search results.

    Args:
        results (list): List of matching historical event dictionaries from search_historical_events().
        current_depth (int or float): Current drilling depth in meters.
        formation (str): Current geological formation.

    Returns:
        list: List of evidence dictionaries derived strictly from existing record fields.
    """
    if not results:
        return []

    evidence_list = []

    for event in results:
        depth_diff = event.get("depth_difference_m")
        if depth_diff is None:
            event_depth = event.get("depth_m", 0)
            depth_diff = abs(event_depth - current_depth)

        # Generate deterministic explanation
        event_formation = event.get("formation")
        is_same_formation = (event_formation == formation)

        if is_same_formation:
            if depth_diff == 0:
                reason = "Same formation and event occurred at the current depth."
            else:
                reason = f"Same formation and historical event occurred {depth_diff} m from the current depth."
        else:
            if depth_diff == 0:
                reason = "Event occurred at the current depth."
            else:
                reason = f"Historical event occurred {depth_diff} m from the current depth."

        evidence_item = {
            "well_id": event.get("well_id"),
            "event_type": event.get("event_type"),
            "event_depth_m": event.get("depth_m"),
            "depth_difference_m": depth_diff,
            "relevance_score": event.get("relevance_score"),
            "reason": reason,
            "cause": event.get("cause"),
            "mitigation": event.get("mitigation"),
            "outcome": event.get("outcome"),
            "source": event.get("report_id"),
        }

        evidence_list.append(evidence_item)

    return evidence_list

def search_historical_events(
    events,
    nearby_well_ids,
    current_depth,
    formation,
    depth_tolerance=100,
    event_type=None
):
    """
    Filters historical events matching nearby wells, target formation, depth range,
    and optional event type, calculates relevance scores, and returns sorted results.

    Args:
        events (list): List of historical event dictionaries.
        nearby_well_ids (list): List of well IDs considered nearby.
        current_depth (int or float): Current drilling depth in meters.
        formation (str): Name of the geological formation.
        depth_tolerance (int or float, optional): Depth window in meters (±). Defaults to 100.
        event_type (str, optional): Filter by event type (case-insensitive). Defaults to None.

    Returns:
        list: Matching historical event dictionaries with depth_difference_m and
              relevance_score, sorted from highest to lowest relevance score.
    """
    matching_events = []

    # Prepare normalized event_type for case-insensitive comparison
    normalized_event_type = event_type.strip().lower() if event_type and event_type.strip() else None

    for event in events:
        same_well = True if nearby_well_ids is None else event.get("well_id") in nearby_well_ids
        same_formation = True if formation.lower() == "all" else (event.get("formation", "").lower() == formation.lower())
        depth_m = event.get("depth_m", 0)
        depth_difference = abs(depth_m - current_depth)
        similar_depth = depth_difference <= depth_tolerance

        # Check event type matching (case-insensitive) if provided
        if normalized_event_type:
            event_type_str = str(event.get("event_type", "")).strip().lower()
            matches_event_type = (event_type_str == normalized_event_type)
        else:
            matches_event_type = True

        if same_well and same_formation and similar_depth and matches_event_type:
            # Calculate depth relevance score (avoid division by zero)
            if depth_tolerance > 0:
                depth_score = 100 * (1 - depth_difference / depth_tolerance)
            else:
                depth_score = 100.0 if depth_difference == 0 else 0.0

            # Copy event and add computed fields
            event_result = dict(event)
            event_result["depth_difference_m"] = depth_difference
            event_result["relevance_score"] = round(depth_score, 2)
            matching_events.append(event_result)

    # Sort results by relevance_score from highest to lowest
    matching_events.sort(key=lambda x: x["relevance_score"], reverse=True)

    return matching_events

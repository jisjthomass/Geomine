import os
from data_loader import load_historical_events
from intelligence import analyze_well


def get_user_inputs():
    """
    Collects and validates search parameters interactively from the terminal.
    """
    # 1. Current depth in metres (must be numeric)
    depth_str = input("Enter current depth (m): ").strip()
    try:
        current_depth = float(depth_str)
        if current_depth.is_integer():
            current_depth = int(current_depth)
    except ValueError:
        print("Error: Depth must be numeric.")
        return None

    # 2. Formation name (must not be empty)
    formation = input("Enter formation: ").strip()
    if not formation:
        print("Error: Formation must not be empty.")
        return None

    # 3. Optional event type (press Enter to search all events)
    event_type_input = input("Enter event type (press Enter to search all events): ").strip()
    event_type = event_type_input if event_type_input else None

    # 4. Nearby well IDs (comma-separated, at least one required)
    wells_input = input("Enter nearby well IDs (comma-separated): ").strip()
    if not wells_input:
        print("Error: At least one nearby well ID must be provided.")
        return None

    nearby_wells = [w.strip() for w in wells_input.split(",") if w.strip()]
    if not nearby_wells:
        print("Error: At least one nearby well ID must be provided.")
        return None

    # 5. Optional depth tolerance (defaults to 100m if left blank)
    tolerance_input = input("Enter depth tolerance (default 100m): ").strip()
    if not tolerance_input:
        depth_tolerance = 100
    else:
        try:
            depth_tolerance = float(tolerance_input)
            if depth_tolerance <= 0:
                print("Error: Depth tolerance must be greater than 0.")
                return None
            if depth_tolerance.is_integer():
                depth_tolerance = int(depth_tolerance)
        except ValueError:
            print("Error: Depth tolerance must be numeric if provided.")
            return None

    return current_depth, formation, event_type, nearby_wells, depth_tolerance


def display_analysis(analysis):
    """
    Displays the aggregated historical pattern analysis.
    """
    print("\n" + "=" * 50)
    print("HISTORICAL PATTERN ANALYSIS")
    print("=" * 50)
    print(f"Total Events     : {analysis['total_events']}")
    print(f"Unique Wells     : {analysis['unique_wells']}")
    print(f"Most Common Event: {analysis['most_common_event'] if analysis['most_common_event'] else 'N/A'}")

    min_d = analysis["depth_range"]["min_depth"]
    max_d = analysis["depth_range"]["max_depth"]
    if min_d is not None and max_d is not None:
        print(f"Depth Range      : {min_d} m - {max_d} m")
        print(f"Average Depth    : {analysis['average_depth']:.2f} m")
    else:
        print("Depth Range      : N/A")
        print("Average Depth    : N/A")

    print("\nEvent Frequencies:")
    if analysis["event_frequency"]:
        for evt, count in analysis["event_frequency"].items():
            print(f"  - {evt}: {count}")
    else:
        print("  - None")

    print("\nCommon Causes:")
    if analysis["cause_frequency"]:
        for cause, count in analysis["cause_frequency"].items():
            print(f"  - {cause}: {count}")
    else:
        print("  - None")

    print("\nPrevious Mitigations:")
    if analysis["mitigation_frequency"]:
        for mit, count in analysis["mitigation_frequency"].items():
            print(f"  - {mit}: {count}")
    else:
        print("  - None")
    print("=" * 50)


def display_evidence(evidence):
    """
    Displays the generated deterministic historical evidence items.
    """
    print("\n" + "=" * 50)
    print("HISTORICAL EVIDENCE")
    print("=" * 50)
    if not evidence:
        print("No historical evidence found.")
    else:
        for item in evidence:
            print(f"Well: {item.get('well_id')}")
            print(f"Event: {item.get('event_type')}")
            print(f"Event Depth: {item.get('event_depth_m')} m")
            print(f"Depth Difference: {item.get('depth_difference_m')} m")
            rel_score = item.get("relevance_score")
            if isinstance(rel_score, (int, float)):
                print(f"Relevance Score: {rel_score:.2f}")
            else:
                print(f"Relevance Score: {rel_score}")
            print(f"Why relevant: {item.get('reason')}")
            print(f"Cause: {item.get('cause')}")
            print(f"Previous Mitigation: {item.get('mitigation')}")
            print(f"Outcome: {item.get('outcome')}")
            print(f"Source Report: {item.get('source')}")
            print("-" * 50)


def main():
    # Resolve the path to the dataset relative to this file
    data_file_path = os.path.join(
        os.path.dirname(__file__), "..", "nwis_mock_historical_events.json"
    )

    # 1. Load historical events dataset
    events = load_historical_events(data_file_path)

    # 2. Prompt user for dynamic inputs
    user_inputs = get_user_inputs()
    if user_inputs is None:
        return

    current_depth, formation, event_type, nearby_wells, depth_tolerance = user_inputs

    # 3. Analyze well using the Historical Intelligence Engine entry point
    intelligence_report = analyze_well(
        events=events,
        nearby_well_ids=nearby_wells,
        current_depth=current_depth,
        formation=formation,
        event_type=event_type,
        depth_tolerance=depth_tolerance,
    )

    results = intelligence_report["historical_events"]
    analysis = intelligence_report["pattern_analysis"]
    evidence = intelligence_report["evidence"]

    # 4. Display individual matching events
    print("\n" + "=" * 50)
    print("NWIS: RELEVANT HISTORICAL EVENTS")
    print("=" * 50)
    print(f"Current Depth   : {current_depth} m (Tolerance: ±{depth_tolerance} m)")
    print(f"Target Formation: {formation}")
    print(f"Event Type      : {event_type if event_type else 'All Events'}")
    print(f"Nearby Wells    : {', '.join(nearby_wells)}")
    print(f"Total Matches   : {len(results)}")
    print("-" * 50)

    if not results:
        print("No matching historical events found.")
    else:
        for event in results:
            print(f"Well: {event.get('well_id')}")
            print(f"Depth: {event.get('depth_m')} m")
            print(f"Formation: {event.get('formation')}")
            print(f"Event: {event.get('event_type')}")
            print(f"Cause: {event.get('cause')}")
            print(f"Mitigation: {event.get('mitigation')}")
            print(f"Outcome: {event.get('outcome')}")
            print(f"Depth Difference: {event.get('depth_difference_m')} m")
            print(f"Relevance Score: {event.get('relevance_score'):.2f}")
            print(f"Report ID: {event.get('report_id')}")
            print("-" * 50)

    # 5. Display pattern analysis summary
    display_analysis(analysis)

    # 6. Display generated historical evidence
    display_evidence(evidence)


if __name__ == "__main__":
    main()


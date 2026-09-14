"""
Document builder for converting historical drilling events into structured
documents and readable text suitable for semantic embeddings.
"""


def event_to_document(event: dict) -> str:
    """
    Convert ONE historical drilling event into clean, readable text
    suitable for semantic embedding.

    Structure:
    Well: <well_id>
    Depth: <depth_m> m
    Formation: <formation>
    Event: <event_type>
    Cause: <cause>
    Mitigation: <mitigation>
    Outcome: <outcome>
    """
    if not isinstance(event, dict):
        return ""

    well_id = event.get("well_id", "")
    depth_m = event.get("depth_m", "")
    formation = event.get("formation", "")
    event_type = event.get("event_type", "")
    cause = event.get("cause", "")
    mitigation = event.get("mitigation", "")
    outcome = event.get("outcome", "")

    depth_str = f"{depth_m} m" if depth_m not in (None, "") else ""

    lines = [
        f"Well: {well_id if well_id is not None else ''}",
        f"Depth: {depth_str}",
        f"Formation: {formation if formation is not None else ''}",
        f"Event: {event_type if event_type is not None else ''}",
        f"Cause: {cause if cause is not None else ''}",
        f"Mitigation: {mitigation if mitigation is not None else ''}",
        f"Outcome: {outcome if outcome is not None else ''}",
    ]
    return "\n".join(lines)


def events_to_documents(events: list[dict]) -> list[dict]:
    """
    Convert a list of historical drilling events into a list of document
    dictionaries with formatted text and metadata.

    Returns:
    [
        {
            "text": "...",
            "metadata": {
                "well_id": ...,
                "depth_m": ...,
                "formation": ...,
                "event_type": ...,
                "report_id": ...
            }
        }
    ]
    """
    if not events:
        return []

    documents = []
    for event in events:
        if not isinstance(event, dict):
            continue
        doc = {
            "text": event_to_document(event),
            "metadata": {
                "well_id": event.get("well_id"),
                "depth_m": event.get("depth_m"),
                "formation": event.get("formation"),
                "event_type": event.get("event_type"),
                "cause": event.get("cause"),
                "mitigation": event.get("mitigation"),
                "outcome": event.get("outcome"),
                "report_id": event.get("report_id"),
                "document_type": event.get("document_type"),
            },
        }
        documents.append(doc)
    return documents

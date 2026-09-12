from typing import Any, Dict, List, Optional


def build_rag_context(
    evidence: Optional[List[Dict[str, Any]]],
    max_results: int = 5
) -> str:
    """
    Converts retrieved historical evidence records into a clean, factual text context
    suitable for grounding LLM generation.

    Args:
        evidence (list[dict], optional): List of retrieved evidence items (from HybridRetriever
            or RAGRetrievalService).
        max_results (int): Maximum number of evidence items to include. Defaults to 5.

    Returns:
        str: Formatted context string containing only factual historical evidence.
    """
    if not evidence:
        return ""

    selected = evidence[:max_results]
    context_blocks = []

    for idx, item in enumerate(selected, start=1):
        if not isinstance(item, dict):
            continue

        # Extract metadata if nested, otherwise fall back to top-level dict
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            metadata = item

        # Well ID
        well_id = metadata.get("well_id") or item.get("well_id")
        well_str = str(well_id).strip() if well_id else "Not recorded"

        # Depth
        depth_val = metadata.get("depth_m") if metadata.get("depth_m") is not None else item.get("depth_m")
        if depth_val is not None and str(depth_val).strip():
            raw_depth = str(depth_val).strip()
            depth_str = raw_depth if raw_depth.endswith("m") else f"{raw_depth} m"
        else:
            depth_str = "Not recorded"

        # Formation
        formation = metadata.get("formation") or item.get("formation")
        formation_str = str(formation).strip() if formation else "Not recorded"

        # Event Type
        event_type = metadata.get("event_type") or item.get("event_type")
        event_str = str(event_type).strip() if event_type else "Not recorded"

        # Cause
        cause = metadata.get("cause") or item.get("cause")
        cause_str = str(cause).strip() if cause else "Not recorded"

        # Mitigation
        mitigation = metadata.get("mitigation") or item.get("mitigation")
        mitigation_str = str(mitigation).strip() if mitigation else "Not recorded"

        # Outcome
        outcome = metadata.get("outcome") or item.get("outcome")
        outcome_str = str(outcome).strip() if outcome else "Not recorded"

        # Report ID
        report_id = metadata.get("report_id") or item.get("report_id")
        report_str = str(report_id).strip() if report_id else "Not recorded"

        block = (
            f"Historical Evidence {idx}:\n"
            f"Well: {well_str}\n"
            f"Depth: {depth_str}\n"
            f"Formation: {formation_str}\n"
            f"Event: {event_str}\n"
            f"Cause: {cause_str}\n"
            f"Mitigation: {mitigation_str}\n"
            f"Outcome: {outcome_str}\n"
            f"Report: {report_str}"
        )
        context_blocks.append(block)

    return "\n\n".join(context_blocks)

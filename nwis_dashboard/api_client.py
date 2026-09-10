import requests

from config import ANALYZE_ENDPOINT


def analyze_drilling_risk(payload: dict) -> dict:
    fallback_response = {
        "status": "error",
        "error": "Backend unavailable",
        "active_well": {},
        "nearby_wells": [],
        "ml_prediction": {
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "predicted_event": "Data unavailable",
        },
        "historical_context": {
            "nearby_well_count": 0,
            "evidence_string": "Data unavailable",
            "recommended_action": "Data unavailable",
        },
    }

    try:
        print(f"\n\n=== STREAMLIT IS TRYING TO HIT API: {ANALYZE_ENDPOINT} ===\n\n", flush=True)
        response = requests.post(
            ANALYZE_ENDPOINT,
            json=payload,
            timeout=90,
        )

        response.raise_for_status()

        return response.json()

    except Exception as error:
        print(f"\n\n=== API REQUEST FAILED: {error} ===\n\n", flush=True)
        fallback_response["error"] = str(error)

        return fallback_response
def generate_ai_summary(payload: dict) -> dict:
    try:
        import requests
        from config import BACKEND_URL
        res = requests.post(f"{BACKEND_URL}/api/generate_ai_summary", json=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as error:
        return {"explanation": f"Failed to load AI summary: {error}"}

def ingest_historical_report(raw_text: str) -> dict:
    try:
        import requests
        from config import BACKEND_URL
        res = requests.post(f"{BACKEND_URL}/api/ingest_report", json={"raw_text": raw_text}, timeout=15)
        res.raise_for_status()
        return res.json()
    except Exception as error:
        return {"status": "error", "message": str(error)}

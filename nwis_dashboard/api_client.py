import requests
import streamlit as st

from config import ANALYZE_ENDPOINT, BACKEND_URL

def get_auth_headers():
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def handle_401(response):
    if response.status_code == 401:
        st.session_state["authenticated"] = False
        st.session_state.pop("access_token", None)
        st.rerun()

def login_user(identifier, password):
    try:
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json={"identifier": identifier, "password": password})
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Login error: {e}")
    return None

def validate_token(token: str):
    try:
        response = requests.get(f"{BACKEND_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

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
            headers=get_auth_headers(),
            timeout=90,
        )

        handle_401(response)
        response.raise_for_status()

        return response.json()

    except Exception as error:
        print(f"\n\n=== API REQUEST FAILED: {error} ===\n\n", flush=True)
        fallback_response["error"] = str(error)

        return fallback_response

def generate_ai_summary(payload: dict) -> dict:
    try:
        res = requests.post(f"{BACKEND_URL}/api/generate_ai_summary", json=payload, headers=get_auth_headers(), timeout=10)
        handle_401(res)
        res.raise_for_status()
        return res.json()
    except Exception as error:
        return {"explanation": f"Failed to load AI summary: {error}"}

def ingest_historical_report(raw_text: str) -> dict:
    try:
        res = requests.post(f"{BACKEND_URL}/api/ingest_report", json={"raw_text": raw_text}, headers=get_auth_headers(), timeout=15)
        handle_401(res)
        res.raise_for_status()
        return res.json()
    except Exception as error:
        return {"status": "error", "message": str(error)}

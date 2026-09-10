import requests
import time

url = "http://127.0.0.1:8000/api/telemetry/ingest"

# Fake live drilling data
payload = {
    "depth": 2800.0,
    "rop": 15.2,
    "rpm": 120.5,
    "torque": 4500.2,
    "wob": 10.5,
    "lat": 28.61,
    "lon": 77.20,
    "target_formation": "Formation X"
}

print("Sending live telemetry to Thomas's Backend...")
try:
    response = requests.post(url, json=payload)
    print(f"Backend Response: {response.json()}")
    print("Success! The global state is now populated.")
except Exception as e:
    print(f"Failed to send request: {e}")
    print("Ensure the FastAPI server is running with 'uvicorn main:app --reload'")

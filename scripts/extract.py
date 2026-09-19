"""
Extract layer: pull raw JSON from the TfL Unified API.
These functions are side-effect-light and can be tested locally without AWS or Airflow.
"""
from __future__ import annotations
import os
import sys
import requests
import datetime

def extract_bikepoint() -> tuple[list, str]:
    api_key = os.getenv("TFL_APP_KEY")
    app_id = os.getenv("TFL_APP_ID")
    url = os.getenv("TFL_BIKEPOINT_URL", "https://api.tfl.gov.uk/BikePoint")

    params = {}
    if app_id:
        params["app_id"] = app_id
    if api_key:
        params["app_key"] = api_key

    headers = {"Cache-Control": "no-cache"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        stations_data = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"TRANSIENT API FAILURE: Could not fetch or parse TfL response. Error: {e}", file=sys.stderr)
        return [], ""

    if not isinstance(stations_data, list):
        print(f"TRANSIENT API FAILURE: Unexpected response shape ({type(stations_data).__name__}), expected a list.", file=sys.stderr)
        return [], ""
    
    # Capture execution metadata right now
    capture_time = datetime.datetime.now(datetime.UTC)
    capture_timestamp_raw = capture_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return stations_data, capture_timestamp_raw


if __name__ == "__main__":
    print("Testing TfL API Connection...")
    stations, captured_at = extract_bikepoint()
    print(f"Status: Received {len(stations)} stations from London at {captured_at}")
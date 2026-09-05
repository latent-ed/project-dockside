"""
Extract layer: pull raw JSON from the TfL Unified API.
These functions are side-effect-light and can be tested locally without AWS or Airflow.
"""
from __future__ import annotations
import os
import sys
import requests
import datetime

def extract_bikepoint() -> dict:
    """
    Fetches live cycle data from the TfL /BikePoint endpoint.
    Folds capture metadata directly into the response payload dictionary.
    """
    # Explicitly pull the API Key and URL from your .env file variables
    api_key = os.getenv("TFL_APP_KEY")
    
    # CORRECTED: Point the fallback URL to the dedicated /BikePoint data endpoint 
    url = os.getenv("TFL_BIKEPOINT_URL", "https://api.tfl.gov.uk/bikepoint")  # Default to the correct endpoint if not set
    
    # Configure the query parameters using your TFL_APP_KEY
    params = {"app_key": api_key} if api_key else {}
    headers = {"Cache-Control": "no-cache"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        stations_data = response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"TRANSIENT API FAILURE: Could not fetch or parse TfL response. Error: {e}", file=sys.stderr)
        return {}

    if not isinstance(stations_data, list):
        print(f"TRANSIENT API FAILURE: Unexpected response shape ({type(stations_data).__name__}), expected a list.", file=sys.stderr)
        return {}

    # Capture execution metadata right now
    capture_time = datetime.datetime.now(datetime.UTC)
    capture_timestamp_raw = capture_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Fold metadata into a single package alongside the raw records array
    return {
        "capture_timestamp_raw": capture_timestamp_raw,
        "station_count": len(stations_data),
        "data": stations_data  # This is the ~800 stations array from your Postman call
    }

if __name__ == "__main__":
    # Test block to verify it works in isolation
    print("Testing TfL API Connection...")
    test_data = extract_bikepoint()
    print(f"Status: Received {test_data.get('station_count', 0)} stations from London!")

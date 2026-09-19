"""
Entry point: runs the full extract -> load sequence.
Used both as the Airflow-invoked script and as the
command a README tells a stranger to run locally:
    python3 -m scripts.run_aws_pipeline [scheduled_iso_timestamp]
"""
import os
import sys
from datetime import datetime, timezone
from scripts.extract import extract_bikepoint
from scripts.load import load_to_s3


def main():
    bucket_name = os.getenv("S3_BUCKET")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")

    required = {
        "TFL_APP_KEY": os.getenv("TFL_APP_KEY"),
        "S3_BUCKET": bucket_name,
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"CRITICAL CONFIGURATION ERROR: missing {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        scheduled_dt = datetime.fromisoformat(sys.argv[1])
    else:
        scheduled_dt = datetime.now(timezone.utc)

    stations_data, capture_timestamp_raw = extract_bikepoint()
    if not stations_data:
        print("No data retrieved from TfL API — treating as failure so Airflow retries.", file=sys.stderr)
        sys.exit(1)

    try:
        s3_key = load_to_s3(stations_data, capture_timestamp_raw, scheduled_dt, bucket_name, aws_region)
        print(f"SUCCESS: Landed s3://{bucket_name}/{s3_key} ({len(stations_data)} stations)")
    except Exception as e:
        print(f"CRITICAL AWS INTERACTION ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
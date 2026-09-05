import os
import sys
import json
import boto3
from datetime import datetime
from tfl_api_test import extract_bikepoint

def main():
    # Enforce strict configuration checking matching your .env file names (Criterion 5)
    api_key = os.getenv("TFL_APP_KEY")
    bucket_name = os.getenv("S3_BUCKET")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")
    
    required = {
        "TFL_APP_KEY": api_key,
        "S3_BUCKET": bucket_name,
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
}
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"CRITICAL CONFIGURATION ERROR: missing {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # 1. Extract data using our clean module
    payload = extract_bikepoint() #api_key=api_key
    
    if not payload or not payload.get("data"):
        print("No data retrieved from TfL API — treating as failure so Airflow retries.")
        sys.exit(1) # Exit cleanly to allow the next 15-minute cron slot to try again

    # 2. Extract partition details from our generated metadata
    capture_dt = datetime.fromisoformat(payload["capture_timestamp_raw"].rstrip("Z"))
    date_folder = capture_dt.strftime("%Y-%m-%d")
    hour_folder = capture_dt.strftime("%H")
    file_name = f"snapshot_{capture_dt.strftime('%Y%m%dT%H%M%SZ')}.json"
    
    s3_key = f"raw/bikepoint/dt={date_folder}/hour={hour_folder}/{file_name}"

    # 3. Ship the untransformed data to the S3 bucket stage
    try:
        s3_client = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(payload)
        )
        print(f"SUCCESS: Landed s3://{bucket_name}/{s3_key} ({payload['station_count']} stations)")
    except Exception as e:
        print(f"CRITICAL AWS INTERACTION ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

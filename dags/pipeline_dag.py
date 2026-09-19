"""
Airflow DAG for Project Dockside (LATENT ED).
Runs every 15 minutes: lands a TfL BikePoint snapshot to S3.

Scope note: this DAG currently covers extract -> S3 landing only, per
the current PR's approved scope. Bronze (Snowflake) and dbt stages are
built separately and will be added to this DAG in a follow-up PR once
that phase is sorted.
"""
import os
import sys
from datetime import datetime, timedelta

import pendulum
from airflow.decorators import dag, task

# Make the repo root importable so `from scripts.extract import ...` works
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

default_args = {
    "owner": "Talk Data To Me",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="tfl_bikepoint_pipeline",
    default_args=default_args,
    description="TfL BikePoint snapshot pipeline: extract -> S3 landing",
    schedule="*/15 * * * *",
    start_date=pendulum.datetime(2026, 8, 31, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["dockside", "elt"],
)
def tfl_bikepoint_pipeline():

    @task(execution_timeout=timedelta(minutes=5))
    def land_snapshot(data_interval_start=None) -> str:
        """Fetch TfL BikePoint data and land it in S3. Returns the S3 key."""
        from scripts.extract import extract_bikepoint
        from scripts.load import load_to_s3

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
            raise RuntimeError(f"CRITICAL CONFIGURATION ERROR: missing {', '.join(missing)}")

        scheduled_dt = data_interval_start or datetime.now(pendulum.UTC)

        stations_data, capture_timestamp_raw = extract_bikepoint()
        if not stations_data:
            raise RuntimeError("No data retrieved from TfL API — treating as failure so Airflow retries.")

        s3_key = load_to_s3(stations_data, capture_timestamp_raw, scheduled_dt, bucket_name, aws_region)
        print(f"SUCCESS: Landed s3://{bucket_name}/{s3_key} ({len(stations_data)} stations)")
        return s3_key

    land_snapshot()


tfl_bikepoint_pipeline()
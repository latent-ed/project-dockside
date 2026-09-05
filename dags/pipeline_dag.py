"""
Airflow DAG for Project Dockside (LATENT ED).
Runs every 15 minutes and executes the run_aws_pipeline.py script
using BashOperator, as required by the programme specification.
"""

import os
import pendulum
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator # type: ignore

# Path inside the Airflow container
EXTRACT_SCRIPT = "/opt/airflow/dags/project-dockside/scripts/run_aws_pipeline.py"
#EXTRACT_SCRIPT = os.path.join(os.path.dirname(__file__), "scripts", "run_aws_pipeline.py")

default_args = {
    "owner": "Talk Data To Me",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="tfl_bikepoint_pipeline",
    default_args=default_args,
    description="TfL BikePoint snapshot pipeline using BashOperator",
    schedule="*/15 * * * *",   # REQUIRED by LATENT ED "*/15 * * * *"
    start_date=pendulum.datetime(2026, 8, 31, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["dockside", "elt"],
)

run_extract_snapshot = BashOperator(
    task_id="run_aws_pipeline",
    bash_command=f"python3 {EXTRACT_SCRIPT}",
    append_env=True,
    env={k: v for k, v in {
        "TFL_APP_KEY": os.getenv("TFL_APP_KEY"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION"),
        "S3_BUCKET": os.getenv("S3_BUCKET"),
    }.items() if v is not None},
    execution_timeout=timedelta(minutes=5),
    dag=dag,
)

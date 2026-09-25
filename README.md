# Project Dockside: Phase 1 (ELT Extraction & S3 Landing)

Phase 1 is complete, verified locally, and running in the monorepo Airflow
stack (`tfl_bikepoint_pipeline`). The pipeline calls the live TfL
`/BikePoint` API on a 15-minute schedule and lands raw, untransformed JSON
snapshots to S3.

### Implementation Details

#### 1. Extract layer (`scripts/extract.py`)
* `response.raise_for_status()` handles API errors and rate-limiting.
* `try/except` catches both network failures and malformed JSON responses gracefully.
* Validates the response is a list before proceeding — guards against a malformed payload silently corrupting a snapshot.
* Adds a UTC capture timestamp to each fetch, independent of any per-property `modified` field in the API response.
* Returns raw station data as a plain list — no wrapper object — plus the capture timestamp, separately.

#### 2. Load layer (`scripts/load.py`)
* Writes the station list to S3, partitioned by the **scheduled** interval (`data_interval_start`), not wall-clock execution time — so a retry overwrites the same S3 key instead of creating a duplicate snapshot.
* Capture timestamp and station count are attached as S3 object metadata rather than embedded in the JSON body.

#### 3. Pipeline entry point (`scripts/run_aws_pipeline.py`)
* Enforces strict environment variable checks: `TFL_APP_KEY`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` — fails fast with a named missing variable rather than a cryptic downstream error.
* Exits with `sys.exit(1)` on any failure (missing config, empty API response, or S3 write error) to trigger Airflow's retry policy. A failed run is never silently treated as success.
* Run locally via: `python3 -m scripts.run_aws_pipeline`

#### 4. Airflow DAG (`dags/pipeline_dag.py`)
* Uses TaskFlow (`@task`) rather than `BashOperator` — the extract/load logic runs natively in the Airflow worker process rather than shelling out to a script path.
* Script path resolution is relative to the repo root, not a hardcoded container path.
* `schedule="*/15 * * * *"`, `catchup=False`, `max_active_runs=1` — matches the programme's required cadence.
* Currently covers extract → S3 landing only. Bronze (Snowflake) and dbt stages will be added in a follow-up PR once that phase is approved to start.

### Verification Checklist
* [x] Script runs locally via terminal: `python3 -m scripts.run_aws_pipeline`
* [x] DAG loads in Airflow UI with zero import errors
* [x] Manual trigger goes green
* [x] S3 bucket shows files landing in the correct `dt=/hour=` partitions
* [x] Re-running the same scheduled slot overwrites the existing S3 key rather than creating a duplicate

**Reviewer:** @onyinyechi-ogbonna
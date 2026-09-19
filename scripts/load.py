"""
Load layer: write extracted station data to the S3 raw landing zone.
Knows nothing about the TfL API — only takes data and ships it to S3.
"""
import json
import boto3


def load_to_s3(stations_data: list, capture_timestamp_raw: str, scheduled_dt, bucket_name: str, aws_region: str) -> str:
    """
    Uploads the station list to S3, partitioned by the scheduled interval
    (not wall-clock time) so retries overwrite the same key rather than
    creating duplicates. Returns the S3 key written, for the caller to log
    or pass downstream.
    """
    date_folder = scheduled_dt.strftime("%Y-%m-%d")
    hour_folder = scheduled_dt.strftime("%H")
    file_name = f"snapshot_{scheduled_dt.strftime('%Y%m%dT%H%M%SZ')}.json"
    s3_key = f"raw/bikepoint/dt={date_folder}/hour={hour_folder}/{file_name}"

    s3_client = boto3.client("s3", region_name=aws_region)
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(stations_data),
        Metadata={
            "capture-timestamp-raw": capture_timestamp_raw,
            "station-count": str(len(stations_data)),
        },
    )
    return s3_key
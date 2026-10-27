"""Day 17: after Terraform creates the bucket, register it in the Port catalog (linked to the run)."""
import os
import sys

from port_api import call
from port_run import port_log

name = os.environ["BUCKET_NAME"]
env = os.environ["TF_VAR_env"]
region = os.environ.get("AWS_REGION", "ap-south-1")

entity = {
    "identifier": name,
    "title": name,
    "properties": {
        "bucket_name": name,
        "environment": env,
        "region": region,
        "purpose": os.environ["TF_VAR_purpose"],
        "requested_by": os.environ.get("TF_VAR_requested_by", "unknown"),
        "console_url": f"https://s3.console.aws.amazon.com/s3/buckets/{name}?region={region}",
    },
}
params = {"upsert": "true", "merge": "true"}
if os.environ.get("RUN_ID"):
    params["run_id"] = os.environ["RUN_ID"]  # ties the new entity to the developer's run

status, data = call("POST", "/blueprints/s3Bucket/entities", body=entity, params=params)
if status not in (200, 201):
    port_log(f"Could not register {name} in the catalog (HTTP {status})")
    sys.exit(1)
port_log(f"Registered {name} in the Port catalog")
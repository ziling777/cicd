#!/bin/bash

dbt deps
dbt docs generate

aws s3 cp target/catalog.json s3://${S3_BUCKET}/dbt-catalog/
aws s3 cp target/index.html s3://${S3_BUCKET}/dbt-catalog/
aws s3 cp target/manifest.json s3://${S3_BUCKET}/dbt-catalog/
aws s3 cp target/run_results.json s3://${S3_BUCKET}/dbt-catalog/
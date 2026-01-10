#!/bin/sh
set -e

# MinIO Initialization Script
# ---------------------------
# This script configures the local MinIO server with a single bucket named 'ams-media'.
# The bucket contains two directories:
#   1. public/
#   2. private/
#
# The script uses the MinIO Client (mc) to connect to the MinIO server and set up the bucket.
#
# Usage:
#   This script is intended to be run automatically by Docker Compose as part of the local development environment.
#   It assumes the MinIO server is available at http://minio:9000 and that the MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
#   environment variables are set.
#
# Note: The script waits briefly to ensure the MinIO server is ready before running commands.

# Wait for MinIO server to be ready
sleep 5

# Set up MinIO client alias for local server
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Create ams-media buckets (if they doesn't exist)
mc mb --ignore-existing local/ams-media-public
mc mb --ignore-existing local/ams-media-private

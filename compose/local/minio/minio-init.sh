#!/bin/sh
set -e

# MinIO Initialization Script
# ---------------------------
# This script configures the local MinIO server with a single bucket named 'ams-media'.
# The bucket contains two directories:
#   1. public/  - Allows anonymous (unauthenticated) read access. Intended for files that should be accessible to anyone.
#   2. private/ - Requires authentication for all access. Intended for sensitive or internal files.
#
# The script uses the MinIO Client (mc) to connect to the MinIO server and set up the bucket and policies.
#
# Usage:
#   This script is intended to be run automatically by Docker Compose as part of the local development environment.
#   It assumes the MinIO server is available at http://minio:9000 and that the MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
#   environment variables are set.
#
# Bucket Policies:
#   - ams-media/public/*: Anonymous users can download (read) files. Upload and delete require authentication.
#   - ams-media/private/*: All operations require authentication.
#
# Note: The script waits briefly to ensure the MinIO server is ready before running commands.

# Wait for MinIO server to be ready
sleep 5

# Set up MinIO client alias for local server
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Create ams-media buckets (if they doesn't exist)
mc mb --ignore-existing local/ams-media-public
mc mb --ignore-existing local/ams-media-private

# Set bucket policies
mc anonymous set-json /public-bucket-policy.json local/ams-media-public
mc anonymous set-json /private-bucket-policy.json local/ams-media-private

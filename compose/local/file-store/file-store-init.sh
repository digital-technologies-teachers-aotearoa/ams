#!/bin/sh
# Configure the RustFS CLI target, create the media buckets, and allow public
# reads from the public media bucket.
set -eu

rc alias set local "$FILE_STORE_ENDPOINT_URL" "$RUSTFS_ACCESS_KEY" "$RUSTFS_SECRET_KEY" --bucket-lookup path
rc bucket create local/ams-media-public --ignore-existing
rc bucket create local/ams-media-private --ignore-existing
rc bucket anonymous set public local/ams-media-public

# Media Storage Bucket Policies

This directory contains example bucket policies for two object storage buckets used by the AMS application:

- `public-bucket-policy.json` – Grants anonymous read access **to objects only** (via `s3:GetObject`), while explicitly denying bucket ("directory") listing. This lets you serve media files directly (e.g. images) without exposing overall bucket contents.
- `private-bucket-policy.json` – Denies unauthenticated bucket listing. Objects are not publicly readable; access must occur through signed URLs, authenticated IAM users/roles, or application proxy logic.

These policies are written for AWS S3 but are equally valid for DigitalOcean Spaces (or any S3‑compatible storage) with minimal changes.

## 1. Policy Details

### Public Bucket (`ams-media-public`)

Statement summary:

1. Allow `s3:GetObject` on `arn:aws:s3:::ams-media-public/*` for Principal `*` (anyone) so objects can be fetched directly.
2. Deny `s3:ListBucket` and `s3:ListBucketVersions` on the bucket itself, preventing anonymous directory listing (and version enumeration) even though reads are permitted.

### Private Bucket (`ams-media-private`)

Statement summary:

1. Deny anonymous `s3:ListBucket` and `s3:ListBucketVersions`. (No Allow for `GetObject` is provided, so objects are private by default.)

### Why deny listing?

Blocking listing reduces information disclosure (enumeration of object keys) and slightly lowers the risk of scraping. Public objects remain fetchable only when you know (or generate) the exact key.

## 2. Adapting Bucket Names

If you use different bucket names, update every occurrence of:

- `ams-media-public` (and trailing `/*` where present) in `public-bucket-policy.json`
- `ams-media-private` in `private-bucket-policy.json`

Object access (`s3:GetObject`) must target the **object ARN form**: `arn:aws:s3:::your-bucket-name/*`. Using only the bucket ARN for `GetObject` will produce an error like: `unsupported Resource found [arn:aws:s3:::...] for action s3:GetObject`.

## 3. Applying Policies on AWS S3

### Via AWS Console

1. Open the S3 console.
2. Select your bucket (e.g. `ams-media-public`).
3. Go to the Permissions tab → Bucket policy.
4. Paste the JSON contents of the corresponding policy file.
5. Save.

Repeat for the private bucket.

### Via AWS CLI

Ensure you have credentials with permission `s3:PutBucketPolicy`.

```bash
# Apply public bucket policy
aws s3api put-bucket-policy \
  --bucket ams-media-public \
  --policy file://public-bucket-policy.json

# Apply private bucket policy
aws s3api put-bucket-policy \
  --bucket ams-media-private \
  --policy file://private-bucket-policy.json

# Verify
aws s3api get-bucket-policy --bucket ams-media-public
```

(If using a profile add `--profile yourprofile`.)

### References (AWS)

- Bucket policies overview: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html>
- Example policies: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html>

## 4. Applying Policies on DigitalOcean Spaces

DigitalOcean Spaces is S3‑compatible. You can apply these policies using the AWS CLI by specifying the Space’s endpoint, or via the DO control panel (limited policy editor features may vary).

### Using AWS CLI Against Spaces

Replace `<region>` with your Spaces region (e.g. `nyc3`, `ams3`, `sgp1`).

```bash
ENDPOINT="https://nyc3.digitaloceanspaces.com"

aws s3api put-bucket-policy \
  --endpoint-url "$ENDPOINT" \
  --bucket ams-media-public \
  --policy file://public-bucket-policy.json

aws s3api put-bucket-policy \
  --endpoint-url "$ENDPOINT" \
  --bucket ams-media-private \
  --policy file://private-bucket-policy.json
```

### References (DigitalOcean)

- Managing access & permissions: <https://docs.digitaloceans.com/products/spaces/how-to/manage-access/>
- Spaces overview: <https://docs.digitaloceans.com/products/spaces/>

## 5. Verifying Behavior

### Public Object Read Works

```bash
curl -I https://ams-media-public.s3.amazonaws.com/path/to/object.jpg
# or (Spaces)
curl -I https://ams-media-public.nyc3.cdn.digitaloceanspaces.com/path/to/object.jpg
```

Expect `200 OK` (or `301/302` redirect then `200`).

### Bucket Listing Fails (AccessDenied)

```bash
aws s3api list-objects-v2 --bucket ams-media-public || echo "Listing denied as expected"
```

Should return `AccessDenied` because of the explicit Deny.

### Private Object Requires Auth

Attempting unauthenticated access to a private bucket object should yield `AccessDenied` or `403`.

## 6. Common Pitfalls & Notes

- Do NOT include `s3:PutObject` or `s3:DeleteObject` for anonymous principals unless you intend a writable public drop bucket (highly discouraged).
- The Deny for listing overrides any implicit Allows; if later you attach an IAM policy allowing listing, the explicit bucket policy Deny still wins.
- If you need authenticated listing for application roles, add an additional statement restricting listing to specific IAM principals (ARNs) instead of removing the Deny.
- For CloudFront / CDN usage, these policies still apply; ensure origin access (if using Origin Access Identity or SigV4 signed requests) is configured if you later restrict public reads.

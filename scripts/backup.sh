#!/bin/bash
# PNS CRM PostgreSQL Backup Script
# Streams pg_dump custom format directly through age encryption.
# Never writes plaintext to disk.  SHA256 checksum is of the
# encrypted artifact.  Uploads to S3 with daily/weekly/monthly keys.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_ENCRYPT_KEY:?BACKUP_ENCRYPT_KEY is required (age public key)}"
: "${BACKUP_S3_BUCKET:?BACKUP_S3_BUCKET is required}"
: "${BACKUP_S3_ENDPOINT:?BACKUP_S3_ENDPOINT is required}"
: "${BACKUP_S3_REGION:?BACKUP_S3_REGION is required}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
DAILY_KEY="backups/daily/pns-crm-$(date -u +%Y%m%d).dump.age"
WEEKLY_KEY="backups/weekly/pns-crm-$(date -u +%Y-W%V).dump.age"
MONTHLY_KEY="backups/monthly/pns-crm-$(date -u +%Y-%m).dump.age"
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "=== PNS CRM Backup $(date -u) ==="

# ── 1. Stream pg_dump through age, hash the ENCRYPTED artifact ──
ENC_FILE="${WORKDIR}/backup.dump.age"
pg_dump "$DATABASE_URL" --format=custom --no-owner --no-acl --compress=6 \
  | age -e -r "$BACKUP_ENCRYPT_KEY" -o "$ENC_FILE"
echo "[dump] Encrypted size: $(du -h "$ENC_FILE" | cut -f1)"

# SHA256 of the encrypted artifact
MANIFEST_FILE="${WORKDIR}/manifest.sha256"
sha256sum "$ENC_FILE" | awk '{print $1}' > "$MANIFEST_FILE"
EXPECTED_SHA=$(cat "$MANIFEST_FILE")
echo "[manifest] SHA256 (encrypted): ${EXPECTED_SHA}"

# ── 2. Upload daily ──
S3_DAILY="s3://${BACKUP_S3_BUCKET}/${DAILY_KEY}"
aws s3 cp "$ENC_FILE" "$S3_DAILY" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors
aws s3 cp "$MANIFEST_FILE" "${S3_DAILY}.sha256" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors
echo "[upload] Daily: ${S3_DAILY}"

# ── 3. Weekly (Sunday) ──
if [ "$(date -u +%w)" = "0" ]; then
  S3_WEEKLY="s3://${BACKUP_S3_BUCKET}/${WEEKLY_KEY}"
  aws s3 cp "$ENC_FILE" "$S3_WEEKLY" \
    --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors
  echo "[upload] Weekly: ${S3_WEEKLY}"
fi

# ── 4. Monthly (1st) ──
if [ "$(date -u +%d)" = "01" ]; then
  S3_MONTHLY="s3://${BACKUP_S3_BUCKET}/${MONTHLY_KEY}"
  aws s3 cp "$ENC_FILE" "$S3_MONTHLY" \
    --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors
  echo "[upload] Monthly: ${S3_MONTHLY}"
fi

# ── 5. Freshness marker ──
echo "$TIMESTAMP" | aws s3 cp - "s3://${BACKUP_S3_BUCKET}/backups/.last_backup" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION"

echo "=== Backup complete ==="

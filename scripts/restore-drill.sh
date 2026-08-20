#!/bin/bash
# PNS CRM Restore Drill Script
# Restores from S3 backup into a disposable database.
# Requires explicit DISPOSABLE_DATABASE_URL and RESTORE_SAFETY_TOKEN.
# Refuses production hosts.  Fails on missing schema or invalid restore.
set -euo pipefail

: "${DISPOSABLE_DATABASE_URL:?DISPOSABLE_DATABASE_URL is required}"
: "${RESTORE_SAFETY_TOKEN:?RESTORE_SAFETY_TOKEN must be 'restore-drill-allowed'}"
: "${BACKUP_DECRYPT_KEY:?BACKUP_DECRYPT_KEY is required (age identity or identity-file path)}"
: "${BACKUP_S3_BUCKET:?BACKUP_S3_BUCKET is required}"
: "${BACKUP_S3_ENDPOINT:?BACKUP_S3_ENDPOINT is required}"
: "${BACKUP_S3_REGION:?BACKUP_S3_REGION is required}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"

if [ "$RESTORE_SAFETY_TOKEN" != "restore-drill-allowed" ]; then
  echo "[FATAL] RESTORE_SAFETY_TOKEN must be 'restore-drill-allowed'"
  exit 1
fi

DISPOSABLE_URL="$DISPOSABLE_DATABASE_URL"
if echo "$DISPOSABLE_URL" | grep -qiE 'prod|railway\.app|pns-crm[^-]'; then
  echo "[FATAL] DISPOSABLE_DATABASE_URL appears to target production"
  exit 1
fi

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
FAILURES=0

# Railway stores the recovery identity as a secret value.  `age -i` expects a
# filename, so materialize an inline age identity only in this short-lived,
# owner-readable work directory.  A file path remains supported for manual
# drills where the operator keeps the identity outside the repository.
DECRYPT_IDENTITY_FILE="$BACKUP_DECRYPT_KEY"
if echo "$BACKUP_DECRYPT_KEY" | grep -q '^AGE-SECRET-KEY-'; then
  DECRYPT_IDENTITY_FILE="${WORKDIR}/age-identity.txt"
  umask 077
  printf '%s\n' "$BACKUP_DECRYPT_KEY" > "$DECRYPT_IDENTITY_FILE"
fi

echo "=== PNS CRM Restore Drill ${TIMESTAMP} ==="

# --- 1. Find latest daily backup ---
LATEST_KEY=$(aws s3 ls "s3://${BACKUP_S3_BUCKET}/backups/daily/" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" \
  | grep '\.dump\.age$' | sort | tail -1 | awk '{print $4}') || true
if [ -z "$LATEST_KEY" ]; then
  echo "[FATAL] No daily backup found"
  exit 1
fi
echo "[restore] Latest: ${LATEST_KEY}"

# --- 2. Download encrypted backup and manifest ---
aws s3 cp "s3://${BACKUP_S3_BUCKET}/backups/daily/${LATEST_KEY}" \
  "${WORKDIR}/backup.dump.age" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors
aws s3 cp "s3://${BACKUP_S3_BUCKET}/backups/daily/${LATEST_KEY}.sha256" \
  "${WORKDIR}/expected.sha256" \
  --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" --only-show-errors 2>/dev/null || true
EXPECTED_SHA=$(cat "${WORKDIR}/expected.sha256" 2>/dev/null | tr -d '[:space:]') || EXPECTED_SHA=""

# --- 3. Verify encrypted checksum BEFORE decryption ---
if [ -f "${WORKDIR}/expected.sha256" ] && [ -n "$EXPECTED_SHA" ]; then
  ACTUAL_ENC_SHA=$(sha256sum "${WORKDIR}/backup.dump.age" | awk '{print $1}')
  if [ "$ACTUAL_ENC_SHA" != "$EXPECTED_SHA" ]; then
    echo "[FATAL] Encrypted checksum mismatch: expected ${EXPECTED_SHA}, got ${ACTUAL_ENC_SHA}"
    exit 1
  fi
  echo "[verify] Encrypted SHA256 matches manifest"
else
  echo "[WARN] No SHA256 manifest found. Skipping encrypted checksum verification."
fi

# --- 4. Decrypt ---
age -d -i "$DECRYPT_IDENTITY_FILE" -o "${WORKDIR}/backup.dump" "${WORKDIR}/backup.dump.age"
rm "${WORKDIR}/backup.dump.age"

# --- 5. List and validate backup contents ---
pg_restore --list "${WORKDIR}/backup.dump" > "${WORKDIR}/toc.txt"
REQUIRED_TABLES="companies contacts tasks activities leads alembic_version"
for table in $REQUIRED_TABLES; do
  if ! grep -q "TABLE DATA.*${table}" "${WORKDIR}/toc.txt"; then
    echo "[FATAL] Required table '${table}' missing from backup"
    FAILURES=$((FAILURES + 1))
  fi
done
if [ "$FAILURES" -gt 0 ]; then
  echo "[FATAL] ${FAILURES} required tables missing. Backup invalid."
  exit 1
fi
echo "[verify] All required tables present in backup"

# --- 6. Restore ---
pg_restore --dbname="$DISPOSABLE_URL" --no-owner --no-acl --clean --if-exists \
  "${WORKDIR}/backup.dump"

# --- 7. Post-restore verification ---
ALEMBIC_VER=$(psql "$DISPOSABLE_URL" -t -c "SELECT version_num FROM alembic_version LIMIT 1" | tr -d '[:space:]')
echo "[verify] Alembic version: ${ALEMBIC_VER}"

ROW_COUNT=$(psql "$DISPOSABLE_URL" -t -c "SELECT COUNT(*) FROM companies" | tr -d '[:space:]')
echo "[verify] companies: ${ROW_COUNT} rows"

for table in $REQUIRED_TABLES; do
  EXISTS=$(psql "$DISPOSABLE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='${table}')" | tr -d '[:space:]')
  if [ "$EXISTS" != "t" ]; then
    echo "[FATAL] Table '${table}' missing after restore"
    FAILURES=$((FAILURES + 1))
  fi
done
if [ "$FAILURES" -gt 0 ]; then
  echo "[FATAL] ${FAILURES} tables missing after restore"
  exit 1
fi

echo "=== Restore drill passed ==="
echo "Disposable database is ready for inspection and must be destroyed manually."

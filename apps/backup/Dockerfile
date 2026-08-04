# =============================================================================
# PNS CRM - Backup Cron Service (Railway Cron compatible)
# =============================================================================
# Runs scripts/backup.sh on a schedule.  No plaintext persistence.
# All artifacts are streamed through age encryption directly to S3/R2.
#
# Required env vars (no defaults - must be set):
#   DATABASE_URL          - PostgreSQL connection string
#   BACKUP_ENCRYPT_KEY    - age public key for encryption
#   BACKUP_S3_BUCKET      - S3/R2 bucket name
#   BACKUP_S3_ENDPOINT    - S3/R2 endpoint URL
#   BACKUP_S3_REGION      - S3/R2 region
#   AWS_ACCESS_KEY_ID     - S3/R2 access key
#   AWS_SECRET_ACCESS_KEY - S3/R2 secret key
#
# Build:
#   docker build -t pns-backup -f apps/backup/Dockerfile .
#
# Run (manual):
#   docker run --rm -e DATABASE_URL=... -e BACKUP_ENCRYPT_KEY=... \
#     -e BACKUP_S3_BUCKET=... -e BACKUP_S3_ENDPOINT=... \
#     -e BACKUP_S3_REGION=... -e AWS_ACCESS_KEY_ID=... \
#     -e AWS_SECRET_ACCESS_KEY=... pns-backup
#
# Railway Cron: set your Railway service to use this Dockerfile and
# configure the CRON_SCHEDULE variable (e.g., "0 2 * * *" for 2 AM daily).
# =============================================================================

FROM postgres:18-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- age encryption tool + AWS CLI v2 ---
ARG AGE_VERSION=v1.2.1
COPY apps/backup/install-tools.sh /tmp/install-tools.sh
RUN sed -i 's/\r$//' /tmp/install-tools.sh \
    && chmod +x /tmp/install-tools.sh \
    && AGE_VERSION=${AGE_VERSION} /tmp/install-tools.sh \
    && rm /tmp/install-tools.sh

WORKDIR /app

# --- Version metadata ---
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\"}" > /app/version.json

# --- Scripts ---
COPY scripts/backup.sh /app/backup.sh
RUN sed -i 's/\r$//' /app/backup.sh && chmod +x /app/backup.sh

# Verify required tools are available
RUN pg_dump --version && age --version && aws --version && bash -n /app/backup.sh

# No volumes, no plaintext persistence.  All data flows through pipes.
# Default command: run backup once.  Override for cron scheduling via Railway Cron.
CMD ["/app/backup.sh"]

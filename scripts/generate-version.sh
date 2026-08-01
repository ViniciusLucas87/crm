#!/bin/bash
# Generate version metadata at build time.
# This script is called from Dockerfiles to inject build identity
# into the image. It creates a version.json file that both the
# API and frontend can consume.
#
# Output format:
# {
#   "git_commit": "abc1234",
#   "git_branch": "main",
#   "build_time": "2026-07-23T16:00:00Z",
#   "image_version": "2026-07-23-abc1234",
#   "alembic_head": "20260722"
# }

set -euo pipefail

OUTPUT="${1:-version.json}"

# Collect metadata
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
IMAGE_VERSION="${BUILD_TIME}-${GIT_COMMIT}"

# Find alembic head (latest migration)
ALEMBIC_DIR="apps/api/alembic/versions"
ALEMBIC_HEAD="unknown"
if [ -d "$ALEMBIC_DIR" ]; then
    # Get the latest migration file by name (they are timestamp-prefixed)
    LATEST_MIGRATION=$(ls "$ALEMBIC_DIR"/*.py 2>/dev/null | grep -v __pycache__ | sort -r | head -1)
    if [ -n "$LATEST_MIGRATION" ]; then
        # Extract the revision prefix from filename (e.g., 20260722 from 20260722_0008_calls_table.py)
        ALEMBIC_HEAD=$(basename "$LATEST_MIGRATION" .py | cut -d'_' -f1)
    fi
fi

cat > "$OUTPUT" << EOF
{
  "git_commit": "${GIT_COMMIT}",
  "git_branch": "${GIT_BRANCH}",
  "build_time": "${BUILD_TIME}",
  "image_version": "${IMAGE_VERSION}",
  "alembic_head": "${ALEMBIC_HEAD}"
}
EOF

echo "Generated $OUTPUT:"
cat "$OUTPUT"

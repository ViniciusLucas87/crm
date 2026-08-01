FROM python:3.12-slim

WORKDIR /app

# ── Version metadata (injected via build args) ──
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
ARG ALEMBIC_HEAD=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\",\"alembic_head\":\"${ALEMBIC_HEAD}\"}" > /app/version.json

# ── Dependencies ──
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──
COPY apps/api .

# ── Validate models at BUILD TIME ──
RUN python -c "from app.infrastructure.db.base import Base; from app.infrastructure.db import models; Base.registry.configure(); print(f'Build-time model check: {len(Base.registry.mappers)} mappers OK')"

# ── OCI Image Metadata ──
LABEL org.opencontainers.image.title="Pacific North Systems API"
LABEL org.opencontainers.image.description="FastAPI backend for PNS CRM"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.created="${BUILD_TIME}"
LABEL org.opencontainers.image.source="https://github.com/pacificnorthsystems/crm"
LABEL com.pns.build_id="${IMAGE_VERSION}"
LABEL com.pns.git_commit="${GIT_COMMIT}"
LABEL com.pns.service="api"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

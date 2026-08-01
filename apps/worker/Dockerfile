FROM python:3.12-slim

WORKDIR /app

# ── Version metadata ──
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\"}" > /app/version.json

# ── Dependencies ──
COPY apps/worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──
COPY apps/worker .
# Worker needs API code to import models, session, LLM provider
COPY apps/api ./api
ENV PYTHONPATH=/app/api:$PYTHONPATH

# ── Validate models at BUILD TIME ──
RUN PYTHONPATH=/app/api python -c "from app.infrastructure.db.base import Base; from app.infrastructure.db import models; Base.registry.configure(); print(f'Build-time model check: {len(Base.registry.mappers)} mappers OK')"

# ── OCI Image Metadata ──
LABEL org.opencontainers.image.title="Pacific North Systems Worker"
LABEL org.opencontainers.image.description="Celery worker for PNS CRM"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.created="${BUILD_TIME}"
LABEL org.opencontainers.image.source="https://github.com/pacificnorthsystems/crm"
LABEL com.pns.build_id="${IMAGE_VERSION}"
LABEL com.pns.git_commit="${GIT_COMMIT}"
LABEL com.pns.service="worker"

CMD ["celery", "-A", "worker_tasks.celery_app", "worker", "--loglevel=INFO", "--concurrency=4"]

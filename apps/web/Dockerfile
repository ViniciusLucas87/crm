FROM node:20-alpine AS deps
WORKDIR /app
COPY apps/web/package.json ./package.json
RUN npm install --legacy-peer-deps --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app

# ── Version metadata ──
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\"}" > /app/version.json

COPY --from=deps /app/node_modules ./node_modules
COPY apps/web .
RUN npm run build
RUN npm prune --omit=dev --no-audit

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app .

# ── OCI Image Metadata ──
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
LABEL org.opencontainers.image.title="Pacific North Systems Web"
LABEL org.opencontainers.image.description="Next.js frontend for PNS CRM"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.created="${BUILD_TIME}"
LABEL org.opencontainers.image.source="https://github.com/pacificnorthsystems/crm"
LABEL com.pns.build_id="${IMAGE_VERSION}"
LABEL com.pns.git_commit="${GIT_COMMIT}"
LABEL com.pns.service="web"

EXPOSE 3000
CMD ["npm", "run", "start"]

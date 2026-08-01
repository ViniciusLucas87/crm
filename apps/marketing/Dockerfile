# ── Marketing Website Dockerfile (Railway production) ──
# Standalone build — does NOT require monorepo root context
# Build from: apps/marketing/

FROM node:20-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.2 --activate
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile --prod=false 2>/dev/null || pnpm install --no-frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.2 --activate

ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\"}" > /app/version.json

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./

ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
LABEL org.opencontainers.image.title="Pacific North Systems Marketing"
LABEL org.opencontainers.image.description="Next.js public website"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.created="${BUILD_TIME}"
LABEL com.pns.service="marketing"

EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]

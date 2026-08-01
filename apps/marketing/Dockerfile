# ── Marketing Website Dockerfile (Railway production) ──
# Pacific North Systems — public website at pacificnorthsystems.com
# Uses pnpm workspace, builds from monorepo root context

FROM node:20-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.2 --activate

# Copy workspace root files for pnpm resolution
COPY pnpm-workspace.yaml ./
COPY pnpm-lock.yaml ./
COPY package.json ./

# Copy marketing + shared contracts manifests
COPY apps/marketing/package.json ./apps/marketing/package.json
COPY packages/contracts/package.json ./packages/contracts/package.json
COPY packages/contracts ./packages/contracts

RUN pnpm install --frozen-lockfile --filter @pns/marketing

FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.12.2 --activate

# ── Version metadata ──
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ARG IMAGE_VERSION=unknown
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"build_time\":\"${BUILD_TIME}\",\"image_version\":\"${IMAGE_VERSION}\"}" > /app/version.json

COPY pnpm-workspace.yaml ./
COPY pnpm-lock.yaml ./
COPY package.json ./
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/marketing/node_modules ./apps/marketing/node_modules
COPY --from=deps /app/packages/contracts/node_modules ./packages/contracts/node_modules
COPY apps/marketing ./apps/marketing
COPY packages/contracts ./packages/contracts

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/apps/marketing
RUN pnpm build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

COPY --from=builder /app/apps/marketing/.next ./.next
COPY --from=builder /app/apps/marketing/package.json ./
COPY --from=builder /app/apps/marketing/node_modules ./node_modules
COPY --from=builder /app/apps/marketing/public ./public
COPY --from=builder /app/apps/marketing/next.config.mjs ./

# ── OCI Metadata ──
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

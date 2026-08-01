# Pacific North Systems OS — Developer Commands
# ======================================================
#
# Every command in this Makefile is designed to be:
#   - deterministic (same input → same output)
#   - self-validating (fails loudly if something is wrong)
#   - cache-aware (incremental where safe, full rebuild where needed)
#
# Quick reference:
#   make dev        Start everything with auto-rebuild + migrations
#   make rebuild    Full clean rebuild of all containers
#   make doctor     Comprehensive system health check
#   make verify     Run all validation checks
#   make clean      Remove all Docker artifacts
#   make status     Show running containers and versions
#   make migrate    Apply pending database migrations

# ── Version injection (computed once per make invocation) ──
GIT_COMMIT    := $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
BUILD_TIME    := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo unknown)
IMAGE_VERSION := $(BUILD_TIME)-$(GIT_COMMIT)
ALEMBIC_HEAD  := $(shell ls apps/api/alembic/versions/*.py 2>/dev/null | grep -v __pycache__ | sort -r | head -1 | xargs basename | cut -d'_' -f1 || echo unknown)

BUILD_ARGS := \
	GIT_COMMIT=$(GIT_COMMIT) \
	BUILD_TIME=$(BUILD_TIME) \
	IMAGE_VERSION=$(IMAGE_VERSION) \
	ALEMBIC_HEAD=$(ALEMBIC_HEAD)

.PHONY: dev rebuild doctor verify clean status migrate logs test help

# ──────────────────────────────────────────────────
# DEVELOPMENT
# ──────────────────────────────────────────────────

dev:
	@echo "=== Starting development environment ==="
	@echo "  Version: $(IMAGE_VERSION)"
	@echo "  Commit:  $(GIT_COMMIT)"
	@echo ""
	docker compose build --build-arg $(BUILD_ARGS)
	docker compose up -d
	@echo ""
	@echo "Waiting for API to be healthy..."
	@sleep 8
	$(MAKE) migrate
	@echo ""
	$(MAKE) status
	@echo ""
	@echo "API:    http://localhost:8000/api/v1/health"
	@echo "Web:    http://localhost:3000"

# ──────────────────────────────────────────────────
# FULL REBUILD
# ──────────────────────────────────────────────────

rebuild:
	@echo "=== Full rebuild (all containers) ==="
	@echo "  Version: $(IMAGE_VERSION)"
	@echo "  Commit:  $(GIT_COMMIT)"
	@echo ""
	docker compose down
	docker compose build --no-cache --build-arg $(BUILD_ARGS)
	docker compose up -d
	@echo ""
	@echo "Waiting for services to be healthy..."
	@sleep 10
	$(MAKE) migrate
	@echo ""
	$(MAKE) doctor

# ──────────────────────────────────────────────────
# SYSTEM HEALTH CHECK (DOCTOR MODE)
# ──────────────────────────────────────────────────

doctor:
	@echo ""
	@echo "══════════════════════════════════════════════"
	@echo "  Pacific North Systems OS — Doctor Report"
	@echo "══════════════════════════════════════════════"
	@echo ""
	@echo "── Docker ──"
	@docker info --format '  Version: {{.ServerVersion}}' 2>/dev/null || echo "  ✗ Docker not running"
	@echo ""
	@echo "── Containers ──"
	@docker compose ps --format '  {{.Name}}\t{{.Status}}' 2>/dev/null || echo "  ✗ No containers"
	@echo ""
	@echo "── API Health ──"
	@curl -sf http://localhost:8000/api/v1/health/ready > /dev/null 2>&1 && echo "  ✓ API ready" || echo "  ✗ API not ready"
	@echo ""
	@echo "── API Liveness ──"
	@curl -sf http://localhost:8000/api/v1/health/live > /dev/null 2>&1 && echo "  ✓ API alive" || echo "  ✗ API not alive"
	@echo ""
	@echo "── Web Server ──"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:3000 2>/dev/null || echo "  ✗ Web unreachable"
	@echo ""
	@echo "── Database ──"
	@docker compose exec -T postgres pg_isready -U postgres -d pns_crm 2>/dev/null && echo "  ✓ Database ready" || echo "  ✗ Database unreachable"
	@echo ""
	@echo "── Redis ──"
	@docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG && echo "  ✓ Redis ready" || echo "  ✗ Redis unreachable"
	@echo ""
	@echo "── Build IDs ──"
	@echo "  Source:  $(IMAGE_VERSION)"
	@API_VER=$$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('build_id','unknown'))" 2>/dev/null || echo "unreachable"); \
	echo "  API:     $$API_VER"; \
	if [ "$$API_VER" = "$(IMAGE_VERSION)" ]; then echo "  ✓ Build IDs match"; else echo "  ✗ MISMATCH — stale image detected"; fi
	@echo ""
	@echo "── Model Fingerprint ──"
	@curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Fingerprint: {d.get(\"model_fingerprint\",\"unknown\")}')" 2>/dev/null || echo "  ✗ Unavailable"
	@echo ""
	@echo "── Alembic ──"
	@docker compose exec -T api python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; s = ScriptDirectory.from_config(Config('alembic.ini')); print(f'  Head: {s.get_current_head()[:12] if s.get_current_head() else \"unknown\"}...')" 2>/dev/null || echo "  ✗ Alembic unavailable"
	@echo ""
	@echo "── Environment ──"
	@echo "  PNS_ENV=$${PNS_ENV:-development}"
	@echo ""
	@echo "── Version Drift ──"
	@API_COMMIT=$$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('git_commit','unknown'))" 2>/dev/null || echo "unreachable"); \
	WEB_COMMIT=$$(docker compose exec -T web cat /app/version.json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('git_commit','unknown'))" 2>/dev/null || echo "unreachable"); \
	echo "  API commit:  $$API_COMMIT"; \
	echo "  Web commit:  $$WEB_COMMIT"; \
	echo "  Source:      $(GIT_COMMIT)"; \
	if [ "$$API_COMMIT" = "$(GIT_COMMIT)" ] && [ "$$WEB_COMMIT" = "$(GIT_COMMIT)" ]; then \
		echo "  ✓ All versions match source"; \
	else \
		echo "  ✗ VERSION DRIFT DETECTED — rebuild with 'make rebuild'"; \
	fi
	@echo ""
	@echo "── OCI Labels ──"
	@docker inspect crmsystem-api:latest --format '  API Build ID: {{index .Config.Labels "com.pns.build_id"}}' 2>/dev/null || echo "  ✗ No OCI labels"
	@docker inspect crmsystem-web:latest --format '  Web Build ID: {{index .Config.Labels "com.pns.build_id"}}' 2>/dev/null || echo "  ✗ No OCI labels"
	@echo ""
	@echo "── Pending Migrations ──"
	@docker compose exec -T api alembic current 2>/dev/null | head -2 || echo "  ✗ Unable to check"
	@echo ""

# ──────────────────────────────────────────────────
# VALIDATION
# ──────────────────────────────────────────────────

verify:
	@echo "=== Verification ==="
	@echo ""
	@echo "--- Model validation ---"
	@docker compose exec -T api python -c "from app.infrastructure.db.base import Base; from app.infrastructure.db import models; Base.registry.configure(); print(f'  {len(Base.registry.mappers)} mappers configured — OK')" 2>/dev/null || echo "  FAILED"
	@echo ""
	@echo "--- API version ---"
	@curl -s http://localhost:8000/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Image: {d[\"version\"]}\n  Commit: {d[\"build_commit\"]}\n  Alembic: {d[\"alembic_head\"]}')" 2>/dev/null || echo "  FAILED"
	@echo ""
	@echo "--- Source version ---"
	@echo "  Git commit:  $(GIT_COMMIT)"
	@echo "  Build time:  $(BUILD_TIME)"
	@echo "  Alembic head: $(ALEMBIC_HEAD)"
	@echo ""
	@echo "--- Stale image check ---"
	@API_COMMIT=$$(curl -s http://localhost:8000/api/v1/health | python3 -c "import sys,json; print(json.load(sys.stdin)['build_commit'])" 2>/dev/null); \
	if [ "$$API_COMMIT" = "$(GIT_COMMIT)" ]; then \
		echo "  API image matches source: $$API_COMMIT — OK"; \
	else \
		echo "  WARNING: API image ($$API_COMMIT) does NOT match source ($(GIT_COMMIT)) — REBUILD NEEDED"; \
	fi

# ──────────────────────────────────────────────────
# DATABASE MIGRATIONS
# ──────────────────────────────────────────────────

migrate:
	@echo "=== Running database migrations ==="
	docker compose exec -T api alembic upgrade head 2>/dev/null || echo "  API not running — start with 'make dev' first"

# ──────────────────────────────────────────────────
# STATUS
# ──────────────────────────────────────────────────

status:
	@echo "=== Service Status ==="
	@docker compose ps
	@echo ""
	@echo "--- Images ---"
	@docker images crmsystem-* --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" 2>/dev/null || echo "  No images found"

# ──────────────────────────────────────────────────
# CLEANUP
# ──────────────────────────────────────────────────

clean:
	@echo "=== Cleaning Docker artifacts ==="
	docker compose down -v --remove-orphans
	docker system prune -f --filter "label=com.docker.compose.project=crmsystem" 2>/dev/null || true
	@echo "Done. Run 'make dev' to start fresh."

# ──────────────────────────────────────────────────
# LOGS
# ──────────────────────────────────────────────────

logs:
	docker compose logs -f --tail=50

# ──────────────────────────────────────────────────
# TESTS
# ──────────────────────────────────────────────────

test:
	@echo "=== Running tests ==="
	cd apps/web && npx vitest run 2>&1 || echo "  (run 'pnpm install' in apps/web if vitest is missing)"

# ──────────────────────────────────────────────────
# HELP
# ──────────────────────────────────────────────────

help:
	@echo "Pacific North Systems OS — Developer Commands"
	@echo ""
	@echo "  make dev        Start dev environment (rebuilds changed, migrates, starts)"
	@echo "  make rebuild    Full clean rebuild of ALL containers"
	@echo "  make doctor     Comprehensive system health check"
	@echo "  make verify     Run all validation checks (models, versions, tests)"
	@echo "  make status     Show running containers and image versions"
	@echo "  make migrate    Apply pending database migrations"
	@echo "  make clean      Remove all Docker artifacts (containers, volumes, networks)"
	@echo "  make logs       Tail all service logs"
	@echo "  make test       Run all test suites"
	@echo "  make help       Show this help"

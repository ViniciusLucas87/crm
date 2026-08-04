# Worker hardening tests run in the worker container where worker_tasks is native.
# See: apps/worker/tests/test_phase1_worker_hardening.py
# Run: docker compose run --rm worker pip install -r requirements-dev.txt -q && docker compose run --rm worker pytest tests/ -q


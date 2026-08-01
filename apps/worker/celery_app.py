import os

from celery import Celery

redis_password = os.getenv("REDIS_PASSWORD", "redis_dev")
broker_url = os.getenv("REDIS_URL", f"redis://:{redis_password}@redis:6379/0")
backend_url = os.getenv("REDIS_RESULT_URL", broker_url)

celery_app = Celery(
    "pns_worker",
    broker=broker_url,
    backend=backend_url,
)


@celery_app.task(name="jobs.ping")
def ping() -> str:
    return "pong"

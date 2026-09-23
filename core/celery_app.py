from celery import Celery
from core.config import settings


celery_app = Celery("docmind", broker=settings.redis_url, backend=settings.redis_url, include=['services.tasks'],)
celery_app.conf.update(
    task_track_started=True,
    worker_max_tasks_per_child=50,
    broker_connection_retry_on_startup=True,
)


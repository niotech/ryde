"""
Celery configuration for the Ryde project.

This module configures Celery for background task processing.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'challenge.settings')

app = Celery('challenge')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')


# Optional: Configure periodic tasks
app.conf.beat_schedule = {
    # Example: Run a task every hour
    # 'cleanup-old-data': {
    #     'task': 'users.tasks.cleanup_old_users',
    #     'schedule': 3600.0,  # 1 hour
    # },
}
import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

app = Celery('django_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'subscriptions': {
        'task': 'telegram_bot.tasks.subscriptions',
        'schedule': 600
    }
}

app.autodiscover_tasks()

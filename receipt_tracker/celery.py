import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipt_tracker.settings')

app = Celery('receipt_tracker')
app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('niplan')
# On utilise Redis comme "Broker" (le facteur qui transporte les messages)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
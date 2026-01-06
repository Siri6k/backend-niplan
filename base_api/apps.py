from django.apps import AppConfig

class BaseApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base_api'

    def ready(self):
        import base_api.signals # Importation indispensable
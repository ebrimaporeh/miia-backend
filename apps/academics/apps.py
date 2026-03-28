# apps/academics/apps.py
from django.apps import AppConfig

class AcademicsConfig(AppConfig):  # Changed from CoreConfig to AcademicsConfig
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.academics'
    
    # def ready(self):
    #     import apps.academics.signals  # Optional: if you have signals
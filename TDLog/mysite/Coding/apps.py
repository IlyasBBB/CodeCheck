from django.apps import AppConfig


class CodingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Coding'

    def ready(self):
        from .views import create_default_questions
        create_default_questions()
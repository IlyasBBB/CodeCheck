from django.apps import AppConfig


class CodingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Coding"
    # Default questions are created on first visit to the initial test (views.take_initial_test),
    # not here: querying the database at startup breaks "migrate" on a fresh database.

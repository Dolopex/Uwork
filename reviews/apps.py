from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'

    def ready(self):
        # Importa las señales que recalculan la calificación promedio.
        from . import signals  # noqa: F401

from django.apps import AppConfig


class GestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestion"
    verbose_name = "Gestion des dossiers"

    def ready(self):
        """Charge les signaux au démarrage de l'application."""
        try:
            import gestion.signals  # noqa: F401
        except ImportError:
            pass

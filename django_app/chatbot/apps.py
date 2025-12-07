"""
Configuration de l'application Chatbot
"""

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    verbose_name = 'Assistant IA / Chatbot'

    def ready(self):
        # Import des signaux si necessaire
        pass

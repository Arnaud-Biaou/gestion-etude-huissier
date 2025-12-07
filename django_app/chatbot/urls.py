"""
URLs du module Chatbot.
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Interface principale
    path('', views.chatbot_home, name='home'),

    # API REST pour fallback si WebSocket indisponible
    path('api/message/', views.api_envoyer_message, name='api_message'),
    path('api/sessions/', views.api_liste_sessions, name='api_sessions'),
    path('api/session/<uuid:session_id>/', views.api_detail_session, name='api_session_detail'),
    path('api/session/<uuid:session_id>/messages/', views.api_messages_session, name='api_session_messages'),

    # Actions en attente de validation
    path('api/actions/en-attente/', views.api_actions_en_attente, name='api_actions_en_attente'),
    path('api/action/<uuid:action_id>/valider/', views.api_valider_action, name='api_valider_action'),
    path('api/action/<uuid:action_id>/refuser/', views.api_refuser_action, name='api_refuser_action'),

    # Configuration
    path('api/config/', views.api_configuration, name='api_config'),
    path('api/config/vocal/', views.api_config_vocal, name='api_config_vocal'),

    # Statistiques
    path('api/stats/', views.api_statistiques, name='api_stats'),

    # Nettoyage des sessions expirees (a appeler via cron)
    path('api/nettoyer-sessions/', views.api_nettoyer_sessions, name='api_nettoyer'),
]

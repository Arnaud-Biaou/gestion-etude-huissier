"""
URLs pour le Portail Client
"""

from django.urls import path
from . import views

app_name = 'portail_client'

urlpatterns = [
    # Pages publiques
    path('', views.landing_page, name='landing_page'),
    path('contact/', views.portail_contact, name='portail_contact'),

    # Authentification
    path('connexion/', views.portail_connexion, name='portail_connexion'),
    path('deconnexion/', views.portail_deconnexion, name='portail_deconnexion'),

    # Espace client
    path('espace/', views.portail_tableau_bord, name='portail_tableau_bord'),
    path('espace/profil/', views.portail_mon_profil, name='portail_mon_profil'),

    # Dossiers
    path('espace/dossiers/', views.portail_mes_dossiers, name='portail_mes_dossiers'),
    path('espace/dossiers/<int:dossier_id>/', views.portail_dossier_detail, name='portail_dossier_detail'),

    # Documents
    path('espace/documents/', views.portail_mes_documents, name='portail_mes_documents'),
    path('espace/documents/<int:doc_id>/telecharger/', views.portail_telecharger_document, name='portail_telecharger_document'),

    # Messages
    path('espace/messages/', views.portail_mes_messages, name='portail_mes_messages'),
    path('espace/messages/envoyer/', views.portail_envoyer_message, name='portail_envoyer_message'),

    # Notifications
    path('espace/notifications/', views.portail_notifications, name='portail_notifications'),
    path('espace/notifications/<int:notif_id>/lue/', views.portail_marquer_notification_lue, name='portail_marquer_notification_lue'),

    # API endpoints
    path('api/notifications/count/', views.api_notifications_count, name='api_notifications_count'),
    path('api/messages/count/', views.api_messages_count, name='api_messages_count'),
]

"""
URLs du module Gérance Immobilière
"""

from django.urls import path
from . import views

app_name = 'gerance'

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('proprietaires/', views.proprietaires, name='proprietaires'),
    path('biens/', views.biens, name='biens'),
    path('locataires/', views.locataires, name='locataires'),
    path('baux/', views.baux_view, name='baux'),
    path('loyers/', views.loyers_view, name='loyers'),
    path('incidents/', views.incidents_view, name='incidents'),
    path('reversements/', views.reversements_view, name='reversements'),

    # API - Propriétaires
    path('api/proprietaires/creer/', views.api_creer_proprietaire, name='api_creer_proprietaire'),

    # API - Biens
    path('api/biens/creer/', views.api_creer_bien, name='api_creer_bien'),

    # API - Locataires
    path('api/locataires/creer/', views.api_creer_locataire, name='api_creer_locataire'),

    # API - Baux
    path('api/baux/creer/', views.api_creer_bail, name='api_creer_bail'),

    # API - Loyers
    path('api/loyers/paiement/', views.api_enregistrer_paiement, name='api_enregistrer_paiement'),
    path('api/loyers/generer/', views.api_generer_loyers, name='api_generer_loyers'),

    # API - Incidents
    path('api/incidents/creer/', views.api_creer_incident, name='api_creer_incident'),
    path('api/incidents/<uuid:incident_id>/resoudre/', views.api_resoudre_incident, name='api_resoudre_incident'),

    # API - Statistiques
    path('api/statistiques/', views.api_statistiques, name='api_statistiques'),
]

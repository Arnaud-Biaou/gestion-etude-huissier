"""
URLs du module Gerance Immobiliere
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

    # CORRECTION #22: URLs vues detail
    path('proprietaires/<uuid:pk>/', views.proprietaire_detail, name='proprietaire_detail'),
    path('biens/<uuid:pk>/', views.bien_detail, name='bien_detail'),
    path('locataires/<uuid:pk>/', views.locataire_detail, name='locataire_detail'),
    path('baux/<uuid:pk>/', views.bail_detail, name='bail_detail'),

    # CORRECTION #23: Vue etats des lieux
    path('etats-lieux/', views.etats_lieux_view, name='etats_lieux'),

    # CORRECTION #29: Vue quittances
    path('quittances/', views.quittances_view, name='quittances'),

    # API - Proprietaires
    path('api/proprietaires/creer/', views.api_creer_proprietaire, name='api_creer_proprietaire'),

    # API - Biens
    path('api/biens/creer/', views.api_creer_bien, name='api_creer_bien'),

    # API - Locataires
    path('api/locataires/creer/', views.api_creer_locataire, name='api_creer_locataire'),

    # API - Baux
    path('api/baux/creer/', views.api_creer_bail, name='api_creer_bail'),
    path('api/baux/renouveler/', views.api_renouveler_bail, name='api_renouveler_bail'),  # CORRECTION #25
    path('api/baux/resilier/', views.api_resilier_bail, name='api_resilier_bail'),  # CORRECTION #26

    # API - Loyers
    path('api/loyers/paiement/', views.api_enregistrer_paiement, name='api_enregistrer_paiement'),
    path('api/loyers/generer/', views.api_generer_loyers, name='api_generer_loyers'),

    # API - Incidents
    path('api/incidents/creer/', views.api_creer_incident, name='api_creer_incident'),
    path('api/incidents/<uuid:incident_id>/resoudre/', views.api_resoudre_incident, name='api_resoudre_incident'),

    # API - Reversements
    path('api/reversements/calculer/', views.api_calculer_reversements, name='api_calculer_reversements'),  # CORRECTION #24
    path('api/reversements/effectuer/', views.api_effectuer_reversement, name='api_effectuer_reversement'),

    # API - Etats des lieux
    path('api/etats-lieux/creer/', views.api_creer_etat_lieux, name='api_creer_etat_lieux'),  # CORRECTION #23

    # API - Statistiques
    path('api/statistiques/', views.api_statistiques, name='api_statistiques'),

    # CORRECTION #27: Exports PDF
    path('export/quittance/', views.export_quittance_pdf, name='export_quittance_pdf'),
    path('export/bail/', views.export_bail_pdf, name='export_bail_pdf'),
    path('export/baux/', views.export_baux_pdf, name='export_baux_pdf'),
    path('export/releve/', views.export_releve_pdf, name='export_releve_pdf'),

    # CORRECTION #28: Exports Excel
    path('export/loyers/excel/', views.export_loyers_excel, name='export_loyers_excel'),
    path('export/reversements/excel/', views.export_reversements_excel, name='export_reversements_excel'),
]

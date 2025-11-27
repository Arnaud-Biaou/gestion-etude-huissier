"""
URLs du module Trésorerie
"""

from django.urls import path
from . import views

app_name = 'tresorerie'

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('comptes/', views.comptes, name='comptes'),
    path('mouvements/', views.mouvements, name='mouvements'),
    path('previsions/', views.previsions_view, name='previsions'),
    path('rapprochements/', views.rapprochements, name='rapprochements'),

    # API - Comptes
    path('api/comptes/creer/', views.api_creer_compte, name='api_creer_compte'),
    path('api/comptes/soldes/', views.api_soldes_comptes, name='api_soldes_comptes'),

    # API - Mouvements
    path('api/mouvements/creer/', views.api_creer_mouvement, name='api_creer_mouvement'),
    path('api/mouvements/<uuid:mouvement_id>/valider/', views.api_valider_mouvement, name='api_valider_mouvement'),
    path('api/mouvements/<uuid:mouvement_id>/annuler/', views.api_annuler_mouvement, name='api_annuler_mouvement'),

    # API - Prévisions
    path('api/previsions/creer/', views.api_creer_prevision, name='api_creer_prevision'),

    # API - Rapprochements
    path('api/rapprochements/creer/', views.api_creer_rapprochement, name='api_creer_rapprochement'),

    # API - Alertes
    path('api/alertes/<uuid:alerte_id>/lue/', views.api_marquer_alerte_lue, name='api_marquer_alerte_lue'),

    # API - Statistiques
    path('api/statistiques/', views.api_statistiques, name='api_statistiques'),
]

"""
URLs du module Recouvrement de Créances
"""

from django.urls import path
from . import views

app_name = 'recouvrement'

urlpatterns = [
    # Point Global Créancier - Vue principale
    path('point-global/', views.point_global_creancier, name='point_global_creancier'),

    # APIs Point Global
    path('api/point-global/generer/', views.api_generer_point_global, name='api_generer_point_global'),
    path('api/point-global/<uuid:point_id>/telecharger/', views.api_telecharger_point_global, name='api_telecharger_point_global'),
    path('api/point-global/<uuid:point_id>/regenerer/', views.api_regenerer_pdf, name='api_regenerer_pdf'),
    path('api/point-global/<uuid:point_id>/supprimer/', views.api_supprimer_point_global, name='api_supprimer_point_global'),
    path('api/point-global/<uuid:point_id>/', views.api_detail_point_global, name='api_detail_point_global'),
    path('api/points-globaux/', views.api_liste_points_globaux, name='api_liste_points_globaux'),
    path('api/points-globaux/creancier/<int:creancier_id>/', views.api_liste_points_globaux, name='api_liste_points_globaux_creancier'),

    # APIs Dossiers et Créanciers
    path('api/creancier/<int:creancier_id>/dossiers/', views.api_dossiers_creancier, name='api_dossiers_creancier'),
    path('api/creancier/<int:creancier_id>/statistiques/', views.api_statistiques_creancier, name='api_statistiques_creancier'),

    # API Calcul honoraires
    path('api/calculer-honoraires/', views.api_calculer_honoraires, name='api_calculer_honoraires'),
]

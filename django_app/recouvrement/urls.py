"""
URLs du module Recouvrement de Créances
"""

from django.urls import path
from . import views

app_name = 'recouvrement'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════════════════════════════
    path('', views.dashboard_recouvrement, name='dashboard_recouvrement'),

    # ═══════════════════════════════════════════════════════════════════
    # VUES CRUD - DOSSIERS DE RECOUVREMENT
    # ═══════════════════════════════════════════════════════════════════
    path('dossiers/', views.liste_dossiers_recouvrement, name='liste_dossiers_recouvrement'),
    path('dossiers/nouveau/', views.creer_dossier_recouvrement, name='creer_dossier_recouvrement'),
    path('dossiers/<uuid:dossier_id>/', views.detail_dossier_recouvrement, name='detail_dossier_recouvrement'),
    path('dossiers/<uuid:dossier_id>/modifier/', views.modifier_dossier_recouvrement, name='modifier_dossier_recouvrement'),

    # ═══════════════════════════════════════════════════════════════════
    # POINT GLOBAL CRÉANCIER
    # ═══════════════════════════════════════════════════════════════════
    path('point-global/', views.point_global_creancier, name='point_global_creancier'),

    # APIs Point Global
    path('api/point-global/generer/', views.api_generer_point_global, name='api_generer_point_global'),
    path('api/point-global/<uuid:point_id>/telecharger/', views.api_telecharger_point_global, name='api_telecharger_point_global'),
    path('api/point-global/<uuid:point_id>/regenerer/', views.api_regenerer_pdf, name='api_regenerer_pdf'),
    path('api/point-global/<uuid:point_id>/supprimer/', views.api_supprimer_point_global, name='api_supprimer_point_global'),
    path('api/point-global/<uuid:point_id>/', views.api_detail_point_global, name='api_detail_point_global'),
    path('api/points-globaux/', views.api_liste_points_globaux, name='api_liste_points_globaux'),
    path('api/points-globaux/creancier/<int:creancier_id>/', views.api_liste_points_globaux, name='api_liste_points_globaux_creancier'),

    # ═══════════════════════════════════════════════════════════════════
    # APIs PAIEMENT
    # ═══════════════════════════════════════════════════════════════════
    path('api/paiement/enregistrer/', views.api_enregistrer_paiement, name='api_enregistrer_paiement'),
    path('api/paiement/<uuid:paiement_id>/reverser/', views.api_effectuer_reversement, name='api_effectuer_reversement'),
    path('api/paiement/<uuid:paiement_id>/imputer/', views.api_imputer_reserve, name='api_imputer_reserve'),

    # ═══════════════════════════════════════════════════════════════════
    # APIs DOSSIER
    # ═══════════════════════════════════════════════════════════════════
    path('api/dossier/<uuid:dossier_id>/paiements/', views.api_liste_paiements, name='api_liste_paiements'),
    path('api/dossier/<uuid:dossier_id>/situation/', views.api_situation_dossier, name='api_situation_dossier'),
    path('api/dossier/<uuid:dossier_id>/historique/', views.api_historique_dossier, name='api_historique_dossier'),

    # ═══════════════════════════════════════════════════════════════════
    # APIs CRÉANCIERS
    # ═══════════════════════════════════════════════════════════════════
    path('api/creancier/<int:creancier_id>/dossiers/', views.api_dossiers_creancier, name='api_dossiers_creancier'),
    path('api/creancier/<int:creancier_id>/statistiques/', views.api_statistiques_creancier, name='api_statistiques_creancier'),

    # ═══════════════════════════════════════════════════════════════════
    # API CALCUL HONORAIRES
    # ═══════════════════════════════════════════════════════════════════
    path('api/calculer-honoraires/', views.api_calculer_honoraires, name='api_calculer_honoraires'),
]

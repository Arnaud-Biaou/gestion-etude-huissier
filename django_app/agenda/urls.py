"""
URLs pour le module Agenda
"""

from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    # Page principale
    path('', views.agenda_home, name='home'),

    # ==========================================================================
    # API RENDEZ-VOUS
    # ==========================================================================
    path('api/rdv/', views.api_liste_rdv, name='api_liste_rdv'),
    path('api/rdv/<uuid:rdv_id>/', views.api_detail_rdv, name='api_detail_rdv'),
    path('api/rdv/creer/', views.api_creer_rdv, name='api_creer_rdv'),
    path('api/rdv/<uuid:rdv_id>/modifier/', views.api_modifier_rdv, name='api_modifier_rdv'),
    path('api/rdv/<uuid:rdv_id>/supprimer/', views.api_supprimer_rdv, name='api_supprimer_rdv'),

    # ==========================================================================
    # API TÂCHES
    # ==========================================================================
    path('api/taches/', views.api_liste_taches, name='api_liste_taches'),
    path('api/taches/<uuid:tache_id>/', views.api_detail_tache, name='api_detail_tache'),
    path('api/taches/creer/', views.api_creer_tache, name='api_creer_tache'),
    path('api/taches/<uuid:tache_id>/modifier/', views.api_modifier_tache, name='api_modifier_tache'),
    path('api/taches/<uuid:tache_id>/terminer/', views.api_terminer_tache, name='api_terminer_tache'),
    path('api/taches/<uuid:tache_id>/supprimer/', views.api_supprimer_tache, name='api_supprimer_tache'),

    # ==========================================================================
    # API DÉLÉGATION
    # ==========================================================================
    path('api/taches/<uuid:tache_id>/deleguer/', views.api_deleguer_tache, name='api_deleguer_tache'),
    path('api/taches/<uuid:tache_id>/accepter/', views.api_accepter_delegation, name='api_accepter_delegation'),
    path('api/taches/<uuid:tache_id>/aide/', views.api_demander_aide, name='api_demander_aide'),
    path('api/taches/<uuid:tache_id>/valider/', views.api_valider_delegation, name='api_valider_delegation'),
    path('api/delegations/', views.api_taches_deleguees, name='api_taches_deleguees'),

    # ==========================================================================
    # API COMMENTAIRES ET CHECKLIST
    # ==========================================================================
    path('api/taches/<uuid:tache_id>/commentaire/', views.api_ajouter_commentaire, name='api_ajouter_commentaire'),
    path('api/taches/<uuid:tache_id>/checklist/', views.api_ajouter_checklist_item, name='api_ajouter_checklist_item'),
    path('api/checklist/<uuid:item_id>/toggle/', views.api_toggle_checklist_item, name='api_toggle_checklist_item'),

    # ==========================================================================
    # API VUES PRINCIPALES (BOUTONS)
    # ==========================================================================
    # BOUTON 1: Tous les RDV et Tâches -> api_liste_rdv + api_liste_taches
    # BOUTON 2: Tâches Déléguées
    # path('api/delegations/', ...) - défini ci-dessus

    # BOUTON 3: Dossiers en attente
    path('api/dossiers-attente/', views.api_dossiers_en_attente, name='api_dossiers_en_attente'),

    # BOUTON 4: Actions du jour
    path('api/actions-jour/', views.api_actions_du_jour, name='api_actions_du_jour'),

    # BOUTON 5: Vue d'ensemble
    path('api/vue-ensemble/', views.api_vue_ensemble, name='api_vue_ensemble'),

    # ==========================================================================
    # API CLÔTURE DE JOURNÉE
    # ==========================================================================
    path('api/cloturer-journee/', views.api_cloturer_journee, name='api_cloturer_journee'),
    path('api/bilan-journee/<str:date_str>/', views.api_bilan_journee, name='api_bilan_journee'),

    # ==========================================================================
    # API NOTIFICATIONS
    # ==========================================================================
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('api/notifications/<uuid:notif_id>/lue/', views.api_marquer_notification_lue, name='api_marquer_notification_lue'),
    path('api/notifications/toutes-lues/', views.api_marquer_toutes_lues, name='api_marquer_toutes_lues'),

    # ==========================================================================
    # API ÉTIQUETTES
    # ==========================================================================
    path('api/etiquettes/', views.api_liste_etiquettes, name='api_liste_etiquettes'),
    path('api/etiquettes/creer/', views.api_creer_etiquette, name='api_creer_etiquette'),

    # ==========================================================================
    # API CONFIGURATION
    # ==========================================================================
    path('api/configuration/', views.api_configuration, name='api_configuration'),
    path('api/configuration/modifier/', views.api_modifier_configuration, name='api_modifier_configuration'),

    # ==========================================================================
    # API UTILITAIRES
    # ==========================================================================
    path('api/collaborateurs/', views.api_collaborateurs, name='api_collaborateurs'),
    path('api/dossiers-liste/', views.api_dossiers_liste, name='api_dossiers_liste'),
    path('api/recherche/', views.api_recherche_globale, name='api_recherche_globale'),
]

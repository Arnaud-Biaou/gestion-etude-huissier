"""
URLs pour le module Paramètres
"""

from django.urls import path
from . import views

app_name = 'parametres'

urlpatterns = [
    # Page principale
    path('', views.index, name='index'),

    # API Configuration générale
    path('api/config/', views.api_get_config, name='api_get_config'),
    path('api/config/sauvegarder/', views.api_sauvegarder_config, name='api_sauvegarder_config'),
    path('api/config/upload-image/', views.api_upload_image, name='api_upload_image'),

    # API Sites/Agences
    path('api/sites/', views.api_sites_list, name='api_sites_list'),
    path('api/sites/creer/', views.api_site_create, name='api_site_create'),
    path('api/sites/<int:site_id>/modifier/', views.api_site_update, name='api_site_update'),
    path('api/sites/<int:site_id>/supprimer/', views.api_site_delete, name='api_site_delete'),

    # API Types de dossier
    path('api/types-dossier/', views.api_types_dossier_list, name='api_types_dossier_list'),
    path('api/types-dossier/creer/', views.api_type_dossier_create, name='api_type_dossier_create'),
    path('api/types-dossier/<int:type_id>/modifier/', views.api_type_dossier_update, name='api_type_dossier_update'),
    path('api/types-dossier/<int:type_id>/supprimer/', views.api_type_dossier_delete, name='api_type_dossier_delete'),

    # API Statuts de dossier
    path('api/statuts-dossier/', views.api_statuts_dossier_list, name='api_statuts_dossier_list'),
    path('api/statuts-dossier/creer/', views.api_statut_dossier_create, name='api_statut_dossier_create'),
    path('api/statuts-dossier/<int:statut_id>/modifier/', views.api_statut_dossier_update, name='api_statut_dossier_update'),

    # API Modèles de documents
    path('api/modeles-document/', views.api_modeles_document_list, name='api_modeles_document_list'),
    path('api/modeles-document/creer/', views.api_modele_document_create, name='api_modele_document_create'),
    path('api/modeles-document/<int:modele_id>/modifier/', views.api_modele_document_update, name='api_modele_document_update'),
    path('api/modeles-document/<int:modele_id>/dupliquer/', views.api_modele_document_duplicate, name='api_modele_document_duplicate'),
    path('api/modeles-document/<int:modele_id>/supprimer/', views.api_modele_document_delete, name='api_modele_document_delete'),

    # API Localités
    path('api/localites/', views.api_localites_list, name='api_localites_list'),
    path('api/localites/creer/', views.api_localite_create, name='api_localite_create'),
    path('api/localites/<int:localite_id>/modifier/', views.api_localite_update, name='api_localite_update'),
    path('api/localites/importer/', views.api_localites_import, name='api_localites_import'),

    # API Taux légaux
    path('api/taux-legaux/', views.api_taux_legaux_list, name='api_taux_legaux_list'),
    path('api/taux-legaux/creer/', views.api_taux_legal_create, name='api_taux_legal_create'),
    path('api/taux-legaux/<int:taux_id>/modifier/', views.api_taux_legal_update, name='api_taux_legal_update'),

    # API Jours fériés
    path('api/jours-feries/', views.api_jours_feries_list, name='api_jours_feries_list'),
    path('api/jours-feries/creer/', views.api_jour_ferie_create, name='api_jour_ferie_create'),
    path('api/jours-feries/<int:jour_id>/modifier/', views.api_jour_ferie_update, name='api_jour_ferie_update'),

    # API Types d'actes
    path('api/types-actes/', views.api_types_actes_list, name='api_types_actes_list'),
    path('api/types-actes/creer/', views.api_type_acte_create, name='api_type_acte_create'),
    path('api/types-actes/<int:type_id>/modifier/', views.api_type_acte_update, name='api_type_acte_update'),

    # API Juridictions
    path('api/juridictions/', views.api_juridictions_list, name='api_juridictions_list'),
    path('api/juridictions/creer/', views.api_juridiction_create, name='api_juridiction_create'),
    path('api/juridictions/<int:juridiction_id>/modifier/', views.api_juridiction_update, name='api_juridiction_update'),

    # API Sauvegardes
    path('api/sauvegardes/creer/', views.api_backup_create, name='api_backup_create'),
    path('api/sauvegardes/<int:backup_id>/restaurer/', views.api_backup_restore, name='api_backup_restore'),

    # API Exports
    path('api/export/<str:format_type>/', views.api_export_data, name='api_export_data'),

    # API Tests connexions
    path('api/test/smtp/', views.api_test_smtp, name='api_test_smtp'),
    path('api/test/sms/', views.api_test_sms, name='api_test_sms'),

    # API Journal
    path('api/journal/', views.api_journal_list, name='api_journal_list'),
]

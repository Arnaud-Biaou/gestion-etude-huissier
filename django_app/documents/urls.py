"""
URLs pour le module Documents
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Vues principales
    path('', views.drive_view, name='drive'),
    path('dossier/<uuid:dossier_id>/', views.documents_dossier_view, name='dossier_documents'),

    # API Documents
    path('api/documents/', views.api_documents_liste, name='api_documents_liste'),
    path('api/documents/<uuid:document_id>/', views.api_document_detail, name='api_document_detail'),
    path('api/documents/upload/', views.api_document_upload, name='api_document_upload'),
    path('api/documents/<uuid:document_id>/telecharger/', views.api_document_telecharger, name='api_document_telecharger'),
    path('api/documents/supprimer/', views.api_document_supprimer, name='api_document_supprimer'),
    path('api/documents/restaurer/', views.api_document_restaurer, name='api_document_restaurer'),
    path('api/documents/deplacer/', views.api_document_deplacer, name='api_document_deplacer'),
    path('api/documents/renommer/', views.api_document_renommer, name='api_document_renommer'),

    # API Génération de documents
    path('api/generer/fiche-dossier/', views.api_generer_fiche_dossier, name='api_generer_fiche_dossier'),
    path('api/generer/acte/', views.api_generer_acte, name='api_generer_acte'),
    path('api/generer/facture/', views.api_generer_facture_pdf, name='api_generer_facture'),
    path('api/generer/decompte/', views.api_generer_decompte, name='api_generer_decompte'),
    path('api/generer/lettre/', views.api_generer_lettre, name='api_generer_lettre'),

    # API Dossiers virtuels
    path('api/dossiers/', views.api_dossiers_liste, name='api_dossiers_liste'),
    path('api/dossiers/creer/', views.api_dossier_creer, name='api_dossier_creer'),
    path('api/dossiers/supprimer/', views.api_dossier_supprimer, name='api_dossier_supprimer'),
    path('api/dossiers/renommer/', views.api_dossier_renommer, name='api_dossier_renommer'),

    # API Modèles de documents
    path('api/modeles/', views.api_modeles_liste, name='api_modeles_liste'),
    path('api/modeles/<uuid:modele_id>/', views.api_modele_detail, name='api_modele_detail'),
    path('api/modeles/sauvegarder/', views.api_modele_sauvegarder, name='api_modele_sauvegarder'),

    # API Partage
    path('api/partage/creer/', views.api_partage_creer, name='api_partage_creer'),
    path('api/partage/revoquer/', views.api_partage_revoquer, name='api_partage_revoquer'),

    # API Statistiques et Audit
    path('api/statistiques/', views.api_statistiques, name='api_statistiques'),
    path('api/audit/<uuid:document_id>/', views.api_audit_document, name='api_audit_document'),
    path('api/activite/', views.api_activite_recente, name='api_activite_recente'),

    # API Corbeille
    path('api/corbeille/', views.api_corbeille_liste, name='api_corbeille_liste'),
    path('api/corbeille/vider/', views.api_corbeille_vider, name='api_corbeille_vider'),

    # Partage public (sans authentification)
    path('partage/<str:token>/', views.partage_public_view, name='partage_public'),
]

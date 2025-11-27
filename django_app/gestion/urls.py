from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/nouveau/', views.nouveau_dossier, name='nouveau_dossier'),
    path('facturation/', views.facturation, name='facturation'),
    path('calcul/', views.calcul_recouvrement, name='calcul'),
    path('drive/', views.drive, name='drive'),
    path('securite/', views.securite, name='securite'),

    # Modules en construction
    path('tresorerie/', views.module_en_construction, {'module_name': 'tresorerie'}, name='tresorerie'),
    path('rh/', views.module_en_construction, {'module_name': 'rh'}, name='rh'),
    path('gerance/', views.module_en_construction, {'module_name': 'gerance'}, name='gerance'),
    path('agenda/', views.module_en_construction, {'module_name': 'agenda'}, name='agenda'),
    path('parametres/', views.module_en_construction, {'module_name': 'parametres'}, name='parametres'),

    # API endpoints - Facturation
    path('api/generer-numero-facture/', views.api_generer_numero_facture, name='api_generer_numero_facture'),
    path('api/sauvegarder-facture/', views.api_sauvegarder_facture, name='api_sauvegarder_facture'),
    path('api/supprimer-facture/', views.api_supprimer_facture, name='api_supprimer_facture'),
    path('api/normaliser-mecef/', views.api_normaliser_mecef, name='api_normaliser_mecef'),
    path('api/exporter-factures/', views.api_exporter_factures, name='api_exporter_factures'),

    # API endpoints - Calcul Recouvrement
    path('api/calculer-interets/', views.api_calculer_interets, name='api_calculer_interets'),
    path('api/calculer-emoluments/', views.api_calculer_emoluments, name='api_calculer_emoluments'),
    path('api/sauvegarder-calcul/', views.api_sauvegarder_calcul, name='api_sauvegarder_calcul'),
    path('api/supprimer-calcul/', views.api_supprimer_calcul, name='api_supprimer_calcul'),
    path('api/charger-historique/', views.api_charger_historique, name='api_charger_historique'),

    # API endpoints - Autres
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
    path('api/supprimer-dossier/', views.api_supprimer_dossier, name='api_supprimer_dossier'),
]

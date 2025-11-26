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

    # Module Trésorerie
    path('tresorerie/', views.tresorerie, name='tresorerie'),

    # Modules en construction
    path('comptabilite/', views.module_en_construction, {'module_name': 'comptabilite'}, name='comptabilite'),
    path('rh/', views.module_en_construction, {'module_name': 'rh'}, name='rh'),
    path('gerance/', views.module_en_construction, {'module_name': 'gerance'}, name='gerance'),
    path('agenda/', views.module_en_construction, {'module_name': 'agenda'}, name='agenda'),
    path('parametres/', views.module_en_construction, {'module_name': 'parametres'}, name='parametres'),

    # API endpoints - Calculs
    path('api/calculer-interets/', views.api_calculer_interets, name='api_calculer_interets'),
    path('api/calculer-emoluments/', views.api_calculer_emoluments, name='api_calculer_emoluments'),
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
    path('api/supprimer-dossier/', views.api_supprimer_dossier, name='api_supprimer_dossier'),

    # API endpoints - Trésorerie: Caisses
    path('api/tresorerie/caisse/ouvrir/', views.api_caisse_ouvrir, name='api_caisse_ouvrir'),
    path('api/tresorerie/caisse/fermer/', views.api_caisse_fermer, name='api_caisse_fermer'),
    path('api/tresorerie/caisse/creer/', views.api_caisse_creer, name='api_caisse_creer'),

    # API endpoints - Trésorerie: Encaissements
    path('api/tresorerie/encaissement/creer/', views.api_encaissement_creer, name='api_encaissement_creer'),

    # API endpoints - Trésorerie: Décaissements
    path('api/tresorerie/decaissement/creer/', views.api_decaissement_creer, name='api_decaissement_creer'),
    path('api/tresorerie/decaissement/approuver/', views.api_decaissement_approuver, name='api_decaissement_approuver'),
    path('api/tresorerie/decaissement/rejeter/', views.api_decaissement_rejeter, name='api_decaissement_rejeter'),
    path('api/tresorerie/decaissement/payer/', views.api_decaissement_payer, name='api_decaissement_payer'),

    # API endpoints - Trésorerie: Opérations
    path('api/tresorerie/operation/annuler/', views.api_operation_annuler, name='api_operation_annuler'),

    # API endpoints - Trésorerie: Consignations
    path('api/tresorerie/consignation/creer/', views.api_consignation_creer, name='api_consignation_creer'),
    path('api/tresorerie/consignation/reverser/', views.api_consignation_reverser, name='api_consignation_reverser'),

    # API endpoints - Trésorerie: Rapprochement bancaire
    path('api/tresorerie/rapprochement/creer/', views.api_rapprochement_creer, name='api_rapprochement_creer'),

    # API endpoints - Trésorerie: Statistiques et Journal
    path('api/tresorerie/stats/', views.api_tresorerie_stats, name='api_tresorerie_stats'),
    path('api/tresorerie/journal/', views.api_journal_tresorerie, name='api_journal_tresorerie'),
]

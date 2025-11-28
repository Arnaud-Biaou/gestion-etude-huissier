from django.urls import path
from . import views

app_name = 'comptabilite'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_comptabilite, name='dashboard'),

    # Saisie des écritures
    path('saisie/', views.saisie_ecriture, name='saisie'),
    path('ecritures/', views.liste_ecritures, name='ecritures'),
    path('ecritures/<int:ecriture_id>/', views.detail_ecriture, name='detail_ecriture'),

    # Journaux
    path('journaux/', views.journaux, name='journaux'),
    path('journal-centralisateur/', views.journal_centralisateur, name='journal_centralisateur'),

    # Grand livre
    path('grand-livre/', views.grand_livre, name='grand_livre'),

    # Balance
    path('balance/', views.balance, name='balance'),
    path('balance-agee/', views.balance_agee, name='balance_agee'),

    # États financiers
    path('etats-financiers/', views.etats_financiers, name='etats_financiers'),

    # Plan comptable
    path('plan-comptable/', views.plan_comptable, name='plan_comptable'),

    # TVA
    path('tva/', views.gestion_tva, name='tva'),
    path('tva/<int:declaration_id>/', views.detail_declaration_tva, name='detail_declaration_tva'),

    # Clôture
    path('cloture/', views.cloture_exercice, name='cloture'),

    # Rapports
    path('rapports/', views.rapports, name='rapports'),
    path('rapports/<int:rapport_id>/', views.detail_rapport, name='detail_rapport'),

    # Lettrage
    path('lettrage/', views.lettrage, name='lettrage'),

    # Aide
    path('aide/', views.aide_comptabilite, name='aide'),

    # API endpoints - Saisie
    path('api/ecriture-facile/', views.api_creer_ecriture_facile, name='api_ecriture_facile'),
    path('api/ecriture-guidee/', views.api_creer_ecriture_guidee, name='api_ecriture_guidee'),
    path('api/ecriture-expert/', views.api_creer_ecriture_expert, name='api_ecriture_expert'),
    path('api/valider-ecriture/', views.api_valider_ecriture, name='api_valider_ecriture'),
    path('api/configurer/', views.api_configurer_comptabilite, name='api_configurer'),
    path('api/comptes/<str:classe>/', views.api_comptes_par_classe, name='api_comptes_classe'),

    # API endpoints - Clôture
    path('api/pre-cloture/', views.api_pre_cloture, name='api_pre_cloture'),
    path('api/cloture/', views.api_cloture_exercice, name='api_cloture'),

    # API endpoints - TVA
    path('api/declaration-tva/', views.api_creer_declaration_tva, name='api_creer_declaration_tva'),

    # API endpoints - Lettrage
    path('api/lettrage/', views.api_creer_lettrage, name='api_creer_lettrage'),

    # Exports
    path('export/balance/pdf/', views.export_balance_pdf, name='export_balance_pdf'),
    path('export/balance/excel/', views.export_balance_excel, name='export_balance_excel'),
    path('export/grand-livre/excel/', views.export_grand_livre_excel, name='export_grand_livre_excel'),
    path('export/csv/', views.export_csv, name='export_csv'),
]

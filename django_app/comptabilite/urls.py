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

    # Grand livre
    path('grand-livre/', views.grand_livre, name='grand_livre'),

    # Balance
    path('balance/', views.balance, name='balance'),

    # États financiers
    path('etats-financiers/', views.etats_financiers, name='etats_financiers'),

    # Plan comptable
    path('plan-comptable/', views.plan_comptable, name='plan_comptable'),

    # TVA
    path('tva/', views.gestion_tva, name='tva'),

    # Clôture
    path('cloture/', views.cloture_exercice, name='cloture'),

    # Rapports
    path('rapports/', views.rapports, name='rapports'),

    # Aide
    path('aide/', views.aide_comptabilite, name='aide'),

    # API endpoints
    path('api/ecriture-facile/', views.api_creer_ecriture_facile, name='api_ecriture_facile'),
    path('api/ecriture-guidee/', views.api_creer_ecriture_guidee, name='api_ecriture_guidee'),
    path('api/ecriture-expert/', views.api_creer_ecriture_expert, name='api_ecriture_expert'),
    path('api/valider-ecriture/', views.api_valider_ecriture, name='api_valider_ecriture'),
    path('api/configurer/', views.api_configurer_comptabilite, name='api_configurer'),
    path('api/comptes/<str:classe>/', views.api_comptes_par_classe, name='api_comptes_classe'),
]

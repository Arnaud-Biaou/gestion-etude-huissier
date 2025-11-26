from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/nouveau/', views.nouveau_dossier, name='nouveau_dossier'),
    path('dossiers/<str:reference>/', views.voir_dossier, name='voir_dossier'),
    path('dossiers/<str:reference>/modifier/', views.modifier_dossier, name='modifier_dossier'),
    path('facturation/', views.facturation, name='facturation'),
    path('calcul/', views.calcul_recouvrement, name='calcul'),
    path('drive/', views.drive, name='drive'),
    path('securite/', views.securite, name='securite'),

    # Modules en construction
    path('tresorerie/', views.module_en_construction, {'module_name': 'tresorerie'}, name='tresorerie'),
    path('comptabilite/', views.module_en_construction, {'module_name': 'comptabilite'}, name='comptabilite'),
    path('rh/', views.module_en_construction, {'module_name': 'rh'}, name='rh'),
    path('gerance/', views.module_en_construction, {'module_name': 'gerance'}, name='gerance'),
    path('agenda/', views.module_en_construction, {'module_name': 'agenda'}, name='agenda'),
    path('parametres/', views.module_en_construction, {'module_name': 'parametres'}, name='parametres'),

    # API endpoints
    path('api/calculer-interets/', views.api_calculer_interets, name='api_calculer_interets'),
    path('api/calculer-emoluments/', views.api_calculer_emoluments, name='api_calculer_emoluments'),
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
    path('api/supprimer-dossier/', views.api_supprimer_dossier, name='api_supprimer_dossier'),
    path('api/creer-dossier/', views.api_creer_dossier, name='api_creer_dossier'),
    path('api/modifier-dossier/', views.api_modifier_dossier, name='api_modifier_dossier'),
]

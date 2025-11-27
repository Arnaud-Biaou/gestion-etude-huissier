"""
URLs pour le module MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES DE CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES DE CITATIONS
"""

from django.urls import path
from . import views

app_name = 'citations'

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('cedules/', views.cedules, name='cedules'),
    path('cedules/nouvelle/', views.nouvelle_cedule, name='nouvelle_cedule'),
    path('cedules/<int:cedule_id>/', views.cedule_detail, name='cedule_detail'),
    path('memoires/', views.memoires, name='memoires'),
    path('memoires/nouveau/', views.nouveau_memoire, name='nouveau_memoire'),
    path('memoires/<int:memoire_id>/', views.memoire_detail, name='memoire_detail'),
    path('baremes/', views.baremes, name='baremes'),
    path('localites/', views.localites, name='localites'),
    path('registre/', views.registre_parquet, name='registre_parquet'),

    # API - CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules
    path('api/cedules/creer/', views.api_cedule_creer, name='api_cedule_creer'),
    path('api/cedules/<int:cedule_id>/', views.api_cedule_detail, name='api_cedule_detail'),
    path('api/cedules/<int:cedule_id>/modifier/', views.api_cedule_modifier, name='api_cedule_modifier'),

    # API - Destinataires
    path('api/cedules/<int:cedule_id>/destinataires/ajouter/', views.api_destinataire_ajouter, name='api_destinataire_ajouter'),
    path('api/destinataires/<int:destinataire_id>/supprimer/', views.api_destinataire_supprimer, name='api_destinataire_supprimer'),

    # API - Signification
    path('api/destinataires/<int:destinataire_id>/signifier/', views.api_signification_creer, name='api_signification_creer'),
    path('api/calculer-frais/', views.api_calculer_frais, name='api_calculer_frais'),

    # API - MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires
    path('api/memoires/creer/', views.api_memoire_creer, name='api_memoire_creer'),
    path('api/memoires/<int:memoire_id>/', views.api_memoire_detail, name='api_memoire_detail'),
    path('api/memoires/<int:memoire_id>/certifier/', views.api_memoire_certifier, name='api_memoire_certifier'),
    path('api/memoires/<int:memoire_id>/soumettre/', views.api_memoire_soumettre, name='api_memoire_soumettre'),
    path('api/memoires/<int:memoire_id>/viser/', views.api_memoire_viser, name='api_memoire_viser'),
    path('api/memoires/<int:memoire_id>/taxer/', views.api_memoire_taxer, name='api_memoire_taxer'),
    path('api/memoires/<int:memoire_id>/payer/', views.api_memoire_payer, name='api_memoire_payer'),

    # API - LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s
    path('api/localites/', views.api_localites_liste, name='api_localites_liste'),
    path('api/localites/<int:localite_id>/distance/', views.api_localite_distance, name='api_localite_distance'),

    # API - Statistiques
    path('api/statistiques/', views.api_statistiques, name='api_statistiques'),
]

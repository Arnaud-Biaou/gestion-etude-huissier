"""
URLs du module Ressources Humaines
"""

from django.urls import path
from . import views

app_name = 'rh'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Employés
    path('employes/', views.liste_employes, name='employes'),
    path('employes/nouveau/', views.nouveau_employe, name='nouveau_employe'),
    path('employes/<int:employe_id>/', views.detail_employe, name='detail_employe'),
    path('api/employes/sauvegarder/', views.sauvegarder_employe, name='sauvegarder_employe'),

    # Contrats
    path('contrats/', views.liste_contrats, name='contrats'),
    path('api/contrats/avenant/', views.creer_avenant, name='creer_avenant'),

    # Paie
    path('paie/', views.paie_dashboard, name='paie'),
    path('paie/bulletin/<int:bulletin_id>/', views.detail_bulletin, name='detail_bulletin'),
    path('paie/bulletin/<int:bulletin_id>/imprimer/', views.imprimer_bulletin, name='imprimer_bulletin'),
    path('api/paie/generer/', views.generer_bulletins, name='generer_bulletins'),
    path('api/paie/bulletin/<int:bulletin_id>/valider/', views.valider_bulletin, name='valider_bulletin'),
    path('api/paie/bulletin/<int:bulletin_id>/payer/', views.payer_bulletin, name='payer_bulletin'),

    # Congés
    path('conges/', views.conges_dashboard, name='conges'),
    path('api/conges/demander/', views.demander_conge, name='demander_conge'),
    path('api/conges/<int:conge_id>/approuver/', views.approuver_conge, name='approuver_conge'),

    # Absences
    path('absences/', views.absences_dashboard, name='absences'),
    path('api/absences/enregistrer/', views.enregistrer_absence, name='enregistrer_absence'),

    # Prêts et avances
    path('prets/', views.prets_dashboard, name='prets'),
    path('api/prets/demander/', views.demander_pret, name='demander_pret'),
    path('api/prets/<int:pret_id>/approuver/', views.approuver_pret, name='approuver_pret'),

    # Déclarations
    path('declarations/', views.declarations_dashboard, name='declarations'),
    path('api/declarations/generer/', views.generer_declaration, name='generer_declaration'),

    # Évaluations
    path('evaluations/', views.evaluations_dashboard, name='evaluations'),
    path('api/evaluations/creer/', views.creer_evaluation, name='creer_evaluation'),

    # Formations
    path('formations/', views.formations_dashboard, name='formations'),

    # Discipline
    path('discipline/', views.discipline_dashboard, name='discipline'),

    # Fins de contrat
    path('fins-contrat/', views.fins_contrat_dashboard, name='fins_contrat'),
    path('api/fins-contrat/initier/', views.initier_fin_contrat, name='initier_fin_contrat'),

    # Configuration
    path('configuration/', views.configuration, name='configuration'),
    path('api/configuration/sauvegarder/', views.sauvegarder_configuration, name='sauvegarder_configuration'),

    # Rapports
    path('rapports/registre/', views.registre_employeur, name='registre_employeur'),
    path('rapports/livre-paie/', views.livre_paie, name='livre_paie'),

    # API
    path('api/employes/', views.api_employes, name='api_employes'),
    path('api/employes/<int:employe_id>/solde-conges/', views.api_solde_conges, name='api_solde_conges'),
    path('api/statistiques/', views.api_statistiques_rh, name='api_statistiques'),
]

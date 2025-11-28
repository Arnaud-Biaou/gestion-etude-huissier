from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/nouveau/', views.nouveau_dossier, name='nouveau_dossier'),
    path('facturation/', views.facturation, name='facturation'),
    path('memoires/', views.memoires, name='memoires'),
    path('calcul/', views.calcul_recouvrement, name='calcul'),
    path('drive/', views.drive, name='drive'),
    path('securite/', views.securite, name='securite'),

    # Pages créanciers, encaissements, reversements
    path('creanciers/', views.creanciers, name='creanciers'),
    path('encaissements/', views.encaissements, name='encaissements'),
    path('reversements/', views.reversements, name='reversements'),

    # Note: Les modules tresorerie, rh, gerance, agenda, parametres
    # ont maintenant leurs propres applications Django dediees
    # et sont configures dans etude_huissier/urls.py

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

    # API endpoints - Créanciers
    path('api/creanciers/', views.api_creanciers_liste, name='api_creanciers_liste'),
    path('api/creanciers/creer/', views.api_creancier_creer, name='api_creancier_creer'),
    path('api/creanciers/<int:creancier_id>/', views.api_creancier_detail, name='api_creancier_detail'),
    path('api/creanciers/<int:creancier_id>/tableau-bord/', views.api_creancier_tableau_bord, name='api_creancier_tableau_bord'),
    path('api/creanciers/<int:creancier_id>/encaissements-disponibles/', views.api_reversements_encaissements_disponibles, name='api_encaissements_disponibles'),
    path('api/creanciers/<int:creancier_id>/point-global/generer/', views.api_point_global_generer, name='api_point_global_generer'),
    path('api/creanciers/<int:creancier_id>/envoi-automatique/configurer/', views.api_envoi_automatique_configurer, name='api_envoi_automatique_configurer'),
    path('api/creanciers/<int:creancier_id>/envoi-automatique/historique/', views.api_envoi_automatique_historique, name='api_envoi_automatique_historique'),

    # API endpoints - Encaissements
    path('api/encaissements/', views.api_encaissements_liste, name='api_encaissements_liste'),
    path('api/encaissements/creer/', views.api_encaissement_creer, name='api_encaissement_creer'),
    path('api/encaissements/export/', views.api_encaissements_export, name='api_encaissements_export'),
    path('api/encaissements/<int:encaissement_id>/', views.api_encaissement_detail, name='api_encaissement_detail'),
    path('api/encaissements/<int:encaissement_id>/valider/', views.api_encaissement_valider, name='api_encaissement_valider'),
    path('api/encaissements/<int:encaissement_id>/annuler/', views.api_encaissement_annuler, name='api_encaissement_annuler'),
    path('api/dossiers/<int:dossier_id>/encaissements/', views.api_encaissements_historique_dossier, name='api_encaissements_historique_dossier'),

    # API endpoints - Reversements
    path('api/reversements/', views.api_reversements_liste, name='api_reversements_liste'),
    path('api/reversements/creer/', views.api_reversement_creer, name='api_reversement_creer'),
    path('api/reversements/<int:reversement_id>/effectuer/', views.api_reversement_effectuer, name='api_reversement_effectuer'),

    # API endpoints - Basculement amiable → forcé
    path('api/dossiers/<int:dossier_id>/basculer-force/', views.api_dossier_basculer_force, name='api_dossier_basculer_force'),
    path('api/dossiers/<int:dossier_id>/basculements/', views.api_dossier_historique_basculements, name='api_dossier_historique_basculements'),

    # API endpoints - Points globaux créanciers
    path('api/points-globaux/<int:point_id>/', views.api_point_global_detail, name='api_point_global_detail'),
    path('api/points-globaux/<int:point_id>/export/', views.api_point_global_export_excel, name='api_point_global_export_excel'),

    # API endpoints - Autres
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
    path('api/supprimer-dossier/', views.api_supprimer_dossier, name='api_supprimer_dossier'),

    # API endpoints - Mémoires de Cédules
    path('api/memoires/creer/', views.api_memoire_creer, name='api_memoire_creer'),
    path('api/memoires/supprimer/', views.api_memoire_supprimer, name='api_memoire_supprimer'),
    path('api/memoires/<int:memoire_id>/', views.api_memoire_detail, name='api_memoire_detail'),
    path('api/memoires/<int:memoire_id>/certifier/', views.api_memoire_certifier, name='api_memoire_certifier'),
    path('api/memoires/<int:memoire_id>/verifier/', views.api_memoire_verifier, name='api_memoire_verifier'),
    path('api/memoires/<int:memoire_id>/export/', views.api_memoire_export_pdf, name='api_memoire_export_pdf'),

    # API endpoints - Affaires du mémoire
    path('api/memoires/<int:memoire_id>/affaires/creer/', views.api_affaire_creer, name='api_affaire_creer'),
    path('api/affaires/<int:affaire_id>/modifier/', views.api_affaire_modifier, name='api_affaire_modifier'),
    path('api/affaires/<int:affaire_id>/supprimer/', views.api_affaire_supprimer, name='api_affaire_supprimer'),

    # API endpoints - Destinataires
    path('api/affaires/<int:affaire_id>/destinataires/creer/', views.api_destinataire_creer, name='api_destinataire_creer'),
    path('api/destinataires/<int:destinataire_id>/modifier/', views.api_destinataire_modifier, name='api_destinataire_modifier'),
    path('api/destinataires/<int:destinataire_id>/supprimer/', views.api_destinataire_supprimer, name='api_destinataire_supprimer'),

    # API endpoints - Actes
    path('api/destinataires/<int:destinataire_id>/actes/creer/', views.api_acte_creer, name='api_acte_creer'),
    path('api/actes/<int:acte_id>/modifier/', views.api_acte_modifier, name='api_acte_modifier'),
    path('api/actes/<int:acte_id>/supprimer/', views.api_acte_supprimer, name='api_acte_supprimer'),

    # API endpoints - Autorités requérantes
    path('api/autorites/', views.api_autorites_liste, name='api_autorites_liste'),
    path('api/autorites/creer/', views.api_autorite_creer, name='api_autorite_creer'),

    # API endpoints - Tableau de bord avancé
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard_data'),
]

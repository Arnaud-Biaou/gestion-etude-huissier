from django.urls import path
from . import views
from . import views_verification

app_name = 'gestion'

urlpatterns = [
    # === VÉRIFICATION PUBLIQUE DES ACTES (pas de login requis) ===
    path('v/<str:code>/', views_verification.verification_acte, name='verification_acte_court'),
    path('verification/', views_verification.verification_accueil, name='verification_accueil'),
    path('verification/<str:code>/', views_verification.verification_acte, name='verification_acte'),
    path('api/verification/<str:code>/', views_verification.verification_acte_api, name='verification_acte_api'),

    # Pages principales
    path('', views.dashboard, name='dashboard'),
    path('recherche/', views.recherche_globale, name='recherche_globale'),
    path('dossiers/', views.dossiers, name='dossiers'),
    path('dossiers/nouveau/', views.nouveau_dossier, name='nouveau_dossier'),
    path('dossiers/<int:pk>/', views.dossier_detail, name='dossier_detail'),
    path('dossiers/<int:pk>/modifier/', views.modifier_dossier, name='modifier_dossier'),

    # === ACTES SÉCURISÉS ===
    path('dossier/<int:dossier_id>/securiser/', views.securiser_acte, name='securiser_acte'),
    path('acte-securise/<int:acte_id>/', views.acte_securise_detail, name='acte_securise_detail'),
    path('dossier/<int:dossier_id>/actes-securises/', views.liste_actes_securises, name='liste_actes_securises'),

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

    # API endpoints - Gestion des utilisateurs (sécurité)
    path('api/utilisateurs/', views.api_utilisateurs_liste, name='api_utilisateurs_liste'),
    path('api/utilisateurs/creer/', views.api_utilisateur_creer, name='api_utilisateur_creer'),
    path('api/utilisateurs/<int:pk>/', views.api_utilisateur_detail, name='api_utilisateur_detail'),
    path('api/utilisateurs/<int:pk>/modifier/', views.api_utilisateur_modifier, name='api_utilisateur_modifier'),
    path('api/utilisateurs/<int:pk>/toggle-actif/', views.api_utilisateur_toggle_actif, name='api_utilisateur_toggle_actif'),
    path('api/utilisateurs/<int:pk>/reset-mdp/', views.api_utilisateur_reset_mdp, name='api_utilisateur_reset_mdp'),

    # API endpoints - Facturation
    path('api/generer-numero-facture/', views.api_generer_numero_facture, name='api_generer_numero_facture'),
    path('api/sauvegarder-facture/', views.api_sauvegarder_facture, name='api_sauvegarder_facture'),
    path('api/supprimer-facture/', views.api_supprimer_facture, name='api_supprimer_facture'),
    path('api/normaliser-mecef/', views.api_normaliser_mecef, name='api_normaliser_mecef'),
    path('api/exporter-factures/', views.api_exporter_factures, name='api_exporter_factures'),
    path('factures/<int:facture_id>/imprimer/', views.imprimer_facture, name='imprimer_facture'),

    # === AVOIRS (Factures d'avoir) ===
    path('api/factures/<int:facture_id>/creer-avoir/', views.api_creer_avoir, name='api_creer_avoir'),
    path('api/factures/<int:facture_id>/creer-corrective/', views.api_creer_corrective, name='api_creer_corrective'),

    # === PROFORMAS ===
    path('proformas/', views.liste_proformas, name='liste_proformas'),
    path('proformas/nouveau/', views.nouvelle_proforma, name='nouvelle_proforma'),
    path('proformas/<int:proforma_id>/', views.detail_proforma, name='detail_proforma'),
    path('proformas/<int:proforma_id>/imprimer/', views.imprimer_proforma, name='imprimer_proforma'),
    path('proformas/<int:proforma_id>/convertir/', views.convertir_proforma, name='convertir_proforma'),

    # API endpoints - Proformas
    path('api/proforma/sauvegarder/', views.api_sauvegarder_proforma, name='api_sauvegarder_proforma'),
    path('api/proforma/supprimer/', views.api_supprimer_proforma, name='api_supprimer_proforma'),
    path('api/proforma/<int:proforma_id>/', views.api_proforma_detail, name='api_proforma_detail'),

    # API endpoints - Calcul Recouvrement
    path('api/calculer-interets/', views.api_calculer_interets, name='api_calculer_interets'),
    path('api/calculer-emoluments/', views.api_calculer_emoluments, name='api_calculer_emoluments'),
    path('api/sauvegarder-calcul/', views.api_sauvegarder_calcul, name='api_sauvegarder_calcul'),
    path('api/supprimer-calcul/', views.api_supprimer_calcul, name='api_supprimer_calcul'),
    path('api/charger-historique/', views.api_charger_historique, name='api_charger_historique'),
    path('api/exporter-decompte-pdf/', views.api_exporter_decompte_pdf, name='api_exporter_decompte_pdf'),
    path('api/exporter-decompte-excel/', views.api_exporter_decompte_excel, name='api_exporter_decompte_excel'),

    # API endpoints - Créanciers
    path('api/creanciers/', views.api_creanciers_liste, name='api_creanciers_liste'),
    path('api/creanciers/export/', views.api_creanciers_export, name='api_creanciers_export'),
    path('api/creanciers/creer/', views.api_creancier_creer, name='api_creancier_creer'),
    path('api/creanciers/<int:creancier_id>/', views.api_creancier_detail, name='api_creancier_detail'),
    path('api/creanciers/<int:creancier_id>/desactiver/', views.api_creancier_desactiver, name='api_creancier_desactiver'),
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
    path('api/encaissements/<int:encaissement_id>/recu/', views.encaissement_recu_pdf, name='encaissement_recu_pdf'),
    path('api/dossiers/<int:dossier_id>/encaissements/', views.api_encaissements_historique_dossier, name='api_encaissements_historique_dossier'),

    # API endpoints - Reversements
    path('api/reversements/', views.api_reversements_liste, name='api_reversements_liste'),
    path('api/reversements/creer/', views.api_reversement_creer, name='api_reversement_creer'),
    path('api/reversements/<int:reversement_id>/effectuer/', views.api_reversement_effectuer, name='api_reversement_effectuer'),
    path('api/reversements/<int:reversement_id>/bordereau/', views.reversement_bordereau_pdf, name='reversement_bordereau_pdf'),

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
    path('api/memoires/<int:memoire_id>/viser/', views.api_memoire_viser, name='api_memoire_viser'),
    path('api/memoires/<int:memoire_id>/taxer/', views.api_memoire_taxer, name='api_memoire_taxer'),
    path('api/memoires/<int:memoire_id>/transmettre-tresor/', views.api_memoire_transmettre_tresor, name='api_memoire_transmettre_tresor'),
    path('api/memoires/<int:memoire_id>/payer/', views.api_memoire_payer, name='api_memoire_payer'),

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

    # Calendriers Saisie Immobilière
    path('calendriers-saisie-immo/', views.calendriers_saisie_immo, name='calendriers_saisie_immo'),
    path('calendriers-saisie-immo/<int:pk>/', views.calendrier_saisie_detail, name='calendrier_saisie_detail'),
    path('api/calendrier-saisie/creer/', views.api_creer_calendrier_saisie, name='api_creer_calendrier_saisie'),
    path('api/calendrier-saisie/calculer/', views.api_calculer_dates_saisie, name='api_calculer_dates_saisie'),
    path('api/calendrier-saisie/<int:pk>/', views.api_calendrier_saisie_detail, name='api_calendrier_saisie_detail'),
    path('api/calendrier-saisie/<int:pk>/pdf/', views.api_telecharger_calendrier_pdf, name='api_telecharger_calendrier_pdf'),
    path('api/calendrier-saisie/<int:pk>/pdf-detail/', views.api_telecharger_calendrier_pdf_detail, name='api_telecharger_calendrier_pdf_detail'),
    path('api/calendrier-saisie/<int:pk>/modifier/', views.api_modifier_calendrier_saisie, name='api_modifier_calendrier_saisie'),
    path('api/calendrier-saisie/<int:pk>/supprimer/', views.api_supprimer_calendrier_saisie, name='api_supprimer_calendrier_saisie'),

    # Rapports - Point des factures et notes de frais
    path('rapports/factures/dossier/', views.point_factures_par_dossier, name='point_factures_dossier'),
    path('rapports/factures/client/', views.point_factures_par_client, name='point_factures_client'),
    path('rapports/factures/avocat/', views.point_factures_par_avocat, name='point_factures_avocat'),
    path('rapports/notes-frais/', views.point_notes_frais, name='point_notes_frais'),

    # API Autocomplétion et suggestions parties
    path('api/parties/autocomplete/', views.api_autocomplete_parties, name='api_autocomplete_parties'),
    path('api/parties/suggerer-normalisation/', views.api_suggerer_normalisation, name='api_suggerer_normalisation'),
    path('api/dossiers/verifier-similaire/', views.api_verifier_dossier_similaire, name='api_verifier_dossier_similaire'),

    # Admin suggestions parties
    path('admin/suggestions-parties/', views.admin_suggestions_parties, name='admin_suggestions_parties'),
    path('admin/appliquer-suggestion/<int:partie_id>/', views.admin_appliquer_suggestion, name='admin_appliquer_suggestion'),

    # Import de données
    path('import/', views.import_donnees_accueil, name='import_accueil'),
    path('import/nouvelle/', views.import_donnees_nouvelle_session, name='import_nouvelle_session'),
    path('import/<int:session_id>/analyser/', views.import_donnees_analyser, name='import_analyser'),
    path('import/<int:session_id>/valider/', views.import_donnees_valider, name='import_valider'),
    path('import/<int:session_id>/executer/', views.import_donnees_executer, name='import_executer'),
]

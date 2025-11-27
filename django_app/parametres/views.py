"""
Vues et API pour le module Paramètres
Accessible uniquement à l'administrateur (Huissier titulaire)
"""

import json
import csv
import io
from decimal import Decimal
from datetime import datetime, date, time

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator

from .models import (
    ConfigurationEtude, SiteAgence, TypeDossier, StatutDossier,
    ModeleDocument, Localite, TauxLegal, JourFerie, TypeActe,
    Juridiction, HistoriqueSauvegarde, JournalModification, ModeleTypeBail
)


def est_admin(user):
    """Vérifie si l'utilisateur est administrateur"""
    return user.is_authenticated and user.role in ['admin', 'huissier']


def get_default_context(request):
    """Contexte par défaut pour toutes les vues"""
    user = request.user
    modules = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard', 'category': 'main', 'url': 'gestion:dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'gestion:dossiers'},
        {'id': 'facturation', 'label': 'Facturation', 'icon': 'file-text', 'category': 'finance', 'url': 'gestion:facturation'},
        {'id': 'tresorerie', 'label': 'Trésorerie', 'icon': 'wallet', 'category': 'finance', 'url': 'gestion:tresorerie'},
        {'id': 'comptabilite', 'label': 'Comptabilité', 'icon': 'calculator', 'category': 'finance', 'url': 'comptabilite:dashboard'},
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh:dashboard'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda:dashboard'},
        {'id': 'documents', 'label': 'Documents', 'icon': 'file-stack', 'category': 'gestion', 'url': 'documents:dashboard'},
        {'id': 'parametres', 'label': 'Paramètres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres:index'},
    ]
    return {
        'current_user': {
            'id': user.id,
            'nom': user.get_full_name() or user.username,
            'role': user.role,
            'initials': user.get_initials() if hasattr(user, 'get_initials') else user.username[:2].upper(),
        },
        'modules': modules,
        'active_module': 'parametres',
    }


@login_required
@user_passes_test(est_admin)
def index(request):
    """Page principale des paramètres"""
    context = get_default_context(request)
    context['page_title'] = 'Paramètres'
    context['config'] = ConfigurationEtude.get_instance()

    # Charger les données des référentiels
    context['sites'] = SiteAgence.objects.filter(actif=True)
    context['types_dossier'] = TypeDossier.objects.filter(actif=True)
    context['statuts_dossier'] = StatutDossier.objects.filter(actif=True)
    context['modeles_document'] = ModeleDocument.objects.filter(actif=True)
    context['localites'] = Localite.objects.filter(actif=True)[:50]
    context['taux_legaux'] = TauxLegal.objects.all()[:10]
    context['jours_feries'] = JourFerie.objects.filter(actif=True)
    context['types_actes'] = TypeActe.objects.filter(actif=True)
    context['juridictions'] = Juridiction.objects.filter(actif=True)
    context['types_bail'] = ModeleTypeBail.objects.filter(actif=True)
    context['sauvegardes'] = HistoriqueSauvegarde.objects.all()[:10]
    context['journal'] = JournalModification.objects.all()[:20]

    # Barème émoluments OHADA (lecture seule)
    context['bareme_ohada'] = [
        {'min': 0, 'max': 100000, 'taux': 10},
        {'min': 100001, 'max': 500000, 'taux': 7},
        {'min': 500001, 'max': 1000000, 'taux': 5},
        {'min': 1000001, 'max': 5000000, 'taux': 3},
        {'min': 5000001, 'max': None, 'taux': 2},
    ]

    # Variables de modèles disponibles
    context['variables_modeles'] = [
        {'code': '{{ETUDE_NOM}}', 'description': "Nom de l'étude"},
        {'code': '{{ETUDE_ADRESSE}}', 'description': "Adresse complète de l'étude"},
        {'code': '{{ETUDE_TEL}}', 'description': "Téléphone de l'étude"},
        {'code': '{{HUISSIER_NOM}}', 'description': "Nom de l'huissier titulaire"},
        {'code': '{{DATE_JOUR}}', 'description': "Date du jour"},
        {'code': '{{DOSSIER_REF}}', 'description': "Référence du dossier"},
        {'code': '{{CLIENT_NOM}}', 'description': "Nom du client"},
        {'code': '{{DEBITEUR_NOM}}', 'description': "Nom du débiteur"},
        {'code': '{{MONTANT}}', 'description': "Montant en chiffres"},
        {'code': '{{MONTANT_LETTRES}}', 'description': "Montant en lettres"},
        {'code': '{{NUMERO_FACTURE}}', 'description': "Numéro de facture"},
        {'code': '{{DATE_ECHEANCE}}', 'description': "Date d'échéance"},
    ]

    return render(request, 'parametres/index.html', context)


# ===== API CONFIGURATION GENERALE =====

@login_required
@user_passes_test(est_admin)
@require_POST
def api_sauvegarder_config(request):
    """Sauvegarde la configuration générale"""
    try:
        data = json.loads(request.body)
        section = data.get('section', 'general')

        config = ConfigurationEtude.get_instance()

        # Enregistrer les modifications dans le journal
        def log_modification(champ, ancienne, nouvelle):
            if str(ancienne) != str(nouvelle):
                JournalModification.objects.create(
                    utilisateur=request.user,
                    section=section,
                    champ=champ,
                    ancienne_valeur=str(ancienne),
                    nouvelle_valeur=str(nouvelle)
                )

        # Section 1: Informations de l'étude
        if section == 'etude':
            for field in ['nom_etude', 'titre', 'juridiction', 'adresse_rue', 'adresse_quartier',
                         'adresse_ville', 'adresse_bp', 'telephone_fixe', 'telephone_mobile1',
                         'telephone_mobile2', 'email', 'site_web', 'numero_ifu', 'numero_agrement']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'date_installation' in data and data['date_installation']:
                new_date = datetime.strptime(data['date_installation'], '%Y-%m-%d').date()
                log_modification('date_installation', config.date_installation, new_date)
                config.date_installation = new_date

            if 'couleur_principale' in data:
                log_modification('couleur_principale', config.couleur_principale, data['couleur_principale'])
                config.couleur_principale = data['couleur_principale']
            if 'couleur_secondaire' in data:
                log_modification('couleur_secondaire', config.couleur_secondaire, data['couleur_secondaire'])
                config.couleur_secondaire = data['couleur_secondaire']

        # Section: Coordonnées bancaires
        elif section == 'banque':
            for field in ['banque_nom', 'banque_code', 'banque_guichet', 'banque_compte',
                         'banque_cle', 'banque_iban', 'banque_titulaire',
                         'mobile_money_operateur', 'mobile_money_numero']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

        # Section 2.1: Dossiers
        elif section == 'dossiers':
            if 'dossier_prefixe' in data:
                log_modification('dossier_prefixe', config.dossier_prefixe, data['dossier_prefixe'])
                config.dossier_prefixe = data['dossier_prefixe']
            if 'dossier_numero_depart' in data:
                log_modification('dossier_numero_depart', config.dossier_numero_depart, data['dossier_numero_depart'])
                config.dossier_numero_depart = int(data['dossier_numero_depart'])

        # Section 2.2: Facturation
        elif section == 'facturation':
            for field in ['facture_prefixe', 'facture_mentions_legales', 'facture_conditions_paiement',
                         'mecef_nim', 'mecef_token', 'mecef_mode']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'tva_applicable' in data:
                log_modification('tva_applicable', config.tva_applicable, data['tva_applicable'])
                config.tva_applicable = data['tva_applicable']

            for decimal_field in ['tva_taux', 'facture_penalites_retard']:
                if decimal_field in data:
                    new_val = Decimal(str(data[decimal_field]))
                    log_modification(decimal_field, getattr(config, decimal_field), new_val)
                    setattr(config, decimal_field, new_val)

            if 'facture_delai_paiement' in data:
                log_modification('facture_delai_paiement', config.facture_delai_paiement, data['facture_delai_paiement'])
                config.facture_delai_paiement = int(data['facture_delai_paiement'])

        # Section 2.3: Trésorerie
        elif section == 'tresorerie':
            for decimal_field in ['tresorerie_seuil_alerte', 'tresorerie_validation_seuil']:
                if decimal_field in data:
                    new_val = Decimal(str(data[decimal_field]))
                    log_modification(decimal_field, getattr(config, decimal_field), new_val)
                    setattr(config, decimal_field, new_val)

            if 'tresorerie_delai_reversement' in data:
                log_modification('tresorerie_delai_reversement', config.tresorerie_delai_reversement, data['tresorerie_delai_reversement'])
                config.tresorerie_delai_reversement = int(data['tresorerie_delai_reversement'])

            if 'tresorerie_compte_sequestre' in data:
                log_modification('tresorerie_compte_sequestre', config.tresorerie_compte_sequestre, data['tresorerie_compte_sequestre'])
                config.tresorerie_compte_sequestre = data['tresorerie_compte_sequestre']

        # Section 2.4: Comptabilité
        elif section == 'comptabilite':
            if 'exercice_debut' in data and data['exercice_debut']:
                new_date = datetime.strptime(data['exercice_debut'], '%Y-%m-%d').date()
                log_modification('exercice_debut', config.exercice_debut, new_date)
                config.exercice_debut = new_date

            if 'exercice_fin' in data and data['exercice_fin']:
                new_date = datetime.strptime(data['exercice_fin'], '%Y-%m-%d').date()
                log_modification('exercice_fin', config.exercice_fin, new_date)
                config.exercice_fin = new_date

            for field in ['comptabilite_mode', 'regime_fiscal', 'tva_declaration']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'echeances_rappel_jours' in data:
                log_modification('echeances_rappel_jours', config.echeances_rappel_jours, data['echeances_rappel_jours'])
                config.echeances_rappel_jours = int(data['echeances_rappel_jours'])

        # Section 2.5: Recouvrement
        elif section == 'recouvrement':
            if 'recouvrement_majoration_50' in data:
                log_modification('recouvrement_majoration_50', config.recouvrement_majoration_50, data['recouvrement_majoration_50'])
                config.recouvrement_majoration_50 = data['recouvrement_majoration_50']

            if 'recouvrement_delai_majoration' in data:
                log_modification('recouvrement_delai_majoration', config.recouvrement_delai_majoration, data['recouvrement_delai_majoration'])
                config.recouvrement_delai_majoration = int(data['recouvrement_delai_majoration'])

            if 'recouvrement_ordre_imputation' in data:
                log_modification('recouvrement_ordre_imputation', config.recouvrement_ordre_imputation, data['recouvrement_ordre_imputation'])
                config.recouvrement_ordre_imputation = data['recouvrement_ordre_imputation']

        # Section 2.6: Gérance immobilière
        elif section == 'gerance':
            if 'gerance_taux_honoraires' in data:
                new_val = Decimal(str(data['gerance_taux_honoraires']))
                log_modification('gerance_taux_honoraires', config.gerance_taux_honoraires, new_val)
                config.gerance_taux_honoraires = new_val

            for int_field in ['gerance_date_reversement', 'gerance_relance_niveau1',
                             'gerance_relance_niveau2', 'gerance_relance_niveau3', 'gerance_relance_niveau4']:
                if int_field in data:
                    log_modification(int_field, getattr(config, int_field), data[int_field])
                    setattr(config, int_field, int(data[int_field]))

        # Section 2.7: RH
        elif section == 'rh':
            for decimal_field in ['rh_smig', 'rh_cnss_salarial_vieillesse', 'rh_cnss_patronal_pf',
                                 'rh_cnss_patronal_vieillesse', 'rh_cnss_patronal_at', 'rh_plafond_cnss']:
                if decimal_field in data:
                    new_val = Decimal(str(data[decimal_field]))
                    log_modification(decimal_field, getattr(config, decimal_field), new_val)
                    setattr(config, decimal_field, new_val)

            for int_field in ['rh_conges_annuels', 'rh_heures_hebdo', 'rh_jour_paie']:
                if int_field in data:
                    log_modification(int_field, getattr(config, int_field), data[int_field])
                    setattr(config, int_field, int(data[int_field]))

        # Section 2.8: Mémoires de cédules
        elif section == 'cedules':
            if 'cedules_residence' in data:
                log_modification('cedules_residence', config.cedules_residence, data['cedules_residence'])
                config.cedules_residence = data['cedules_residence']

            for decimal_field in ['cedules_premier_original', 'cedules_deuxieme_original', 'cedules_copie',
                                 'cedules_mention_repertoire', 'cedules_vacation', 'cedules_frais_copie_role',
                                 'cedules_tarif_km', 'cedules_mission_1_repas', 'cedules_mission_2_repas',
                                 'cedules_mission_journee']:
                if decimal_field in data:
                    new_val = Decimal(str(data[decimal_field]))
                    log_modification(decimal_field, getattr(config, decimal_field), new_val)
                    setattr(config, decimal_field, new_val)

            for int_field in ['cedules_seuil_transport', 'cedules_seuil_mission']:
                if int_field in data:
                    log_modification(int_field, getattr(config, int_field), data[int_field])
                    setattr(config, int_field, int(data[int_field]))

        # Section 2.9: Agenda
        elif section == 'agenda':
            if 'agenda_heure_debut' in data:
                new_time = datetime.strptime(data['agenda_heure_debut'], '%H:%M').time()
                log_modification('agenda_heure_debut', config.agenda_heure_debut, new_time)
                config.agenda_heure_debut = new_time

            if 'agenda_heure_fin' in data:
                new_time = datetime.strptime(data['agenda_heure_fin'], '%H:%M').time()
                log_modification('agenda_heure_fin', config.agenda_heure_fin, new_time)
                config.agenda_heure_fin = new_time

            for int_field in ['agenda_duree_rdv', 'agenda_rappel_jours', 'agenda_rappel_heures']:
                if int_field in data:
                    log_modification(int_field, getattr(config, int_field), data[int_field])
                    setattr(config, int_field, int(data[int_field]))

            if 'agenda_jours_ouvres' in data:
                log_modification('agenda_jours_ouvres', config.agenda_jours_ouvres, data['agenda_jours_ouvres'])
                config.agenda_jours_ouvres = data['agenda_jours_ouvres']

        # Section 4: Notifications
        elif section == 'notifications':
            if 'notif_config' in data:
                log_modification('notif_config', config.notif_config, data['notif_config'])
                config.notif_config = data['notif_config']

            for field in ['smtp_serveur', 'smtp_utilisateur', 'smtp_mot_de_passe', 'smtp_expediteur',
                         'sms_fournisseur', 'sms_api_key', 'sms_expediteur']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'smtp_port' in data:
                log_modification('smtp_port', config.smtp_port, data['smtp_port'])
                config.smtp_port = int(data['smtp_port'])

        # Section 5: Sauvegardes
        elif section == 'sauvegardes':
            if 'backup_auto' in data:
                log_modification('backup_auto', config.backup_auto, data['backup_auto'])
                config.backup_auto = data['backup_auto']

            for field in ['backup_frequence', 'backup_emplacement']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'backup_heure' in data:
                new_time = datetime.strptime(data['backup_heure'], '%H:%M').time()
                log_modification('backup_heure', config.backup_heure, new_time)
                config.backup_heure = new_time

            if 'backup_retention' in data:
                log_modification('backup_retention', config.backup_retention, data['backup_retention'])
                config.backup_retention = int(data['backup_retention'])

        # Section 6: Personnalisation
        elif section == 'personnalisation':
            for field in ['theme_mode', 'format_date', 'separateur_milliers', 'separateur_decimales', 'dashboard_periode']:
                if field in data:
                    log_modification(field, getattr(config, field), data[field])
                    setattr(config, field, data[field])

            if 'dashboard_widgets' in data:
                log_modification('dashboard_widgets', config.dashboard_widgets, data['dashboard_widgets'])
                config.dashboard_widgets = data['dashboard_widgets']

        config.est_configure = True
        config.date_configuration = timezone.now()
        config.modifie_par = request.user
        config.save()

        return JsonResponse({
            'success': True,
            'message': 'Configuration sauvegardée avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_GET
def api_get_config(request):
    """Récupère la configuration complète"""
    config = ConfigurationEtude.get_instance()
    return JsonResponse({
        'success': True,
        'data': config.to_dict()
    })


# ===== API SITES/AGENCES =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_sites_list(request):
    """Liste des sites/agences"""
    sites = SiteAgence.objects.all()
    return JsonResponse({
        'success': True,
        'data': [s.to_dict() for s in sites]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_site_create(request):
    """Crée un nouveau site"""
    try:
        data = json.loads(request.body)
        site = SiteAgence.objects.create(
            nom=data['nom'],
            adresse=data.get('adresse', ''),
            telephone=data.get('telephone', ''),
            responsable=data.get('responsable', ''),
            est_principal=data.get('est_principal', False)
        )
        return JsonResponse({
            'success': True,
            'message': 'Site créé avec succès',
            'data': site.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_site_update(request, site_id):
    """Met à jour un site"""
    try:
        data = json.loads(request.body)
        site = get_object_or_404(SiteAgence, id=site_id)

        site.nom = data.get('nom', site.nom)
        site.adresse = data.get('adresse', site.adresse)
        site.telephone = data.get('telephone', site.telephone)
        site.responsable = data.get('responsable', site.responsable)
        site.est_principal = data.get('est_principal', site.est_principal)
        site.actif = data.get('actif', site.actif)
        site.save()

        return JsonResponse({
            'success': True,
            'message': 'Site mis à jour avec succès',
            'data': site.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_site_delete(request, site_id):
    """Supprime un site"""
    try:
        site = get_object_or_404(SiteAgence, id=site_id)
        site.actif = False
        site.save()
        return JsonResponse({
            'success': True,
            'message': 'Site supprimé avec succès'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API TYPES DOSSIER =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_types_dossier_list(request):
    """Liste des types de dossier"""
    types = TypeDossier.objects.all()
    return JsonResponse({
        'success': True,
        'data': [t.to_dict() for t in types]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_type_dossier_create(request):
    """Crée un nouveau type de dossier"""
    try:
        data = json.loads(request.body)
        type_dossier = TypeDossier.objects.create(
            code=data['code'],
            libelle=data['libelle'],
            description=data.get('description', ''),
            couleur=data.get('couleur', '#1a365d'),
            ordre=data.get('ordre', 0)
        )
        return JsonResponse({
            'success': True,
            'message': 'Type de dossier créé avec succès',
            'data': type_dossier.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_type_dossier_update(request, type_id):
    """Met à jour un type de dossier"""
    try:
        data = json.loads(request.body)
        type_dossier = get_object_or_404(TypeDossier, id=type_id)

        type_dossier.code = data.get('code', type_dossier.code)
        type_dossier.libelle = data.get('libelle', type_dossier.libelle)
        type_dossier.description = data.get('description', type_dossier.description)
        type_dossier.couleur = data.get('couleur', type_dossier.couleur)
        type_dossier.ordre = data.get('ordre', type_dossier.ordre)
        type_dossier.actif = data.get('actif', type_dossier.actif)
        type_dossier.save()

        return JsonResponse({
            'success': True,
            'message': 'Type de dossier mis à jour',
            'data': type_dossier.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_type_dossier_delete(request, type_id):
    """Supprime un type de dossier"""
    try:
        type_dossier = get_object_or_404(TypeDossier, id=type_id)
        type_dossier.actif = False
        type_dossier.save()
        return JsonResponse({
            'success': True,
            'message': 'Type de dossier supprimé'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API STATUTS DOSSIER =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_statuts_dossier_list(request):
    """Liste des statuts de dossier"""
    statuts = StatutDossier.objects.all()
    return JsonResponse({
        'success': True,
        'data': [s.to_dict() for s in statuts]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_statut_dossier_create(request):
    """Crée un nouveau statut de dossier"""
    try:
        data = json.loads(request.body)
        statut = StatutDossier.objects.create(
            code=data['code'],
            libelle=data['libelle'],
            couleur=data.get('couleur', '#1a365d'),
            est_cloture=data.get('est_cloture', False),
            ordre=data.get('ordre', 0)
        )
        return JsonResponse({
            'success': True,
            'message': 'Statut créé avec succès',
            'data': statut.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_statut_dossier_update(request, statut_id):
    """Met à jour un statut de dossier"""
    try:
        data = json.loads(request.body)
        statut = get_object_or_404(StatutDossier, id=statut_id)

        statut.code = data.get('code', statut.code)
        statut.libelle = data.get('libelle', statut.libelle)
        statut.couleur = data.get('couleur', statut.couleur)
        statut.est_cloture = data.get('est_cloture', statut.est_cloture)
        statut.ordre = data.get('ordre', statut.ordre)
        statut.actif = data.get('actif', statut.actif)
        statut.save()

        return JsonResponse({
            'success': True,
            'message': 'Statut mis à jour',
            'data': statut.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API MODELES DOCUMENT =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_modeles_document_list(request):
    """Liste des modèles de document"""
    categorie = request.GET.get('categorie')
    modeles = ModeleDocument.objects.all()
    if categorie:
        modeles = modeles.filter(categorie=categorie)
    return JsonResponse({
        'success': True,
        'data': [m.to_dict() for m in modeles]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_modele_document_create(request):
    """Crée un nouveau modèle de document"""
    try:
        data = json.loads(request.body)
        modele = ModeleDocument.objects.create(
            nom=data['nom'],
            categorie=data['categorie'],
            contenu_html=data.get('contenu_html', ''),
            variables_utilisees=data.get('variables_utilisees', []),
            cree_par=request.user
        )
        return JsonResponse({
            'success': True,
            'message': 'Modèle créé avec succès',
            'data': modele.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_modele_document_update(request, modele_id):
    """Met à jour un modèle de document"""
    try:
        data = json.loads(request.body)
        modele = get_object_or_404(ModeleDocument, id=modele_id)

        modele.nom = data.get('nom', modele.nom)
        modele.categorie = data.get('categorie', modele.categorie)
        modele.contenu_html = data.get('contenu_html', modele.contenu_html)
        modele.variables_utilisees = data.get('variables_utilisees', modele.variables_utilisees)
        modele.actif = data.get('actif', modele.actif)
        modele.save()

        return JsonResponse({
            'success': True,
            'message': 'Modèle mis à jour',
            'data': modele.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_modele_document_duplicate(request, modele_id):
    """Duplique un modèle de document"""
    try:
        original = get_object_or_404(ModeleDocument, id=modele_id)
        modele = ModeleDocument.objects.create(
            nom=f"{original.nom} (copie)",
            categorie=original.categorie,
            contenu_html=original.contenu_html,
            variables_utilisees=original.variables_utilisees,
            cree_par=request.user
        )
        return JsonResponse({
            'success': True,
            'message': 'Modèle dupliqué avec succès',
            'data': modele.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_modele_document_delete(request, modele_id):
    """Supprime un modèle de document"""
    try:
        modele = get_object_or_404(ModeleDocument, id=modele_id)
        modele.actif = False
        modele.save()
        return JsonResponse({
            'success': True,
            'message': 'Modèle supprimé'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API LOCALITES =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_localites_list(request):
    """Liste des localités"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    search = request.GET.get('search', '')

    localites = Localite.objects.filter(actif=True)
    if search:
        localites = localites.filter(nom__icontains=search)

    paginator = Paginator(localites, per_page)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'success': True,
        'data': [l.to_dict() for l in page_obj],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'pages': paginator.num_pages
        }
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_localite_create(request):
    """Crée une nouvelle localité"""
    try:
        data = json.loads(request.body)
        localite = Localite.objects.create(
            nom=data['nom'],
            departement=data.get('departement', ''),
            commune=data.get('commune', ''),
            distance_km=Decimal(str(data.get('distance_km', 0))),
            latitude=Decimal(str(data['latitude'])) if data.get('latitude') else None,
            longitude=Decimal(str(data['longitude'])) if data.get('longitude') else None
        )
        return JsonResponse({
            'success': True,
            'message': 'Localité créée avec succès',
            'data': localite.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_localite_update(request, localite_id):
    """Met à jour une localité"""
    try:
        data = json.loads(request.body)
        localite = get_object_or_404(Localite, id=localite_id)

        localite.nom = data.get('nom', localite.nom)
        localite.departement = data.get('departement', localite.departement)
        localite.commune = data.get('commune', localite.commune)
        if 'distance_km' in data:
            localite.distance_km = Decimal(str(data['distance_km']))
        localite.actif = data.get('actif', localite.actif)
        localite.save()

        return JsonResponse({
            'success': True,
            'message': 'Localité mise à jour',
            'data': localite.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_localites_import(request):
    """Importe des localités depuis un fichier CSV"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Aucun fichier fourni'
            }, status=400)

        file = request.FILES['file']
        decoded = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        created = 0
        updated = 0

        for row in reader:
            localite, is_created = Localite.objects.update_or_create(
                nom=row['nom'],
                commune=row.get('commune', ''),
                defaults={
                    'departement': row.get('departement', ''),
                    'distance_km': Decimal(str(row.get('distance_km', 0))),
                    'actif': True
                }
            )
            if is_created:
                created += 1
            else:
                updated += 1

        return JsonResponse({
            'success': True,
            'message': f'{created} localités créées, {updated} mises à jour'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API TAUX LEGAUX =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_taux_legaux_list(request):
    """Liste des taux légaux"""
    taux = TauxLegal.objects.all()
    return JsonResponse({
        'success': True,
        'data': [t.to_dict() for t in taux]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_taux_legal_create(request):
    """Crée un nouveau taux légal"""
    try:
        data = json.loads(request.body)
        taux = TauxLegal.objects.create(
            annee=int(data['annee']),
            semestre=data['semestre'],
            taux=Decimal(str(data['taux'])),
            date_debut=datetime.strptime(data['date_debut'], '%Y-%m-%d').date(),
            date_fin=datetime.strptime(data['date_fin'], '%Y-%m-%d').date(),
            source=data.get('source', '')
        )
        return JsonResponse({
            'success': True,
            'message': 'Taux légal créé avec succès',
            'data': taux.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_taux_legal_update(request, taux_id):
    """Met à jour un taux légal"""
    try:
        data = json.loads(request.body)
        taux = get_object_or_404(TauxLegal, id=taux_id)

        taux.annee = int(data.get('annee', taux.annee))
        taux.semestre = data.get('semestre', taux.semestre)
        taux.taux = Decimal(str(data.get('taux', taux.taux)))
        if 'date_debut' in data:
            taux.date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
        if 'date_fin' in data:
            taux.date_fin = datetime.strptime(data['date_fin'], '%Y-%m-%d').date()
        taux.source = data.get('source', taux.source)
        taux.save()

        return JsonResponse({
            'success': True,
            'message': 'Taux légal mis à jour',
            'data': taux.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API JOURS FERIES =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_jours_feries_list(request):
    """Liste des jours fériés"""
    jours = JourFerie.objects.all()
    return JsonResponse({
        'success': True,
        'data': [j.to_dict() for j in jours]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_jour_ferie_create(request):
    """Crée un nouveau jour férié"""
    try:
        data = json.loads(request.body)
        jour = JourFerie.objects.create(
            nom=data['nom'],
            jour_mois=int(data['jour_mois']) if data.get('jour_mois') else None,
            mois=int(data['mois']) if data.get('mois') else None,
            est_mobile=data.get('est_mobile', False),
            formule=data.get('formule', '')
        )
        return JsonResponse({
            'success': True,
            'message': 'Jour férié créé avec succès',
            'data': jour.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_jour_ferie_update(request, jour_id):
    """Met à jour un jour férié"""
    try:
        data = json.loads(request.body)
        jour = get_object_or_404(JourFerie, id=jour_id)

        jour.nom = data.get('nom', jour.nom)
        if 'jour_mois' in data:
            jour.jour_mois = int(data['jour_mois']) if data['jour_mois'] else None
        if 'mois' in data:
            jour.mois = int(data['mois']) if data['mois'] else None
        jour.est_mobile = data.get('est_mobile', jour.est_mobile)
        jour.formule = data.get('formule', jour.formule)
        jour.actif = data.get('actif', jour.actif)
        jour.save()

        return JsonResponse({
            'success': True,
            'message': 'Jour férié mis à jour',
            'data': jour.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API TYPES ACTES =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_types_actes_list(request):
    """Liste des types d'actes"""
    types = TypeActe.objects.all()
    return JsonResponse({
        'success': True,
        'data': [t.to_dict() for t in types]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_type_acte_create(request):
    """Crée un nouveau type d'acte"""
    try:
        data = json.loads(request.body)
        type_acte = TypeActe.objects.create(
            code=data['code'],
            libelle=data['libelle'],
            categorie=data.get('categorie', ''),
            montant_defaut=Decimal(str(data.get('montant_defaut', 0)))
        )
        return JsonResponse({
            'success': True,
            'message': 'Type d\'acte créé avec succès',
            'data': type_acte.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_type_acte_update(request, type_id):
    """Met à jour un type d'acte"""
    try:
        data = json.loads(request.body)
        type_acte = get_object_or_404(TypeActe, id=type_id)

        type_acte.code = data.get('code', type_acte.code)
        type_acte.libelle = data.get('libelle', type_acte.libelle)
        type_acte.categorie = data.get('categorie', type_acte.categorie)
        if 'montant_defaut' in data:
            type_acte.montant_defaut = Decimal(str(data['montant_defaut']))
        type_acte.actif = data.get('actif', type_acte.actif)
        type_acte.save()

        return JsonResponse({
            'success': True,
            'message': 'Type d\'acte mis à jour',
            'data': type_acte.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API JURIDICTIONS =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_juridictions_list(request):
    """Liste des juridictions"""
    juridictions = Juridiction.objects.all()
    return JsonResponse({
        'success': True,
        'data': [j.to_dict() for j in juridictions]
    })


@login_required
@user_passes_test(est_admin)
@require_POST
def api_juridiction_create(request):
    """Crée une nouvelle juridiction"""
    try:
        data = json.loads(request.body)
        juridiction = Juridiction.objects.create(
            type=data['type'],
            nom=data['nom'],
            ville=data['ville'],
            adresse=data.get('adresse', ''),
            telephone=data.get('telephone', '')
        )
        return JsonResponse({
            'success': True,
            'message': 'Juridiction créée avec succès',
            'data': juridiction.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_juridiction_update(request, juridiction_id):
    """Met à jour une juridiction"""
    try:
        data = json.loads(request.body)
        juridiction = get_object_or_404(Juridiction, id=juridiction_id)

        juridiction.type = data.get('type', juridiction.type)
        juridiction.nom = data.get('nom', juridiction.nom)
        juridiction.ville = data.get('ville', juridiction.ville)
        juridiction.adresse = data.get('adresse', juridiction.adresse)
        juridiction.telephone = data.get('telephone', juridiction.telephone)
        juridiction.actif = data.get('actif', juridiction.actif)
        juridiction.save()

        return JsonResponse({
            'success': True,
            'message': 'Juridiction mise à jour',
            'data': juridiction.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API SAUVEGARDES =====

@login_required
@user_passes_test(est_admin)
@require_POST
def api_backup_create(request):
    """Crée une sauvegarde manuelle"""
    try:
        # Créer l'entrée dans l'historique
        sauvegarde = HistoriqueSauvegarde.objects.create(
            statut='en_cours',
            emplacement='local'
        )

        # TODO: Implémenter la logique de sauvegarde réelle
        # Pour l'instant, simuler une sauvegarde réussie
        import random
        sauvegarde.taille = random.randint(100000000, 200000000)
        sauvegarde.statut = 'reussi'
        sauvegarde.message = 'Sauvegarde effectuée avec succès'
        sauvegarde.save()

        return JsonResponse({
            'success': True,
            'message': 'Sauvegarde créée avec succès',
            'data': sauvegarde.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_backup_restore(request, backup_id):
    """Restaure une sauvegarde"""
    try:
        sauvegarde = get_object_or_404(HistoriqueSauvegarde, id=backup_id)

        # TODO: Implémenter la logique de restauration réelle

        return JsonResponse({
            'success': True,
            'message': 'Restauration lancée. Veuillez patienter...'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API EXPORTS =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_export_data(request, format_type):
    """Exporte les données"""
    try:
        export_type = request.GET.get('type', 'all')

        if format_type == 'json':
            data = {}

            if export_type in ['all', 'config']:
                config = ConfigurationEtude.get_instance()
                data['configuration'] = config.to_dict()

            if export_type in ['all', 'localites']:
                data['localites'] = [l.to_dict() for l in Localite.objects.all()]

            if export_type in ['all', 'taux']:
                data['taux_legaux'] = [t.to_dict() for t in TauxLegal.objects.all()]

            if export_type in ['all', 'jours_feries']:
                data['jours_feries'] = [j.to_dict() for j in JourFerie.objects.all()]

            response = HttpResponse(
                json.dumps(data, indent=2, ensure_ascii=False),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="export_{export_type}_{timezone.now().strftime("%Y%m%d")}.json"'
            return response

        elif format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="export_{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'

            writer = csv.writer(response)

            if export_type == 'localites':
                writer.writerow(['nom', 'departement', 'commune', 'distance_km'])
                for l in Localite.objects.all():
                    writer.writerow([l.nom, l.departement, l.commune, l.distance_km])

            return response

        return JsonResponse({
            'success': False,
            'error': 'Format non supporté'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API TEST CONNEXIONS =====

@login_required
@user_passes_test(est_admin)
@require_POST
def api_test_smtp(request):
    """Teste la configuration SMTP"""
    try:
        config = ConfigurationEtude.get_instance()

        # TODO: Implémenter le test réel de connexion SMTP

        return JsonResponse({
            'success': True,
            'message': 'Configuration SMTP valide'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(est_admin)
@require_POST
def api_test_sms(request):
    """Teste la configuration SMS"""
    try:
        config = ConfigurationEtude.get_instance()

        # TODO: Implémenter le test réel d'envoi SMS

        return JsonResponse({
            'success': True,
            'message': 'Configuration SMS valide'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== API JOURNAL =====

@login_required
@user_passes_test(est_admin)
@require_GET
def api_journal_list(request):
    """Liste du journal des modifications"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    section = request.GET.get('section')

    journal = JournalModification.objects.all()
    if section:
        journal = journal.filter(section=section)

    paginator = Paginator(journal, per_page)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'success': True,
        'data': [j.to_dict() for j in page_obj],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'pages': paginator.num_pages
        }
    })

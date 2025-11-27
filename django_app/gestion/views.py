from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
import hashlib
import random
import string

from .models import (
    Dossier, Facture, Collaborateur, Partie, ActeProcedure,
    HistoriqueCalcul, TauxLegal, Utilisateur, LigneFacture,
    Creancier, PortefeuilleCreancier, Encaissement, ImputationEncaissement,
    Reversement, BasculementAmiableForce, PointGlobalCreancier,
    EnvoiAutomatiquePoint, HistoriqueEnvoiPoint,
    # Mémoires de Cédules
    AutoriteRequerante, Memoire, AffaireMemoire, DestinataireAffaire, ActeDestinataire
)


# Donnees par defaut pour le contexte (simulant les donnees React)
def get_default_context(request):
    """Contexte par defaut pour tous les templates"""
    # Utilisateur courant simule
    current_user = {
        'id': 1,
        'nom': 'BIAOU Martial Arnaud',
        'role': 'admin',
        'email': 'mab@etude-biaou.bj',
        'initials': 'MA'
    }

    # Modules de navigation
    modules = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'home', 'category': 'main', 'url': 'gestion:dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'gestion:dossiers', 'badge': 14},
        {'id': 'facturation', 'label': 'Facturation & MECeF', 'icon': 'file-text', 'category': 'main', 'url': 'gestion:facturation'},
        {'id': 'calcul', 'label': 'Calcul Recouvrement', 'icon': 'calculator', 'category': 'main', 'url': 'gestion:calcul'},
        {'id': 'tresorerie', 'label': 'Trésorerie', 'icon': 'piggy-bank', 'category': 'finance', 'url': 'tresorerie:dashboard'},
        {'id': 'comptabilite', 'label': 'Comptabilité', 'icon': 'book-open', 'category': 'finance', 'url': 'comptabilite:dashboard'},
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh:dashboard'},
        {'id': 'drive', 'label': 'Drive', 'icon': 'hard-drive', 'category': 'gestion', 'url': 'documents:drive'},
        {'id': 'gerance', 'label': 'Gérance Immobilière', 'icon': 'building-2', 'category': 'gestion', 'url': 'gerance:dashboard'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda:home'},
        {'id': 'parametres', 'label': 'Parametres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres:index'},
        {'id': 'securite', 'label': 'Securite & Acces', 'icon': 'shield', 'category': 'admin', 'url': 'gestion:securite'},
    ]

    # Collaborateurs par defaut
    collaborateurs = [
        {'id': 1, 'nom': 'Me BIAOU Martial', 'role': 'Huissier'},
        {'id': 2, 'nom': 'ADJOVI Carine', 'role': 'Clerc Principal'},
        {'id': 3, 'nom': 'HOUNKPATIN Paul', 'role': 'Clerc'},
        {'id': 4, 'nom': 'DOSSOU Marie', 'role': 'Secretaire'},
    ]

    return {
        'current_user': current_user,
        'modules': modules,
        'collaborateurs': collaborateurs,
        'active_module': '',
    }


def dashboard(request):
    """Vue du tableau de bord"""
    context = get_default_context(request)
    context['active_module'] = 'dashboard'
    context['page_title'] = 'Tableau de bord'

    # Statistiques depuis la base de donnees
    nb_dossiers = Dossier.objects.filter(statut='actif').count()
    nb_urgents = Dossier.objects.filter(statut='urgent').count()

    # Calcul du CA mensuel
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ca_mensuel = Facture.objects.filter(
        date_emission__gte=debut_mois,
        statut='payee'
    ).aggregate(total=Sum('montant_ttc'))['total'] or 0

    context['stats'] = {
        'dossiers_actifs': nb_dossiers or 127,
        'ca_mensuel': f"{ca_mensuel/1000000:.1f} M" if ca_mensuel >= 1000000 else f"{ca_mensuel:,.0f}",
        'actes_signifies': 89,
        'urgents': nb_urgents or 14,
    }

    return render(request, 'gestion/dashboard.html', context)


def dossiers(request):
    """Vue de la liste des dossiers"""
    context = get_default_context(request)
    context['active_module'] = 'dossiers'
    context['page_title'] = 'Dossiers'

    # Filtres
    search = request.GET.get('search', '')
    type_filter = request.GET.get('type', 'all')
    assigned_filter = request.GET.get('assigned', 'all')
    tab = request.GET.get('tab', 'all')

    # Charger les dossiers depuis la base de donnees
    dossiers_qs = Dossier.objects.all().order_by('-date_creation')

    if tab == 'actifs':
        dossiers_qs = dossiers_qs.filter(statut='actif')
    elif tab == 'urgents':
        dossiers_qs = dossiers_qs.filter(statut='urgent')
    elif tab == 'archives':
        dossiers_qs = dossiers_qs.filter(statut__in=['archive', 'cloture'])

    # Donnees de demonstration si pas de dossiers en base
    if not dossiers_qs.exists():
        context['dossiers_list'] = [
            {
                'reference': '173_1125_MAB',
                'intitule': 'SODECO SA C/ SOGEMA Sarl',
                'type': 'Recouvrement',
                'nature': 'contentieux',
                'montant': '15 750 000',
                'affecte_a': 'Me BIAOU',
                'statut': 'actif',
            },
            {
                'reference': '174_1125_MAB',
                'intitule': 'Banque Atlantique C/ TECH SOLUTIONS',
                'type': 'Recouvrement',
                'nature': 'contentieux',
                'montant': '8 500 000',
                'affecte_a': 'ADJOVI Carine',
                'statut': 'urgent',
            },
        ]
    else:
        context['dossiers_list'] = [{
            'reference': d.reference,
            'intitule': d.get_intitule(),
            'type': d.get_type_dossier_display(),
            'nature': 'contentieux' if d.is_contentieux else 'non-contentieux',
            'montant': f"{d.montant_creance:,.0f}" if d.montant_creance else '-',
            'affecte_a': d.affecte_a.nom if d.affecte_a else '-',
            'statut': d.statut,
        } for d in dossiers_qs[:50]]

    context['tabs'] = [
        {'id': 'all', 'label': 'Tous', 'count': Dossier.objects.count() or 127},
        {'id': 'actifs', 'label': 'Actifs', 'count': Dossier.objects.filter(statut='actif').count() or 89},
        {'id': 'urgents', 'label': 'Urgents', 'count': Dossier.objects.filter(statut='urgent').count() or 14},
        {'id': 'archives', 'label': 'Archives', 'count': Dossier.objects.filter(statut__in=['archive', 'cloture']).count() or 24},
    ]
    context['current_tab'] = tab
    context['filters'] = {
        'search': search,
        'type': type_filter,
        'assigned': assigned_filter,
    }

    return render(request, 'gestion/dossiers.html', context)


def nouveau_dossier(request):
    """Vue pour creer un nouveau dossier"""
    context = get_default_context(request)
    context['active_module'] = 'dossiers'
    context['page_title'] = 'Nouveau dossier'

    if request.method == 'POST':
        # Traitement du formulaire
        data = request.POST
        # Creer le dossier...
        messages.success(request, 'Dossier cree avec succes!')
        return redirect('dossiers')

    # Generer une nouvelle reference
    context['reference'] = Dossier.generer_reference()
    context['types_dossier'] = Dossier.TYPE_DOSSIER_CHOICES

    return render(request, 'gestion/nouveau_dossier.html', context)


def facturation(request):
    """Vue de la facturation"""
    context = get_default_context(request)
    context['active_module'] = 'facturation'
    context['page_title'] = 'Facturation & MECeF'

    tab = request.GET.get('tab', 'liste')

    # Charger les factures depuis la base de donnees
    factures_qs = Facture.objects.all().select_related('dossier').prefetch_related('lignes').order_by('-date_emission')

    factures_list = []
    total_ht = 0
    total_ttc = 0
    nb_attente = 0

    for f in factures_qs:
        lignes = [{'description': l.description, 'quantite': l.quantite, 'prix_unitaire': float(l.prix_unitaire)} for l in f.lignes.all()]
        facture_data = {
            'id': f.id,
            'numero': f.numero,
            'client': f.client,
            'ifu': f.ifu if hasattr(f, 'ifu') else '',
            'montant_ht': float(f.montant_ht),
            'tva': float(f.montant_tva),
            'total': float(f.montant_ttc),
            'date': f.date_emission.strftime('%d/%m/%Y'),
            'date_emission': f.date_emission.strftime('%Y-%m-%d'),
            'date_echeance': f.date_echeance.strftime('%Y-%m-%d') if f.date_echeance else '',
            'statut': f.statut,
            'mecef_numero': f.mecef_numero,
            'mecef_qr': f.mecef_qr,
            'nim': f.nim if hasattr(f, 'nim') else '',
            'date_mecef': f.date_mecef.strftime('%d/%m/%Y') if hasattr(f, 'date_mecef') and f.date_mecef else '',
            'dossier': f.dossier_id,
            'observations': f.observations if hasattr(f, 'observations') else '',
            'lignes': lignes
        }
        factures_list.append(facture_data)
        total_ht += float(f.montant_ht)
        total_ttc += float(f.montant_ttc)
        if f.statut == 'attente':
            nb_attente += 1

    # Si pas de factures en base, utiliser des donnees de demo
    if not factures_list:
        factures_list = [
            {
                'id': 1,
                'numero': 'FAC-2025-001',
                'client': 'SODECO SA',
                'ifu': '3201900001234',
                'montant_ht': 150000,
                'tva': 27000,
                'total': 177000,
                'date': '15/11/2025',
                'date_emission': '2025-11-15',
                'date_echeance': '2025-12-15',
                'statut': 'payee',
                'mecef_numero': 'MECeF-2025-00001',
                'mecef_qr': '',
                'nim': '1234567890',
                'date_mecef': '15/11/2025',
                'dossier': None,
                'observations': '',
                'lignes': [
                    {'description': 'Commandement de payer', 'quantite': 1, 'prix_unitaire': 150000}
                ]
            },
            {
                'id': 2,
                'numero': 'FAC-2025-002',
                'client': 'SOGEMA Sarl',
                'ifu': '',
                'montant_ht': 85000,
                'tva': 15300,
                'total': 100300,
                'date': '18/11/2025',
                'date_emission': '2025-11-18',
                'date_echeance': '2025-12-18',
                'statut': 'attente',
                'mecef_numero': '',
                'mecef_qr': '',
                'nim': '',
                'date_mecef': '',
                'dossier': None,
                'observations': '',
                'lignes': [
                    {'description': 'Signification de titre executoire', 'quantite': 1, 'prix_unitaire': 85000}
                ]
            },
            {
                'id': 3,
                'numero': 'FAC-2025-003',
                'client': 'Banque Atlantique',
                'ifu': '3201900005678',
                'montant_ht': 250000,
                'tva': 45000,
                'total': 295000,
                'date': '20/11/2025',
                'date_emission': '2025-11-20',
                'date_echeance': '2025-12-20',
                'statut': 'attente',
                'mecef_numero': '',
                'mecef_qr': '',
                'nim': '',
                'date_mecef': '',
                'dossier': None,
                'observations': '',
                'lignes': [
                    {'description': 'PV de Saisie-Vente', 'quantite': 1, 'prix_unitaire': 250000}
                ]
            },
        ]
        total_ht = 485000
        total_ttc = 572300
        nb_attente = 2

    context['factures'] = factures_list
    context['factures_json'] = json.dumps(factures_list)
    context['total_ht'] = total_ht
    context['total_ttc'] = total_ttc
    context['nb_attente'] = nb_attente

    # Dossiers pour le select
    context['dossiers'] = Dossier.objects.all().values('id', 'reference')[:100]

    context['tabs'] = [
        {'id': 'liste', 'label': 'Liste des factures'},
        {'id': 'memoires', 'label': 'Memoires'},
        {'id': 'mecef', 'label': 'MECeF'},
    ]
    context['current_tab'] = tab

    return render(request, 'gestion/facturation.html', context)


def calcul_recouvrement(request):
    """Vue du calcul de recouvrement OHADA"""
    context = get_default_context(request)
    context['active_module'] = 'calcul'
    context['page_title'] = 'Calcul Recouvrement'

    # Taux legaux UEMOA
    context['taux_legaux'] = json.dumps({
        2010: 6.4800, 2011: 6.2500, 2012: 4.2500, 2013: 4.1141, 2014: 3.7274,
        2015: 3.5000, 2016: 3.5000, 2017: 3.5437, 2018: 4.5000, 2019: 4.5000,
        2020: 4.5000, 2021: 4.2391, 2022: 4.0000, 2023: 4.2205, 2024: 5.0336,
        2025: 5.5000
    })

    # Catalogue des actes
    context['catalogue_actes'] = [
        {'id': 'cmd', 'label': 'Commandement de payer', 'tarif': 15000},
        {'id': 'sign_titre', 'label': 'Signification de titre executoire', 'tarif': 10000},
        {'id': 'pv_saisie', 'label': 'PV de Saisie-Vente', 'tarif': 25000},
        {'id': 'pv_carence', 'label': 'PV de Carence', 'tarif': 15000},
        {'id': 'denonc', 'label': 'Denonciation de saisie', 'tarif': 12000},
        {'id': 'assign', 'label': 'Assignation', 'tarif': 20000},
        {'id': 'sign_ord', 'label': 'Signification Ordonnance', 'tarif': 10000},
        {'id': 'certif', 'label': 'Certificat de non recours', 'tarif': 5000},
        {'id': 'mainlevee', 'label': 'Mainlevee', 'tarif': 15000},
        {'id': 'sommation', 'label': 'Sommation interpellative', 'tarif': 12000},
        {'id': 'constat', 'label': 'Proces-verbal de constat', 'tarif': 30000},
    ]

    # Charger l'historique depuis la base
    historique = []
    historique_qs = HistoriqueCalcul.objects.all().order_by('-date_creation')[:20]
    for h in historique_qs:
        historique.append({
            'id': h.id,
            'nom': h.nom,
            'mode': h.mode,
            'total': float(h.total),
            'date': h.date_creation.strftime('%d/%m/%Y %H:%M'),
            'donnees': h.donnees,
            'resultats': h.resultats,
        })
    context['historique'] = json.dumps(historique)

    return render(request, 'gestion/calcul_recouvrement.html', context)


def drive(request):
    """Vue du Drive"""
    context = get_default_context(request)
    context['active_module'] = 'drive'
    context['page_title'] = 'Drive'

    context['dossiers_drive'] = [
        {'nom': '173_1125_MAB', 'type': 'folder'},
        {'nom': '174_1125_MAB', 'type': 'folder'},
        {'nom': '175_1125_MAB', 'type': 'folder'},
    ]

    return render(request, 'gestion/drive.html', context)


def securite(request):
    """Vue Securite & Acces - Module complet de gestion de la securite"""
    context = get_default_context(request)
    context['active_module'] = 'securite'
    context['page_title'] = 'Securite & Acces'

    # Onglet actif
    tab = request.GET.get('tab', 'utilisateurs')
    context['current_tab'] = tab

    # Import des modeles de securite
    from .models import (
        Role, Permission, SessionUtilisateur, JournalAudit,
        AlerteSecurite, PolitiqueSecurite, AdresseIPAutorisee, AdresseIPBloquee
    )

    # =================================
    # SECTION 1: UTILISATEURS
    # =================================
    utilisateurs_db = Utilisateur.objects.all().order_by('last_name', 'first_name')
    utilisateurs_list = []

    for u in utilisateurs_db:
        utilisateurs_list.append({
            'id': u.id,
            'nom': f"{u.last_name} {u.first_name}" if u.last_name else u.username,
            'prenoms': u.first_name,
            'email': u.email,
            'telephone': u.telephone,
            'role': u.get_role_display(),
            'role_code': u.role,
            'actif': u.is_active,
            'derniere_connexion': u.last_login,
            'date_creation': u.date_joined,
            'initials': u.get_initials(),
        })

    # Si pas d'utilisateurs en base, utiliser les donnees de demo
    if not utilisateurs_list:
        utilisateurs_list = [
            {
                'id': 1,
                'nom': 'BIAOU Martial Arnaud',
                'prenoms': 'Martial Arnaud',
                'email': 'biaou@etude.bj',
                'telephone': '+229 97 00 00 01',
                'role': 'Administrateur (Huissier titulaire)',
                'role_code': 'admin',
                'actif': True,
                'derniere_connexion': timezone.now(),
                'date_creation': timezone.now(),
                'initials': 'MA',
            },
            {
                'id': 2,
                'nom': 'ADJOVI Marie',
                'prenoms': 'Marie',
                'email': 'adjovi@etude.bj',
                'telephone': '+229 97 00 00 02',
                'role': 'Clerc principal',
                'role_code': 'clerc_principal',
                'actif': True,
                'derniere_connexion': timezone.now() - timedelta(hours=1),
                'date_creation': timezone.now() - timedelta(days=365),
                'initials': 'AM',
            },
            {
                'id': 3,
                'nom': 'KONOU Paul',
                'prenoms': 'Paul',
                'email': 'konou@etude.bj',
                'telephone': '+229 97 00 00 03',
                'role': 'Clerc',
                'role_code': 'clerc',
                'actif': False,
                'derniere_connexion': timezone.now() - timedelta(days=12),
                'date_creation': timezone.now() - timedelta(days=180),
                'initials': 'KP',
            },
            {
                'id': 4,
                'nom': 'SAVI Jean',
                'prenoms': 'Jean',
                'email': 'savi@etude.bj',
                'telephone': '+229 97 00 00 04',
                'role': 'Secretaire',
                'role_code': 'secretaire',
                'actif': True,
                'derniere_connexion': timezone.now() - timedelta(hours=2),
                'date_creation': timezone.now() - timedelta(days=90),
                'initials': 'SJ',
            },
        ]

    context['utilisateurs'] = utilisateurs_list
    context['nb_utilisateurs_actifs'] = len([u for u in utilisateurs_list if u['actif']])
    context['nb_utilisateurs_inactifs'] = len([u for u in utilisateurs_list if not u['actif']])

    # =================================
    # SECTION 2: ROLES ET PERMISSIONS
    # =================================
    roles_systeme = [
        {'code': 'admin', 'nom': 'Administrateur (Huissier titulaire)', 'description': 'Acces complet a tous les modules', 'est_systeme': True},
        {'code': 'clerc_principal', 'nom': 'Clerc principal', 'description': 'Gestion des dossiers et supervision', 'est_systeme': True},
        {'code': 'clerc', 'nom': 'Clerc', 'description': 'Gestion de ses propres dossiers', 'est_systeme': True},
        {'code': 'secretaire', 'nom': 'Secretaire', 'description': 'Gestion administrative', 'est_systeme': True},
        {'code': 'agent_recouvrement', 'nom': 'Agent de recouvrement', 'description': 'Encaissement sur dossiers assignes', 'est_systeme': True},
        {'code': 'comptable', 'nom': 'Comptable', 'description': 'Acces comptabilite et tresorerie', 'est_systeme': True},
        {'code': 'stagiaire', 'nom': 'Stagiaire', 'description': 'Acces limite en consultation', 'est_systeme': True},
        {'code': 'consultant', 'nom': 'Consultant (lecture seule)', 'description': 'Consultation uniquement', 'est_systeme': True},
    ]
    context['roles'] = roles_systeme

    # Matrice des permissions (simplifiee pour l'affichage)
    context['matrice_permissions'] = {
        'dossiers': {
            'voir_tous': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': True},
            'voir_siens': {'admin': True, 'clerc_principal': True, 'clerc': True, 'secretaire': True, 'agent_recouvrement': True, 'comptable': False, 'stagiaire': True, 'consultant': True},
            'creer': {'admin': True, 'clerc_principal': True, 'clerc': True, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
            'modifier': {'admin': True, 'clerc_principal': True, 'clerc': 'limite', 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
            'supprimer': {'admin': True, 'clerc_principal': False, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
            'cloturer': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
        },
        'facturation': {
            'voir': {'admin': True, 'clerc_principal': True, 'clerc': True, 'secretaire': True, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': True},
            'creer': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': True, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': False},
            'modifier': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': False},
            'annuler': {'admin': True, 'clerc_principal': False, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
            'normaliser_mecef': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': False},
        },
        'tresorerie': {
            'voir': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': True},
            'encaisser': {'admin': True, 'clerc_principal': True, 'clerc': True, 'secretaire': True, 'agent_recouvrement': True, 'comptable': True, 'stagiaire': False, 'consultant': False},
            'decaisser': {'admin': True, 'clerc_principal': True, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': True, 'stagiaire': False, 'consultant': False},
            'approuver_decaissement': {'admin': True, 'clerc_principal': False, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
        },
        'securite': {
            'acces': {'admin': True, 'clerc_principal': False, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
        },
        'parametres': {
            'acces': {'admin': True, 'clerc_principal': False, 'clerc': False, 'secretaire': False, 'agent_recouvrement': False, 'comptable': False, 'stagiaire': False, 'consultant': False},
        },
    }

    # =================================
    # SECTION 3: POLITIQUE DE SECURITE
    # =================================
    try:
        politique = PolitiqueSecurite.get_politique()
        context['politique'] = {
            'mdp_longueur_min': politique.mdp_longueur_min,
            'mdp_exiger_majuscule': politique.mdp_exiger_majuscule,
            'mdp_exiger_minuscule': politique.mdp_exiger_minuscule,
            'mdp_exiger_chiffre': politique.mdp_exiger_chiffre,
            'mdp_exiger_special': politique.mdp_exiger_special,
            'mdp_expiration_jours': politique.mdp_expiration_jours,
            'mdp_historique': politique.mdp_historique,
            'mdp_tentatives_blocage': politique.mdp_tentatives_blocage,
            'mdp_duree_blocage': politique.mdp_duree_blocage,
            'session_duree_heures': politique.session_duree_heures,
            'session_inactivite_minutes': politique.session_inactivite_minutes,
            'session_simultanees': politique.session_simultanees,
            'session_forcer_deconnexion': politique.session_forcer_deconnexion,
            'session_multi_appareils': politique.session_multi_appareils,
            'mode_2fa': politique.mode_2fa,
            'restriction_ip_active': politique.restriction_ip_active,
            'restriction_horaires_active': politique.restriction_horaires_active,
            'horaire_debut': politique.horaire_debut.strftime('%H:%M') if politique.horaire_debut else '06:00',
            'horaire_fin': politique.horaire_fin.strftime('%H:%M') if politique.horaire_fin else '22:00',
            'jours_autorises': politique.jours_autorises or [1, 2, 3, 4, 5],
            'maintenance_active': politique.maintenance_active,
            'maintenance_message': politique.maintenance_message,
            'alerte_email': politique.alerte_email,
        }
    except:
        # Valeurs par defaut si la politique n'existe pas
        context['politique'] = {
            'mdp_longueur_min': 8,
            'mdp_exiger_majuscule': True,
            'mdp_exiger_minuscule': True,
            'mdp_exiger_chiffre': True,
            'mdp_exiger_special': False,
            'mdp_expiration_jours': 90,
            'mdp_historique': 5,
            'mdp_tentatives_blocage': 5,
            'mdp_duree_blocage': 30,
            'session_duree_heures': 8,
            'session_inactivite_minutes': 30,
            'session_simultanees': 1,
            'session_forcer_deconnexion': True,
            'session_multi_appareils': False,
            'mode_2fa': 'optionnel',
            'restriction_ip_active': False,
            'restriction_horaires_active': False,
            'horaire_debut': '06:00',
            'horaire_fin': '22:00',
            'jours_autorises': [1, 2, 3, 4, 5],
            'maintenance_active': False,
            'maintenance_message': "L'application est temporairement indisponible pour maintenance.",
            'alerte_email': 'admin@etude.bj',
        }

    # =================================
    # SECTION 4: JOURNAL D'AUDIT
    # =================================
    try:
        journal_entries = JournalAudit.objects.all()[:50]
        context['journal_audit'] = [{
            'id': e.id,
            'date_heure': e.date_heure,
            'utilisateur': e.utilisateur_nom or 'SYSTEME',
            'action': e.get_action_display(),
            'module': e.get_module_display(),
            'details': e.details,
            'adresse_ip': e.adresse_ip,
            'user_agent': e.user_agent[:50] if e.user_agent else '',
        } for e in journal_entries]
    except:
        # Donnees de demo
        context['journal_audit'] = [
            {
                'id': 1,
                'date_heure': timezone.now() - timedelta(minutes=15),
                'utilisateur': 'ADJOVI Marie',
                'action': 'Creation',
                'module': 'Dossiers',
                'details': 'DOS-2025-090 - SANI c/ KOFFI - Recouvrement',
                'adresse_ip': '192.168.1.45',
                'user_agent': 'Chrome 120',
            },
            {
                'id': 2,
                'date_heure': timezone.now() - timedelta(minutes=18),
                'utilisateur': 'ADJOVI Marie',
                'action': 'Connexion',
                'module': 'Connexion',
                'details': 'Connexion reussie',
                'adresse_ip': '192.168.1.45',
                'user_agent': 'Chrome 120',
            },
            {
                'id': 3,
                'date_heure': timezone.now() - timedelta(minutes=35),
                'utilisateur': 'Me BIAOU',
                'action': 'Approbation',
                'module': 'Tresorerie',
                'details': '450 000 F - Paiement fournisseur SONEB',
                'adresse_ip': '192.168.1.10',
                'user_agent': 'Safari 17',
            },
            {
                'id': 4,
                'date_heure': timezone.now() - timedelta(minutes=40),
                'utilisateur': 'SYSTEME',
                'action': 'Echec de connexion',
                'module': 'Connexion',
                'details': '3eme tentative - konou@etude.bj',
                'adresse_ip': '41.138.77.92',
                'user_agent': '',
            },
            {
                'id': 5,
                'date_heure': timezone.now() - timedelta(minutes=45),
                'utilisateur': 'Me BIAOU',
                'action': 'Connexion',
                'module': 'Connexion',
                'details': 'Connexion reussie',
                'adresse_ip': '192.168.1.10',
                'user_agent': 'Safari 17 / MacOS',
            },
        ]

    # =================================
    # SECTION 5: SESSIONS ACTIVES
    # =================================
    try:
        sessions_actives = SessionUtilisateur.objects.filter(active=True)
        context['sessions_actives'] = [{
            'id': s.id,
            'utilisateur': str(s.utilisateur),
            'initials': s.utilisateur.get_initials() if hasattr(s.utilisateur, 'get_initials') else 'XX',
            'adresse_ip': s.adresse_ip,
            'navigateur': s.navigateur or 'Inconnu',
            'systeme_os': s.systeme_os or 'Inconnu',
            'date_connexion': s.date_creation,
            'derniere_activite': s.date_derniere_activite,
            'module_actuel': s.module_actuel or 'Tableau de bord',
            'est_inactif': s.est_inactive(),
        } for s in sessions_actives]
    except:
        # Donnees de demo
        context['sessions_actives'] = [
            {
                'id': 1,
                'utilisateur': 'Me BIAOU Martial Arnaud',
                'initials': 'MA',
                'adresse_ip': '192.168.1.10',
                'navigateur': 'Safari 17',
                'systeme_os': 'MacOS',
                'date_connexion': timezone.now() - timedelta(hours=3, minutes=30),
                'derniere_activite': timezone.now() - timedelta(minutes=2),
                'module_actuel': 'Tableau de bord',
                'est_inactif': False,
                'est_admin': True,
            },
            {
                'id': 2,
                'utilisateur': 'ADJOVI Marie',
                'initials': 'AM',
                'adresse_ip': '192.168.1.45',
                'navigateur': 'Chrome 120',
                'systeme_os': 'Windows 11',
                'date_connexion': timezone.now() - timedelta(hours=3, minutes=3),
                'derniere_activite': timezone.now() - timedelta(minutes=5),
                'module_actuel': 'Dossiers',
                'est_inactif': False,
                'est_admin': False,
            },
            {
                'id': 3,
                'utilisateur': 'SAVI Jean',
                'initials': 'SJ',
                'adresse_ip': '192.168.1.52',
                'navigateur': 'Firefox 121',
                'systeme_os': 'Linux',
                'date_connexion': timezone.now() - timedelta(hours=1, minutes=45),
                'derniere_activite': timezone.now() - timedelta(minutes=25),
                'module_actuel': 'Agenda',
                'est_inactif': True,
                'est_admin': False,
            },
        ]

    context['nb_sessions_actives'] = len(context['sessions_actives'])

    # =================================
    # SECTION 6: ALERTES DE SECURITE
    # =================================
    try:
        alertes = AlerteSecurite.objects.filter(traitee=False).order_by('-date_heure')[:10]
        context['alertes_securite'] = [{
            'id': a.id,
            'date_heure': a.date_heure,
            'type': a.get_type_alerte_display(),
            'type_code': a.type_alerte,
            'gravite': a.gravite,
            'description': a.description,
            'utilisateur': a.utilisateur_nom or 'Inconnu',
            'adresse_ip': a.adresse_ip,
            'traitee': a.traitee,
        } for a in alertes]
    except:
        # Donnees de demo
        context['alertes_securite'] = [
            {
                'id': 1,
                'date_heure': timezone.now() - timedelta(minutes=40),
                'type': 'Echec de connexion repete',
                'type_code': 'echec_connexion',
                'gravite': 'critical',
                'description': '3 echecs de connexion consecutifs',
                'utilisateur': 'konou@etude.bj',
                'adresse_ip': '41.138.77.92',
                'traitee': False,
            },
            {
                'id': 2,
                'date_heure': timezone.now() - timedelta(hours=10, minutes=45),
                'type': 'Connexion hors horaires',
                'type_code': 'hors_horaires',
                'gravite': 'warning',
                'description': 'Connexion en dehors des horaires autorises',
                'utilisateur': 'adjovi@etude.bj',
                'adresse_ip': '192.168.1.45',
                'traitee': False,
            },
        ]

    context['nb_alertes_non_traitees'] = len([a for a in context['alertes_securite'] if not a['traitee']])

    # =================================
    # SECTION 7: IPS AUTORISEES/BLOQUEES
    # =================================
    try:
        context['ips_autorisees'] = list(AdresseIPAutorisee.objects.filter(active=True).values('id', 'adresse_ip', 'description'))
        context['ips_bloquees'] = list(AdresseIPBloquee.objects.filter(active=True).values('id', 'adresse_ip', 'raison', 'date_blocage'))
    except:
        context['ips_autorisees'] = []
        context['ips_bloquees'] = []

    # =================================
    # ONGLETS DE NAVIGATION
    # =================================
    context['tabs'] = [
        {'id': 'utilisateurs', 'label': 'Utilisateurs', 'icon': 'users'},
        {'id': 'roles', 'label': 'Roles & Permissions', 'icon': 'shield-check'},
        {'id': 'politique', 'label': 'Politique de securite', 'icon': 'lock'},
        {'id': 'audit', 'label': 'Journal d\'audit', 'icon': 'file-text'},
        {'id': 'sessions', 'label': 'Sessions actives', 'icon': 'monitor'},
        {'id': 'alertes', 'label': 'Alertes', 'icon': 'alert-triangle'},
        {'id': 'protection', 'label': 'Protection des donnees', 'icon': 'database'},
        {'id': 'maintenance', 'label': 'Maintenance', 'icon': 'wrench'},
    ]

    # Liste des roles pour le formulaire
    context['roles_choices'] = [
        ('admin', 'Administrateur (Huissier titulaire)'),
        ('clerc_principal', 'Clerc principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secretaire'),
        ('agent_recouvrement', 'Agent de recouvrement'),
        ('comptable', 'Comptable'),
        ('stagiaire', 'Stagiaire'),
        ('consultant', 'Consultant (lecture seule)'),
    ]

    return render(request, 'gestion/securite.html', context)


def module_en_construction(request, module_name):
    """Vue pour les modules non implementes"""
    context = get_default_context(request)
    context['active_module'] = module_name

    # Trouver le label du module
    for m in context['modules']:
        if m['id'] == module_name:
            context['page_title'] = m['label']
            break
    else:
        context['page_title'] = 'Module'

    return render(request, 'gestion/en_construction.html', context)


# ============================================
# API ENDPOINTS FACTURATION
# ============================================

@require_POST
def api_generer_numero_facture(request):
    """API pour generer un numero de facture unique"""
    try:
        numero = Facture.generer_numero()
        return JsonResponse({'success': True, 'numero': numero})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_sauvegarder_facture(request):
    """API pour creer ou modifier une facture"""
    try:
        data = json.loads(request.body)

        facture_id = data.get('id')
        numero = data.get('numero')
        date_emission = datetime.strptime(data.get('date_emission'), '%Y-%m-%d').date()
        date_echeance = None
        if data.get('date_echeance'):
            date_echeance = datetime.strptime(data.get('date_echeance'), '%Y-%m-%d').date()
        statut = data.get('statut', 'attente')
        client = data.get('client')
        ifu = data.get('ifu', '')
        dossier_id = data.get('dossier') or None
        observations = data.get('observations', '')
        lignes = data.get('lignes', [])

        # Calculer les totaux
        montant_ht = sum(l.get('quantite', 1) * l.get('prix_unitaire', 0) for l in lignes)
        montant_tva = montant_ht * Decimal('0.18')
        montant_ttc = montant_ht + montant_tva

        if facture_id:
            # Modification
            facture = get_object_or_404(Facture, id=facture_id)
            facture.date_emission = date_emission
            facture.date_echeance = date_echeance
            facture.statut = statut
            facture.client = client
            facture.ifu = ifu
            facture.dossier_id = dossier_id
            facture.observations = observations
            facture.montant_ht = montant_ht
            facture.montant_tva = montant_tva
            facture.montant_ttc = montant_ttc
            facture.save()

            # Supprimer les anciennes lignes et recreer
            facture.lignes.all().delete()
        else:
            # Creation
            facture = Facture.objects.create(
                numero=numero,
                date_emission=date_emission,
                date_echeance=date_echeance,
                statut=statut,
                client=client,
                ifu=ifu,
                dossier_id=dossier_id,
                observations=observations,
                montant_ht=montant_ht,
                montant_tva=montant_tva,
                montant_ttc=montant_ttc,
            )

        # Creer les lignes
        for ligne in lignes:
            LigneFacture.objects.create(
                facture=facture,
                description=ligne.get('description', ''),
                quantite=ligne.get('quantite', 1),
                prix_unitaire=ligne.get('prix_unitaire', 0)
            )

        return JsonResponse({
            'success': True,
            'facture_id': facture.id,
            'numero': facture.numero
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_supprimer_facture(request):
    """API pour supprimer une facture"""
    try:
        data = json.loads(request.body)
        facture_id = data.get('id')

        facture = get_object_or_404(Facture, id=facture_id)

        # Verifier si la facture est normalisee
        if facture.mecef_numero:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de supprimer une facture normalisee MECeF'
            }, status=400)

        facture.delete()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_normaliser_mecef(request):
    """API pour normaliser une facture avec MECeF"""
    try:
        data = json.loads(request.body)
        facture_id = data.get('id')

        facture = get_object_or_404(Facture, id=facture_id)

        if facture.mecef_numero:
            return JsonResponse({
                'success': False,
                'error': 'Cette facture est deja normalisee'
            }, status=400)

        # Generer le numero MECeF (simulation)
        now = timezone.now()
        sequence = Facture.objects.filter(mecef_numero__isnull=False).count() + 1
        mecef_numero = f"MECeF-{now.year}-{str(sequence).zfill(5)}"

        # Generer le NIM (simulation)
        nim = ''.join(random.choices(string.digits, k=10))

        # Generer un QR code data (simulation)
        qr_data = f"NIM:{nim}|NUM:{mecef_numero}|TTC:{facture.montant_ttc}|DATE:{now.strftime('%Y%m%d%H%M%S')}"
        qr_hash = hashlib.md5(qr_data.encode()).hexdigest()[:16].upper()

        # Mettre a jour la facture
        facture.mecef_numero = mecef_numero
        facture.nim = nim
        facture.mecef_qr = qr_hash
        facture.date_mecef = now
        facture.save()

        return JsonResponse({
            'success': True,
            'mecef_numero': mecef_numero,
            'nim': nim,
            'qr_code': qr_hash
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def api_exporter_factures(request):
    """API pour exporter les factures en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="factures_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Numero', 'Client', 'IFU', 'Montant HT', 'TVA', 'Total TTC', 'Date', 'Statut', 'MECeF'])

    factures = Facture.objects.all().order_by('-date_emission')
    for f in factures:
        writer.writerow([
            f.numero,
            f.client,
            f.ifu if hasattr(f, 'ifu') else '',
            f.montant_ht,
            f.montant_tva,
            f.montant_ttc,
            f.date_emission.strftime('%d/%m/%Y'),
            f.statut,
            f.mecef_numero or ''
        ])

    return response


# ============================================
# API ENDPOINTS CALCUL RECOUVREMENT
# ============================================

@require_POST
def api_calculer_interets(request):
    """API pour calculer les interets OHADA"""
    try:
        data = json.loads(request.body)

        # Recuperer les parametres
        montant_principal = Decimal(str(data.get('montant_principal', 0)))

        if montant_principal <= 0:
            return JsonResponse({'success': False, 'error': 'Le montant principal doit etre superieur a 0'}, status=400)

        date_creance_str = data.get('date_creance')
        date_saisie_str = data.get('date_saisie')

        if not date_creance_str or not date_saisie_str:
            return JsonResponse({'success': False, 'error': 'Les dates sont obligatoires'}, status=400)

        date_creance = datetime.strptime(date_creance_str, '%Y-%m-%d')
        date_saisie = datetime.strptime(date_saisie_str, '%Y-%m-%d')

        if date_saisie <= date_creance:
            return JsonResponse({'success': False, 'error': 'La date de saisie doit etre posterieure a la date de creance'}, status=400)

        type_taux = data.get('type_taux', 'legal')
        taux_conventionnel = Decimal(str(data.get('taux_conventionnel', 0)))
        type_calcul = data.get('type_calcul', 'simple')
        appliquer_majoration = data.get('appliquer_majoration', False)
        date_decision = data.get('date_decision')
        calculer_emoluments = data.get('calculer_emoluments', False)
        type_titre = data.get('type_titre', 'sans')
        frais_justice = Decimal(str(data.get('frais_justice', 0)))
        actes = data.get('actes', [])
        arrondir = data.get('arrondir', True)

        # Taux legaux UEMOA
        taux_legaux = {
            2010: Decimal('6.4800'), 2011: Decimal('6.2500'), 2012: Decimal('4.2500'),
            2013: Decimal('4.1141'), 2014: Decimal('3.7274'), 2015: Decimal('3.5000'),
            2016: Decimal('3.5000'), 2017: Decimal('3.5437'), 2018: Decimal('4.5000'),
            2019: Decimal('4.5000'), 2020: Decimal('4.5000'), 2021: Decimal('4.2391'),
            2022: Decimal('4.0000'), 2023: Decimal('4.2205'), 2024: Decimal('5.0336'),
            2025: Decimal('5.5000')
        }

        def est_bissextile(annee):
            return (annee % 4 == 0 and annee % 100 != 0) or (annee % 400 == 0)

        def jours_annee(annee):
            return 366 if est_bissextile(annee) else 365

        def obtenir_taux(annee):
            return taux_legaux.get(annee, Decimal('5.5'))

        # Calcul des interets par periode
        def calculer_interets_periode(montant, debut, fin, majore=False):
            current = debut + timedelta(days=1)
            end = fin
            total = Decimal('0')
            periodes = []

            while current <= end:
                annee = current.year
                fin_annee = datetime(annee, 12, 31)
                borne = min(fin_annee, end)
                jours = (borne - current).days + 1

                if type_taux == 'legal':
                    taux = obtenir_taux(annee)
                elif type_taux == 'cima':
                    taux = Decimal('60')  # 5% * 12 mois
                else:
                    taux = taux_conventionnel

                taux_applique = taux
                if majore:
                    taux_applique = taux * Decimal('1.5')

                if type_calcul == 'simple':
                    interet = (montant * taux_applique * jours) / (100 * jours_annee(annee))
                else:
                    # Interets composes
                    interet = montant * ((1 + taux_applique / 100) ** (Decimal(jours) / jours_annee(annee)) - 1)

                periodes.append({
                    'annee': annee,
                    'debut': current.strftime('%d/%m/%Y'),
                    'fin': borne.strftime('%d/%m/%Y'),
                    'jours': jours,
                    'taux': float(taux),
                    'taux_applique': float(taux_applique),
                    'majore': majore,
                    'interet': float(round(interet) if arrondir else interet)
                })

                total += interet
                current = datetime(annee + 1, 1, 1)

            return {
                'periodes': periodes,
                'total': float(round(total) if arrondir else total)
            }

        # Calcul des emoluments proportionnels
        def calculer_emoluments_prop(base):
            baremes = {
                'sans': [
                    {'min': 1, 'max': 5000000, 'taux': Decimal('10')},
                    {'min': 5000001, 'max': 20000000, 'taux': Decimal('8')},
                    {'min': 20000001, 'max': 50000000, 'taux': Decimal('6')},
                    {'min': 50000001, 'max': float('inf'), 'taux': Decimal('4')},
                ],
                'avec': [
                    {'min': 1, 'max': 5000000, 'taux': Decimal('10')},
                    {'min': 5000001, 'max': 20000000, 'taux': Decimal('3.5')},
                    {'min': 20000001, 'max': 50000000, 'taux': Decimal('2')},
                    {'min': 50000001, 'max': float('inf'), 'taux': Decimal('1')},
                ]
            }

            restant = base
            total = Decimal('0')
            cumul = 0
            details = []

            for tranche in baremes[type_titre]:
                if restant <= 0:
                    break
                taille_tranche = Decimal(str(tranche['max'])) - cumul if tranche['max'] != float('inf') else restant
                part = min(restant, taille_tranche)
                if part > 0:
                    em = (part * tranche['taux']) / 100
                    total += em
                    details.append({
                        'tranche': f"{cumul+1:,.0f} - {tranche['max']:,.0f}" if tranche['max'] != float('inf') else f"> {cumul:,.0f}",
                        'taux': float(tranche['taux']),
                        'base': float(part),
                        'emolument': float(round(em) if arrondir else em)
                    })
                    restant -= part
                    cumul += float(part)

            return {
                'total': float(round(total) if arrondir else total),
                'details': details,
                'type_titre': type_titre
            }

        # Calcul principal
        date_maj = None
        if appliquer_majoration and date_decision:
            d = datetime.strptime(date_decision, '%Y-%m-%d')
            date_maj = d + timedelta(days=60)  # 2 mois apres decision
            if date_saisie <= date_maj:
                date_maj = None  # Pas de majoration si saisie avant delai

        # Interets echus
        if date_maj and date_maj < date_saisie:
            # Calcul en deux periodes: avant et apres majoration
            p1 = calculer_interets_periode(montant_principal, date_creance, date_maj, False)
            p2 = calculer_interets_periode(montant_principal, date_maj, date_saisie, True)
            interets_echus = {
                'periodes': p1['periodes'] + p2['periodes'],
                'total': p1['total'] + p2['total']
            }
        else:
            interets_echus = calculer_interets_periode(montant_principal, date_creance, date_saisie, False)

        # Interets a echoir (1 mois)
        date_fin_echoir = date_saisie + timedelta(days=30)
        interets_echoir = calculer_interets_periode(
            montant_principal, date_saisie, date_fin_echoir,
            appliquer_majoration and date_maj is not None
        )

        # Emoluments
        emoluments = None
        base_emol = montant_principal + Decimal(str(interets_echus['total']))
        if calculer_emoluments:
            base_emol += frais_justice
            emoluments = calculer_emoluments_prop(base_emol)

        # Total des actes
        total_actes = sum(float(a.get('montant', 0)) for a in actes)

        # Total general
        total = float(montant_principal) + interets_echus['total'] + float(frais_justice)
        if emoluments:
            total += emoluments['total']
        total += total_actes

        resultats = {
            'mode': 'complet',
            'principal': float(montant_principal),
            'interets_echus': interets_echus,
            'interets_echoir': interets_echoir,
            'emoluments': emoluments,
            'base_emoluments': float(base_emol),
            'frais_justice': float(frais_justice),
            'actes': total_actes,
            'total': round(total) if arrondir else total,
            'date_debut': (date_creance + timedelta(days=1)).strftime('%d/%m/%Y'),
            'date_fin': date_saisie.strftime('%d/%m/%Y'),
            'majoration': appliquer_majoration,
            'date_limite_majoration': date_maj.strftime('%d/%m/%Y') if date_maj else None,
            'type_calcul': type_calcul,
            'type_taux': type_taux
        }

        return JsonResponse({'success': True, 'resultats': resultats})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_calculer_emoluments(request):
    """API pour calculer les emoluments seuls"""
    try:
        data = json.loads(request.body)

        base = Decimal(str(data.get('base', 0)))

        if base <= 0:
            return JsonResponse({'success': False, 'error': 'La base de calcul doit etre superieure a 0'}, status=400)

        type_titre = data.get('type_titre', 'sans')
        arrondir = data.get('arrondir', True)

        baremes = {
            'sans': [
                {'min': 1, 'max': 5000000, 'taux': Decimal('10')},
                {'min': 5000001, 'max': 20000000, 'taux': Decimal('8')},
                {'min': 20000001, 'max': 50000000, 'taux': Decimal('6')},
                {'min': 50000001, 'max': float('inf'), 'taux': Decimal('4')},
            ],
            'avec': [
                {'min': 1, 'max': 5000000, 'taux': Decimal('10')},
                {'min': 5000001, 'max': 20000000, 'taux': Decimal('3.5')},
                {'min': 20000001, 'max': 50000000, 'taux': Decimal('2')},
                {'min': 50000001, 'max': float('inf'), 'taux': Decimal('1')},
            ]
        }

        restant = base
        total = Decimal('0')
        cumul = 0
        details = []

        for tranche in baremes[type_titre]:
            if restant <= 0:
                break
            taille_tranche = Decimal(str(tranche['max'])) - cumul if tranche['max'] != float('inf') else restant
            part = min(restant, taille_tranche)
            if part > 0:
                em = (part * tranche['taux']) / 100
                total += em
                details.append({
                    'tranche': f"De {cumul+1:,.0f} a {int(cumul + float(part)):,.0f}" if tranche['max'] != float('inf') else f"Au-dela de {cumul:,.0f}",
                    'taux': float(tranche['taux']),
                    'base': float(part),
                    'emolument': float(round(em) if arrondir else em)
                })
                restant -= part
                cumul += float(part)

        emol_total = float(round(total) if arrondir else total)

        resultats = {
            'mode': 'emoluments',
            'base': float(base),
            'type_titre': type_titre,
            'emoluments': {
                'total': emol_total,
                'details': details
            },
            'total': float(base) + emol_total
        }

        return JsonResponse({'success': True, 'resultats': resultats})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_sauvegarder_calcul(request):
    """API pour sauvegarder un calcul dans l'historique"""
    try:
        data = json.loads(request.body)

        nom = data.get('nom', f"Calcul du {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        mode = data.get('mode', 'complet')
        donnees = data.get('donnees', {})
        resultats = data.get('resultats', {})
        total = Decimal(str(data.get('total', 0)))

        historique = HistoriqueCalcul.objects.create(
            nom=nom,
            mode=mode,
            donnees=donnees,
            resultats=resultats,
            total=total,
            utilisateur=None  # A remplacer par request.user si authentification
        )

        return JsonResponse({
            'success': True,
            'id': historique.id,
            'message': 'Calcul sauvegarde'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_supprimer_calcul(request):
    """API pour supprimer un calcul de l'historique"""
    try:
        data = json.loads(request.body)
        calcul_id = data.get('id')

        HistoriqueCalcul.objects.filter(id=calcul_id).delete()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def api_charger_historique(request):
    """API pour charger l'historique des calculs"""
    try:
        historique = []
        historique_qs = HistoriqueCalcul.objects.all().order_by('-date_creation')[:50]
        for h in historique_qs:
            historique.append({
                'id': h.id,
                'nom': h.nom,
                'mode': h.mode,
                'total': float(h.total),
                'date': h.date_creation.strftime('%d/%m/%Y %H:%M'),
                'donnees': h.donnees,
                'resultats': h.resultats,
            })
        return JsonResponse({'success': True, 'historique': historique})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API CHATBOT ET AUTRES
# ============================================

@require_POST
def api_chatbot(request):
    """API pour le chatbot"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').lower()
        user_role = data.get('user_role', 'user')

        # Reponses contextuelles
        if 'supprim' in message and user_role != 'admin':
            reponse = "Desole, seul l'administrateur peut supprimer des elements."
        elif 'interet' in message or 'calcul' in message:
            reponse = "Pour calculer des interets, rendez-vous dans le module 'Calcul Recouvrement'. Je peux vous y guider si vous le souhaitez."
        elif 'dossier' in message:
            reponse = "Pour creer ou consulter un dossier, utilisez le module 'Dossiers'. Vous pouvez cliquer sur 'Nouveau dossier' pour en creer un."
        elif 'facture' in message:
            reponse = "Le module 'Facturation & MECeF' vous permet de gerer vos factures et de les normaliser avec le systeme MECeF."
        elif 'bonjour' in message or 'salut' in message:
            reponse = "Bonjour Maitre ! Comment puis-je vous aider aujourd'hui ?"
        elif 'mecef' in message:
            reponse = "MECeF est le systeme de normalisation des factures au Benin. Pour normaliser une facture, allez dans Facturation et cliquez sur 'Normaliser'."
        elif 'ohada' in message:
            reponse = "L'OHADA regit le droit des affaires dans la zone UEMOA. Le module Calcul Recouvrement applique les taux legaux UEMOA et les regles OHADA."
        else:
            reponse = "Je peux vous aider a rediger des actes, calculer des interets ou rechercher des informations juridiques."

        return JsonResponse({'success': True, 'reponse': reponse})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_supprimer_dossier(request):
    """API pour supprimer un dossier (admin only)"""
    try:
        data = json.loads(request.body)
        dossier_id = data.get('dossier_id')
        user_role = data.get('user_role', 'user')

        if user_role != 'admin':
            return JsonResponse({
                'success': False,
                'error': "Action non autorisee : Seul l'administrateur peut supprimer un dossier."
            }, status=403)

        # Ici, on supprimerait le dossier en base
        # Dossier.objects.filter(id=dossier_id).delete()

        return JsonResponse({'success': True, 'message': 'Dossier supprime'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API CREANCIERS
# ============================================

def creanciers(request):
    """Vue liste des créanciers"""
    context = get_default_context(request)
    context['active_module'] = 'creanciers'
    context['page_title'] = 'Créanciers'

    # Liste des créanciers
    creanciers_list = Creancier.objects.filter(actif=True).order_by('nom')

    # Statistiques
    for creancier in creanciers_list:
        creancier.nb_dossiers = creancier.dossiers.count()
        creancier.total_creances = creancier.get_total_creances()
        creancier.total_encaisse = creancier.get_total_encaisse()
        creancier.total_reverse = creancier.get_total_reverse()

    context['creanciers'] = creanciers_list

    return render(request, 'gestion/creanciers.html', context)


@require_GET
def api_creanciers_liste(request):
    """API pour la liste des créanciers"""
    try:
        creanciers_list = Creancier.objects.filter(actif=True).order_by('nom')

        data = []
        for creancier in creanciers_list:
            data.append({
                'id': creancier.id,
                'code': creancier.code,
                'nom': creancier.nom,
                'type_creancier': creancier.type_creancier,
                'telephone': creancier.telephone,
                'email': creancier.email,
                'taux_commission': float(creancier.taux_commission),
                'nb_dossiers': creancier.dossiers.count(),
                'total_creances': float(creancier.get_total_creances()),
                'total_encaisse': float(creancier.get_total_encaisse()),
                'total_reverse': float(creancier.get_total_reverse()),
            })

        return JsonResponse({'success': True, 'creanciers': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creancier_creer(request):
    """API pour créer un créancier"""
    try:
        data = json.loads(request.body)

        creancier = Creancier(
            code=data.get('code') or Creancier.generer_code(),
            nom=data.get('nom'),
            type_creancier=data.get('type_creancier', 'entreprise'),
            adresse=data.get('adresse', ''),
            telephone=data.get('telephone', ''),
            email=data.get('email', ''),
            ifu=data.get('ifu', ''),
            rccm=data.get('rccm', ''),
            contact_nom=data.get('contact_nom', ''),
            contact_fonction=data.get('contact_fonction', ''),
            contact_telephone=data.get('contact_telephone', ''),
            contact_email=data.get('contact_email', ''),
            banque_nom=data.get('banque_nom', ''),
            banque_iban=data.get('banque_iban', ''),
            banque_rib=data.get('banque_rib', ''),
            taux_commission=Decimal(str(data.get('taux_commission', 10))),
            delai_reversement=data.get('delai_reversement', 15),
            notes=data.get('notes', ''),
        )
        creancier.save()

        # Créer le portefeuille associé
        PortefeuilleCreancier.objects.create(
            creancier=creancier,
            date_debut_relation=timezone.now().date()
        )

        return JsonResponse({
            'success': True,
            'creancier_id': creancier.id,
            'code': creancier.code,
            'message': f'Créancier {creancier.nom} créé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_creancier_detail(request, creancier_id):
    """API pour le détail d'un créancier"""
    try:
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        # Dossiers du créancier
        dossiers = []
        for dossier in creancier.dossiers.all()[:20]:
            dossiers.append({
                'id': dossier.id,
                'reference': dossier.reference,
                'intitule': dossier.get_intitule(),
                'montant_creance': float(dossier.montant_creance or 0),
                'total_encaisse': float(dossier.get_total_encaisse()),
                'solde_restant': float(dossier.get_solde_restant()),
                'phase': dossier.phase,
                'statut': dossier.statut,
            })

        data = {
            'id': creancier.id,
            'code': creancier.code,
            'nom': creancier.nom,
            'type_creancier': creancier.type_creancier,
            'adresse': creancier.adresse,
            'telephone': creancier.telephone,
            'email': creancier.email,
            'ifu': creancier.ifu,
            'rccm': creancier.rccm,
            'contact_nom': creancier.contact_nom,
            'contact_fonction': creancier.contact_fonction,
            'contact_telephone': creancier.contact_telephone,
            'contact_email': creancier.contact_email,
            'banque_nom': creancier.banque_nom,
            'banque_iban': creancier.banque_iban,
            'banque_rib': creancier.banque_rib,
            'taux_commission': float(creancier.taux_commission),
            'delai_reversement': creancier.delai_reversement,
            'notes': creancier.notes,
            'statistiques': {
                'nb_dossiers': creancier.dossiers.count(),
                'nb_dossiers_actifs': creancier.dossiers.filter(statut__in=['actif', 'urgent']).count(),
                'total_creances': float(creancier.get_total_creances()),
                'total_encaisse': float(creancier.get_total_encaisse()),
                'total_reverse': float(creancier.get_total_reverse()),
                'reste_a_reverser': float(creancier.get_total_encaisse() - creancier.get_total_reverse()),
            },
            'dossiers': dossiers,
        }

        return JsonResponse({'success': True, 'creancier': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API ENCAISSEMENTS
# ============================================

def encaissements(request):
    """Vue liste des encaissements"""
    context = get_default_context(request)
    context['active_module'] = 'encaissements'
    context['page_title'] = 'Historique des Encaissements'

    # Filtres
    dossier_id = request.GET.get('dossier')
    creancier_id = request.GET.get('creancier')
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    encaissements_qs = Encaissement.objects.select_related('dossier', 'dossier__creancier')

    if dossier_id:
        encaissements_qs = encaissements_qs.filter(dossier_id=dossier_id)
    if creancier_id:
        encaissements_qs = encaissements_qs.filter(dossier__creancier_id=creancier_id)
    if statut:
        encaissements_qs = encaissements_qs.filter(statut=statut)
    if date_debut:
        encaissements_qs = encaissements_qs.filter(date_encaissement__gte=date_debut)
    if date_fin:
        encaissements_qs = encaissements_qs.filter(date_encaissement__lte=date_fin)

    # Pagination
    paginator = Paginator(encaissements_qs.order_by('-date_encaissement'), 25)
    page = request.GET.get('page', 1)
    encaissements_page = paginator.get_page(page)

    # Statistiques
    stats = encaissements_qs.filter(statut='valide').aggregate(
        total=Sum('montant'),
        count=Count('id')
    )

    context['encaissements'] = encaissements_page
    context['stats'] = stats
    context['creanciers'] = Creancier.objects.filter(actif=True)

    return render(request, 'gestion/encaissements.html', context)


@require_GET
def api_encaissements_liste(request):
    """API pour la liste des encaissements avec filtres"""
    try:
        # Filtres
        dossier_id = request.GET.get('dossier')
        creancier_id = request.GET.get('creancier')
        statut = request.GET.get('statut')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 25))

        encaissements_qs = Encaissement.objects.select_related(
            'dossier', 'dossier__creancier', 'cree_par', 'valide_par'
        )

        if dossier_id:
            encaissements_qs = encaissements_qs.filter(dossier_id=dossier_id)
        if creancier_id:
            encaissements_qs = encaissements_qs.filter(dossier__creancier_id=creancier_id)
        if statut:
            encaissements_qs = encaissements_qs.filter(statut=statut)
        if date_debut:
            encaissements_qs = encaissements_qs.filter(date_encaissement__gte=date_debut)
        if date_fin:
            encaissements_qs = encaissements_qs.filter(date_encaissement__lte=date_fin)

        # Pagination
        paginator = Paginator(encaissements_qs.order_by('-date_encaissement'), per_page)
        encaissements_page = paginator.get_page(page)

        data = []
        for enc in encaissements_page:
            data.append({
                'id': enc.id,
                'reference': enc.reference,
                'dossier': {
                    'id': enc.dossier.id,
                    'reference': enc.dossier.reference,
                    'intitule': enc.dossier.get_intitule(),
                },
                'creancier': {
                    'id': enc.dossier.creancier.id,
                    'nom': enc.dossier.creancier.nom,
                } if enc.dossier.creancier else None,
                'montant': float(enc.montant),
                'date_encaissement': enc.date_encaissement.isoformat(),
                'mode_paiement': enc.mode_paiement,
                'payeur_nom': enc.payeur_nom,
                'statut': enc.statut,
                'reversement_statut': enc.reversement_statut,
                'cumul_encaisse_apres': float(enc.cumul_encaisse_apres),
                'solde_restant': float(enc.solde_restant),
                'montant_a_reverser': float(enc.montant_a_reverser),
            })

        # Statistiques globales
        stats = encaissements_qs.filter(statut='valide').aggregate(
            total=Sum('montant'),
            count=Count('id'),
            total_a_reverser=Sum('montant_a_reverser')
        )

        return JsonResponse({
            'success': True,
            'encaissements': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            },
            'statistiques': {
                'total_encaisse': float(stats['total'] or 0),
                'nb_encaissements': stats['count'] or 0,
                'total_a_reverser': float(stats['total_a_reverser'] or 0),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_encaissement_creer(request):
    """API pour créer un encaissement"""
    try:
        data = json.loads(request.body)

        dossier = get_object_or_404(Dossier, pk=data.get('dossier_id'))

        encaissement = Encaissement(
            dossier=dossier,
            montant=Decimal(str(data.get('montant'))),
            date_encaissement=data.get('date_encaissement', timezone.now().date()),
            date_valeur=data.get('date_valeur'),
            mode_paiement=data.get('mode_paiement', 'especes'),
            payeur_nom=data.get('payeur_nom'),
            payeur_telephone=data.get('payeur_telephone', ''),
            payeur_qualite=data.get('payeur_qualite', ''),
            reference_paiement=data.get('reference_paiement', ''),
            banque_emettrice=data.get('banque_emettrice', ''),
            observations=data.get('observations', ''),
            statut='en_attente',
        )
        encaissement.save()

        # Créer les imputations si fournies
        imputations = data.get('imputations', [])
        for imp in imputations:
            ImputationEncaissement.objects.create(
                encaissement=encaissement,
                type_imputation=imp['type'],
                montant=Decimal(str(imp['montant'])),
                observations=imp.get('observations', ''),
            )

        return JsonResponse({
            'success': True,
            'encaissement_id': encaissement.id,
            'reference': encaissement.reference,
            'message': f'Encaissement {encaissement.reference} créé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_encaissement_detail(request, encaissement_id):
    """API pour le détail d'un encaissement"""
    try:
        enc = get_object_or_404(
            Encaissement.objects.select_related('dossier', 'dossier__creancier'),
            pk=encaissement_id
        )

        # Imputations
        imputations = []
        for imp in enc.imputations.all():
            imputations.append({
                'id': imp.id,
                'type_imputation': imp.type_imputation,
                'type_display': imp.get_type_imputation_display(),
                'montant': float(imp.montant),
                'solde_avant': float(imp.solde_avant),
                'solde_apres': float(imp.solde_apres),
                'observations': imp.observations,
            })

        data = {
            'id': enc.id,
            'reference': enc.reference,
            'dossier': {
                'id': enc.dossier.id,
                'reference': enc.dossier.reference,
                'intitule': enc.dossier.get_intitule(),
                'montant_total_du': float(enc.dossier.get_montant_total_du()),
            },
            'creancier': {
                'id': enc.dossier.creancier.id,
                'nom': enc.dossier.creancier.nom,
                'taux_commission': float(enc.dossier.creancier.taux_commission),
            } if enc.dossier.creancier else None,
            'montant': float(enc.montant),
            'date_encaissement': enc.date_encaissement.isoformat(),
            'date_valeur': enc.date_valeur.isoformat() if enc.date_valeur else None,
            'mode_paiement': enc.mode_paiement,
            'mode_paiement_display': enc.get_mode_paiement_display(),
            'payeur_nom': enc.payeur_nom,
            'payeur_telephone': enc.payeur_telephone,
            'payeur_qualite': enc.payeur_qualite,
            'reference_paiement': enc.reference_paiement,
            'banque_emettrice': enc.banque_emettrice,
            'statut': enc.statut,
            'statut_display': enc.get_statut_display(),
            'date_validation': enc.date_validation.isoformat() if enc.date_validation else None,
            'cumul_encaisse_avant': float(enc.cumul_encaisse_avant),
            'cumul_encaisse_apres': float(enc.cumul_encaisse_apres),
            'solde_restant': float(enc.solde_restant),
            'montant_a_reverser': float(enc.montant_a_reverser),
            'reversement_statut': enc.reversement_statut,
            'observations': enc.observations,
            'imputations': imputations,
            'date_creation': enc.date_creation.isoformat(),
        }

        return JsonResponse({'success': True, 'encaissement': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_encaissement_valider(request, encaissement_id):
    """API pour valider un encaissement"""
    try:
        enc = get_object_or_404(Encaissement, pk=encaissement_id)

        if enc.statut != 'en_attente':
            return JsonResponse({
                'success': False,
                'error': 'Cet encaissement ne peut pas être validé'
            }, status=400)

        # Simuler un utilisateur (en production, utiliser request.user)
        utilisateur = Utilisateur.objects.first()
        enc.valider(utilisateur)

        return JsonResponse({
            'success': True,
            'message': f'Encaissement {enc.reference} validé avec succès',
            'cumul_encaisse_apres': float(enc.cumul_encaisse_apres),
            'solde_restant': float(enc.solde_restant),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_encaissement_annuler(request, encaissement_id):
    """API pour annuler un encaissement"""
    try:
        data = json.loads(request.body)
        enc = get_object_or_404(Encaissement, pk=encaissement_id)

        if enc.statut == 'annule':
            return JsonResponse({
                'success': False,
                'error': 'Cet encaissement est déjà annulé'
            }, status=400)

        motif = data.get('motif', '')
        enc.annuler(motif)

        return JsonResponse({
            'success': True,
            'message': f'Encaissement {enc.reference} annulé'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_encaissements_historique_dossier(request, dossier_id):
    """API pour l'historique des encaissements d'un dossier avec cumuls"""
    try:
        dossier = get_object_or_404(Dossier, pk=dossier_id)

        encaissements = dossier.encaissements.filter(
            statut='valide'
        ).order_by('date_encaissement', 'date_creation')

        data = []
        cumul = 0
        for enc in encaissements:
            cumul += enc.montant
            data.append({
                'id': enc.id,
                'reference': enc.reference,
                'date_encaissement': enc.date_encaissement.isoformat(),
                'montant': float(enc.montant),
                'mode_paiement': enc.get_mode_paiement_display(),
                'payeur_nom': enc.payeur_nom,
                'cumul_progressif': float(cumul),
                'solde_restant': float(dossier.get_montant_total_du() - cumul),
                'imputations': [
                    {
                        'type': imp.get_type_imputation_display(),
                        'montant': float(imp.montant)
                    }
                    for imp in enc.imputations.all()
                ]
            })

        return JsonResponse({
            'success': True,
            'dossier': {
                'reference': dossier.reference,
                'montant_total_du': float(dossier.get_montant_total_du()),
                'total_encaisse': float(dossier.get_total_encaisse()),
                'solde_restant': float(dossier.get_solde_restant()),
                'taux_recouvrement': round(dossier.get_taux_recouvrement(), 2),
            },
            'encaissements': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_encaissements_export(request):
    """API pour exporter les encaissements en CSV"""
    try:
        # Filtres
        dossier_id = request.GET.get('dossier')
        creancier_id = request.GET.get('creancier')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')

        encaissements_qs = Encaissement.objects.select_related(
            'dossier', 'dossier__creancier'
        ).filter(statut='valide')

        if dossier_id:
            encaissements_qs = encaissements_qs.filter(dossier_id=dossier_id)
        if creancier_id:
            encaissements_qs = encaissements_qs.filter(dossier__creancier_id=creancier_id)
        if date_debut:
            encaissements_qs = encaissements_qs.filter(date_encaissement__gte=date_debut)
        if date_fin:
            encaissements_qs = encaissements_qs.filter(date_encaissement__lte=date_fin)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="encaissements.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'Référence', 'Date', 'Dossier', 'Créancier', 'Montant',
            'Mode paiement', 'Payeur', 'Cumul', 'Solde restant',
            'Montant à reverser', 'Statut reversement'
        ])

        for enc in encaissements_qs.order_by('date_encaissement'):
            writer.writerow([
                enc.reference,
                enc.date_encaissement.strftime('%d/%m/%Y'),
                enc.dossier.reference,
                enc.dossier.creancier.nom if enc.dossier.creancier else '',
                enc.montant,
                enc.get_mode_paiement_display(),
                enc.payeur_nom,
                enc.cumul_encaisse_apres,
                enc.solde_restant,
                enc.montant_a_reverser,
                enc.reversement_statut,
            ])

        return response

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API REVERSEMENTS
# ============================================

def reversements(request):
    """Vue liste des reversements"""
    context = get_default_context(request)
    context['active_module'] = 'reversements'
    context['page_title'] = 'Suivi des Reversements'

    # Filtres
    creancier_id = request.GET.get('creancier')
    statut = request.GET.get('statut')

    reversements_qs = Reversement.objects.select_related('creancier')

    if creancier_id:
        reversements_qs = reversements_qs.filter(creancier_id=creancier_id)
    if statut:
        reversements_qs = reversements_qs.filter(statut=statut)

    # Pagination
    paginator = Paginator(reversements_qs.order_by('-date_creation'), 25)
    page = request.GET.get('page', 1)
    reversements_page = paginator.get_page(page)

    context['reversements'] = reversements_page
    context['creanciers'] = Creancier.objects.filter(actif=True)

    return render(request, 'gestion/reversements.html', context)


@require_GET
def api_reversements_liste(request):
    """API pour la liste des reversements"""
    try:
        creancier_id = request.GET.get('creancier')
        statut = request.GET.get('statut')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 25))

        reversements_qs = Reversement.objects.select_related('creancier')

        if creancier_id:
            reversements_qs = reversements_qs.filter(creancier_id=creancier_id)
        if statut:
            reversements_qs = reversements_qs.filter(statut=statut)

        paginator = Paginator(reversements_qs.order_by('-date_creation'), per_page)
        reversements_page = paginator.get_page(page)

        data = []
        for rev in reversements_page:
            data.append({
                'id': rev.id,
                'reference': rev.reference,
                'creancier': {
                    'id': rev.creancier.id,
                    'nom': rev.creancier.nom,
                },
                'montant': float(rev.montant),
                'date_reversement': rev.date_reversement.isoformat() if rev.date_reversement else None,
                'mode_reversement': rev.mode_reversement,
                'mode_display': rev.get_mode_reversement_display(),
                'reference_virement': rev.reference_virement,
                'numero_cheque': rev.numero_cheque,
                'statut': rev.statut,
                'statut_display': rev.get_statut_display(),
                'nb_encaissements': rev.encaissements.count(),
            })

        # Statistiques
        stats = reversements_qs.aggregate(
            total_effectue=Sum('montant', filter=Q(statut='effectue')),
            total_en_attente=Sum('montant', filter=Q(statut='en_attente')),
            nb_effectues=Count('id', filter=Q(statut='effectue')),
            nb_en_attente=Count('id', filter=Q(statut='en_attente')),
        )

        return JsonResponse({
            'success': True,
            'reversements': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            },
            'statistiques': {
                'total_effectue': float(stats['total_effectue'] or 0),
                'total_en_attente': float(stats['total_en_attente'] or 0),
                'nb_effectues': stats['nb_effectues'] or 0,
                'nb_en_attente': stats['nb_en_attente'] or 0,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_reversement_creer(request):
    """API pour créer un reversement"""
    try:
        data = json.loads(request.body)

        creancier = get_object_or_404(Creancier, pk=data.get('creancier_id'))

        reversement = Reversement(
            creancier=creancier,
            montant=Decimal(str(data.get('montant'))),
            mode_reversement=data.get('mode_reversement', 'virement'),
            reference_virement=data.get('reference_virement', ''),
            numero_cheque=data.get('numero_cheque', ''),
            banque=data.get('banque', ''),
            observations=data.get('observations', ''),
        )
        reversement.save()

        # Associer les encaissements si fournis
        encaissement_ids = data.get('encaissement_ids', [])
        if encaissement_ids:
            encaissements = Encaissement.objects.filter(
                id__in=encaissement_ids,
                dossier__creancier=creancier,
                reversement_statut='en_attente'
            )
            reversement.encaissements.set(encaissements)

        return JsonResponse({
            'success': True,
            'reversement_id': reversement.id,
            'reference': reversement.reference,
            'message': f'Reversement {reversement.reference} créé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_reversement_effectuer(request, reversement_id):
    """API pour marquer un reversement comme effectué"""
    try:
        data = json.loads(request.body)
        rev = get_object_or_404(Reversement, pk=reversement_id)

        if rev.statut == 'effectue':
            return JsonResponse({
                'success': False,
                'error': 'Ce reversement est déjà effectué'
            }, status=400)

        # Mettre à jour les informations de paiement
        if 'reference_virement' in data:
            rev.reference_virement = data['reference_virement']
        if 'numero_cheque' in data:
            rev.numero_cheque = data['numero_cheque']
        if 'date_reversement' in data:
            rev.date_reversement = data['date_reversement']

        utilisateur = Utilisateur.objects.first()
        rev.effectuer(utilisateur)

        return JsonResponse({
            'success': True,
            'message': f'Reversement {rev.reference} effectué avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_reversements_encaissements_disponibles(request, creancier_id):
    """API pour lister les encaissements disponibles pour un reversement"""
    try:
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        # Encaissements validés non reversés
        encaissements = Encaissement.objects.filter(
            dossier__creancier=creancier,
            statut='valide',
            reversement_statut='en_attente'
        ).select_related('dossier').order_by('date_encaissement')

        data = []
        total = 0
        for enc in encaissements:
            data.append({
                'id': enc.id,
                'reference': enc.reference,
                'dossier_reference': enc.dossier.reference,
                'date_encaissement': enc.date_encaissement.isoformat(),
                'montant': float(enc.montant),
                'montant_a_reverser': float(enc.montant_a_reverser),
            })
            total += enc.montant_a_reverser

        return JsonResponse({
            'success': True,
            'encaissements': data,
            'total_a_reverser': float(total),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API BASCULEMENT AMIABLE → FORCÉ
# ============================================

@require_POST
def api_dossier_basculer_force(request, dossier_id):
    """API pour basculer un dossier de la phase amiable vers la phase forcée"""
    try:
        data = json.loads(request.body)
        dossier = get_object_or_404(Dossier, pk=dossier_id)

        if dossier.phase == 'force':
            return JsonResponse({
                'success': False,
                'error': 'Ce dossier est déjà en phase forcée'
            }, status=400)

        # Informations du titre exécutoire
        titre_info = None
        if data.get('titre_executoire'):
            titre_info = {
                'type': data['titre_executoire'].get('type', ''),
                'reference': data['titre_executoire'].get('reference', ''),
                'juridiction': data['titre_executoire'].get('juridiction', ''),
                'date': data['titre_executoire'].get('date'),
            }

        # Frais supplémentaires
        frais_supplementaires = None
        if data.get('frais_supplementaires'):
            frais_supplementaires = {
                'depens': Decimal(str(data['frais_supplementaires'].get('depens', 0))),
                'frais_justice': Decimal(str(data['frais_supplementaires'].get('frais_justice', 0))),
            }

        motif = data.get('motif', 'titre_executoire')
        utilisateur = Utilisateur.objects.first()

        basculement = dossier.basculer_vers_force(
            utilisateur=utilisateur,
            motif=motif,
            titre_info=titre_info,
            frais_supplementaires=frais_supplementaires
        )

        return JsonResponse({
            'success': True,
            'message': f'Dossier {dossier.reference} basculé en phase forcée',
            'basculement': {
                'id': basculement.id,
                'date': basculement.date_basculement.isoformat(),
                'nouveau_total': float(basculement.nouveau_total),
                'emoluments_ohada': float(basculement.emoluments_ohada),
            }
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_dossier_historique_basculements(request, dossier_id):
    """API pour l'historique des basculements d'un dossier"""
    try:
        dossier = get_object_or_404(Dossier, pk=dossier_id)

        basculements = []
        for basc in dossier.basculements.all():
            basculements.append({
                'id': basc.id,
                'date_basculement': basc.date_basculement.isoformat(),
                'motif': basc.motif,
                'motif_display': basc.get_motif_display(),
                'motif_detail': basc.motif_detail,
                'titre': {
                    'type': basc.type_titre,
                    'reference': basc.reference_titre,
                    'juridiction': basc.juridiction,
                    'date': basc.date_titre.isoformat() if basc.date_titre else None,
                },
                'etat_creance': {
                    'principal_restant': float(basc.montant_principal_restant),
                    'interets_restant': float(basc.montant_interets_restant),
                    'frais_restant': float(basc.montant_frais_restant),
                    'total_reste_du': float(basc.total_reste_du),
                },
                'nouveaux_frais': {
                    'depens': float(basc.depens),
                    'frais_justice': float(basc.frais_justice),
                    'emoluments_ohada': float(basc.emoluments_ohada),
                },
                'nouveau_total': float(basc.nouveau_total),
                'donnees_phase_amiable': basc.donnees_phase_amiable,
            })

        return JsonResponse({
            'success': True,
            'dossier': {
                'reference': dossier.reference,
                'phase': dossier.phase,
                'phase_display': dossier.get_phase_display(),
            },
            'basculements': basculements
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API POINT CLIENT / TABLEAU DE BORD CREANCIER
# ============================================

@require_GET
def api_creancier_tableau_bord(request, creancier_id):
    """API pour le tableau de bord d'un créancier"""
    try:
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        # Statistiques générales
        dossiers = creancier.dossiers.all()
        nb_dossiers = dossiers.count()
        nb_actifs = dossiers.filter(statut__in=['actif', 'urgent']).count()
        nb_clotures = dossiers.filter(statut='cloture').count()

        total_creances = creancier.get_total_creances()
        total_encaisse = creancier.get_total_encaisse()
        total_reverse = creancier.get_total_reverse()

        taux_recouvrement = (total_encaisse / total_creances * 100) if total_creances > 0 else 0

        # Évolution mensuelle (12 derniers mois)
        evolution = []
        for i in range(11, -1, -1):
            date_debut = (timezone.now() - timedelta(days=30*i)).replace(day=1)
            if i > 0:
                date_fin = (timezone.now() - timedelta(days=30*(i-1))).replace(day=1) - timedelta(days=1)
            else:
                date_fin = timezone.now()

            encaisse_mois = Encaissement.objects.filter(
                dossier__creancier=creancier,
                statut='valide',
                date_encaissement__gte=date_debut,
                date_encaissement__lte=date_fin
            ).aggregate(total=Sum('montant'))['total'] or 0

            evolution.append({
                'mois': date_debut.strftime('%Y-%m'),
                'libelle': date_debut.strftime('%b %Y'),
                'encaisse': float(encaisse_mois),
            })

        # Répartition par statut
        repartition_statut = []
        for statut in ['actif', 'urgent', 'archive', 'cloture']:
            count = dossiers.filter(statut=statut).count()
            montant = dossiers.filter(statut=statut).aggregate(
                total=Sum('montant_creance')
            )['total'] or 0
            repartition_statut.append({
                'statut': statut,
                'nb_dossiers': count,
                'montant': float(montant),
            })

        # Répartition par phase
        repartition_phase = []
        for phase in ['amiable', 'force']:
            count = dossiers.filter(phase=phase).count()
            montant = dossiers.filter(phase=phase).aggregate(
                total=Sum('montant_creance')
            )['total'] or 0
            repartition_phase.append({
                'phase': phase,
                'nb_dossiers': count,
                'montant': float(montant),
            })

        return JsonResponse({
            'success': True,
            'creancier': {
                'id': creancier.id,
                'code': creancier.code,
                'nom': creancier.nom,
            },
            'statistiques': {
                'nb_dossiers': nb_dossiers,
                'nb_actifs': nb_actifs,
                'nb_clotures': nb_clotures,
                'total_creances': float(total_creances),
                'total_encaisse': float(total_encaisse),
                'total_reverse': float(total_reverse),
                'reste_a_encaisser': float(total_creances - total_encaisse),
                'reste_a_reverser': float(total_encaisse - total_reverse),
                'taux_recouvrement': round(taux_recouvrement, 2),
            },
            'evolution_mensuelle': evolution,
            'repartition_statut': repartition_statut,
            'repartition_phase': repartition_phase,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_point_global_generer(request, creancier_id):
    """API pour générer un point global créancier"""
    try:
        data = json.loads(request.body)
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        # Dates de période
        periode_debut = datetime.strptime(data.get('periode_debut'), '%Y-%m-%d').date()
        periode_fin = datetime.strptime(data.get('periode_fin'), '%Y-%m-%d').date()

        # Filtres optionnels
        filtres = data.get('filtres', {})

        # Créer le point global
        utilisateur = Utilisateur.objects.first()

        point = PointGlobalCreancier(
            creancier=creancier,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            filtres=filtres,
            genere_par=utilisateur,
        )
        point.save()

        # Générer les données
        point.generer_donnees()

        return JsonResponse({
            'success': True,
            'point_id': point.id,
            'message': f'Point global généré pour {creancier.nom}',
            'resume': {
                'nb_dossiers': point.nb_dossiers_total,
                'total_creances': float(point.montant_total_creances),
                'total_encaisse': float(point.montant_total_encaisse),
                'taux_recouvrement': float(point.taux_recouvrement),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_point_global_detail(request, point_id):
    """API pour le détail d'un point global"""
    try:
        point = get_object_or_404(
            PointGlobalCreancier.objects.select_related('creancier'),
            pk=point_id
        )

        return JsonResponse({
            'success': True,
            'point': {
                'id': point.id,
                'creancier': {
                    'id': point.creancier.id,
                    'nom': point.creancier.nom,
                },
                'date_generation': point.date_generation.isoformat(),
                'periode_debut': point.periode_debut.isoformat(),
                'periode_fin': point.periode_fin.isoformat(),
                'filtres': point.filtres,
                'statistiques': {
                    'nb_dossiers_total': point.nb_dossiers_total,
                    'nb_dossiers_actifs': point.nb_dossiers_actifs,
                    'nb_dossiers_clotures': point.nb_dossiers_clotures,
                    'montant_total_creances': float(point.montant_total_creances),
                    'montant_total_encaisse': float(point.montant_total_encaisse),
                    'montant_total_reverse': float(point.montant_total_reverse),
                    'montant_reste_a_encaisser': float(point.montant_reste_a_encaisser),
                    'montant_reste_a_reverser': float(point.montant_reste_a_reverser),
                    'taux_recouvrement': float(point.taux_recouvrement),
                },
                'donnees_detaillees': point.donnees_detaillees,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_point_global_export_excel(request, point_id):
    """API pour exporter un point global en CSV (format Excel)"""
    try:
        point = get_object_or_404(PointGlobalCreancier, pk=point_id)

        response = HttpResponse(content_type='text/csv')
        filename = f"point_{point.creancier.code}_{point.date_generation.strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, delimiter=';')

        # En-tête
        writer.writerow([f'POINT GLOBAL - {point.creancier.nom}'])
        writer.writerow([f'Période: {point.periode_debut} au {point.periode_fin}'])
        writer.writerow([f'Généré le: {point.date_generation.strftime("%d/%m/%Y %H:%M")}'])
        writer.writerow([])

        # Résumé
        writer.writerow(['RÉSUMÉ'])
        writer.writerow(['Nombre de dossiers', point.nb_dossiers_total])
        writer.writerow(['Dossiers actifs', point.nb_dossiers_actifs])
        writer.writerow(['Total créances', f'{point.montant_total_creances:,.0f} FCFA'])
        writer.writerow(['Total encaissé', f'{point.montant_total_encaisse:,.0f} FCFA'])
        writer.writerow(['Total reversé', f'{point.montant_total_reverse:,.0f} FCFA'])
        writer.writerow(['Taux de recouvrement', f'{point.taux_recouvrement:.2f}%'])
        writer.writerow([])

        # Détail par dossier
        writer.writerow(['DÉTAIL PAR DOSSIER'])
        writer.writerow([
            'Référence', 'Intitulé', 'Statut', 'Montant créance',
            'Total encaissé', 'Solde restant', 'Nb encaissements', 'Dernier encaissement'
        ])

        for dossier in point.donnees_detaillees.get('dossiers', []):
            writer.writerow([
                dossier['reference'],
                dossier['intitule'],
                dossier['statut'],
                f"{dossier['montant_creance']:,.0f}",
                f"{dossier['total_encaisse']:,.0f}",
                f"{dossier['solde_restant']:,.0f}",
                dossier['nb_encaissements'],
                dossier['dernier_encaissement'] or '',
            ])

        return response

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API ENVOI AUTOMATIQUE
# ============================================

@require_POST
def api_envoi_automatique_configurer(request, creancier_id):
    """API pour configurer l'envoi automatique de points"""
    try:
        data = json.loads(request.body)
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        # Récupérer ou créer la configuration
        envoi, created = EnvoiAutomatiquePoint.objects.get_or_create(
            creancier=creancier,
            defaults={'frequence': 'mensuel'}
        )

        # Mettre à jour la configuration
        envoi.frequence = data.get('frequence', envoi.frequence)
        envoi.jour_envoi = data.get('jour_envoi', envoi.jour_envoi)
        envoi.heure_envoi = data.get('heure_envoi', envoi.heure_envoi)
        envoi.destinataires = data.get('destinataires', envoi.destinataires)
        envoi.copie_gestionnaire = data.get('copie_gestionnaire', envoi.copie_gestionnaire)
        envoi.filtres_point = data.get('filtres', envoi.filtres_point)
        envoi.actif = data.get('actif', envoi.actif)
        envoi.save()

        # Calculer le prochain envoi
        envoi.calculer_prochain_envoi()

        return JsonResponse({
            'success': True,
            'message': 'Configuration d\'envoi automatique mise à jour',
            'prochain_envoi': envoi.prochain_envoi.isoformat() if envoi.prochain_envoi else None,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_envoi_automatique_historique(request, creancier_id):
    """API pour l'historique des envois automatiques"""
    try:
        creancier = get_object_or_404(Creancier, pk=creancier_id)

        envois = EnvoiAutomatiquePoint.objects.filter(creancier=creancier)

        data = []
        for envoi in envois:
            historique = []
            for h in envoi.historique.all()[:10]:
                historique.append({
                    'date_envoi': h.date_envoi.isoformat(),
                    'statut': h.statut,
                    'destinataires_envoyes': h.destinataires_envoyes,
                    'destinataires_echec': h.destinataires_echec,
                    'message_erreur': h.message_erreur,
                })

            data.append({
                'id': envoi.id,
                'frequence': envoi.frequence,
                'frequence_display': envoi.get_frequence_display(),
                'jour_envoi': envoi.jour_envoi,
                'heure_envoi': str(envoi.heure_envoi),
                'destinataires': envoi.destinataires,
                'actif': envoi.actif,
                'dernier_envoi': envoi.dernier_envoi.isoformat() if envoi.dernier_envoi else None,
                'prochain_envoi': envoi.prochain_envoi.isoformat() if envoi.prochain_envoi else None,
                'nb_envois_total': envoi.nb_envois_total,
                'historique': historique,
            })

        return JsonResponse({
            'success': True,
            'envois_automatiques': data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# MÉMOIRES DE CÉDULES - STRUCTURE HIÉRARCHIQUE
# ============================================

def memoires(request):
    """Vue principale du module Mémoires de Cédules"""
    context = get_default_context(request)
    context['active_module'] = 'facturation'
    context['page_title'] = 'Mémoires de Cédules'

    tab = request.GET.get('tab', 'liste')
    memoire_id = request.GET.get('memoire_id')
    affaire_id = request.GET.get('affaire_id')

    # Charger les mémoires depuis la base de données
    memoires_qs = Memoire.objects.all().select_related(
        'huissier', 'autorite_requerante', 'cree_par'
    ).prefetch_related('affaires').order_by('-annee', '-mois', '-numero')

    # Huissiers pour le formulaire
    huissiers = Collaborateur.objects.filter(role='huissier', actif=True)
    autorites = AutoriteRequerante.objects.filter(actif=True)

    # Mois pour les sélecteurs
    mois_noms = [
        {'id': 1, 'nom': 'Janvier'}, {'id': 2, 'nom': 'Février'}, {'id': 3, 'nom': 'Mars'},
        {'id': 4, 'nom': 'Avril'}, {'id': 5, 'nom': 'Mai'}, {'id': 6, 'nom': 'Juin'},
        {'id': 7, 'nom': 'Juillet'}, {'id': 8, 'nom': 'Août'}, {'id': 9, 'nom': 'Septembre'},
        {'id': 10, 'nom': 'Octobre'}, {'id': 11, 'nom': 'Novembre'}, {'id': 12, 'nom': 'Décembre'},
    ]

    # Types d'actes pour le formulaire
    types_actes = ActeDestinataire.TYPE_ACTE_CHOICES

    # Qualités de destinataires
    qualites_destinataire = DestinataireAffaire.QUALITE_CHOICES

    # Types de mission
    types_mission = DestinataireAffaire.TYPE_MISSION_CHOICES

    # Liste des mémoires
    memoires_list = []
    for m in memoires_qs[:50]:
        memoires_list.append({
            'id': m.id,
            'numero': m.numero,
            'mois': m.mois,
            'mois_nom': mois_noms[m.mois - 1]['nom'] if 1 <= m.mois <= 12 else '',
            'annee': m.annee,
            'huissier': m.huissier.nom if m.huissier else '-',
            'autorite': m.autorite_requerante.nom if m.autorite_requerante else '-',
            'nb_affaires': m.get_nb_affaires(),
            'nb_destinataires': m.get_nb_destinataires(),
            'nb_actes': m.get_nb_actes(),
            'montant_total': m.montant_total,
            'statut': m.statut,
            'statut_display': m.get_statut_display(),
        })

    # Détail d'un mémoire si sélectionné
    memoire_detail = None
    affaires_list = []
    if memoire_id:
        try:
            memoire_detail = Memoire.objects.get(pk=memoire_id)
            for affaire in memoire_detail.affaires.all().prefetch_related('destinataires__actes'):
                destinataires_list = []
                for dest in affaire.destinataires.all():
                    actes_list = []
                    for acte in dest.actes.all():
                        actes_list.append({
                            'id': acte.id,
                            'date_acte': acte.date_acte.strftime('%d/%m/%Y') if acte.date_acte else '',
                            'type_acte': acte.get_type_acte_display(),
                            'type_acte_code': acte.type_acte,
                            'montant_base': acte.montant_base,
                            'copies_supplementaires': acte.copies_supplementaires,
                            'montant_copies': acte.montant_copies,
                            'roles_pieces_jointes': acte.roles_pieces_jointes,
                            'montant_pieces': acte.montant_pieces,
                            'montant_total': acte.montant_total_acte,
                        })

                    destinataires_list.append({
                        'id': dest.id,
                        'nom_complet': dest.get_nom_complet(),
                        'nom': dest.nom,
                        'prenoms': dest.prenoms,
                        'qualite': dest.get_qualite_display(),
                        'qualite_code': dest.qualite,
                        'titre': dest.titre,
                        'adresse': dest.adresse,
                        'localite': dest.localite,
                        'distance_km': dest.distance_km,
                        'type_mission': dest.type_mission,
                        'type_mission_display': dest.get_type_mission_display(),
                        'frais_transport': dest.frais_transport,
                        'frais_mission': dest.frais_mission,
                        'montant_total_actes': dest.montant_total_actes,
                        'montant_total': dest.montant_total_destinataire,
                        'actes': actes_list,
                        'nb_actes': len(actes_list),
                    })

                affaires_list.append({
                    'id': affaire.id,
                    'numero_parquet': affaire.numero_parquet,
                    'intitule': affaire.intitule_affaire,
                    'nature_infraction': affaire.nature_infraction,
                    'date_audience': affaire.date_audience.strftime('%d/%m/%Y') if affaire.date_audience else '',
                    'montant_total_actes': affaire.montant_total_actes,
                    'montant_total_transport': affaire.montant_total_transport,
                    'montant_total_mission': affaire.montant_total_mission,
                    'montant_total': affaire.montant_total_affaire,
                    'destinataires': destinataires_list,
                    'nb_destinataires': len(destinataires_list),
                    'nb_actes': sum(d['nb_actes'] for d in destinataires_list),
                })
        except Memoire.DoesNotExist:
            memoire_detail = None

    context['tabs'] = [
        {'id': 'liste', 'label': 'Liste des mémoires'},
        {'id': 'nouveau', 'label': 'Nouveau mémoire'},
    ]
    context['current_tab'] = tab
    context['memoires_list'] = memoires_list
    context['memoire_detail'] = memoire_detail
    context['affaires_list'] = affaires_list
    context['memoire_id'] = memoire_id
    context['affaire_id'] = affaire_id
    context['huissiers'] = huissiers
    context['autorites'] = autorites
    context['mois_noms'] = mois_noms
    context['types_actes'] = types_actes
    context['qualites_destinataire'] = qualites_destinataire
    context['types_mission'] = types_mission
    context['annee_courante'] = timezone.now().year
    context['mois_courant'] = timezone.now().month

    # Constantes de tarification
    context['tarifs'] = {
        'montant_base_acte': ActeDestinataire.MONTANT_BASE,
        'tarif_copie': ActeDestinataire.TARIF_COPIE_SUPPLEMENTAIRE,
        'tarif_role': ActeDestinataire.TARIF_ROLE_PIECES,
        'tarif_km': DestinataireAffaire.TARIF_KM,
        'seuil_transport': DestinataireAffaire.SEUIL_TRANSPORT_KM,
        'seuil_mission': DestinataireAffaire.SEUIL_MISSION_KM,
        'tarifs_mission': DestinataireAffaire.TARIFS_MISSION,
    }

    return render(request, 'gestion/memoires.html', context)


# API MÉMOIRES DE CÉDULES
@require_POST
def api_memoire_creer(request):
    """API pour créer un nouveau mémoire"""
    try:
        data = json.loads(request.body)

        # Vérifier les données requises
        if not data.get('mois') or not data.get('annee'):
            return JsonResponse({'success': False, 'error': 'Mois et année requis'}, status=400)

        if not data.get('huissier_id'):
            return JsonResponse({'success': False, 'error': 'Huissier requis'}, status=400)

        if not data.get('autorite_id'):
            return JsonResponse({'success': False, 'error': 'Autorité requérante requise'}, status=400)

        huissier = get_object_or_404(Collaborateur, pk=data['huissier_id'])
        autorite = get_object_or_404(AutoriteRequerante, pk=data['autorite_id'])

        # Vérifier l'unicité
        existe = Memoire.objects.filter(
            mois=data['mois'],
            annee=data['annee'],
            huissier=huissier,
            autorite_requerante=autorite
        ).exists()

        if existe:
            return JsonResponse({
                'success': False,
                'error': 'Un mémoire existe déjà pour cette période, cet huissier et cette autorité'
            }, status=400)

        # Créer le mémoire
        utilisateur = Utilisateur.objects.first()
        memoire = Memoire(
            numero=Memoire.generer_numero(),
            mois=data['mois'],
            annee=data['annee'],
            huissier=huissier,
            autorite_requerante=autorite,
            residence_huissier=data.get('residence_huissier', 'Parakou'),
            observations=data.get('observations', ''),
            cree_par=utilisateur,
        )
        memoire.save()

        return JsonResponse({
            'success': True,
            'memoire_id': memoire.id,
            'numero': memoire.numero,
            'message': f'Mémoire N° {memoire.numero} créé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_memoire_supprimer(request):
    """API pour supprimer un mémoire"""
    try:
        data = json.loads(request.body)
        memoire_id = data.get('memoire_id')

        memoire = get_object_or_404(Memoire, pk=memoire_id)

        # Vérifier que le mémoire n'est pas certifié
        if memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de supprimer un mémoire certifié, soumis ou payé'
            }, status=400)

        numero = memoire.numero
        memoire.delete()

        return JsonResponse({
            'success': True,
            'message': f'Mémoire N° {numero} supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_memoire_detail(request, memoire_id):
    """API pour le détail d'un mémoire"""
    try:
        memoire = get_object_or_404(
            Memoire.objects.select_related('huissier', 'autorite_requerante')
            .prefetch_related('affaires__destinataires__actes'),
            pk=memoire_id
        )

        # Construire les données détaillées
        affaires_data = []
        for affaire in memoire.affaires.all():
            destinataires_data = []
            for dest in affaire.destinataires.all():
                actes_data = []
                for acte in dest.actes.all():
                    actes_data.append({
                        'id': acte.id,
                        'date_acte': acte.date_acte.isoformat() if acte.date_acte else None,
                        'type_acte': acte.type_acte,
                        'type_acte_display': acte.get_type_acte_display(),
                        'montant_base': float(acte.montant_base),
                        'copies_supplementaires': acte.copies_supplementaires,
                        'montant_copies': float(acte.montant_copies),
                        'roles_pieces_jointes': acte.roles_pieces_jointes,
                        'montant_pieces': float(acte.montant_pieces),
                        'montant_total': float(acte.montant_total_acte),
                    })

                destinataires_data.append({
                    'id': dest.id,
                    'nom': dest.nom,
                    'prenoms': dest.prenoms,
                    'nom_complet': dest.get_nom_complet(),
                    'qualite': dest.qualite,
                    'qualite_display': dest.get_qualite_display(),
                    'titre': dest.titre,
                    'adresse': dest.adresse,
                    'localite': dest.localite,
                    'distance_km': dest.distance_km,
                    'type_mission': dest.type_mission,
                    'frais_transport': float(dest.frais_transport),
                    'frais_mission': float(dest.frais_mission),
                    'montant_total_actes': float(dest.montant_total_actes),
                    'montant_total': float(dest.montant_total_destinataire),
                    'actes': actes_data,
                })

            affaires_data.append({
                'id': affaire.id,
                'numero_parquet': affaire.numero_parquet,
                'intitule': affaire.intitule_affaire,
                'nature_infraction': affaire.nature_infraction,
                'date_audience': affaire.date_audience.isoformat() if affaire.date_audience else None,
                'montant_total_actes': float(affaire.montant_total_actes),
                'montant_total_transport': float(affaire.montant_total_transport),
                'montant_total_mission': float(affaire.montant_total_mission),
                'montant_total': float(affaire.montant_total_affaire),
                'destinataires': destinataires_data,
            })

        return JsonResponse({
            'success': True,
            'memoire': {
                'id': memoire.id,
                'numero': memoire.numero,
                'mois': memoire.mois,
                'annee': memoire.annee,
                'huissier': {'id': memoire.huissier.id, 'nom': memoire.huissier.nom},
                'autorite': {'id': memoire.autorite_requerante.id, 'nom': memoire.autorite_requerante.nom},
                'residence_huissier': memoire.residence_huissier,
                'montant_total_actes': float(memoire.montant_total_actes),
                'montant_total_transport': float(memoire.montant_total_transport),
                'montant_total_mission': float(memoire.montant_total_mission),
                'montant_total': float(memoire.montant_total),
                'montant_total_lettres': memoire.montant_total_lettres,
                'statut': memoire.statut,
                'statut_display': memoire.get_statut_display(),
                'date_certification': memoire.date_certification.isoformat() if memoire.date_certification else None,
                'lieu_certification': memoire.lieu_certification,
                'affaires': affaires_data,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_memoire_certifier(request, memoire_id):
    """API pour certifier un mémoire"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)

        # Vérifier qu'il y a au moins une affaire
        if not memoire.affaires.exists():
            return JsonResponse({
                'success': False,
                'error': 'Impossible de certifier un mémoire sans affaire'
            }, status=400)

        # Vérifier la cohérence
        alertes = memoire.verifier_coherence()
        alertes_bloquantes = [a for a in alertes if a['type'] in ['doublon_affaire']]

        if alertes_bloquantes:
            return JsonResponse({
                'success': False,
                'error': 'Des erreurs bloquantes empêchent la certification',
                'alertes': alertes_bloquantes
            }, status=400)

        # Certifier
        utilisateur = Utilisateur.objects.first()
        memoire.certifier(utilisateur)

        return JsonResponse({
            'success': True,
            'message': f'Mémoire N° {memoire.numero} certifié avec succès',
            'montant_total': float(memoire.montant_total),
            'montant_total_lettres': memoire.montant_total_lettres,
            'alertes': alertes  # Retourner les alertes non bloquantes
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_memoire_verifier(request, memoire_id):
    """API pour vérifier la cohérence d'un mémoire"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)
        alertes = memoire.verifier_coherence()

        return JsonResponse({
            'success': True,
            'alertes': alertes,
            'nb_alertes': len(alertes),
            'est_valide': len([a for a in alertes if a['type'] in ['doublon_affaire']]) == 0
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# API AFFAIRES
@require_POST
def api_affaire_creer(request, memoire_id):
    """API pour ajouter une affaire à un mémoire"""
    try:
        data = json.loads(request.body)
        memoire = get_object_or_404(Memoire, pk=memoire_id)

        # Vérifier que le mémoire n'est pas certifié
        if memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Vérifier les données requises
        if not data.get('numero_parquet'):
            return JsonResponse({'success': False, 'error': 'Numéro de parquet requis'}, status=400)

        if not data.get('intitule_affaire'):
            return JsonResponse({'success': False, 'error': 'Intitulé de l\'affaire requis'}, status=400)

        # Vérifier l'unicité du numéro de parquet dans le mémoire
        if memoire.affaires.filter(numero_parquet=data['numero_parquet']).exists():
            return JsonResponse({
                'success': False,
                'error': f'L\'affaire {data["numero_parquet"]} existe déjà dans ce mémoire'
            }, status=400)

        # Créer l'affaire
        affaire = AffaireMemoire(
            memoire=memoire,
            numero_parquet=data['numero_parquet'],
            intitule_affaire=data['intitule_affaire'],
            nature_infraction=data.get('nature_infraction', ''),
            date_audience=datetime.strptime(data['date_audience'], '%Y-%m-%d').date() if data.get('date_audience') else None,
            ordre_affichage=memoire.affaires.count(),
        )
        affaire.save()

        return JsonResponse({
            'success': True,
            'affaire_id': affaire.id,
            'message': f'Affaire {affaire.numero_parquet} ajoutée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_affaire_modifier(request, affaire_id):
    """API pour modifier une affaire"""
    try:
        data = json.loads(request.body)
        affaire = get_object_or_404(AffaireMemoire, pk=affaire_id)

        # Vérifier que le mémoire n'est pas certifié
        if affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Mettre à jour
        if 'numero_parquet' in data:
            # Vérifier l'unicité
            existe = affaire.memoire.affaires.exclude(pk=affaire.pk).filter(
                numero_parquet=data['numero_parquet']
            ).exists()
            if existe:
                return JsonResponse({
                    'success': False,
                    'error': f'L\'affaire {data["numero_parquet"]} existe déjà dans ce mémoire'
                }, status=400)
            affaire.numero_parquet = data['numero_parquet']

        if 'intitule_affaire' in data:
            affaire.intitule_affaire = data['intitule_affaire']
        if 'nature_infraction' in data:
            affaire.nature_infraction = data['nature_infraction']
        if 'date_audience' in data:
            affaire.date_audience = datetime.strptime(data['date_audience'], '%Y-%m-%d').date() if data['date_audience'] else None

        affaire.save()

        return JsonResponse({
            'success': True,
            'message': 'Affaire modifiée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_affaire_supprimer(request, affaire_id):
    """API pour supprimer une affaire"""
    try:
        affaire = get_object_or_404(AffaireMemoire, pk=affaire_id)

        # Vérifier que le mémoire n'est pas certifié
        if affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        numero = affaire.numero_parquet
        memoire = affaire.memoire
        affaire.delete()

        # Recalculer les totaux du mémoire
        memoire.calculer_totaux()

        return JsonResponse({
            'success': True,
            'message': f'Affaire {numero} supprimée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# API DESTINATAIRES
@require_POST
def api_destinataire_creer(request, affaire_id):
    """API pour ajouter un destinataire à une affaire"""
    try:
        data = json.loads(request.body)
        affaire = get_object_or_404(AffaireMemoire, pk=affaire_id)

        # Vérifier que le mémoire n'est pas certifié
        if affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Vérifier les données requises
        if not data.get('nom'):
            return JsonResponse({'success': False, 'error': 'Nom du destinataire requis'}, status=400)

        if not data.get('qualite'):
            return JsonResponse({'success': False, 'error': 'Qualité du destinataire requise'}, status=400)

        if not data.get('localite'):
            return JsonResponse({'success': False, 'error': 'Localité requise'}, status=400)

        # Créer le destinataire
        destinataire = DestinataireAffaire(
            affaire=affaire,
            nom=data['nom'],
            prenoms=data.get('prenoms', ''),
            raison_sociale=data.get('raison_sociale', ''),
            qualite=data['qualite'],
            titre=data.get('titre', ''),
            adresse=data.get('adresse', ''),
            localite=data['localite'],
            distance_km=data.get('distance_km', 0),
            observations=data.get('observations', ''),
            ordre_affichage=affaire.destinataires.count(),
        )

        # Calculer les frais automatiquement
        destinataire.type_mission = destinataire.determiner_type_mission()
        destinataire.frais_transport = destinataire.calculer_frais_transport()
        destinataire.frais_mission = destinataire.calculer_frais_mission()

        destinataire.save()

        return JsonResponse({
            'success': True,
            'destinataire_id': destinataire.id,
            'message': f'Destinataire {destinataire.get_nom_complet()} ajouté avec succès',
            'frais_transport': float(destinataire.frais_transport),
            'frais_mission': float(destinataire.frais_mission),
            'type_mission': destinataire.type_mission,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_destinataire_modifier(request, destinataire_id):
    """API pour modifier un destinataire"""
    try:
        data = json.loads(request.body)
        destinataire = get_object_or_404(DestinataireAffaire, pk=destinataire_id)

        # Vérifier que le mémoire n'est pas certifié
        if destinataire.affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Mettre à jour les champs
        if 'nom' in data:
            destinataire.nom = data['nom']
        if 'prenoms' in data:
            destinataire.prenoms = data['prenoms']
        if 'raison_sociale' in data:
            destinataire.raison_sociale = data['raison_sociale']
        if 'qualite' in data:
            destinataire.qualite = data['qualite']
        if 'titre' in data:
            destinataire.titre = data['titre']
        if 'adresse' in data:
            destinataire.adresse = data['adresse']
        if 'localite' in data:
            destinataire.localite = data['localite']
        if 'distance_km' in data:
            destinataire.distance_km = data['distance_km']
            # Recalculer les frais
            destinataire.type_mission = destinataire.determiner_type_mission()
            destinataire.frais_transport = destinataire.calculer_frais_transport()
            destinataire.frais_mission = destinataire.calculer_frais_mission()
        if 'type_mission' in data:
            destinataire.type_mission = data['type_mission']
            destinataire.frais_mission = destinataire.calculer_frais_mission()
        if 'observations' in data:
            destinataire.observations = data['observations']

        destinataire.save()
        destinataire.calculer_totaux()

        return JsonResponse({
            'success': True,
            'message': 'Destinataire modifié avec succès',
            'frais_transport': float(destinataire.frais_transport),
            'frais_mission': float(destinataire.frais_mission),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_destinataire_supprimer(request, destinataire_id):
    """API pour supprimer un destinataire"""
    try:
        destinataire = get_object_or_404(DestinataireAffaire, pk=destinataire_id)

        # Vérifier que le mémoire n'est pas certifié
        if destinataire.affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        nom = destinataire.get_nom_complet()
        affaire = destinataire.affaire
        destinataire.delete()

        # Recalculer les totaux
        affaire.calculer_totaux()

        return JsonResponse({
            'success': True,
            'message': f'Destinataire {nom} supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# API ACTES
@require_POST
def api_acte_creer(request, destinataire_id):
    """API pour ajouter un acte à un destinataire"""
    try:
        data = json.loads(request.body)
        destinataire = get_object_or_404(DestinataireAffaire, pk=destinataire_id)

        # Vérifier que le mémoire n'est pas certifié
        if destinataire.affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Vérifier les données requises
        if not data.get('date_acte'):
            return JsonResponse({'success': False, 'error': 'Date de l\'acte requise'}, status=400)

        if not data.get('type_acte'):
            return JsonResponse({'success': False, 'error': 'Type d\'acte requis'}, status=400)

        # Créer l'acte
        acte = ActeDestinataire(
            destinataire=destinataire,
            date_acte=datetime.strptime(data['date_acte'], '%Y-%m-%d').date(),
            type_acte=data['type_acte'],
            type_acte_autre=data.get('type_acte_autre', ''),
            copies_supplementaires=data.get('copies_supplementaires', 0),
            roles_pieces_jointes=data.get('roles_pieces_jointes', 0),
            observations=data.get('observations', ''),
        )
        # Les montants seront calculés automatiquement dans save()
        acte.save()

        return JsonResponse({
            'success': True,
            'acte_id': acte.id,
            'message': f'Acte ajouté avec succès',
            'montant_total': float(acte.montant_total_acte),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_acte_modifier(request, acte_id):
    """API pour modifier un acte"""
    try:
        data = json.loads(request.body)
        acte = get_object_or_404(ActeDestinataire, pk=acte_id)

        # Vérifier que le mémoire n'est pas certifié
        if acte.destinataire.affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        # Mettre à jour les champs
        if 'date_acte' in data:
            acte.date_acte = datetime.strptime(data['date_acte'], '%Y-%m-%d').date()
        if 'type_acte' in data:
            acte.type_acte = data['type_acte']
        if 'type_acte_autre' in data:
            acte.type_acte_autre = data['type_acte_autre']
        if 'copies_supplementaires' in data:
            acte.copies_supplementaires = data['copies_supplementaires']
        if 'roles_pieces_jointes' in data:
            acte.roles_pieces_jointes = data['roles_pieces_jointes']
        if 'observations' in data:
            acte.observations = data['observations']

        # Les montants seront recalculés automatiquement dans save()
        acte.save()

        return JsonResponse({
            'success': True,
            'message': 'Acte modifié avec succès',
            'montant_total': float(acte.montant_total_acte),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_acte_supprimer(request, acte_id):
    """API pour supprimer un acte"""
    try:
        acte = get_object_or_404(ActeDestinataire, pk=acte_id)

        # Vérifier que le mémoire n'est pas certifié
        if acte.destinataire.affaire.memoire.statut in ['certifie', 'soumis', 'paye']:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de modifier un mémoire certifié'
            }, status=400)

        destinataire = acte.destinataire
        acte.delete()

        # Recalculer les totaux
        destinataire.calculer_totaux()

        return JsonResponse({
            'success': True,
            'message': 'Acte supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# API AUTORITÉS REQUÉRANTES
@require_GET
def api_autorites_liste(request):
    """API pour la liste des autorités requérantes"""
    try:
        autorites = AutoriteRequerante.objects.filter(actif=True).order_by('nom')

        data = [{
            'id': a.id,
            'code': a.code,
            'nom': a.nom,
            'type_juridiction': a.type_juridiction,
            'ville': a.ville,
        } for a in autorites]

        return JsonResponse({
            'success': True,
            'autorites': data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_autorite_creer(request):
    """API pour créer une autorité requérante"""
    try:
        data = json.loads(request.body)

        if not data.get('code') or not data.get('nom'):
            return JsonResponse({'success': False, 'error': 'Code et nom requis'}, status=400)

        # Vérifier l'unicité
        if AutoriteRequerante.objects.filter(code=data['code']).exists():
            return JsonResponse({'success': False, 'error': 'Ce code existe déjà'}, status=400)

        autorite = AutoriteRequerante(
            code=data['code'],
            nom=data['nom'],
            type_juridiction=data.get('type_juridiction', ''),
            adresse=data.get('adresse', ''),
            ville=data.get('ville', ''),
            telephone=data.get('telephone', ''),
            email=data.get('email', ''),
        )
        autorite.save()

        return JsonResponse({
            'success': True,
            'autorite_id': autorite.id,
            'message': f'Autorité {autorite.nom} créée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# API EXPORT PDF MÉMOIRE
@require_GET
def api_memoire_export_pdf(request, memoire_id):
    """API pour exporter un mémoire en format texte (prévisualisation PDF)"""
    try:
        memoire = get_object_or_404(
            Memoire.objects.select_related('huissier', 'autorite_requerante')
            .prefetch_related('affaires__destinataires__actes'),
            pk=memoire_id
        )

        mois_noms = [
            '', 'JANVIER', 'FÉVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN',
            'JUILLET', 'AOÛT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DÉCEMBRE'
        ]

        # Construire le contenu du mémoire
        contenu = []
        contenu.append('=' * 70)
        contenu.append(f'MÉMOIRE N° {memoire.numero} - {mois_noms[memoire.mois]} {memoire.annee}')
        contenu.append('=' * 70)
        contenu.append(f'Huissier: {memoire.huissier.nom if memoire.huissier else "-"}')
        contenu.append(f'Autorité requérante: {memoire.autorite_requerante.nom if memoire.autorite_requerante else "-"}')
        contenu.append('')

        for affaire in memoire.affaires.all():
            contenu.append('-' * 70)
            contenu.append(f'AFFAIRE: {affaire.numero_parquet} - {affaire.intitule_affaire}')
            contenu.append('-' * 70)

            for dest in affaire.destinataires.all():
                contenu.append(f'\n  {dest.get_nom_complet()}, {dest.get_qualite_display()}, {dest.localite}')
                if dest.distance_km > 0:
                    contenu.append(f'    Distance: {dest.distance_km} km')

                for acte in dest.actes.all():
                    contenu.append(f'    • {acte.get_type_acte_display()} ({acte.date_acte.strftime("%d/%m/%Y")}).......... {acte.montant_base:,.0f} F')
                    if acte.copies_supplementaires > 0:
                        contenu.append(f'      + Copies supplémentaires ({acte.copies_supplementaires}).......... {acte.montant_copies:,.0f} F')
                    if acte.roles_pieces_jointes > 0:
                        contenu.append(f'      + Pièces jointes ({acte.roles_pieces_jointes} rôles).......... {acte.montant_pieces:,.0f} F')

                if dest.frais_transport > 0:
                    contenu.append(f'    • Transport ({dest.distance_km} km × 140 F × 2).......... {dest.frais_transport:,.0f} F')
                if dest.frais_mission > 0:
                    contenu.append(f'    • Mission ({dest.get_type_mission_display()}).......... {dest.frais_mission:,.0f} F')

                contenu.append(f'                                           Sous-total: {dest.montant_total_destinataire:,.0f} F')

            contenu.append(f'\n                               TOTAL AFFAIRE: {affaire.montant_total_affaire:,.0f} F')

        contenu.append('\n' + '=' * 70)
        contenu.append('RÉCAPITULATIF')
        contenu.append('-' * 70)
        for affaire in memoire.affaires.all():
            contenu.append(f'Affaire {affaire.numero_parquet}.......... {affaire.montant_total_affaire:,.0f} F')
        contenu.append('=' * 70)
        contenu.append(f'TOTAL GÉNÉRAL.......... {memoire.montant_total:,.0f} F')
        contenu.append('=' * 70)
        contenu.append('')
        contenu.append(f'Arrêté le présent mémoire à la somme de:')
        contenu.append(memoire.montant_total_lettres or Memoire.nombre_en_lettres(memoire.montant_total))
        contenu.append('')
        contenu.append('Certifié sincère et véritable')
        contenu.append(f'Fait à {memoire.lieu_certification}, le {memoire.date_certification.strftime("%d/%m/%Y") if memoire.date_certification else timezone.now().strftime("%d/%m/%Y")}')
        contenu.append('')
        contenu.append('[Signature]')
        contenu.append(f'                                    {memoire.huissier.nom if memoire.huissier else "Maître [NOM]"}')
        contenu.append('                                    Huissier de Justice')

        response = HttpResponse(content_type='text/plain; charset=utf-8')
        filename = f"memoire_{memoire.numero}_{memoire.mois}_{memoire.annee}.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\n'.join(contenu))

        return response

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# API TABLEAU DE BORD AVANCÉ
# ============================================

@require_GET
def api_dashboard_data(request):
    """
    API pour récupérer toutes les données du tableau de bord avancé.
    Agrège les données de tous les modules de l'application.
    """
    try:
        today = timezone.now().date()
        now = timezone.now()
        debut_mois = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        debut_jour = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Importer les modèles des autres apps si disponibles
        try:
            from agenda.models import RendezVous, Tache, Notification
            has_agenda = True
        except ImportError:
            has_agenda = False

        try:
            from rh.models import Employe, Conge, Contrat
            has_rh = True
        except ImportError:
            has_rh = False

        try:
            from comptabilite.models import EcritureComptable, ExerciceComptable
            has_compta = True
        except ImportError:
            has_compta = False

        # ===== SECTION 1: KPIs RÉSUMÉ =====
        dossiers_actifs = Dossier.objects.filter(statut__in=['actif', 'urgent']).count()
        dossiers_nouveaux_mois = Dossier.objects.filter(date_ouverture__gte=debut_mois.date()).count()

        # Solde trésorerie (somme des encaissements - décaissements)
        total_encaissements = Encaissement.objects.filter(
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

        total_reversements = Reversement.objects.filter(
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

        solde_tresorerie = total_encaissements - total_reversements

        # Encaissements du jour
        encaissements_jour = Encaissement.objects.filter(
            date_encaissement__date=today,
            statut='valide'
        ).aggregate(
            total=Sum('montant'),
            count=Count('id')
        )

        # Alertes urgentes
        dossiers_urgents = Dossier.objects.filter(statut='urgent').count()
        reversements_attente = Reversement.objects.filter(statut='en_attente').count()

        # ===== SECTION 2: DOSSIERS =====
        dossiers_en_cours = Dossier.objects.filter(statut='actif').count()
        dossiers_en_attente = Dossier.objects.filter(statut='archive').count()
        dossiers_clotures_mois = Dossier.objects.filter(
            statut='cloture',
            date_ouverture__gte=debut_mois.date()
        ).count()

        # Répartition par type
        repartition_types = list(Dossier.objects.filter(
            statut__in=['actif', 'urgent']
        ).values('type_dossier').annotate(
            count=Count('id')
        ).order_by('-count'))

        # Derniers dossiers ouverts
        derniers_dossiers = list(Dossier.objects.order_by('-date_ouverture')[:5].values(
            'reference', 'type_dossier', 'date_ouverture', 'statut'
        ))

        # Dossiers sans activité depuis 30 jours
        date_30j = today - timedelta(days=30)
        dossiers_sans_activite = Dossier.objects.filter(
            statut='actif',
            date_ouverture__lt=date_30j
        ).count()

        # ===== SECTION 3: AGENDA =====
        agenda_data = {
            'rendez_vous': [],
            'taches': [],
            'taches_retard': 0
        }

        if has_agenda:
            # RDV du jour
            rdvs_jour = RendezVous.objects.filter(
                date_debut__date=today
            ).order_by('date_debut')[:10]

            agenda_data['rendez_vous'] = [{
                'heure': rdv.date_debut.strftime('%H:%M'),
                'titre': rdv.titre,
                'type': rdv.type_rdv,
                'dossier_ref': rdv.dossier.reference if rdv.dossier else None,
                'lieu': rdv.lieu
            } for rdv in rdvs_jour]

            # Tâches du jour
            taches_jour = Tache.objects.filter(
                date_echeance__date=today
            ).order_by('priorite', 'date_echeance')[:10]

            agenda_data['taches'] = [{
                'titre': t.titre,
                'priorite': t.priorite,
                'statut': t.statut,
                'dossier_ref': t.dossier.reference if t.dossier else None
            } for t in taches_jour]

            # Tâches en retard
            agenda_data['taches_retard'] = Tache.objects.filter(
                date_echeance__lt=today,
                statut__in=['a_faire', 'en_cours']
            ).count()

        # ===== SECTION 4: TRÉSORERIE =====
        # Soldes des caisses (simulé - à adapter avec un modèle Caisse si existant)
        caisses = [
            {'nom': 'Caisse principale Parakou', 'solde': float(solde_tresorerie * Decimal('0.6'))},
            {'nom': 'Caisse secondaire', 'solde': float(solde_tresorerie * Decimal('0.25'))},
            {'nom': 'Compte séquestre', 'solde': float(solde_tresorerie * Decimal('0.15'))},
        ]

        # Décaissements du jour
        decaissements_jour = Reversement.objects.filter(
            date_reversement__date=today,
            statut='effectue'
        ).aggregate(
            total=Sum('montant'),
            count=Count('id')
        )

        # Décaissements en attente d'approbation
        decaissements_attente = Reversement.objects.filter(
            statut='en_attente'
        ).count()

        tresorerie_data = {
            'caisses': caisses,
            'total': float(solde_tresorerie),
            'encaissements_jour': {
                'montant': float(encaissements_jour['total'] or 0),
                'count': encaissements_jour['count'] or 0
            },
            'decaissements_jour': {
                'montant': float(decaissements_jour['total'] or 0),
                'count': decaissements_jour['count'] or 0
            },
            'solde_net_jour': float((encaissements_jour['total'] or 0) - (decaissements_jour['total'] or 0)),
            'decaissements_attente': decaissements_attente
        }

        # ===== SECTION 5: FACTURATION =====
        factures_mois = Facture.objects.filter(date_emission__gte=debut_mois)

        factures_emises = factures_mois.aggregate(
            count=Count('id'),
            total=Sum('montant_ttc')
        )

        factures_payees = factures_mois.filter(statut='payee').aggregate(
            count=Count('id'),
            total=Sum('montant_ttc')
        )

        factures_attente = factures_mois.filter(statut='attente').aggregate(
            count=Count('id'),
            total=Sum('montant_ttc')
        )

        # Factures impayées > 30 jours
        date_30j_ago = today - timedelta(days=30)
        factures_impayees = list(Facture.objects.filter(
            statut='attente',
            date_emission__lt=date_30j_ago
        ).values('numero', 'montant_ttc', 'date_emission')[:5])

        for f in factures_impayees:
            f['jours'] = (today - f['date_emission']).days
            f['montant_ttc'] = float(f['montant_ttc']) if f['montant_ttc'] else 0

        # Taux de recouvrement
        taux_recouvrement = 0
        if factures_emises['total'] and factures_emises['total'] > 0:
            taux_recouvrement = int((factures_payees['total'] or 0) / factures_emises['total'] * 100)

        facturation_data = {
            'emises': {
                'count': factures_emises['count'] or 0,
                'total': float(factures_emises['total'] or 0)
            },
            'payees': {
                'count': factures_payees['count'] or 0,
                'total': float(factures_payees['total'] or 0)
            },
            'attente': {
                'count': factures_attente['count'] or 0,
                'total': float(factures_attente['total'] or 0)
            },
            'impayees_30j': factures_impayees,
            'taux_recouvrement': taux_recouvrement
        }

        # ===== SECTION 6: COMPTABILITÉ =====
        compta_data = {
            'chiffre_affaires': 0,
            'charges': 0,
            'resultat_net': 0,
            'evolution_ca': [],
            'tva_a_declarer': 0
        }

        if has_compta:
            # Calcul du CA, charges et résultat (à adapter selon les comptes OHADA)
            pass
        else:
            # Données simulées basées sur les factures
            ca_mois = float(factures_payees['total'] or 0)
            compta_data['chiffre_affaires'] = ca_mois
            compta_data['charges'] = ca_mois * 0.45  # Estimation
            compta_data['resultat_net'] = ca_mois - compta_data['charges']
            compta_data['tva_a_declarer'] = ca_mois * 0.18 * 0.3  # TVA collectée estimée

        # ===== SECTION 7: RECOUVREMENT =====
        # Dossiers amiables
        dossiers_amiables = Dossier.objects.filter(
            phase='amiable',
            statut__in=['actif', 'urgent']
        ).aggregate(
            count=Count('id'),
            total=Sum('montant_creance')
        )

        # Dossiers forcés
        dossiers_forces = Dossier.objects.filter(
            phase='force',
            statut__in=['actif', 'urgent']
        ).aggregate(
            count=Count('id'),
            total=Sum('montant_creance')
        )

        # Encaissements du mois
        encaissements_mois = Encaissement.objects.filter(
            date_encaissement__gte=debut_mois,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

        # Reversements du mois
        reversements_mois = Reversement.objects.filter(
            date_reversement__gte=debut_mois,
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

        # Émoluments générés (estimation 10% des encaissements)
        emoluments_mois = float(encaissements_mois) * 0.10

        # Taux de recouvrement global
        total_creances = (dossiers_amiables['total'] or 0) + (dossiers_forces['total'] or 0)
        taux_recouvrement_global = 0
        if total_creances > 0:
            taux_recouvrement_global = int(float(total_encaissements) / float(total_creances) * 100)

        # Reversements en attente
        reversements_en_attente = Reversement.objects.filter(
            statut='en_attente'
        ).aggregate(
            count=Count('id'),
            total=Sum('montant')
        )

        # Dossiers sans activité 60 jours
        date_60j = today - timedelta(days=60)
        dossiers_sans_activite_60j = Dossier.objects.filter(
            statut='actif',
            date_ouverture__lt=date_60j
        ).count()

        recouvrement_data = {
            'amiables': {
                'count': dossiers_amiables['count'] or 0,
                'total': float(dossiers_amiables['total'] or 0)
            },
            'forces': {
                'count': dossiers_forces['count'] or 0,
                'total': float(dossiers_forces['total'] or 0)
            },
            'total_creances': float(total_creances),
            'encaissements_mois': float(encaissements_mois),
            'reversements_mois': float(reversements_mois),
            'emoluments_mois': emoluments_mois,
            'taux_recouvrement': taux_recouvrement_global,
            'reversements_attente': {
                'count': reversements_en_attente['count'] or 0,
                'total': float(reversements_en_attente['total'] or 0)
            },
            'dossiers_sans_activite': dossiers_sans_activite_60j
        }

        # ===== SECTION 8: GÉRANCE IMMOBILIÈRE =====
        # Données simulées (à connecter avec le module gérance quand disponible)
        gerance_data = {
            'biens_gestion': 28,
            'biens_loues': 24,
            'biens_vacants': 4,
            'taux_occupation': 86,
            'loyers_attendus': 4200000,
            'loyers_encaisses': 3650000,
            'loyers_impayes': 550000,
            'locataires_impayes': 5,
            'etats_lieux_a_faire': 2,
            'reversements_proprietaires': 2890000,
            'baux_expirent_30j': 1
        }

        # ===== SECTION 9: RESSOURCES HUMAINES =====
        rh_data = {
            'effectif_total': 8,
            'presents_aujourdhui': 7,
            'en_conge': 1,
            'absents': 0,
            'conges_en_cours': [],
            'alertes': []
        }

        if has_rh:
            # Effectif total
            rh_data['effectif_total'] = Employe.objects.filter(actif=True).count()

            # Congés en cours
            conges_en_cours = Conge.objects.filter(
                date_debut__lte=today,
                date_fin__gte=today,
                statut='approuve'
            )
            rh_data['en_conge'] = conges_en_cours.count()
            rh_data['presents_aujourdhui'] = rh_data['effectif_total'] - rh_data['en_conge']

            rh_data['conges_en_cours'] = [{
                'employe': c.employe.nom_complet,
                'type': c.type_conge.nom if c.type_conge else 'Congé',
                'date_fin': c.date_fin.strftime('%d/%m')
            } for c in conges_en_cours[:3]]

            # Alertes RH
            # Fins de période d'essai
            date_15j = today + timedelta(days=15)
            fins_essai = Contrat.objects.filter(
                date_fin_essai__lte=date_15j,
                date_fin_essai__gte=today,
                statut='actif'
            )
            for c in fins_essai:
                rh_data['alertes'].append({
                    'type': 'fin_essai',
                    'message': f"Fin période essai : {c.employe.nom_complet}",
                    'date': c.date_fin_essai.strftime('%d/%m')
                })

            # Fins de CDD
            date_60j = today + timedelta(days=60)
            fins_cdd = Contrat.objects.filter(
                type_contrat='CDD',
                date_fin__lte=date_60j,
                date_fin__gte=today,
                statut='actif'
            )
            for c in fins_cdd:
                rh_data['alertes'].append({
                    'type': 'fin_cdd',
                    'message': f"Fin CDD : {c.employe.nom_complet}",
                    'date': c.date_fin.strftime('%d/%m')
                })

        # ===== SECTION 10: MÉMOIRES DE CÉDULES =====
        memoires_attente_paiement = Memoire.objects.filter(
            statut__in=['soumis', 'certifie']
        ).aggregate(
            count=Count('id'),
            total=Sum('montant_total')
        )

        memoires_payes_mois = Memoire.objects.filter(
            statut='paye',
            date_paiement__gte=debut_mois
        ).aggregate(
            count=Count('id'),
            total=Sum('montant_total')
        )

        # Cédules en cours de signification (approximation via les affaires)
        cedules_en_cours = AffaireMemoire.objects.filter(
            memoire__statut='brouillon'
        ).count()

        # Derniers paiements
        derniers_paiements = list(Memoire.objects.filter(
            statut='paye'
        ).order_by('-date_paiement')[:3].values(
            'numero', 'montant_total', 'date_paiement'
        ))

        for p in derniers_paiements:
            p['montant_total'] = float(p['montant_total']) if p['montant_total'] else 0

        # Mémoires en attente depuis longtemps
        date_60j_ago = today - timedelta(days=60)
        memoires_attente_longue = list(Memoire.objects.filter(
            statut__in=['soumis', 'certifie'],
            date_creation__lt=date_60j_ago
        ).values('numero', 'montant_total', 'date_creation')[:3])

        for m in memoires_attente_longue:
            m['jours'] = (today - m['date_creation'].date()).days if m['date_creation'] else 0
            m['montant_total'] = float(m['montant_total']) if m['montant_total'] else 0

        memoires_data = {
            'attente_paiement': {
                'count': memoires_attente_paiement['count'] or 0,
                'total': float(memoires_attente_paiement['total'] or 0)
            },
            'payes_mois': {
                'count': memoires_payes_mois['count'] or 0,
                'total': float(memoires_payes_mois['total'] or 0)
            },
            'cedules_en_cours': cedules_en_cours,
            'derniers_paiements': derniers_paiements,
            'attente_longue': memoires_attente_longue
        }

        # ===== SECTION 11: ALERTES =====
        alertes = {
            'urgentes': [],
            'importantes': [],
            'informations': []
        }

        # Alertes urgentes
        if dossiers_urgents > 0:
            alertes['urgentes'].append({
                'type': 'dossier_urgent',
                'message': f'{dossiers_urgents} dossier(s) urgent(s) à traiter'
            })

        if decaissements_attente > 0:
            alertes['urgentes'].append({
                'type': 'decaissement_attente',
                'message': f'{decaissements_attente} décaissement(s) en attente d\'approbation'
            })

        if has_agenda:
            if agenda_data['taches_retard'] > 0:
                alertes['urgentes'].append({
                    'type': 'taches_retard',
                    'message': f'{agenda_data["taches_retard"]} tâche(s) en retard'
                })

        # Alertes importantes
        if reversements_en_attente['count'] > 0:
            alertes['importantes'].append({
                'type': 'reversements',
                'message': f'{reversements_en_attente["count"]} reversement(s) créanciers à effectuer'
            })

        if compta_data['tva_a_declarer'] > 0:
            alertes['importantes'].append({
                'type': 'tva',
                'message': f"TVA à déclarer : {compta_data['tva_a_declarer']:,.0f} F"
            })

        # Informations
        if len(factures_impayees) > 0:
            alertes['informations'].append({
                'type': 'factures_impayees',
                'message': f'{len(factures_impayees)} facture(s) impayée(s) > 30 jours'
            })

        if dossiers_sans_activite > 0:
            alertes['informations'].append({
                'type': 'dossiers_inactifs',
                'message': f'{dossiers_sans_activite} dossier(s) sans activité > 30 jours'
            })

        # ===== CONSTRUCTION DE LA RÉPONSE =====
        response_data = {
            'success': True,
            'timestamp': now.isoformat(),
            'date_formatted': now.strftime('%A %d %B %Y'),
            'heure': now.strftime('%H:%M'),

            # KPIs principaux
            'kpis': {
                'dossiers_en_cours': dossiers_actifs,
                'dossiers_nouveaux_mois': dossiers_nouveaux_mois,
                'solde_tresorerie': float(solde_tresorerie),
                'encaissements_jour': {
                    'montant': float(encaissements_jour['total'] or 0),
                    'count': encaissements_jour['count'] or 0
                },
                'rdv_aujourdhui': len(agenda_data['rendez_vous']) if has_agenda else 5,
                'taches_aujourdhui': len(agenda_data['taches']) if has_agenda else 8,
                'audiences_aujourdhui': 2,  # À calculer depuis agenda
                'alertes_urgentes': len(alertes['urgentes'])
            },

            # Sections détaillées
            'dossiers': {
                'en_cours': dossiers_en_cours,
                'en_attente': dossiers_en_attente,
                'clotures_mois': dossiers_clotures_mois,
                'repartition_types': repartition_types,
                'derniers': derniers_dossiers,
                'sans_activite_30j': dossiers_sans_activite
            },

            'agenda': agenda_data,
            'tresorerie': tresorerie_data,
            'facturation': facturation_data,
            'comptabilite': compta_data,
            'recouvrement': recouvrement_data,
            'gerance': gerance_data,
            'rh': rh_data,
            'memoires': memoires_data,
            'alertes': alertes
        }

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

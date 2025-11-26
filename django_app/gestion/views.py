from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Dossier, Facture, Collaborateur, Partie, ActeProcedure,
    HistoriqueCalcul, TauxLegal, Utilisateur,
    # Modèles Trésorerie
    Caisse, JournalCaisse, OperationTresorerie, Consignation,
    MouvementConsignation, CompteBancaire, RapprochementBancaire,
    LigneRapprochement, AuditTresorerie
)


# Données par défaut pour le contexte (simulant les données React)
def get_default_context(request):
    """Contexte par défaut pour tous les templates"""
    # Utilisateur courant simulé
    current_user = {
        'id': 1,
        'nom': 'BIAOU Martial Arnaud',
        'role': 'admin',
        'email': 'mab@etude-biaou.bj',
        'initials': 'MA'
    }

    # Modules de navigation
    modules = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'home', 'category': 'main', 'url': 'dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'dossiers', 'badge': 14},
        {'id': 'facturation', 'label': 'Facturation & MECeF', 'icon': 'file-text', 'category': 'main', 'url': 'facturation'},
        {'id': 'calcul', 'label': 'Calcul Recouvrement', 'icon': 'calculator', 'category': 'main', 'url': 'calcul'},
        {'id': 'tresorerie', 'label': 'Trésorerie', 'icon': 'piggy-bank', 'category': 'finance', 'url': 'tresorerie'},
        {'id': 'comptabilite', 'label': 'Comptabilité', 'icon': 'bar-chart-3', 'category': 'finance', 'url': 'comptabilite'},
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh'},
        {'id': 'drive', 'label': 'Drive', 'icon': 'hard-drive', 'category': 'gestion', 'url': 'drive'},
        {'id': 'gerance', 'label': 'Gérance Immobilière', 'icon': 'building-2', 'category': 'gestion', 'url': 'gerance'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda'},
        {'id': 'parametres', 'label': 'Paramètres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres'},
        {'id': 'securite', 'label': 'Sécurité & Accès', 'icon': 'shield', 'category': 'admin', 'url': 'securite'},
    ]

    # Collaborateurs par défaut
    collaborateurs = [
        {'id': 1, 'nom': 'Me BIAOU Martial', 'role': 'Huissier'},
        {'id': 2, 'nom': 'ADJOVI Carine', 'role': 'Clerc Principal'},
        {'id': 3, 'nom': 'HOUNKPATIN Paul', 'role': 'Clerc'},
        {'id': 4, 'nom': 'DOSSOU Marie', 'role': 'Secrétaire'},
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

    # Statistiques
    context['stats'] = {
        'dossiers_actifs': 127,
        'ca_mensuel': '18,5 M',
        'actes_signifies': 89,
        'urgents': 14,
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

    # Données de démonstration (comme dans React)
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

    context['tabs'] = [
        {'id': 'all', 'label': 'Tous', 'count': 127},
        {'id': 'actifs', 'label': 'Actifs', 'count': 89},
        {'id': 'urgents', 'label': 'Urgents', 'count': 14},
        {'id': 'archives', 'label': 'Archivés', 'count': 24},
    ]
    context['current_tab'] = tab
    context['filters'] = {
        'search': search,
        'type': type_filter,
        'assigned': assigned_filter,
    }

    return render(request, 'gestion/dossiers.html', context)


def nouveau_dossier(request):
    """Vue pour créer un nouveau dossier"""
    context = get_default_context(request)
    context['active_module'] = 'dossiers'
    context['page_title'] = 'Nouveau dossier'

    if request.method == 'POST':
        # Traitement du formulaire
        data = request.POST
        # Créer le dossier...
        messages.success(request, 'Dossier créé avec succès!')
        return redirect('dossiers')

    # Générer une nouvelle référence
    context['reference'] = Dossier.generer_reference()
    context['types_dossier'] = Dossier.TYPE_DOSSIER_CHOICES

    return render(request, 'gestion/nouveau_dossier.html', context)


def facturation(request):
    """Vue de la facturation"""
    context = get_default_context(request)
    context['active_module'] = 'facturation'
    context['page_title'] = 'Facturation & MECeF'

    tab = request.GET.get('tab', 'liste')

    # Factures de démonstration
    context['factures'] = [
        {'id': 'FAC-2025-001', 'client': 'SODECO SA', 'montant_ht': 150000, 'tva': 27000, 'total': 177000, 'date': '15/11/2025', 'statut': 'payee'},
        {'id': 'FAC-2025-002', 'client': 'SOGEMA Sarl', 'montant_ht': 85000, 'tva': 15300, 'total': 100300, 'date': '18/11/2025', 'statut': 'attente'},
        {'id': 'FAC-2025-003', 'client': 'Banque Atlantique', 'montant_ht': 250000, 'tva': 45000, 'total': 295000, 'date': '20/11/2025', 'statut': 'attente'},
    ]

    context['tabs'] = [
        {'id': 'liste', 'label': 'Liste des factures'},
        {'id': 'memoires', 'label': 'Mémoires'},
        {'id': 'mecef', 'label': 'MECeF'},
    ]
    context['current_tab'] = tab

    return render(request, 'gestion/facturation.html', context)


def calcul_recouvrement(request):
    """Vue du calcul de recouvrement OHADA"""
    context = get_default_context(request)
    context['active_module'] = 'calcul'
    context['page_title'] = 'Calcul Recouvrement'

    # Taux légaux UEMOA
    context['taux_legaux'] = {
        2010: 6.4800, 2011: 6.2500, 2012: 4.2500, 2013: 4.1141, 2014: 3.7274,
        2015: 3.5000, 2016: 3.5000, 2017: 3.5437, 2018: 4.5000, 2019: 4.5000,
        2020: 4.5000, 2021: 4.2391, 2022: 4.0000, 2023: 4.2205, 2024: 5.0336,
        2025: 5.5000
    }

    # Catalogue des actes
    context['catalogue_actes'] = [
        {'id': 'cmd', 'label': 'Commandement de payer', 'tarif': 15000},
        {'id': 'sign_titre', 'label': 'Signification de titre exécutoire', 'tarif': 10000},
        {'id': 'pv_saisie', 'label': 'PV de Saisie-Vente', 'tarif': 25000},
        {'id': 'pv_carence', 'label': 'PV de Carence', 'tarif': 15000},
        {'id': 'denonc', 'label': 'Dénonciation de saisie', 'tarif': 12000},
        {'id': 'assign', 'label': 'Assignation', 'tarif': 20000},
        {'id': 'sign_ord', 'label': 'Signification Ordonnance', 'tarif': 10000},
        {'id': 'certif', 'label': 'Certificat de non recours', 'tarif': 5000},
        {'id': 'mainlevee', 'label': 'Mainlevée', 'tarif': 15000},
        {'id': 'sommation', 'label': 'Sommation interpellative', 'tarif': 12000},
        {'id': 'constat', 'label': 'Procès-verbal de constat', 'tarif': 30000},
    ]

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
    """Vue Sécurité & Accès"""
    context = get_default_context(request)
    context['active_module'] = 'securite'
    context['page_title'] = 'Sécurité & Accès'

    # Utilisateurs avec leurs emails générés
    context['utilisateurs'] = []
    for collab in context['collaborateurs']:
        email = collab['nom'].lower().replace(' ', '.').replace('me ', '') + '@etude-biaou.bj'
        context['utilisateurs'].append({
            **collab,
            'email': email,
            'statut': 'actif'
        })

    return render(request, 'gestion/securite.html', context)


def module_en_construction(request, module_name):
    """Vue pour les modules non implémentés"""
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
# API ENDPOINTS (pour AJAX)
# ============================================

@require_POST
def api_calculer_interets(request):
    """API pour calculer les intérêts OHADA"""
    try:
        data = json.loads(request.body)

        # Récupérer les paramètres
        montant_principal = Decimal(str(data.get('montant_principal', 0)))
        date_creance = datetime.strptime(data.get('date_creance'), '%Y-%m-%d')
        date_saisie = datetime.strptime(data.get('date_saisie'), '%Y-%m-%d')
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

        # Taux légaux UEMOA
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

        def obtenir_taux(date):
            return taux_legaux.get(date.year, Decimal('5.5'))

        # Calcul des intérêts par période
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
                    taux = obtenir_taux(current)
                elif type_taux == 'cima':
                    taux = Decimal('60')  # 5% * 12 mois
                else:
                    taux = taux_conventionnel

                if majore:
                    taux = taux * Decimal('1.5')

                if type_calcul == 'simple':
                    interet = (montant * taux * jours) / (100 * jours_annee(annee))
                else:
                    interet = montant * ((1 + taux / 100) ** (Decimal(jours) / jours_annee(annee)) - 1)

                periodes.append({
                    'annee': annee,
                    'debut': current.strftime('%d/%m/%Y'),
                    'fin': borne.strftime('%d/%m/%Y'),
                    'jours': jours,
                    'taux': float(taux),
                    'interet': float(round(interet) if arrondir else interet)
                })

                total += interet
                current = datetime(annee + 1, 1, 1)

            return {
                'periodes': periodes,
                'total': float(round(total) if arrondir else total)
            }

        # Calcul des émoluments proportionnels
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

            for tranche in baremes[type_titre]:
                if restant <= 0:
                    break
                part = min(restant, Decimal(str(tranche['max'])) - cumul)
                if part > 0:
                    em = (part * tranche['taux']) / 100
                    total += em
                    restant -= part
                    cumul += float(part)

            return {'total': float(round(total) if arrondir else total)}

        # Calcul principal
        date_maj = None
        if appliquer_majoration and date_decision:
            d = datetime.strptime(date_decision, '%Y-%m-%d')
            date_maj = d + timedelta(days=60)  # 2 mois
            if date_saisie <= date_maj:
                date_maj = None

        # Intérêts échus
        if date_maj and date_maj < date_saisie:
            p1 = calculer_interets_periode(montant_principal, date_creance, date_maj, False)
            p2 = calculer_interets_periode(montant_principal, date_maj, date_saisie, True)
            interets_echus = {
                'periodes': p1['periodes'] + p2['periodes'],
                'total': p1['total'] + p2['total']
            }
        else:
            interets_echus = calculer_interets_periode(montant_principal, date_creance, date_saisie, False)

        # Intérêts à échoir (1 mois)
        date_fin_echoir = date_saisie + timedelta(days=30)
        interets_echoir = calculer_interets_periode(
            montant_principal, date_saisie, date_fin_echoir,
            appliquer_majoration and date_maj is not None
        )

        # Émoluments
        emoluments = None
        base_emol = montant_principal + Decimal(str(interets_echus['total']))
        if calculer_emoluments:
            base_emol += frais_justice
            emoluments = calculer_emoluments_prop(base_emol)

        # Total des actes
        total_actes = sum(float(a.get('montant', 0)) for a in actes)

        # Total général
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
            'date_limite_majoration': date_maj.strftime('%d/%m/%Y') if date_maj else None
        }

        return JsonResponse({'success': True, 'resultats': resultats})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_calculer_emoluments(request):
    """API pour calculer les émoluments seuls"""
    try:
        data = json.loads(request.body)

        base = Decimal(str(data.get('base', 0)))
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

        for tranche in baremes[type_titre]:
            if restant <= 0:
                break
            part = min(restant, Decimal(str(tranche['max'])) - cumul)
            if part > 0:
                em = (part * tranche['taux']) / 100
                total += em
                restant -= part
                cumul += float(part)

        emol_total = float(round(total) if arrondir else total)

        resultats = {
            'mode': 'emoluments',
            'base': float(base),
            'emoluments': {'total': emol_total},
            'total': float(base) + emol_total
        }

        return JsonResponse({'success': True, 'resultats': resultats})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_chatbot(request):
    """API pour le chatbot"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').lower()
        user_role = data.get('user_role', 'user')

        # Réponses contextuelles
        if 'supprim' in message and user_role != 'admin':
            reponse = "Désolé, seul l'administrateur peut supprimer des éléments."
        elif 'intérêt' in message or 'calcul' in message:
            reponse = "Pour calculer des intérêts, rendez-vous dans le module 'Calcul Recouvrement'. Je peux vous y guider si vous le souhaitez."
        elif 'dossier' in message:
            reponse = "Pour créer ou consulter un dossier, utilisez le module 'Dossiers'. Vous pouvez cliquer sur 'Nouveau dossier' pour en créer un."
        elif 'facture' in message:
            reponse = "Le module 'Facturation & MECeF' vous permet de gérer vos factures et de les normaliser avec le système MECeF."
        elif 'bonjour' in message or 'salut' in message:
            reponse = "Bonjour Maître ! Comment puis-je vous aider aujourd'hui ?"
        else:
            reponse = "Je peux vous aider à rédiger des actes, calculer des intérêts ou rechercher des informations juridiques."

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
                'error': "Action non autorisée : Seul l'administrateur peut supprimer un dossier."
            }, status=403)

        # Ici, on supprimerait le dossier en base
        # Dossier.objects.filter(id=dossier_id).delete()

        return JsonResponse({'success': True, 'message': 'Dossier supprimé'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ============================================
# MODULE TRÉSORERIE - VUES
# ============================================

def tresorerie(request):
    """Vue principale du module trésorerie"""
    context = get_default_context(request)
    context['active_module'] = 'tresorerie'
    context['page_title'] = 'Trésorerie'

    tab = request.GET.get('tab', 'dashboard')
    context['current_tab'] = tab

    # Onglets du module
    context['tabs'] = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'id': 'caisses', 'label': 'Caisses', 'icon': 'landmark'},
        {'id': 'encaissements', 'label': 'Encaissements', 'icon': 'trending-up'},
        {'id': 'decaissements', 'label': 'Décaissements', 'icon': 'trending-down'},
        {'id': 'consignations', 'label': 'Consignations', 'icon': 'lock'},
        {'id': 'rapprochement', 'label': 'Rapprochement', 'icon': 'git-compare'},
        {'id': 'journal', 'label': 'Journal', 'icon': 'book-open'},
        {'id': 'rapports', 'label': 'Rapports', 'icon': 'file-bar-chart'},
    ]

    # Récupérer les données
    caisses = Caisse.objects.filter(actif=True)
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    debut_semaine = today - timedelta(days=today.weekday())

    # Statistiques du tableau de bord
    solde_total = sum(c.solde_actuel for c in caisses) if caisses.exists() else 0

    # Encaissements
    encaissements_jour = OperationTresorerie.objects.filter(
        type_operation='encaissement',
        date_operation=today,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    encaissements_semaine = OperationTresorerie.objects.filter(
        type_operation='encaissement',
        date_operation__gte=debut_semaine,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    encaissements_mois = OperationTresorerie.objects.filter(
        type_operation='encaissement',
        date_operation__gte=debut_mois,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Décaissements
    decaissements_jour = OperationTresorerie.objects.filter(
        type_operation='decaissement',
        date_operation=today,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    decaissements_semaine = OperationTresorerie.objects.filter(
        type_operation='decaissement',
        date_operation__gte=debut_semaine,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    decaissements_mois = OperationTresorerie.objects.filter(
        type_operation='decaissement',
        date_operation__gte=debut_mois,
        statut__in=['valide', 'paye']
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Alertes
    consignations_a_reverser = Consignation.objects.filter(
        statut__in=['active', 'partielle'],
        date_echeance_reversement__lte=today + timedelta(days=7)
    ).count()

    decaissements_en_attente = OperationTresorerie.objects.filter(
        type_operation='decaissement',
        statut='en_attente_approbation'
    ).count()

    caisses_solde_faible = Caisse.objects.filter(
        actif=True,
        solde_actuel__lt=50000
    ).count()

    context['stats'] = {
        'solde_total': solde_total,
        'encaissements': {
            'jour': encaissements_jour,
            'semaine': encaissements_semaine,
            'mois': encaissements_mois,
        },
        'decaissements': {
            'jour': decaissements_jour,
            'semaine': decaissements_semaine,
            'mois': decaissements_mois,
        },
        'alertes': {
            'consignations_a_reverser': consignations_a_reverser,
            'decaissements_en_attente': decaissements_en_attente,
            'caisses_solde_faible': caisses_solde_faible,
        }
    }

    # Données pour les onglets
    context['caisses'] = caisses
    context['comptes_bancaires'] = CompteBancaire.objects.filter(actif=True)

    # Operations récentes
    context['operations_recentes'] = OperationTresorerie.objects.all()[:10]

    # Encaissements (filtré par onglet)
    encaissements_qs = OperationTresorerie.objects.filter(type_operation='encaissement')
    filtre_encaissement = request.GET.get('filtre_enc', 'tous')
    if filtre_encaissement == 'attente':
        encaissements_qs = encaissements_qs.filter(statut='en_attente')
    elif filtre_encaissement == 'valide':
        encaissements_qs = encaissements_qs.filter(statut__in=['valide', 'paye'])
    context['encaissements'] = encaissements_qs[:50]

    # Décaissements
    decaissements_qs = OperationTresorerie.objects.filter(type_operation='decaissement')
    filtre_decaissement = request.GET.get('filtre_dec', 'tous')
    if filtre_decaissement == 'attente':
        decaissements_qs = decaissements_qs.filter(statut__in=['en_attente', 'en_attente_approbation'])
    elif filtre_decaissement == 'approuve':
        decaissements_qs = decaissements_qs.filter(statut__in=['approuve', 'paye'])
    context['decaissements'] = decaissements_qs[:50]

    # Consignations
    consignations_qs = Consignation.objects.all()
    filtre_cons = request.GET.get('filtre_cons', 'actives')
    if filtre_cons == 'actives':
        consignations_qs = consignations_qs.filter(statut__in=['active', 'partielle'])
    elif filtre_cons == 'reversees':
        consignations_qs = consignations_qs.filter(statut='reversee')
    elif filtre_cons == 'retard':
        consignations_qs = consignations_qs.filter(
            date_echeance_reversement__lt=today,
            statut__in=['active', 'partielle']
        )
    context['consignations'] = consignations_qs[:50]

    # Rapprochements bancaires
    context['rapprochements'] = RapprochementBancaire.objects.all()[:20]

    # Journal des opérations
    periode_journal = request.GET.get('periode_journal', 'mois')
    journal_qs = OperationTresorerie.objects.all()
    if periode_journal == 'jour':
        journal_qs = journal_qs.filter(date_operation=today)
    elif periode_journal == 'semaine':
        journal_qs = journal_qs.filter(date_operation__gte=debut_semaine)
    elif periode_journal == 'mois':
        journal_qs = journal_qs.filter(date_operation__gte=debut_mois)
    context['journal_operations'] = journal_qs[:100]

    # Types pour les formulaires
    context['types_encaissement'] = OperationTresorerie.TYPE_ENCAISSEMENT_CHOICES
    context['types_decaissement'] = OperationTresorerie.TYPE_DECAISSEMENT_CHOICES
    context['modes_paiement'] = OperationTresorerie.MODE_PAIEMENT_CHOICES

    # Parties (pour les formulaires)
    context['parties'] = Partie.objects.all()[:100]

    # Dossiers actifs (pour les formulaires)
    context['dossiers_actifs'] = Dossier.objects.filter(statut__in=['actif', 'urgent'])[:50]

    # Données pour les graphiques (30 derniers jours)
    graphique_data = []
    for i in range(30, -1, -1):
        date_i = today - timedelta(days=i)
        enc = OperationTresorerie.objects.filter(
            type_operation='encaissement',
            date_operation=date_i,
            statut__in=['valide', 'paye']
        ).aggregate(total=Sum('montant'))['total'] or 0
        dec = OperationTresorerie.objects.filter(
            type_operation='decaissement',
            date_operation=date_i,
            statut__in=['valide', 'paye']
        ).aggregate(total=Sum('montant'))['total'] or 0
        graphique_data.append({
            'date': date_i.strftime('%d/%m'),
            'encaissements': float(enc),
            'decaissements': float(dec),
        })
    context['graphique_data'] = json.dumps(graphique_data)

    return render(request, 'gestion/tresorerie.html', context)


# ============================================
# API TRÉSORERIE
# ============================================

@require_POST
def api_caisse_ouvrir(request):
    """Ouvrir une caisse"""
    try:
        data = json.loads(request.body)
        caisse_id = data.get('caisse_id')
        user_id = data.get('user_id', 1)

        caisse = get_object_or_404(Caisse, id=caisse_id)

        if caisse.statut == 'ouverte':
            return JsonResponse({'success': False, 'error': 'La caisse est déjà ouverte'})

        # Vérifier si un journal existe déjà pour aujourd'hui
        today = timezone.now().date()
        journal, created = JournalCaisse.objects.get_or_create(
            caisse=caisse,
            date=today,
            defaults={
                'solde_ouverture': caisse.solde_actuel,
                'date_ouverture': timezone.now(),
                'ouvert_par_id': user_id,
            }
        )

        if not created:
            journal.date_ouverture = timezone.now()
            journal.ouvert_par_id = user_id
            journal.save()

        caisse.statut = 'ouverte'
        caisse.save()

        # Audit
        AuditTresorerie.objects.create(
            action='ouverture_caisse',
            entite_type='Caisse',
            entite_id=caisse.id,
            entite_reference=caisse.nom,
            description=f"Ouverture de la caisse {caisse.nom}",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Caisse '{caisse.nom}' ouverte avec succès",
            'solde': float(caisse.solde_actuel)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_caisse_fermer(request):
    """Fermer une caisse"""
    try:
        data = json.loads(request.body)
        caisse_id = data.get('caisse_id')
        solde_compte = Decimal(str(data.get('solde_compte', 0)))
        observations = data.get('observations', '')
        user_id = data.get('user_id', 1)

        caisse = get_object_or_404(Caisse, id=caisse_id)

        if caisse.statut != 'ouverte':
            return JsonResponse({'success': False, 'error': 'La caisse n\'est pas ouverte'})

        today = timezone.now().date()
        journal = JournalCaisse.objects.filter(caisse=caisse, date=today).first()

        if journal:
            # Calculer le solde théorique
            encaissements = OperationTresorerie.objects.filter(
                caisse=caisse,
                type_operation='encaissement',
                date_operation=today,
                statut__in=['valide', 'paye']
            ).aggregate(total=Sum('montant'))['total'] or 0

            decaissements = OperationTresorerie.objects.filter(
                caisse=caisse,
                type_operation='decaissement',
                date_operation=today,
                statut__in=['valide', 'paye']
            ).aggregate(total=Sum('montant'))['total'] or 0

            solde_theorique = journal.solde_ouverture + encaissements - decaissements

            journal.date_fermeture = timezone.now()
            journal.solde_fermeture = solde_compte
            journal.solde_theorique = solde_theorique
            journal.ecart = solde_compte - solde_theorique
            journal.observations = observations
            journal.ferme_par_id = user_id
            journal.save()

        caisse.solde_actuel = solde_compte
        caisse.statut = 'fermee'
        caisse.save()

        # Audit
        AuditTresorerie.objects.create(
            action='fermeture_caisse',
            entite_type='Caisse',
            entite_id=caisse.id,
            entite_reference=caisse.nom,
            description=f"Fermeture de la caisse {caisse.nom}. Solde: {solde_compte} FCFA",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Caisse '{caisse.nom}' fermée avec succès",
            'ecart': float(journal.ecart) if journal else 0
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_caisse_creer(request):
    """Créer une nouvelle caisse (admin only)"""
    try:
        data = json.loads(request.body)
        user_role = data.get('user_role', 'user')

        if user_role != 'admin':
            return JsonResponse({
                'success': False,
                'error': "Seul l'administrateur peut créer une caisse"
            }, status=403)

        caisse = Caisse.objects.create(
            nom=data.get('nom'),
            site=data.get('site'),
            solde_initial=Decimal(str(data.get('solde_initial', 0))),
            solde_actuel=Decimal(str(data.get('solde_initial', 0))),
            responsable_id=data.get('responsable_id'),
        )

        # Audit
        AuditTresorerie.objects.create(
            action='creation',
            entite_type='Caisse',
            entite_id=caisse.id,
            entite_reference=caisse.nom,
            description=f"Création de la caisse {caisse.nom}",
            utilisateur_id=data.get('user_id', 1)
        )

        return JsonResponse({
            'success': True,
            'message': f"Caisse '{caisse.nom}' créée avec succès",
            'caisse_id': caisse.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_encaissement_creer(request):
    """Créer un encaissement"""
    try:
        data = json.loads(request.body)

        caisse = get_object_or_404(Caisse, id=data.get('caisse_id'))

        # Vérifier que la caisse est ouverte
        if caisse.statut != 'ouverte':
            return JsonResponse({
                'success': False,
                'error': "La caisse doit être ouverte pour enregistrer un encaissement"
            })

        reference = OperationTresorerie.generer_reference('encaissement')

        operation = OperationTresorerie.objects.create(
            reference=reference,
            type_operation='encaissement',
            categorie=data.get('categorie'),
            montant=Decimal(str(data.get('montant'))),
            date_operation=data.get('date_operation', timezone.now().date()),
            mode_paiement=data.get('mode_paiement', 'especes'),
            reference_paiement=data.get('reference_paiement', ''),
            caisse=caisse,
            dossier_id=data.get('dossier_id'),
            partie_id=data.get('partie_id'),
            emetteur=data.get('emetteur', ''),
            motif=data.get('motif', ''),
            statut='valide',
            cree_par_id=data.get('user_id', 1)
        )

        # Mettre à jour le solde de la caisse
        caisse.solde_actuel += operation.montant
        caisse.save()

        # Si c'est une consignation, créer l'entrée
        if data.get('categorie') == 'consignation' and data.get('partie_id'):
            cons_ref = Consignation.generer_reference()
            consignation = Consignation.objects.create(
                reference=cons_ref,
                client_id=data.get('partie_id'),
                dossier_id=data.get('dossier_id'),
                montant_initial=operation.montant,
                montant_restant=operation.montant,
                objet=data.get('motif', 'Consignation'),
                debiteur=data.get('emetteur', ''),
                cree_par_id=data.get('user_id', 1)
            )

            # Créer le mouvement
            MouvementConsignation.objects.create(
                consignation=consignation,
                type_mouvement='reception',
                montant=operation.montant,
                mode_paiement=operation.mode_paiement,
                reference_paiement=operation.reference_paiement,
                operation=operation,
                cree_par_id=data.get('user_id', 1)
            )

            operation.consignation = consignation
            operation.save()

        # Audit
        AuditTresorerie.objects.create(
            action='creation',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=reference,
            description=f"Encaissement de {operation.montant:,.0f} FCFA - {data.get('categorie')}",
            utilisateur_id=data.get('user_id', 1)
        )

        return JsonResponse({
            'success': True,
            'message': f"Encaissement {reference} créé avec succès",
            'operation_id': operation.id,
            'reference': reference
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_decaissement_creer(request):
    """Créer un décaissement"""
    try:
        data = json.loads(request.body)

        caisse = get_object_or_404(Caisse, id=data.get('caisse_id'))

        # Vérifier que la caisse est ouverte
        if caisse.statut != 'ouverte':
            return JsonResponse({
                'success': False,
                'error': "La caisse doit être ouverte pour enregistrer un décaissement"
            })

        montant = Decimal(str(data.get('montant')))

        # Vérifier le solde disponible
        if montant > caisse.solde_actuel:
            return JsonResponse({
                'success': False,
                'error': f"Solde insuffisant. Disponible: {caisse.solde_actuel:,.0f} FCFA"
            })

        reference = OperationTresorerie.generer_reference('decaissement')
        seuil_validation = Decimal(str(data.get('seuil_validation', 100000)))

        # Déterminer le statut initial
        statut_initial = 'en_attente'
        if montant >= seuil_validation:
            statut_initial = 'en_attente_approbation'

        operation = OperationTresorerie.objects.create(
            reference=reference,
            type_operation='decaissement',
            categorie=data.get('categorie'),
            montant=montant,
            date_operation=data.get('date_operation', timezone.now().date()),
            mode_paiement=data.get('mode_paiement', 'especes'),
            reference_paiement=data.get('reference_paiement', ''),
            caisse=caisse,
            dossier_id=data.get('dossier_id'),
            partie_id=data.get('partie_id'),
            beneficiaire=data.get('beneficiaire', ''),
            motif=data.get('motif', ''),
            statut=statut_initial,
            montant_seuil_validation=seuil_validation,
            cree_par_id=data.get('user_id', 1)
        )

        # Si le décaissement est automatiquement validé (sous le seuil)
        if statut_initial == 'en_attente':
            operation.statut = 'paye'
            operation.save()
            caisse.solde_actuel -= montant
            caisse.save()

        # Si c'est un reversement de consignation
        if data.get('categorie') == 'reversement_client' and data.get('consignation_id'):
            consignation = get_object_or_404(Consignation, id=data.get('consignation_id'))
            MouvementConsignation.objects.create(
                consignation=consignation,
                type_mouvement='reversement',
                montant=montant,
                mode_paiement=operation.mode_paiement,
                reference_paiement=operation.reference_paiement,
                operation=operation,
                cree_par_id=data.get('user_id', 1)
            )
            consignation.montant_reverse += montant
            consignation.montant_restant -= montant
            consignation.mettre_a_jour_statut()

            operation.consignation = consignation
            operation.save()

        # Audit
        AuditTresorerie.objects.create(
            action='creation',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=reference,
            description=f"Décaissement de {montant:,.0f} FCFA - {data.get('categorie')}",
            utilisateur_id=data.get('user_id', 1)
        )

        return JsonResponse({
            'success': True,
            'message': f"Décaissement {reference} créé avec succès",
            'operation_id': operation.id,
            'reference': reference,
            'statut': operation.statut,
            'necessite_approbation': statut_initial == 'en_attente_approbation'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_decaissement_approuver(request):
    """Approuver un décaissement"""
    try:
        data = json.loads(request.body)
        operation_id = data.get('operation_id')
        user_id = data.get('user_id', 1)
        user_role = data.get('user_role', 'user')

        # Seul huissier ou admin peut approuver
        if user_role not in ['admin', 'huissier']:
            return JsonResponse({
                'success': False,
                'error': "Seul l'huissier titulaire ou l'admin peut approuver un décaissement"
            }, status=403)

        operation = get_object_or_404(OperationTresorerie, id=operation_id)

        if operation.statut != 'en_attente_approbation':
            return JsonResponse({
                'success': False,
                'error': "Cette opération n'est pas en attente d'approbation"
            })

        operation.statut = 'approuve'
        operation.approuve_par_id = user_id
        operation.date_approbation = timezone.now()
        operation.save()

        # Audit
        AuditTresorerie.objects.create(
            action='approbation',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=operation.reference,
            description=f"Approbation du décaissement {operation.reference}",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Décaissement {operation.reference} approuvé"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_decaissement_rejeter(request):
    """Rejeter un décaissement"""
    try:
        data = json.loads(request.body)
        operation_id = data.get('operation_id')
        motif = data.get('motif', '')
        user_id = data.get('user_id', 1)
        user_role = data.get('user_role', 'user')

        if user_role not in ['admin', 'huissier']:
            return JsonResponse({
                'success': False,
                'error': "Seul l'huissier titulaire ou l'admin peut rejeter un décaissement"
            }, status=403)

        if not motif:
            return JsonResponse({
                'success': False,
                'error': "Le motif de rejet est obligatoire"
            })

        operation = get_object_or_404(OperationTresorerie, id=operation_id)

        operation.statut = 'rejete'
        operation.motif_rejet = motif
        operation.approuve_par_id = user_id
        operation.date_approbation = timezone.now()
        operation.save()

        # Audit
        AuditTresorerie.objects.create(
            action='rejet',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=operation.reference,
            description=f"Rejet du décaissement {operation.reference}: {motif}",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Décaissement {operation.reference} rejeté"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_decaissement_payer(request):
    """Marquer un décaissement comme payé"""
    try:
        data = json.loads(request.body)
        operation_id = data.get('operation_id')
        user_id = data.get('user_id', 1)

        operation = get_object_or_404(OperationTresorerie, id=operation_id)

        if operation.statut != 'approuve':
            return JsonResponse({
                'success': False,
                'error': "Le décaissement doit être approuvé avant d'être payé"
            })

        caisse = operation.caisse
        if operation.montant > caisse.solde_actuel:
            return JsonResponse({
                'success': False,
                'error': f"Solde insuffisant. Disponible: {caisse.solde_actuel:,.0f} FCFA"
            })

        operation.statut = 'paye'
        operation.save()

        caisse.solde_actuel -= operation.montant
        caisse.save()

        # Audit
        AuditTresorerie.objects.create(
            action='validation',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=operation.reference,
            description=f"Paiement du décaissement {operation.reference}",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Décaissement {operation.reference} payé"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_operation_annuler(request):
    """Annuler une opération"""
    try:
        data = json.loads(request.body)
        operation_id = data.get('operation_id')
        motif = data.get('motif', '')
        user_id = data.get('user_id', 1)

        if not motif:
            return JsonResponse({
                'success': False,
                'error': "Le motif d'annulation est obligatoire"
            })

        operation = get_object_or_404(OperationTresorerie, id=operation_id)

        if operation.statut == 'annule':
            return JsonResponse({
                'success': False,
                'error': "Cette opération est déjà annulée"
            })

        # Reverser les montants si l'opération était validée
        if operation.statut in ['valide', 'paye']:
            caisse = operation.caisse
            if operation.type_operation == 'encaissement':
                caisse.solde_actuel -= operation.montant
            else:
                caisse.solde_actuel += operation.montant
            caisse.save()

        operation.statut = 'annule'
        operation.motif_annulation = motif
        operation.annule_par_id = user_id
        operation.date_annulation = timezone.now()
        operation.save()

        # Audit
        AuditTresorerie.objects.create(
            action='annulation',
            entite_type='OperationTresorerie',
            entite_id=operation.id,
            entite_reference=operation.reference,
            description=f"Annulation de l'opération {operation.reference}: {motif}",
            utilisateur_id=user_id
        )

        return JsonResponse({
            'success': True,
            'message': f"Opération {operation.reference} annulée"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_consignation_creer(request):
    """Créer une consignation directement"""
    try:
        data = json.loads(request.body)

        reference = Consignation.generer_reference()
        montant = Decimal(str(data.get('montant')))

        consignation = Consignation.objects.create(
            reference=reference,
            client_id=data.get('client_id'),
            dossier_id=data.get('dossier_id'),
            montant_initial=montant,
            montant_restant=montant,
            objet=data.get('objet', ''),
            debiteur=data.get('debiteur', ''),
            date_reception=data.get('date_reception', timezone.now().date()),
            date_echeance_reversement=data.get('date_echeance'),
            cree_par_id=data.get('user_id', 1)
        )

        # Audit
        AuditTresorerie.objects.create(
            action='creation',
            entite_type='Consignation',
            entite_id=consignation.id,
            entite_reference=reference,
            description=f"Création consignation {reference} - {montant:,.0f} FCFA",
            utilisateur_id=data.get('user_id', 1)
        )

        return JsonResponse({
            'success': True,
            'message': f"Consignation {reference} créée",
            'consignation_id': consignation.id,
            'reference': reference
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_consignation_reverser(request):
    """Reverser une consignation (via décaissement)"""
    try:
        data = json.loads(request.body)
        consignation_id = data.get('consignation_id')
        montant = Decimal(str(data.get('montant')))

        consignation = get_object_or_404(Consignation, id=consignation_id)

        if montant > consignation.montant_restant:
            return JsonResponse({
                'success': False,
                'error': f"Le montant dépasse le restant à reverser ({consignation.montant_restant:,.0f} FCFA)"
            })

        # Créer le décaissement de reversement
        data['categorie'] = 'reversement_client'
        data['beneficiaire'] = str(consignation.client)
        data['motif'] = f"Reversement consignation {consignation.reference}"

        # Appeler api_decaissement_creer en interne
        return api_decaissement_creer(request)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_rapprochement_creer(request):
    """Créer un nouveau rapprochement bancaire"""
    try:
        data = json.loads(request.body)

        rapprochement = RapprochementBancaire.objects.create(
            compte_id=data.get('compte_id'),
            date_debut=data.get('date_debut'),
            date_fin=data.get('date_fin'),
            solde_releve=Decimal(str(data.get('solde_releve', 0))),
            cree_par_id=data.get('user_id', 1)
        )

        # Calculer le solde comptable
        operations = OperationTresorerie.objects.filter(
            date_operation__range=[rapprochement.date_debut, rapprochement.date_fin],
            statut__in=['valide', 'paye']
        )

        encaissements = operations.filter(type_operation='encaissement').aggregate(
            total=Sum('montant'))['total'] or 0
        decaissements = operations.filter(type_operation='decaissement').aggregate(
            total=Sum('montant'))['total'] or 0

        rapprochement.solde_comptable = encaissements - decaissements
        rapprochement.calculer_ecart()
        rapprochement.save()

        return JsonResponse({
            'success': True,
            'message': "Rapprochement créé",
            'rapprochement_id': rapprochement.id,
            'ecart': float(rapprochement.ecart) if rapprochement.ecart else 0
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_tresorerie_stats(request):
    """Obtenir les statistiques de trésorerie"""
    try:
        today = timezone.now().date()
        debut_mois = today.replace(day=1)

        caisses = Caisse.objects.filter(actif=True)
        solde_total = sum(c.solde_actuel for c in caisses)

        encaissements_mois = OperationTresorerie.objects.filter(
            type_operation='encaissement',
            date_operation__gte=debut_mois,
            statut__in=['valide', 'paye']
        ).aggregate(total=Sum('montant'))['total'] or 0

        decaissements_mois = OperationTresorerie.objects.filter(
            type_operation='decaissement',
            date_operation__gte=debut_mois,
            statut__in=['valide', 'paye']
        ).aggregate(total=Sum('montant'))['total'] or 0

        consignations_actives = Consignation.objects.filter(
            statut__in=['active', 'partielle']
        ).aggregate(total=Sum('montant_restant'))['total'] or 0

        return JsonResponse({
            'success': True,
            'stats': {
                'solde_total': float(solde_total),
                'encaissements_mois': float(encaissements_mois),
                'decaissements_mois': float(decaissements_mois),
                'consignations_actives': float(consignations_actives),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_journal_tresorerie(request):
    """Obtenir le journal des opérations"""
    try:
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        type_op = request.GET.get('type')
        caisse_id = request.GET.get('caisse_id')

        operations = OperationTresorerie.objects.all()

        if date_debut:
            operations = operations.filter(date_operation__gte=date_debut)
        if date_fin:
            operations = operations.filter(date_operation__lte=date_fin)
        if type_op:
            operations = operations.filter(type_operation=type_op)
        if caisse_id:
            operations = operations.filter(caisse_id=caisse_id)

        data = [{
            'id': op.id,
            'reference': op.reference,
            'type': op.type_operation,
            'categorie': op.categorie,
            'montant': float(op.montant),
            'date': op.date_operation.strftime('%d/%m/%Y'),
            'mode': op.get_mode_paiement_display(),
            'statut': op.statut,
            'caisse': op.caisse.nom,
        } for op in operations[:200]]

        return JsonResponse({'success': True, 'operations': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

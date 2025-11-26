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
    HistoriqueCalcul, TauxLegal, Utilisateur
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

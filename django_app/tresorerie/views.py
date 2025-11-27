"""
Vues du module Trésorerie
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    CompteBancaire, MouvementTresorerie, RapprochementBancaire,
    PrevisionTresorerie, AlerteTresorerie
)


def get_default_context(request):
    """Contexte par défaut pour tous les templates"""
    current_user = {
        'id': 1,
        'nom': 'BIAOU Martial Arnaud',
        'role': 'admin',
        'email': 'mab@etude-biaou.bj',
        'initials': 'MA'
    }

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
        {'id': 'parametres', 'label': 'Paramètres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres:index'},
        {'id': 'securite', 'label': 'Sécurité & Accès', 'icon': 'shield', 'category': 'admin', 'url': 'gestion:securite'},
    ]

    return {
        'current_user': current_user,
        'modules': modules,
        'active_module': 'tresorerie',
    }


def dashboard(request):
    """Vue principale du module Trésorerie"""
    context = get_default_context(request)
    context['page_title'] = 'Trésorerie'

    # Récupérer les comptes bancaires
    comptes = CompteBancaire.objects.filter(statut='actif')

    # Calculer les totaux
    solde_total = comptes.aggregate(total=Sum('solde_actuel'))['total'] or Decimal('0')

    # Mouvements du mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mouvements_mois = MouvementTresorerie.objects.filter(
        date_mouvement__gte=debut_mois,
        statut='valide'
    )

    entrees_mois = mouvements_mois.filter(type_mouvement='entree').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')
    sorties_mois = mouvements_mois.filter(type_mouvement='sortie').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')

    # Derniers mouvements
    derniers_mouvements = MouvementTresorerie.objects.all()[:10]

    # Alertes non traitées
    alertes = AlerteTresorerie.objects.filter(traitee=False)[:5]

    # Prévisions à venir (30 jours)
    date_limite = timezone.now().date() + timedelta(days=30)
    previsions = PrevisionTresorerie.objects.filter(
        date_prevue__lte=date_limite,
        statut='prevue'
    )[:10]

    # Statistiques par catégorie
    stats_categories = mouvements_mois.values('categorie', 'type_mouvement').annotate(
        total=Sum('montant'),
        count=Count('id')
    )

    context.update({
        'comptes': comptes,
        'solde_total': solde_total,
        'entrees_mois': entrees_mois,
        'sorties_mois': sorties_mois,
        'solde_mois': entrees_mois - sorties_mois,
        'derniers_mouvements': derniers_mouvements,
        'alertes': alertes,
        'previsions': previsions,
        'stats_categories': list(stats_categories),
    })

    return render(request, 'tresorerie/dashboard.html', context)


def comptes(request):
    """Liste des comptes bancaires"""
    context = get_default_context(request)
    context['page_title'] = 'Comptes bancaires'

    comptes = CompteBancaire.objects.all()
    context['comptes'] = comptes

    return render(request, 'tresorerie/comptes.html', context)


def mouvements(request):
    """Liste des mouvements de trésorerie"""
    context = get_default_context(request)
    context['page_title'] = 'Mouvements'

    # Filtres
    compte_id = request.GET.get('compte')
    type_mvt = request.GET.get('type')
    categorie = request.GET.get('categorie')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    mouvements_qs = MouvementTresorerie.objects.all()

    if compte_id:
        mouvements_qs = mouvements_qs.filter(compte_id=compte_id)
    if type_mvt:
        mouvements_qs = mouvements_qs.filter(type_mouvement=type_mvt)
    if categorie:
        mouvements_qs = mouvements_qs.filter(categorie=categorie)
    if date_debut:
        mouvements_qs = mouvements_qs.filter(date_mouvement__gte=date_debut)
    if date_fin:
        mouvements_qs = mouvements_qs.filter(date_mouvement__lte=date_fin)

    context['mouvements'] = mouvements_qs[:100]
    context['comptes'] = CompteBancaire.objects.filter(statut='actif')
    context['categories'] = MouvementTresorerie.CATEGORIES

    return render(request, 'tresorerie/mouvements.html', context)


def previsions_view(request):
    """Prévisions de trésorerie"""
    context = get_default_context(request)
    context['page_title'] = 'Prévisions'

    previsions = PrevisionTresorerie.objects.filter(statut='prevue').order_by('date_prevue')
    context['previsions'] = previsions

    return render(request, 'tresorerie/previsions.html', context)


def rapprochements(request):
    """Rapprochements bancaires"""
    context = get_default_context(request)
    context['page_title'] = 'Rapprochements bancaires'

    rapprochements_list = RapprochementBancaire.objects.all()[:20]
    context['rapprochements'] = rapprochements_list
    context['comptes'] = CompteBancaire.objects.filter(statut='actif')

    return render(request, 'tresorerie/rapprochements.html', context)


# ==========================================================================
# API ENDPOINTS
# ==========================================================================

@require_POST
def api_creer_compte(request):
    """Créer un nouveau compte bancaire"""
    try:
        data = json.loads(request.body)
        compte = CompteBancaire.objects.create(
            nom=data.get('nom'),
            numero=data.get('numero'),
            banque=data.get('banque'),
            type_compte=data.get('type_compte', 'courant'),
            solde_initial=Decimal(str(data.get('solde_initial', 0))),
            solde_actuel=Decimal(str(data.get('solde_initial', 0))),
            seuil_alerte=Decimal(str(data.get('seuil_alerte', 100000))),
            iban=data.get('iban'),
            bic=data.get('bic'),
            contact_banque=data.get('contact_banque'),
        )
        return JsonResponse({
            'success': True,
            'compte_id': str(compte.id),
            'message': 'Compte créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_mouvement(request):
    """Créer un nouveau mouvement de trésorerie"""
    try:
        data = json.loads(request.body)
        compte = get_object_or_404(CompteBancaire, id=data.get('compte_id'))

        mouvement = MouvementTresorerie.objects.create(
            compte=compte,
            type_mouvement=data.get('type_mouvement'),
            categorie=data.get('categorie', 'autre'),
            montant=Decimal(str(data.get('montant'))),
            date_mouvement=data.get('date_mouvement', timezone.now().date()),
            libelle=data.get('libelle'),
            reference=data.get('reference'),
            mode_paiement=data.get('mode_paiement', 'virement'),
            tiers=data.get('tiers'),
            numero_piece=data.get('numero_piece'),
            numero_cheque=data.get('numero_cheque'),
            notes=data.get('notes'),
            cree_par=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse({
            'success': True,
            'mouvement_id': str(mouvement.id),
            'message': 'Mouvement créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_valider_mouvement(request, mouvement_id):
    """Valider un mouvement de trésorerie"""
    try:
        mouvement = get_object_or_404(MouvementTresorerie, id=mouvement_id)

        if mouvement.statut != 'en_attente':
            return JsonResponse({
                'success': False,
                'error': 'Ce mouvement a déjà été traité'
            }, status=400)

        mouvement.valider(request.user if request.user.is_authenticated else None)

        return JsonResponse({
            'success': True,
            'message': 'Mouvement validé avec succès',
            'nouveau_solde': str(mouvement.compte.solde_actuel)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_annuler_mouvement(request, mouvement_id):
    """Annuler un mouvement de trésorerie"""
    try:
        mouvement = get_object_or_404(MouvementTresorerie, id=mouvement_id)

        if mouvement.statut == 'rapproche':
            return JsonResponse({
                'success': False,
                'error': 'Impossible d\'annuler un mouvement rapproché'
            }, status=400)

        old_statut = mouvement.statut
        mouvement.statut = 'annule'
        mouvement.save()

        # Recalculer le solde si le mouvement était validé
        if old_statut == 'valide':
            mouvement.compte.recalculer_solde()

        return JsonResponse({
            'success': True,
            'message': 'Mouvement annulé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_prevision(request):
    """Créer une prévision de trésorerie"""
    try:
        data = json.loads(request.body)
        compte = get_object_or_404(CompteBancaire, id=data.get('compte_id'))

        prevision = PrevisionTresorerie.objects.create(
            compte=compte,
            type_prevision=data.get('type_prevision'),
            libelle=data.get('libelle'),
            montant=Decimal(str(data.get('montant'))),
            date_prevue=data.get('date_prevue'),
            periodicite=data.get('periodicite', 'unique'),
            categorie=data.get('categorie', 'autre'),
            notes=data.get('notes'),
            cree_par=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse({
            'success': True,
            'prevision_id': str(prevision.id),
            'message': 'Prévision créée avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_statistiques(request):
    """Statistiques de trésorerie"""
    try:
        # Période par défaut: 12 derniers mois
        date_debut = timezone.now() - timedelta(days=365)

        comptes = CompteBancaire.objects.filter(statut='actif')
        solde_total = comptes.aggregate(total=Sum('solde_actuel'))['total'] or Decimal('0')

        mouvements = MouvementTresorerie.objects.filter(
            date_mouvement__gte=date_debut,
            statut='valide'
        )

        entrees = mouvements.filter(type_mouvement='entree').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')
        sorties = mouvements.filter(type_mouvement='sortie').aggregate(
            total=Sum('montant'))['total'] or Decimal('0')

        # Répartition par catégorie
        repartition = mouvements.values('categorie').annotate(
            total=Sum('montant')
        ).order_by('-total')

        # Evolution mensuelle
        evolution = []
        for i in range(12):
            mois = timezone.now() - timedelta(days=30 * i)
            debut = mois.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                fin = timezone.now()
            else:
                fin = (debut + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            mvts_mois = mouvements.filter(date_mouvement__gte=debut.date(), date_mouvement__lte=fin.date())
            entrees_m = mvts_mois.filter(type_mouvement='entree').aggregate(
                total=Sum('montant'))['total'] or Decimal('0')
            sorties_m = mvts_mois.filter(type_mouvement='sortie').aggregate(
                total=Sum('montant'))['total'] or Decimal('0')

            evolution.append({
                'mois': debut.strftime('%m/%Y'),
                'entrees': str(entrees_m),
                'sorties': str(sorties_m),
                'solde': str(entrees_m - sorties_m)
            })

        return JsonResponse({
            'success': True,
            'solde_total': str(solde_total),
            'entrees_periode': str(entrees),
            'sorties_periode': str(sorties),
            'repartition': list(repartition),
            'evolution': evolution[::-1]  # Du plus ancien au plus récent
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_rapprochement(request):
    """Créer un rapprochement bancaire"""
    try:
        data = json.loads(request.body)
        compte = get_object_or_404(CompteBancaire, id=data.get('compte_id'))

        rapprochement = RapprochementBancaire.objects.create(
            compte=compte,
            date_debut=data.get('date_debut'),
            date_fin=data.get('date_fin'),
            solde_releve=Decimal(str(data.get('solde_releve'))),
            solde_comptable=compte.solde_actuel,
            cree_par=request.user if request.user.is_authenticated else None,
        )
        rapprochement.calculer_ecart()

        return JsonResponse({
            'success': True,
            'rapprochement_id': str(rapprochement.id),
            'ecart': str(rapprochement.ecart),
            'message': 'Rapprochement créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_marquer_alerte_lue(request, alerte_id):
    """Marquer une alerte comme lue"""
    try:
        alerte = get_object_or_404(AlerteTresorerie, id=alerte_id)
        alerte.lue = True
        alerte.save()

        return JsonResponse({
            'success': True,
            'message': 'Alerte marquée comme lue'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_soldes_comptes(request):
    """Récupérer les soldes de tous les comptes"""
    try:
        comptes = CompteBancaire.objects.filter(statut='actif')
        data = []

        for compte in comptes:
            data.append({
                'id': str(compte.id),
                'nom': compte.nom,
                'banque': compte.banque,
                'type': compte.get_type_compte_display(),
                'solde': str(compte.solde_actuel),
                'seuil_alerte': str(compte.seuil_alerte),
                'alerte': compte.solde_actuel < compte.seuil_alerte
            })

        return JsonResponse({
            'success': True,
            'comptes': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

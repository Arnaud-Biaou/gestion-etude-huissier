"""
Vues du module Trésorerie
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Q, Count, F
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
        {'id': 'creanciers', 'label': 'Recouvrement Créances', 'icon': 'landmark', 'category': 'main', 'url': 'gestion:creanciers'},
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


@login_required
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


@login_required
def comptes(request):
    """Liste des comptes bancaires"""
    context = get_default_context(request)
    context['page_title'] = 'Comptes bancaires'

    # Filtres
    type_compte = request.GET.get('type')
    statut = request.GET.get('statut')
    recherche = request.GET.get('q')

    comptes_qs = CompteBancaire.objects.all()

    if type_compte:
        comptes_qs = comptes_qs.filter(type_compte=type_compte)
    if statut:
        comptes_qs = comptes_qs.filter(statut=statut)
    if recherche:
        comptes_qs = comptes_qs.filter(
            Q(nom__icontains=recherche) |
            Q(numero__icontains=recherche) |
            Q(banque__icontains=recherche)
        )

    context['comptes'] = comptes_qs

    # Statistiques
    comptes_actifs = CompteBancaire.objects.filter(statut='actif')
    context['solde_total'] = comptes_actifs.aggregate(total=Sum('solde_actuel'))['total'] or Decimal('0')
    context['nb_comptes_actifs'] = comptes_actifs.count()
    context['nb_mobile_money'] = comptes_actifs.filter(type_compte='mobile_money').count()
    context['nb_alertes'] = comptes_actifs.filter(solde_actuel__lt=F('seuil_alerte')).count()

    return render(request, 'tresorerie/comptes.html', context)


@login_required
def mouvements(request):
    """Liste des mouvements de trésorerie"""
    context = get_default_context(request)
    context['page_title'] = 'Mouvements'

    # Filtres
    compte_id = request.GET.get('compte')
    type_mvt = request.GET.get('type')
    categorie = request.GET.get('categorie')
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    recherche = request.GET.get('q')

    mouvements_qs = MouvementTresorerie.objects.all()

    if compte_id:
        mouvements_qs = mouvements_qs.filter(compte_id=compte_id)
    if type_mvt:
        mouvements_qs = mouvements_qs.filter(type_mouvement=type_mvt)
    if categorie:
        mouvements_qs = mouvements_qs.filter(categorie=categorie)
    if statut:
        mouvements_qs = mouvements_qs.filter(statut=statut)
    if date_debut:
        mouvements_qs = mouvements_qs.filter(date_mouvement__gte=date_debut)
    if date_fin:
        mouvements_qs = mouvements_qs.filter(date_mouvement__lte=date_fin)
    if recherche:
        mouvements_qs = mouvements_qs.filter(
            Q(libelle__icontains=recherche) |
            Q(reference__icontains=recherche) |
            Q(tiers__icontains=recherche)
        )

    # Calcul des totaux
    mouvements_valides = mouvements_qs.filter(statut='valide')
    total_entrees = mouvements_valides.filter(type_mouvement='entree').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')
    total_sorties = mouvements_valides.filter(type_mouvement='sortie').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')

    context['mouvements'] = mouvements_qs[:100]
    context['comptes'] = CompteBancaire.objects.filter(statut='actif')
    context['categories'] = MouvementTresorerie.CATEGORIES
    context['total_entrees'] = total_entrees
    context['total_sorties'] = total_sorties
    context['solde_periode'] = total_entrees - total_sorties

    return render(request, 'tresorerie/mouvements.html', context)


@login_required
def previsions_view(request):
    """Prévisions de trésorerie"""
    context = get_default_context(request)
    context['page_title'] = 'Prévisions'

    # Filtres
    compte_id = request.GET.get('compte')
    type_prev = request.GET.get('type')
    statut = request.GET.get('statut', 'prevue')
    periodicite = request.GET.get('periodicite')

    previsions_qs = PrevisionTresorerie.objects.all()

    if compte_id:
        previsions_qs = previsions_qs.filter(compte_id=compte_id)
    if type_prev:
        previsions_qs = previsions_qs.filter(type_prevision=type_prev)
    if statut:
        previsions_qs = previsions_qs.filter(statut=statut)
    if periodicite:
        previsions_qs = previsions_qs.filter(periodicite=periodicite)

    previsions_qs = previsions_qs.order_by('date_prevue')

    # Statistiques
    previsions_prevues = PrevisionTresorerie.objects.filter(statut='prevue')
    total_entrees = previsions_prevues.filter(type_prevision='entree').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')
    total_sorties = previsions_prevues.filter(type_prevision='sortie').aggregate(
        total=Sum('montant'))['total'] or Decimal('0')

    # Prévisions dans les 30 prochains jours
    date_limite = timezone.now().date() + timedelta(days=30)
    nb_30j = previsions_prevues.filter(date_prevue__lte=date_limite).count()

    # Résumé mensuel (3 prochains mois)
    resume_mensuel = []
    for i in range(3):
        mois = timezone.now().date() + timedelta(days=30 * i)
        debut_mois = mois.replace(day=1)
        if i < 2:
            fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            fin_mois = (debut_mois + timedelta(days=62)).replace(day=1) - timedelta(days=1)

        prev_mois = previsions_prevues.filter(
            date_prevue__gte=debut_mois,
            date_prevue__lte=fin_mois
        )
        entrees_m = prev_mois.filter(type_prevision='entree').aggregate(total=Sum('montant'))['total'] or Decimal('0')
        sorties_m = prev_mois.filter(type_prevision='sortie').aggregate(total=Sum('montant'))['total'] or Decimal('0')

        resume_mensuel.append({
            'label': debut_mois.strftime('%B %Y'),
            'entrees': entrees_m,
            'sorties': sorties_m,
            'solde': entrees_m - sorties_m
        })

    context['previsions'] = previsions_qs
    context['comptes'] = CompteBancaire.objects.filter(statut='actif')
    context['total_entrees_prevues'] = total_entrees
    context['total_sorties_prevues'] = total_sorties
    context['solde_previsionnel'] = total_entrees - total_sorties
    context['nb_previsions_30j'] = nb_30j
    context['resume_mensuel'] = resume_mensuel

    return render(request, 'tresorerie/previsions.html', context)


@login_required
def rapprochements(request):
    """Rapprochements bancaires"""
    context = get_default_context(request)
    context['page_title'] = 'Rapprochements bancaires'

    # Filtres
    compte_id = request.GET.get('compte')
    statut = request.GET.get('statut')
    periode = request.GET.get('periode')

    rapprochements_qs = RapprochementBancaire.objects.all()

    if compte_id:
        rapprochements_qs = rapprochements_qs.filter(compte_id=compte_id)
    if statut:
        rapprochements_qs = rapprochements_qs.filter(statut=statut)
    if periode:
        try:
            annee, mois = periode.split('-')
            rapprochements_qs = rapprochements_qs.filter(
                date_fin__year=int(annee),
                date_fin__month=int(mois)
            )
        except ValueError:
            pass

    # Statistiques
    all_rapprochements = RapprochementBancaire.objects.all()
    context['nb_total'] = all_rapprochements.count()
    context['nb_en_cours'] = all_rapprochements.filter(statut='en_cours').count()
    context['nb_valides'] = all_rapprochements.filter(statut='valide').count()
    context['nb_avec_ecart'] = all_rapprochements.exclude(ecart=0).count()

    context['rapprochements'] = rapprochements_qs[:50]
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
        type_compte = data.get('type_compte', 'courant')

        compte = CompteBancaire.objects.create(
            nom=data.get('nom'),
            numero=data.get('numero'),
            banque=data.get('banque'),
            type_compte=type_compte,
            operateur_mobile=data.get('operateur_mobile') if type_compte == 'mobile_money' else None,
            solde_initial=Decimal(str(data.get('solde_initial', 0))),
            solde_actuel=Decimal(str(data.get('solde_initial', 0))),
            seuil_alerte=Decimal(str(data.get('seuil_alerte', 100000))),
            iban=data.get('iban') if type_compte != 'mobile_money' else None,
            bic=data.get('bic') if type_compte != 'mobile_money' else None,
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


@require_GET
def api_detail_compte(request, compte_id):
    """Récupérer les détails d'un compte"""
    try:
        compte = get_object_or_404(CompteBancaire, id=compte_id)
        return JsonResponse({
            'success': True,
            'compte': {
                'id': str(compte.id),
                'nom': compte.nom,
                'numero': compte.numero,
                'banque': compte.banque,
                'type_compte': compte.type_compte,
                'operateur_mobile': compte.operateur_mobile,
                'devise': compte.devise,
                'solde_initial': str(compte.solde_initial),
                'solde_actuel': str(compte.solde_actuel),
                'seuil_alerte': str(compte.seuil_alerte),
                'statut': compte.statut,
                'iban': compte.iban,
                'bic': compte.bic,
                'contact_banque': compte.contact_banque,
                'notes': compte.notes,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_modifier_compte(request, compte_id):
    """Modifier un compte bancaire existant"""
    try:
        compte = get_object_or_404(CompteBancaire, id=compte_id)
        data = json.loads(request.body)

        compte.nom = data.get('nom', compte.nom)
        compte.numero = data.get('numero', compte.numero)
        compte.banque = data.get('banque', compte.banque)
        compte.type_compte = data.get('type_compte', compte.type_compte)
        compte.operateur_mobile = data.get('operateur_mobile') if data.get('type_compte') == 'mobile_money' else None

        if data.get('seuil_alerte'):
            compte.seuil_alerte = Decimal(str(data.get('seuil_alerte')))
        if data.get('iban'):
            compte.iban = data.get('iban')
        if data.get('bic'):
            compte.bic = data.get('bic')
        if data.get('contact_banque'):
            compte.contact_banque = data.get('contact_banque')
        if data.get('notes'):
            compte.notes = data.get('notes')

        compte.save()

        return JsonResponse({
            'success': True,
            'message': 'Compte modifié avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_supprimer_compte(request, compte_id):
    """Supprimer un compte bancaire"""
    try:
        compte = get_object_or_404(CompteBancaire, id=compte_id)

        # Vérifier qu'il n'y a pas de mouvements liés
        if compte.mouvements.filter(statut__in=['valide', 'rapproche']).exists():
            return JsonResponse({
                'success': False,
                'error': 'Impossible de supprimer un compte avec des mouvements validés ou rapprochés'
            }, status=400)

        # Marquer comme clôturé plutôt que de supprimer physiquement
        compte.statut = 'cloture'
        compte.date_cloture = timezone.now().date()
        compte.save()

        return JsonResponse({
            'success': True,
            'message': 'Compte clôturé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_virement_interne(request):
    """Effectuer un virement entre deux comptes"""
    try:
        data = json.loads(request.body)

        compte_source = get_object_or_404(CompteBancaire, id=data.get('compte_source_id'))
        compte_destination = get_object_or_404(CompteBancaire, id=data.get('compte_destination_id'))
        montant = Decimal(str(data.get('montant')))
        libelle = data.get('libelle', 'Virement interne')
        date_mouvement = data.get('date_mouvement', timezone.now().date())

        if compte_source.id == compte_destination.id:
            return JsonResponse({
                'success': False,
                'error': 'Les comptes source et destination doivent être différents'
            }, status=400)

        if montant <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Le montant doit être positif'
            }, status=400)

        # Créer le mouvement de sortie
        mouvement_sortie = MouvementTresorerie.objects.create(
            compte=compte_source,
            type_mouvement='sortie',
            categorie='virement_interne',
            montant=montant,
            date_mouvement=date_mouvement,
            libelle=f"{libelle} vers {compte_destination.nom}",
            mode_paiement='virement',
            statut='valide',
            cree_par=request.user if request.user.is_authenticated else None,
            valide_par=request.user if request.user.is_authenticated else None,
            date_validation=timezone.now(),
        )

        # Créer le mouvement d'entrée
        mouvement_entree = MouvementTresorerie.objects.create(
            compte=compte_destination,
            type_mouvement='entree',
            categorie='virement_interne',
            montant=montant,
            date_mouvement=date_mouvement,
            libelle=f"{libelle} depuis {compte_source.nom}",
            reference=str(mouvement_sortie.id)[:8],
            mode_paiement='virement',
            statut='valide',
            cree_par=request.user if request.user.is_authenticated else None,
            valide_par=request.user if request.user.is_authenticated else None,
            date_validation=timezone.now(),
        )

        # Recalculer les soldes
        compte_source.recalculer_solde()
        compte_destination.recalculer_solde()

        return JsonResponse({
            'success': True,
            'message': 'Virement effectué avec succès',
            'mouvement_sortie_id': str(mouvement_sortie.id),
            'mouvement_entree_id': str(mouvement_entree.id),
            'nouveau_solde_source': str(compte_source.solde_actuel),
            'nouveau_solde_destination': str(compte_destination.solde_actuel),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_mouvements_non_rapproches(request):
    """Récupérer les mouvements non rapprochés d'un compte"""
    try:
        compte_id = request.GET.get('compte')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')

        mouvements = MouvementTresorerie.objects.filter(
            compte_id=compte_id,
            statut='valide'
        ).exclude(statut='rapproche')

        if date_debut:
            mouvements = mouvements.filter(date_mouvement__gte=date_debut)
        if date_fin:
            mouvements = mouvements.filter(date_mouvement__lte=date_fin)

        data = []
        for mvt in mouvements[:50]:
            data.append({
                'id': str(mvt.id),
                'date_mouvement': mvt.date_mouvement.strftime('%d/%m/%Y'),
                'libelle': mvt.libelle,
                'type_mouvement': mvt.type_mouvement,
                'montant': str(mvt.montant),
            })

        return JsonResponse({
            'success': True,
            'mouvements': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_valider_rapprochement(request, rapprochement_id):
    """Valider un rapprochement bancaire"""
    try:
        rapprochement = get_object_or_404(RapprochementBancaire, id=rapprochement_id)

        if rapprochement.statut == 'valide':
            return JsonResponse({
                'success': False,
                'error': 'Ce rapprochement est déjà validé'
            }, status=400)

        rapprochement.statut = 'valide'
        rapprochement.valide_par = request.user if request.user.is_authenticated else None
        rapprochement.date_validation = timezone.now()
        rapprochement.save()

        # Marquer les mouvements comme rapprochés
        rapprochement.mouvements_rapproches.update(statut='rapproche')

        return JsonResponse({
            'success': True,
            'message': 'Rapprochement validé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_realiser_prevision(request, prevision_id):
    """Marquer une prévision comme réalisée et créer le mouvement correspondant"""
    try:
        prevision = get_object_or_404(PrevisionTresorerie, id=prevision_id)

        if prevision.statut != 'prevue':
            return JsonResponse({
                'success': False,
                'error': 'Cette prévision a déjà été traitée'
            }, status=400)

        # Créer le mouvement
        mouvement = MouvementTresorerie.objects.create(
            compte=prevision.compte,
            type_mouvement=prevision.type_prevision,
            categorie=prevision.categorie,
            montant=prevision.montant,
            date_mouvement=timezone.now().date(),
            libelle=prevision.libelle,
            notes=f"Créé depuis prévision du {prevision.date_prevue}",
            cree_par=request.user if request.user.is_authenticated else None,
        )

        # Mettre à jour la prévision
        prevision.statut = 'realisee'
        prevision.mouvement_realise = mouvement
        prevision.save()

        return JsonResponse({
            'success': True,
            'message': 'Prévision réalisée et mouvement créé',
            'mouvement_id': str(mouvement.id)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_annuler_prevision(request, prevision_id):
    """Annuler une prévision"""
    try:
        prevision = get_object_or_404(PrevisionTresorerie, id=prevision_id)

        if prevision.statut != 'prevue':
            return JsonResponse({
                'success': False,
                'error': 'Seules les prévisions en attente peuvent être annulées'
            }, status=400)

        prevision.statut = 'annulee'
        prevision.save()

        return JsonResponse({
            'success': True,
            'message': 'Prévision annulée'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def export_mouvements(request):
    """Exporter les mouvements en PDF ou Excel"""
    from django.http import HttpResponse
    import csv

    format_export = request.GET.get('format', 'excel')

    # Appliquer les mêmes filtres que la vue mouvements
    compte_id = request.GET.get('compte')
    type_mvt = request.GET.get('type')
    categorie = request.GET.get('categorie')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    mouvements = MouvementTresorerie.objects.all()

    if compte_id:
        mouvements = mouvements.filter(compte_id=compte_id)
    if type_mvt:
        mouvements = mouvements.filter(type_mouvement=type_mvt)
    if categorie:
        mouvements = mouvements.filter(categorie=categorie)
    if date_debut:
        mouvements = mouvements.filter(date_mouvement__gte=date_debut)
    if date_fin:
        mouvements = mouvements.filter(date_mouvement__lte=date_fin)

    if format_export == 'excel':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="mouvements_{timezone.now().strftime("%Y%m%d")}.csv"'
        response.write('\ufeff')  # BOM pour Excel

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Date', 'Compte', 'Type', 'Catégorie', 'Libellé', 'Tiers', 'Montant', 'Mode', 'Statut', 'Référence'])

        for mvt in mouvements[:1000]:
            signe = '' if mvt.type_mouvement == 'entree' else '-'
            writer.writerow([
                mvt.date_mouvement.strftime('%d/%m/%Y'),
                mvt.compte.nom,
                mvt.get_type_mouvement_display(),
                mvt.get_categorie_display(),
                mvt.libelle,
                mvt.tiers or '',
                f"{signe}{mvt.montant}",
                mvt.get_mode_paiement_display(),
                mvt.get_statut_display(),
                mvt.reference or '',
            ])

        return response

    elif format_export == 'pdf':
        # Pour le PDF, on utilise une approche simple avec HTML
        from django.template.loader import render_to_string

        html_content = render_to_string('tresorerie/export_mouvements_pdf.html', {
            'mouvements': mouvements[:500],
            'date_export': timezone.now(),
            'date_debut': date_debut,
            'date_fin': date_fin,
        })

        response = HttpResponse(content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="mouvements_{timezone.now().strftime("%Y%m%d")}.html"'
        response.write(html_content)
        return response

    return JsonResponse({'success': False, 'error': 'Format non supporté'}, status=400)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.db.models import Sum, Q, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import json
from datetime import datetime, date, timedelta

from .models import (
    ExerciceComptable, CompteComptable, Journal, EcritureComptable,
    LigneEcriture, TypeOperation, ParametrageFiscal, DeclarationTVA,
    RapportComptable, ConfigurationComptable
)


def dashboard_comptabilite(request):
    """Tableau de bord comptable"""
    config = ConfigurationComptable.get_instance()
    exercice = ExerciceComptable.get_exercice_courant()

    context = {
        'page_title': 'Comptabilité',
        'config': config,
        'exercice': exercice,
    }

    # Si pas configuré, rediriger vers l'assistant
    if not config.est_configure:
        return render(request, 'comptabilite/assistant_configuration.html', context)

    if exercice:
        # Calcul du chiffre d'affaires (classe 7)
        ca_query = LigneEcriture.objects.filter(
            compte__classe='7',
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        )
        ca_annee = ca_query.aggregate(total=Coalesce(Sum('credit'), 0) - Coalesce(Sum('debit'), 0))['total']

        # CA du mois en cours
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        ca_mois = ca_query.filter(
            ecriture__date__gte=debut_mois
        ).aggregate(total=Coalesce(Sum('credit'), 0) - Coalesce(Sum('debit'), 0))['total']

        # Calcul des charges (classe 6)
        charges_query = LigneEcriture.objects.filter(
            compte__classe='6',
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        )
        charges_annee = charges_query.aggregate(total=Coalesce(Sum('debit'), 0) - Coalesce(Sum('credit'), 0))['total']

        charges_mois = charges_query.filter(
            ecriture__date__gte=debut_mois
        ).aggregate(total=Coalesce(Sum('debit'), 0) - Coalesce(Sum('credit'), 0))['total']

        # Résultat
        resultat = ca_annee - charges_annee

        # Créances clients (compte 411)
        creances = LigneEcriture.objects.filter(
            compte__numero__startswith='411',
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        ).aggregate(total=Coalesce(Sum('debit'), 0) - Coalesce(Sum('credit'), 0))['total']

        # Dettes fournisseurs (compte 401)
        dettes = LigneEcriture.objects.filter(
            compte__numero__startswith='401',
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        ).aggregate(total=Coalesce(Sum('credit'), 0) - Coalesce(Sum('debit'), 0))['total']

        # Trésorerie (classe 5)
        tresorerie = LigneEcriture.objects.filter(
            compte__classe='5',
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        ).aggregate(total=Coalesce(Sum('debit'), 0) - Coalesce(Sum('credit'), 0))['total']

        # Statistiques écritures
        nb_ecritures_mois = EcritureComptable.objects.filter(
            exercice=exercice,
            date__gte=debut_mois
        ).count()

        nb_brouillons = EcritureComptable.objects.filter(
            exercice=exercice,
            statut='brouillon'
        ).count()

        # Dernières écritures
        dernieres_ecritures = EcritureComptable.objects.filter(
            exercice=exercice
        ).order_by('-date', '-id')[:10]

        # Données pour le graphique mensuel
        mois_labels = []
        ca_mensuel = []
        charges_mensuel = []

        for i in range(6, 0, -1):
            mois_date = today - timedelta(days=30 * i)
            mois_debut = mois_date.replace(day=1)
            if mois_date.month == 12:
                mois_fin = mois_date.replace(year=mois_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                mois_fin = mois_date.replace(month=mois_date.month + 1, day=1) - timedelta(days=1)

            mois_labels.append(mois_date.strftime('%b'))

            ca_m = LigneEcriture.objects.filter(
                compte__classe='7',
                ecriture__exercice=exercice,
                ecriture__statut='valide',
                ecriture__date__gte=mois_debut,
                ecriture__date__lte=mois_fin
            ).aggregate(total=Coalesce(Sum('credit'), 0))['total']
            ca_mensuel.append(int(ca_m))

            ch_m = LigneEcriture.objects.filter(
                compte__classe='6',
                ecriture__exercice=exercice,
                ecriture__statut='valide',
                ecriture__date__gte=mois_debut,
                ecriture__date__lte=mois_fin
            ).aggregate(total=Coalesce(Sum('debit'), 0))['total']
            charges_mensuel.append(int(ch_m))

        context.update({
            'ca_annee': ca_annee,
            'ca_mois': ca_mois,
            'charges_annee': charges_annee,
            'charges_mois': charges_mois,
            'resultat': resultat,
            'creances': creances,
            'dettes': dettes,
            'tresorerie': tresorerie,
            'nb_ecritures_mois': nb_ecritures_mois,
            'nb_brouillons': nb_brouillons,
            'dernieres_ecritures': dernieres_ecritures,
            'mois_labels': json.dumps(mois_labels),
            'ca_mensuel': json.dumps(ca_mensuel),
            'charges_mensuel': json.dumps(charges_mensuel),
        })

    return render(request, 'comptabilite/dashboard.html', context)


def saisie_ecriture(request):
    """Page de saisie des écritures avec les 3 modes"""
    config = ConfigurationComptable.get_instance()
    exercice = ExerciceComptable.get_exercice_courant()

    if not exercice:
        messages.error(request, "Aucun exercice comptable ouvert. Veuillez créer un exercice.")
        return redirect('comptabilite:dashboard')

    # Récupérer les types d'opérations pour le mode facile
    types_operations = TypeOperation.objects.filter(actif=True).order_by('ordre_affichage')

    # Récupérer les comptes et journaux pour les modes guidé et expert
    comptes = CompteComptable.objects.filter(actif=True).order_by('numero')
    journaux = Journal.objects.filter(actif=True)

    # Grouper les comptes par classe pour le mode guidé
    comptes_par_classe = {}
    for compte in comptes:
        classe_label = dict(CompteComptable.CLASSE_CHOICES).get(compte.classe, compte.classe)
        if classe_label not in comptes_par_classe:
            comptes_par_classe[classe_label] = []
        comptes_par_classe[classe_label].append(compte)

    context = {
        'page_title': 'Nouvelle écriture',
        'config': config,
        'exercice': exercice,
        'types_operations': types_operations,
        'comptes': comptes,
        'journaux': journaux,
        'comptes_par_classe': comptes_par_classe,
        'mode_defaut': config.mode_saisie_defaut,
        'today': timezone.now().date(),
    }

    return render(request, 'comptabilite/saisie_ecriture.html', context)


@require_POST
def api_creer_ecriture_facile(request):
    """API pour créer une écriture en mode facile"""
    try:
        data = json.loads(request.body)
        type_operation_code = data.get('type_operation')
        montant = Decimal(str(data.get('montant', 0)))
        date_str = data.get('date')
        description = data.get('description', '')

        if montant <= 0:
            return JsonResponse({'success': False, 'error': 'Le montant doit être positif'})

        type_operation = get_object_or_404(TypeOperation, code=type_operation_code)
        exercice = ExerciceComptable.get_exercice_courant()

        if not exercice:
            return JsonResponse({'success': False, 'error': 'Aucun exercice ouvert'})

        date_ecriture = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Créer l'écriture
        numero = EcritureComptable.generer_numero(type_operation.journal, date_ecriture)
        ecriture = EcritureComptable.objects.create(
            numero=numero,
            date=date_ecriture,
            journal=type_operation.journal,
            exercice=exercice,
            libelle=f"{type_operation.libelle} - {description}",
            statut='brouillon',
            origine='manuelle'
        )

        # Créer les lignes
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=type_operation.compte_debit,
            libelle=description or type_operation.libelle,
            debit=montant,
            credit=0
        )

        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=type_operation.compte_credit,
            libelle=description or type_operation.libelle,
            debit=0,
            credit=montant
        )

        return JsonResponse({
            'success': True,
            'ecriture_id': ecriture.id,
            'numero': ecriture.numero,
            'message': f'Écriture {numero} créée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_creer_ecriture_guidee(request):
    """API pour créer une écriture en mode guidé"""
    try:
        data = json.loads(request.body)
        journal_id = data.get('journal')
        compte_debit_id = data.get('compte_debit')
        compte_credit_id = data.get('compte_credit')
        montant = Decimal(str(data.get('montant', 0)))
        date_str = data.get('date')
        libelle = data.get('libelle', '')

        if montant <= 0:
            return JsonResponse({'success': False, 'error': 'Le montant doit être positif'})

        journal = get_object_or_404(Journal, id=journal_id)
        compte_debit = get_object_or_404(CompteComptable, id=compte_debit_id)
        compte_credit = get_object_or_404(CompteComptable, id=compte_credit_id)
        exercice = ExerciceComptable.get_exercice_courant()

        if not exercice:
            return JsonResponse({'success': False, 'error': 'Aucun exercice ouvert'})

        date_ecriture = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Créer l'écriture
        numero = EcritureComptable.generer_numero(journal, date_ecriture)
        ecriture = EcritureComptable.objects.create(
            numero=numero,
            date=date_ecriture,
            journal=journal,
            exercice=exercice,
            libelle=libelle,
            statut='brouillon',
            origine='manuelle'
        )

        # Créer les lignes
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_debit,
            libelle=libelle,
            debit=montant,
            credit=0
        )

        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_credit,
            libelle=libelle,
            debit=0,
            credit=montant
        )

        return JsonResponse({
            'success': True,
            'ecriture_id': ecriture.id,
            'numero': ecriture.numero,
            'message': f'Écriture {numero} créée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_creer_ecriture_expert(request):
    """API pour créer une écriture en mode expert (multi-lignes)"""
    try:
        data = json.loads(request.body)
        journal_id = data.get('journal')
        date_str = data.get('date')
        libelle = data.get('libelle', '')
        lignes = data.get('lignes', [])

        if not lignes or len(lignes) < 2:
            return JsonResponse({'success': False, 'error': 'Une écriture doit avoir au moins 2 lignes'})

        journal = get_object_or_404(Journal, id=journal_id)
        exercice = ExerciceComptable.get_exercice_courant()

        if not exercice:
            return JsonResponse({'success': False, 'error': 'Aucun exercice ouvert'})

        date_ecriture = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Vérifier l'équilibre
        total_debit = sum(Decimal(str(l.get('debit', 0))) for l in lignes)
        total_credit = sum(Decimal(str(l.get('credit', 0))) for l in lignes)

        if total_debit != total_credit:
            return JsonResponse({
                'success': False,
                'error': f'L\'écriture n\'est pas équilibrée. Débit: {total_debit}, Crédit: {total_credit}'
            })

        # Créer l'écriture
        numero = EcritureComptable.generer_numero(journal, date_ecriture)
        ecriture = EcritureComptable.objects.create(
            numero=numero,
            date=date_ecriture,
            journal=journal,
            exercice=exercice,
            libelle=libelle,
            statut='brouillon',
            origine='manuelle'
        )

        # Créer les lignes
        for ligne_data in lignes:
            compte = get_object_or_404(CompteComptable, id=ligne_data.get('compte'))
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte,
                libelle=ligne_data.get('libelle', libelle),
                debit=Decimal(str(ligne_data.get('debit', 0))),
                credit=Decimal(str(ligne_data.get('credit', 0)))
            )

        return JsonResponse({
            'success': True,
            'ecriture_id': ecriture.id,
            'numero': ecriture.numero,
            'message': f'Écriture {numero} créée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_valider_ecriture(request):
    """Valider une écriture brouillon"""
    try:
        data = json.loads(request.body)
        ecriture_id = data.get('ecriture_id')

        ecriture = get_object_or_404(EcritureComptable, id=ecriture_id)

        if not ecriture.est_equilibree:
            return JsonResponse({
                'success': False,
                'error': f'L\'écriture n\'est pas équilibrée'
            })

        ecriture.valider()

        return JsonResponse({
            'success': True,
            'message': f'Écriture {ecriture.numero} validée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def liste_ecritures(request):
    """Liste des écritures comptables"""
    exercice = ExerciceComptable.get_exercice_courant()

    ecritures = EcritureComptable.objects.all()

    # Filtres
    journal_filter = request.GET.get('journal')
    statut_filter = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    search = request.GET.get('search')

    if exercice:
        ecritures = ecritures.filter(exercice=exercice)

    if journal_filter:
        ecritures = ecritures.filter(journal_id=journal_filter)

    if statut_filter:
        ecritures = ecritures.filter(statut=statut_filter)

    if date_debut:
        ecritures = ecritures.filter(date__gte=date_debut)

    if date_fin:
        ecritures = ecritures.filter(date__lte=date_fin)

    if search:
        ecritures = ecritures.filter(
            Q(numero__icontains=search) |
            Q(libelle__icontains=search) |
            Q(reference__icontains=search)
        )

    ecritures = ecritures.order_by('-date', '-numero')

    # Pagination
    paginator = Paginator(ecritures, 25)
    page = request.GET.get('page')
    ecritures_page = paginator.get_page(page)

    context = {
        'page_title': 'Écritures comptables',
        'ecritures': ecritures_page,
        'journaux': Journal.objects.filter(actif=True),
        'exercice': exercice,
        'statuts': EcritureComptable.STATUT_CHOICES,
    }

    return render(request, 'comptabilite/liste_ecritures.html', context)


def detail_ecriture(request, ecriture_id):
    """Détail d'une écriture"""
    ecriture = get_object_or_404(EcritureComptable, id=ecriture_id)

    context = {
        'page_title': f'Écriture {ecriture.numero}',
        'ecriture': ecriture,
        'lignes': ecriture.lignes.all().select_related('compte'),
    }

    return render(request, 'comptabilite/detail_ecriture.html', context)


def journaux(request):
    """Liste des journaux comptables avec leurs écritures"""
    exercice = ExerciceComptable.get_exercice_courant()
    journal_id = request.GET.get('journal')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    journaux_list = Journal.objects.filter(actif=True)
    journal_selectionne = None
    ecritures = []

    if journal_id:
        journal_selectionne = get_object_or_404(Journal, id=journal_id)
        ecritures = EcritureComptable.objects.filter(
            journal=journal_selectionne,
            statut='valide'
        )

        if exercice:
            ecritures = ecritures.filter(exercice=exercice)

        if date_debut:
            ecritures = ecritures.filter(date__gte=date_debut)

        if date_fin:
            ecritures = ecritures.filter(date__lte=date_fin)

        ecritures = ecritures.order_by('date', 'numero').prefetch_related('lignes__compte')

    context = {
        'page_title': 'Journaux comptables',
        'journaux': journaux_list,
        'journal_selectionne': journal_selectionne,
        'ecritures': ecritures,
        'exercice': exercice,
    }

    return render(request, 'comptabilite/journaux.html', context)


def grand_livre(request):
    """Grand livre comptable"""
    exercice = ExerciceComptable.get_exercice_courant()
    compte_id = request.GET.get('compte')
    classe_filter = request.GET.get('classe')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    comptes = CompteComptable.objects.filter(actif=True).order_by('numero')

    if classe_filter:
        comptes = comptes.filter(classe=classe_filter)

    compte_selectionne = None
    mouvements = []
    solde_progressif = Decimal('0')

    if compte_id:
        compte_selectionne = get_object_or_404(CompteComptable, id=compte_id)
        lignes = LigneEcriture.objects.filter(
            compte=compte_selectionne,
            ecriture__statut='valide'
        ).select_related('ecriture', 'ecriture__journal')

        if exercice:
            lignes = lignes.filter(ecriture__exercice=exercice)

        if date_debut:
            lignes = lignes.filter(ecriture__date__gte=date_debut)

        if date_fin:
            lignes = lignes.filter(ecriture__date__lte=date_fin)

        lignes = lignes.order_by('ecriture__date', 'ecriture__numero')

        # Calculer le solde progressif
        for ligne in lignes:
            solde_progressif += ligne.debit - ligne.credit
            mouvements.append({
                'ligne': ligne,
                'solde': solde_progressif
            })

    context = {
        'page_title': 'Grand livre',
        'comptes': comptes,
        'compte_selectionne': compte_selectionne,
        'mouvements': mouvements,
        'exercice': exercice,
        'classes': CompteComptable.CLASSE_CHOICES,
    }

    return render(request, 'comptabilite/grand_livre.html', context)


def balance(request):
    """Balance générale des comptes"""
    exercice = ExerciceComptable.get_exercice_courant()
    classe_filter = request.GET.get('classe')
    date_fin = request.GET.get('date_fin', timezone.now().date())

    if isinstance(date_fin, str):
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

    comptes = CompteComptable.objects.filter(actif=True).order_by('numero')

    if classe_filter:
        comptes = comptes.filter(classe=classe_filter)

    balance_data = []
    totaux = {'debit': 0, 'credit': 0, 'solde_debiteur': 0, 'solde_crediteur': 0}

    for compte in comptes:
        lignes = LigneEcriture.objects.filter(
            compte=compte,
            ecriture__statut='valide'
        )

        if exercice:
            lignes = lignes.filter(
                ecriture__exercice=exercice,
                ecriture__date__lte=date_fin
            )

        agg = lignes.aggregate(
            total_debit=Coalesce(Sum('debit'), Decimal('0')),
            total_credit=Coalesce(Sum('credit'), Decimal('0'))
        )

        total_debit = agg['total_debit']
        total_credit = agg['total_credit']
        solde = total_debit - total_credit

        if total_debit > 0 or total_credit > 0:
            balance_data.append({
                'compte': compte,
                'debit': total_debit,
                'credit': total_credit,
                'solde_debiteur': solde if solde > 0 else 0,
                'solde_crediteur': abs(solde) if solde < 0 else 0
            })

            totaux['debit'] += total_debit
            totaux['credit'] += total_credit
            totaux['solde_debiteur'] += solde if solde > 0 else 0
            totaux['solde_crediteur'] += abs(solde) if solde < 0 else 0

    context = {
        'page_title': 'Balance générale',
        'balance': balance_data,
        'totaux': totaux,
        'exercice': exercice,
        'classes': CompteComptable.CLASSE_CHOICES,
        'date_fin': date_fin,
    }

    return render(request, 'comptabilite/balance.html', context)


def etats_financiers(request):
    """États financiers OHADA (Bilan et Compte de résultat)"""
    exercice = ExerciceComptable.get_exercice_courant()
    type_etat = request.GET.get('type', 'bilan')

    context = {
        'page_title': 'États financiers',
        'exercice': exercice,
        'type_etat': type_etat,
    }

    if exercice:
        if type_etat == 'bilan':
            context['bilan'] = generer_bilan(exercice)
        elif type_etat == 'resultat':
            context['resultat'] = generer_compte_resultat(exercice)
        elif type_etat == 'flux':
            context['flux'] = generer_flux_tresorerie(exercice)

    return render(request, 'comptabilite/etats_financiers.html', context)


def generer_bilan(exercice):
    """Génère les données du bilan"""
    def get_solde_comptes(prefix_list):
        total = Decimal('0')
        for prefix in prefix_list:
            lignes = LigneEcriture.objects.filter(
                compte__numero__startswith=prefix,
                ecriture__exercice=exercice,
                ecriture__statut='valide'
            )
            agg = lignes.aggregate(
                debit=Coalesce(Sum('debit'), Decimal('0')),
                credit=Coalesce(Sum('credit'), Decimal('0'))
            )
            total += agg['debit'] - agg['credit']
        return total

    bilan = {
        'actif': {
            'immobilisations': abs(get_solde_comptes(['2'])),
            'stocks': abs(get_solde_comptes(['3'])),
            'creances_clients': abs(get_solde_comptes(['411'])),
            'autres_creances': abs(get_solde_comptes(['41']) - get_solde_comptes(['411'])),
            'banque': abs(get_solde_comptes(['52'])),
            'caisse': abs(get_solde_comptes(['57'])),
        },
        'passif': {
            'capital': abs(get_solde_comptes(['10'])),
            'reserves': abs(get_solde_comptes(['11'])),
            'resultat': 0,  # Calculé après
            'dettes_fournisseurs': abs(get_solde_comptes(['401'])),
            'dettes_fiscales': abs(get_solde_comptes(['44'])),
            'autres_dettes': abs(get_solde_comptes(['40']) - get_solde_comptes(['401'])),
        }
    }

    # Calcul du résultat
    produits = abs(get_solde_comptes(['7']))
    charges = abs(get_solde_comptes(['6']))
    bilan['passif']['resultat'] = produits - charges

    # Totaux
    bilan['total_actif'] = sum(bilan['actif'].values())
    bilan['total_passif'] = sum(bilan['passif'].values())

    return bilan


def generer_compte_resultat(exercice):
    """Génère les données du compte de résultat"""
    def get_solde_comptes(prefix_list):
        total = Decimal('0')
        for prefix in prefix_list:
            lignes = LigneEcriture.objects.filter(
                compte__numero__startswith=prefix,
                ecriture__exercice=exercice,
                ecriture__statut='valide'
            )
            agg = lignes.aggregate(
                debit=Coalesce(Sum('debit'), Decimal('0')),
                credit=Coalesce(Sum('credit'), Decimal('0'))
            )
            # Pour les produits, le solde est créditeur
            # Pour les charges, le solde est débiteur
            if prefix.startswith('7'):
                total += agg['credit'] - agg['debit']
            else:
                total += agg['debit'] - agg['credit']
        return total

    resultat = {
        'produits': {
            'honoraires': get_solde_comptes(['706']),
            'emoluments': get_solde_comptes(['707']),
            'autres_produits': get_solde_comptes(['70']) - get_solde_comptes(['706', '707']),
            'produits_financiers': get_solde_comptes(['76', '77']),
        },
        'charges': {
            'achats': get_solde_comptes(['60']),
            'services_exterieurs': get_solde_comptes(['61', '62']),
            'charges_personnel': get_solde_comptes(['64']),
            'impots_taxes': get_solde_comptes(['63']),
            'dotations_amortissements': get_solde_comptes(['68']),
            'charges_financieres': get_solde_comptes(['67']),
        }
    }

    resultat['total_produits'] = sum(resultat['produits'].values())
    resultat['total_charges'] = sum(resultat['charges'].values())
    resultat['resultat_net'] = resultat['total_produits'] - resultat['total_charges']

    return resultat


def generer_flux_tresorerie(exercice):
    """Génère un tableau simplifié des flux de trésorerie"""
    def get_variation(prefix_list):
        total = Decimal('0')
        for prefix in prefix_list:
            lignes = LigneEcriture.objects.filter(
                compte__numero__startswith=prefix,
                ecriture__exercice=exercice,
                ecriture__statut='valide'
            )
            agg = lignes.aggregate(
                debit=Coalesce(Sum('debit'), Decimal('0')),
                credit=Coalesce(Sum('credit'), Decimal('0'))
            )
            total += agg['debit'] - agg['credit']
        return total

    flux = {
        'exploitation': {
            'encaissements_clients': get_variation(['52', '57']),
            'decaissements_fournisseurs': 0,
        },
        'investissement': {
            'acquisitions': get_variation(['2']),
        },
        'financement': {
            'apports': get_variation(['10']),
        }
    }

    return flux


def plan_comptable(request):
    """Affichage et gestion du plan comptable"""
    classe_filter = request.GET.get('classe')
    search = request.GET.get('search')

    comptes = CompteComptable.objects.all().order_by('numero')

    if classe_filter:
        comptes = comptes.filter(classe=classe_filter)

    if search:
        comptes = comptes.filter(
            Q(numero__icontains=search) |
            Q(libelle__icontains=search)
        )

    # Grouper par classe
    comptes_par_classe = {}
    for compte in comptes:
        if compte.classe not in comptes_par_classe:
            comptes_par_classe[compte.classe] = []
        comptes_par_classe[compte.classe].append(compte)

    context = {
        'page_title': 'Plan comptable OHADA',
        'comptes_par_classe': comptes_par_classe,
        'classes': CompteComptable.CLASSE_CHOICES,
        'total_comptes': comptes.count(),
    }

    return render(request, 'comptabilite/plan_comptable.html', context)


def gestion_tva(request):
    """Gestion de la TVA et déclarations"""
    exercice = ExerciceComptable.get_exercice_courant()
    declarations = DeclarationTVA.objects.filter(exercice=exercice) if exercice else []

    # Calcul TVA courante
    tva_collectee = Decimal('0')
    tva_deductible = Decimal('0')

    if exercice:
        try:
            params = exercice.parametres_fiscaux
            if params.compte_tva_collectee:
                tva_collectee = LigneEcriture.objects.filter(
                    compte=params.compte_tva_collectee,
                    ecriture__exercice=exercice,
                    ecriture__statut='valide'
                ).aggregate(total=Coalesce(Sum('credit'), Decimal('0')))['total']

            if params.compte_tva_deductible:
                tva_deductible = LigneEcriture.objects.filter(
                    compte=params.compte_tva_deductible,
                    ecriture__exercice=exercice,
                    ecriture__statut='valide'
                ).aggregate(total=Coalesce(Sum('debit'), Decimal('0')))['total']
        except ParametrageFiscal.DoesNotExist:
            pass

    context = {
        'page_title': 'Gestion TVA',
        'exercice': exercice,
        'declarations': declarations,
        'tva_collectee': tva_collectee,
        'tva_deductible': tva_deductible,
        'tva_a_payer': tva_collectee - tva_deductible,
    }

    return render(request, 'comptabilite/gestion_tva.html', context)


def cloture_exercice(request):
    """Assistant de clôture d'exercice"""
    exercice = ExerciceComptable.get_exercice_courant()

    # Vérifications avant clôture
    verifications = []

    if exercice:
        # Écritures non validées
        nb_brouillons = EcritureComptable.objects.filter(
            exercice=exercice,
            statut='brouillon'
        ).count()
        verifications.append({
            'label': 'Écritures brouillon à valider',
            'valeur': nb_brouillons,
            'ok': nb_brouillons == 0,
            'message': f'{nb_brouillons} écriture(s) en brouillon' if nb_brouillons > 0 else 'Toutes les écritures sont validées'
        })

        # Balance équilibrée
        totaux = LigneEcriture.objects.filter(
            ecriture__exercice=exercice,
            ecriture__statut='valide'
        ).aggregate(
            total_debit=Coalesce(Sum('debit'), Decimal('0')),
            total_credit=Coalesce(Sum('credit'), Decimal('0'))
        )
        equilibre = totaux['total_debit'] == totaux['total_credit']
        verifications.append({
            'label': 'Équilibre de la balance',
            'valeur': f"D: {totaux['total_debit']} / C: {totaux['total_credit']}",
            'ok': equilibre,
            'message': 'Balance équilibrée' if equilibre else 'La balance n\'est pas équilibrée'
        })

    context = {
        'page_title': 'Clôture d\'exercice',
        'exercice': exercice,
        'verifications': verifications,
    }

    return render(request, 'comptabilite/cloture_exercice.html', context)


@require_POST
def api_configurer_comptabilite(request):
    """Configure le module comptabilité"""
    try:
        data = json.loads(request.body)

        # Créer l'exercice
        date_debut = datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date()
        date_fin = datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date()

        exercice = ExerciceComptable.objects.create(
            libelle=data.get('libelle', f'Exercice {date_debut.year}'),
            date_debut=date_debut,
            date_fin=date_fin,
            statut='ouvert',
            est_premier_exercice=True
        )

        # Créer les paramètres fiscaux
        ParametrageFiscal.objects.create(
            exercice=exercice,
            taux_tva=Decimal(str(data.get('taux_tva', 18)))
        )

        # Marquer comme configuré
        config = ConfigurationComptable.get_instance()
        config.est_configure = True
        config.date_configuration = timezone.now()
        config.save()

        return JsonResponse({
            'success': True,
            'message': 'Configuration terminée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_GET
def api_comptes_par_classe(request, classe):
    """Retourne les comptes d'une classe spécifique"""
    comptes = CompteComptable.objects.filter(
        classe=classe,
        actif=True
    ).values('id', 'numero', 'libelle')

    return JsonResponse({'comptes': list(comptes)})


def aide_comptabilite(request):
    """Page d'aide et tutoriels"""
    context = {
        'page_title': 'Aide - Comptabilité',
    }
    return render(request, 'comptabilite/aide.html', context)


def rapports(request):
    """Page de génération des rapports"""
    exercice = ExerciceComptable.get_exercice_courant()

    context = {
        'page_title': 'Rapports comptables',
        'exercice': exercice,
    }

    return render(request, 'comptabilite/rapports.html', context)

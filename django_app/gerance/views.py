"""
Vues du module Gerance Immobiliere
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import calendar

from .models import (
    Proprietaire, BienImmobilier, Locataire, Bail, Loyer,
    Quittance, EtatDesLieux, Incident, ReversementProprietaire
)


def get_default_context(request):
    """Contexte par defaut pour tous les templates"""
    # CORRECTION #17: Utiliser request.user au lieu de current_user hardcode
    if request.user.is_authenticated:
        current_user = {
            'id': request.user.id,
            'nom': request.user.get_full_name() or request.user.username,
            'role': 'admin' if request.user.is_superuser else 'user',
            'email': request.user.email,
            'initials': ''.join([n[0].upper() for n in (request.user.get_full_name() or request.user.username).split()[:2]])
        }
    else:
        current_user = {
            'id': 0,
            'nom': 'Utilisateur',
            'role': 'guest',
            'email': '',
            'initials': 'U'
        }

    modules = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'home', 'category': 'main', 'url': 'gestion:dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'gestion:dossiers', 'badge': 14},
        {'id': 'facturation', 'label': 'Facturation & MECeF', 'icon': 'file-text', 'category': 'main', 'url': 'gestion:facturation'},
        {'id': 'calcul', 'label': 'Calcul Recouvrement', 'icon': 'calculator', 'category': 'main', 'url': 'gestion:calcul'},
        {'id': 'creanciers', 'label': 'Recouvrement Creances', 'icon': 'landmark', 'category': 'main', 'url': 'gestion:creanciers'},
        {'id': 'tresorerie', 'label': 'Tresorerie', 'icon': 'piggy-bank', 'category': 'finance', 'url': 'tresorerie:dashboard'},
        {'id': 'comptabilite', 'label': 'Comptabilite', 'icon': 'book-open', 'category': 'finance', 'url': 'comptabilite:dashboard'},
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh:dashboard'},
        {'id': 'drive', 'label': 'Drive', 'icon': 'hard-drive', 'category': 'gestion', 'url': 'documents:drive'},
        {'id': 'gerance', 'label': 'Gerance Immobiliere', 'icon': 'building-2', 'category': 'gestion', 'url': 'gerance:dashboard'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda:home'},
        {'id': 'parametres', 'label': 'Parametres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres:index'},
        {'id': 'securite', 'label': 'Securite & Acces', 'icon': 'shield', 'category': 'admin', 'url': 'gestion:securite'},
    ]

    return {
        'current_user': current_user,
        'modules': modules,
        'active_module': 'gerance',
    }


@login_required
def dashboard(request):
    """Vue principale du module Gerance"""
    context = get_default_context(request)
    context['page_title'] = 'Gerance Immobiliere'

    # Statistiques
    nb_proprietaires = Proprietaire.objects.filter(actif=True).count()
    nb_biens = BienImmobilier.objects.count()
    nb_biens_loues = BienImmobilier.objects.filter(statut='loue').count()
    nb_baux_actifs = Bail.objects.filter(statut='actif').count()

    # Loyers du mois
    mois_actuel = timezone.now().month
    annee_actuelle = timezone.now().year

    loyers_mois = Loyer.objects.filter(mois=mois_actuel, annee=annee_actuelle)
    total_a_percevoir = loyers_mois.aggregate(total=Sum('montant_total'))['total'] or Decimal('0')
    total_percu = loyers_mois.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
    loyers_impayes = loyers_mois.filter(statut__in=['retard', 'impaye']).count()

    # Derniers baux
    derniers_baux = Bail.objects.filter(statut='actif').order_by('-date_debut')[:5]

    # Incidents en cours
    incidents_en_cours = Incident.objects.filter(statut__in=['signale', 'en_cours']).order_by('-date_signalement')[:5]

    # Biens libres
    biens_libres = BienImmobilier.objects.filter(statut='libre')[:5]

    # Baux expirant bientot (dans 60 jours)
    date_limite = timezone.now().date() + timedelta(days=60)
    baux_expirant = Bail.objects.filter(
        statut='actif',
        date_fin__lte=date_limite
    ).order_by('date_fin')[:5]

    context.update({
        'stats': {
            'proprietaires': nb_proprietaires,
            'biens': nb_biens,
            'biens_loues': nb_biens_loues,
            'taux_occupation': round((nb_biens_loues / nb_biens * 100) if nb_biens > 0 else 0, 1),
            'baux_actifs': nb_baux_actifs,
            'total_a_percevoir': total_a_percevoir,
            'total_percu': total_percu,
            'loyers_impayes': loyers_impayes,
        },
        'derniers_baux': derniers_baux,
        'incidents_en_cours': incidents_en_cours,
        'biens_libres': biens_libres,
        'baux_expirant': baux_expirant,
        'mois_actuel': mois_actuel,
        'annee_actuelle': annee_actuelle,
    })

    return render(request, 'gerance/dashboard.html', context)


@login_required
def proprietaires(request):
    """Liste des proprietaires"""
    context = get_default_context(request)
    context['page_title'] = 'Proprietaires'

    q = request.GET.get('q', '')
    type_filter = request.GET.get('type', '')

    proprietaires_list = Proprietaire.objects.filter(actif=True).annotate(
        nb_biens=Count('biens')
    )

    if q:
        proprietaires_list = proprietaires_list.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(telephone__icontains=q) | Q(email__icontains=q)
        )
    if type_filter:
        proprietaires_list = proprietaires_list.filter(type_proprietaire=type_filter)

    context['proprietaires'] = proprietaires_list

    return render(request, 'gerance/proprietaires.html', context)


# CORRECTION #18: Vue detail proprietaire
@login_required
def proprietaire_detail(request, pk):
    """Detail d'un proprietaire"""
    context = get_default_context(request)
    proprietaire = get_object_or_404(Proprietaire, id=pk)
    context['page_title'] = f'Proprietaire - {proprietaire}'
    context['proprietaire'] = proprietaire
    context['biens'] = proprietaire.biens.all()
    context['reversements'] = proprietaire.reversements.order_by('-annee', '-mois')[:12]

    return render(request, 'gerance/proprietaire_detail.html', context)


@login_required
def biens(request):
    """Liste des biens immobiliers"""
    context = get_default_context(request)
    context['page_title'] = 'Biens immobiliers'

    statut = request.GET.get('statut')
    proprietaire_id = request.GET.get('proprietaire')
    type_bien = request.GET.get('type')

    biens_qs = BienImmobilier.objects.all().select_related('proprietaire')

    if statut:
        biens_qs = biens_qs.filter(statut=statut)
    if proprietaire_id:
        biens_qs = biens_qs.filter(proprietaire_id=proprietaire_id)
    if type_bien:
        biens_qs = biens_qs.filter(type_bien=type_bien)

    context['biens'] = biens_qs
    context['proprietaires'] = Proprietaire.objects.filter(actif=True)
    context['types_bien'] = BienImmobilier.TYPES_BIEN
    context['statuts'] = BienImmobilier.STATUTS

    return render(request, 'gerance/biens.html', context)


# CORRECTION #19: Vue detail bien
@login_required
def bien_detail(request, pk):
    """Detail d'un bien immobilier"""
    context = get_default_context(request)
    bien = get_object_or_404(BienImmobilier, id=pk)
    context['page_title'] = f'Bien - {bien.designation}'
    context['bien'] = bien
    context['baux'] = bien.baux.all().order_by('-date_debut')
    context['incidents'] = bien.incidents.all().order_by('-date_signalement')[:10]

    return render(request, 'gerance/bien_detail.html', context)


@login_required
def locataires(request):
    """Liste des locataires"""
    context = get_default_context(request)
    context['page_title'] = 'Locataires'

    locataires_list = Locataire.objects.filter(actif=True)
    context['locataires'] = locataires_list

    return render(request, 'gerance/locataires.html', context)


# CORRECTION #20: Vue detail locataire
@login_required
def locataire_detail(request, pk):
    """Detail d'un locataire"""
    context = get_default_context(request)
    locataire = get_object_or_404(Locataire, id=pk)
    context['page_title'] = f'Locataire - {locataire}'
    context['locataire'] = locataire
    context['baux'] = locataire.baux.all().order_by('-date_debut')

    return render(request, 'gerance/locataire_detail.html', context)


@login_required
def baux_view(request):
    """Liste des baux"""
    context = get_default_context(request)
    context['page_title'] = 'Baux'

    statut = request.GET.get('statut', 'actif')

    baux_qs = Bail.objects.all().select_related('bien', 'locataire', 'bien__proprietaire')

    if statut and statut != 'all':
        baux_qs = baux_qs.filter(statut=statut)

    context['baux'] = baux_qs
    context['statuts'] = Bail.STATUTS
    context['statut_filtre'] = statut

    return render(request, 'gerance/baux.html', context)


# CORRECTION #21: Vue detail bail
@login_required
def bail_detail(request, pk):
    """Detail d'un bail"""
    context = get_default_context(request)
    bail = get_object_or_404(Bail, id=pk)
    context['page_title'] = f'Bail - {bail.reference}'
    context['bail'] = bail
    context['loyers'] = bail.loyers.order_by('-annee', '-mois')[:24]
    context['etats_lieux'] = bail.etats_lieux.all()
    context['incidents'] = bail.incidents.all()

    return render(request, 'gerance/bail_detail.html', context)


@login_required
def loyers_view(request):
    """Gestion des loyers"""
    context = get_default_context(request)
    context['page_title'] = 'Loyers'

    mois = int(request.GET.get('mois', timezone.now().month))
    annee = int(request.GET.get('annee', timezone.now().year))
    statut = request.GET.get('statut')

    loyers_qs = Loyer.objects.filter(mois=mois, annee=annee).select_related(
        'bail', 'bail__bien', 'bail__locataire'
    )

    if statut:
        loyers_qs = loyers_qs.filter(statut=statut)

    # Totaux
    totaux = loyers_qs.aggregate(
        total=Sum('montant_total'),
        paye=Sum('montant_paye'),
        reste=Sum('reste_a_payer')
    )

    context['loyers'] = loyers_qs
    context['mois'] = mois
    context['annee'] = annee
    context['totaux'] = totaux
    context['statuts'] = Loyer.STATUTS

    return render(request, 'gerance/loyers.html', context)


# CORRECTION #29: Vue liste des quittances
@login_required
def quittances_view(request):
    """Liste des quittances"""
    context = get_default_context(request)
    context['page_title'] = 'Quittances'

    quittances_qs = Quittance.objects.all().select_related(
        'loyer', 'loyer__bail', 'loyer__bail__bien', 'loyer__bail__locataire'
    ).order_by('-date_emission')[:100]

    context['quittances'] = quittances_qs

    return render(request, 'gerance/quittances.html', context)


@login_required
def incidents_view(request):
    """Gestion des incidents"""
    context = get_default_context(request)
    context['page_title'] = 'Incidents'

    statut = request.GET.get('statut')
    priorite = request.GET.get('priorite')

    incidents_qs = Incident.objects.all().select_related('bien', 'bail')

    if statut:
        incidents_qs = incidents_qs.filter(statut=statut)
    if priorite:
        incidents_qs = incidents_qs.filter(priorite=priorite)

    context['incidents'] = incidents_qs[:50]
    context['statuts'] = Incident.STATUTS
    context['priorites'] = Incident.PRIORITES

    return render(request, 'gerance/incidents.html', context)


@login_required
def reversements_view(request):
    """Reversements aux proprietaires"""
    context = get_default_context(request)
    context['page_title'] = 'Reversements'

    mois = int(request.GET.get('mois', timezone.now().month))
    annee = int(request.GET.get('annee', timezone.now().year))

    reversements_qs = ReversementProprietaire.objects.filter(
        mois=mois, annee=annee
    ).select_related('proprietaire')

    context['reversements'] = reversements_qs
    context['mois'] = mois
    context['annee'] = annee

    return render(request, 'gerance/reversements.html', context)


# CORRECTION #23: Vues/templates pour EtatDesLieux
@login_required
def etats_lieux_view(request):
    """Liste des etats des lieux"""
    context = get_default_context(request)
    context['page_title'] = 'Etats des lieux'

    etats_qs = EtatDesLieux.objects.all().select_related('bail', 'bail__bien', 'bail__locataire').order_by('-date_etat')[:50]

    context['etats_lieux'] = etats_qs

    return render(request, 'gerance/etats_lieux.html', context)


# ==========================================================================
# API ENDPOINTS - TOUS AVEC @login_required (CORRECTIONS #8-16)
# ==========================================================================

@login_required  # CORRECTION #8
@require_POST
def api_creer_proprietaire(request):
    """Creer un nouveau proprietaire"""
    try:
        data = json.loads(request.body)
        proprietaire = Proprietaire.objects.create(
            type_proprietaire=data.get('type_proprietaire', 'particulier'),
            nom=data.get('nom'),
            prenom=data.get('prenom'),
            adresse=data.get('adresse'),
            ville=data.get('ville'),
            telephone=data.get('telephone'),
            email=data.get('email'),
            taux_honoraires=Decimal(str(data.get('taux_honoraires', 10))),
        )
        return JsonResponse({
            'success': True,
            'proprietaire_id': str(proprietaire.id),
            'message': 'Proprietaire cree avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #9
@require_POST
def api_creer_bien(request):
    """Creer un nouveau bien immobilier"""
    try:
        data = json.loads(request.body)
        proprietaire = get_object_or_404(Proprietaire, id=data.get('proprietaire_id'))

        bien = BienImmobilier.objects.create(
            proprietaire=proprietaire,
            reference=data.get('reference'),
            designation=data.get('designation'),
            type_bien=data.get('type_bien', 'appartement'),
            adresse=data.get('adresse'),
            ville=data.get('ville'),
            surface=data.get('surface'),
            nombre_pieces=data.get('nombre_pieces'),
            loyer_mensuel=Decimal(str(data.get('loyer_mensuel'))),
            charges_mensuelles=Decimal(str(data.get('charges_mensuelles', 0))),
            depot_garantie=Decimal(str(data.get('depot_garantie', 0))),
        )
        return JsonResponse({
            'success': True,
            'bien_id': str(bien.id),
            'message': 'Bien cree avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #10
@require_POST
def api_creer_locataire(request):
    """Creer un nouveau locataire"""
    try:
        data = json.loads(request.body)
        locataire = Locataire.objects.create(
            type_locataire=data.get('type_locataire', 'particulier'),
            nom=data.get('nom'),
            prenom=data.get('prenom'),
            telephone=data.get('telephone'),
            email=data.get('email'),
            profession=data.get('profession'),
        )
        return JsonResponse({
            'success': True,
            'locataire_id': str(locataire.id),
            'message': 'Locataire cree avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #11
@require_POST
def api_creer_bail(request):
    """Creer un nouveau bail"""
    try:
        data = json.loads(request.body)
        bien = get_object_or_404(BienImmobilier, id=data.get('bien_id'))
        locataire = get_object_or_404(Locataire, id=data.get('locataire_id'))

        # Generer reference du bail
        annee = timezone.now().year
        count = Bail.objects.filter(reference__startswith=f"BAIL-{annee}").count() + 1
        reference = f"BAIL-{annee}-{count:04d}"

        bail = Bail.objects.create(
            bien=bien,
            locataire=locataire,
            reference=reference,
            type_bail=data.get('type_bail', 'habitation'),
            date_debut=data.get('date_debut'),
            date_fin=data.get('date_fin'),
            duree_mois=data.get('duree_mois', 12),
            loyer_mensuel=Decimal(str(data.get('loyer_mensuel'))),
            charges_mensuelles=Decimal(str(data.get('charges_mensuelles', 0))),
            depot_garantie=Decimal(str(data.get('depot_garantie', 0))),
            jour_paiement=data.get('jour_paiement', 5),
        )

        # Mettre a jour le statut du bien
        bien.statut = 'loue'
        bien.save()

        return JsonResponse({
            'success': True,
            'bail_id': str(bail.id),
            'reference': reference,
            'message': 'Bail cree avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #12
@require_POST
def api_enregistrer_paiement(request):
    """Enregistrer un paiement de loyer"""
    try:
        data = json.loads(request.body)
        loyer = get_object_or_404(Loyer, id=data.get('loyer_id'))

        montant = Decimal(str(data.get('montant')))
        loyer.montant_paye += montant
        loyer.date_paiement = data.get('date_paiement', timezone.now().date())
        loyer.save()

        # Generer quittance si paiement complet
        if loyer.statut == 'paye':
            annee = timezone.now().year
            count = Quittance.objects.filter(numero__startswith=f"QUIT-{annee}").count() + 1

            # CORRECTION #32: Corriger periode_fin (dernier jour du mois)
            _, dernier_jour = calendar.monthrange(loyer.annee, loyer.mois)
            periode_debut = timezone.now().date().replace(year=loyer.annee, month=loyer.mois, day=1)
            periode_fin = timezone.now().date().replace(year=loyer.annee, month=loyer.mois, day=dernier_jour)

            Quittance.objects.create(
                loyer=loyer,
                numero=f"QUIT-{annee}-{count:05d}",
                montant=loyer.montant_total,
                periode_debut=periode_debut,
                periode_fin=periode_fin,
            )

        return JsonResponse({
            'success': True,
            'message': 'Paiement enregistre avec succes',
            'statut': loyer.statut,
            'reste_a_payer': str(loyer.reste_a_payer)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #13
@require_POST
def api_creer_incident(request):
    """Signaler un nouvel incident"""
    try:
        data = json.loads(request.body)
        bien = get_object_or_404(BienImmobilier, id=data.get('bien_id'))

        bail_id = data.get('bail_id')
        bail = Bail.objects.filter(id=bail_id).first() if bail_id else None

        incident = Incident.objects.create(
            bien=bien,
            bail=bail,
            type_incident=data.get('type_incident', 'panne'),
            priorite=data.get('priorite', 'normale'),
            titre=data.get('titre'),
            description=data.get('description'),
            cout_estime=Decimal(str(data.get('cout_estime', 0))),
        )
        return JsonResponse({
            'success': True,
            'incident_id': str(incident.id),
            'message': 'Incident signale avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #14
@require_POST
def api_resoudre_incident(request, incident_id):
    """Resoudre un incident"""
    try:
        data = json.loads(request.body)
        incident = get_object_or_404(Incident, id=incident_id)

        incident.statut = 'resolu'
        incident.date_resolution = timezone.now()
        incident.cout_reel = Decimal(str(data.get('cout_reel', 0)))
        incident.notes = data.get('notes', '')
        incident.save()

        return JsonResponse({
            'success': True,
            'message': 'Incident resolu avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #15
@require_POST
def api_generer_loyers(request):
    """Generer les loyers pour un mois donne"""
    try:
        data = json.loads(request.body)
        mois = int(data.get('mois', timezone.now().month))
        annee = int(data.get('annee', timezone.now().year))

        baux_actifs = Bail.objects.filter(statut='actif')
        loyers_crees = 0

        for bail in baux_actifs:
            # Verifier si le loyer existe deja
            if not Loyer.objects.filter(bail=bail, mois=mois, annee=annee).exists():
                # CORRECTION #31: Gerer jours > 28 avec calendar.monthrange
                _, dernier_jour_mois = calendar.monthrange(annee, mois)
                jour_paiement = min(bail.jour_paiement, dernier_jour_mois)

                date_echeance = timezone.now().date().replace(
                    year=annee, month=mois, day=jour_paiement
                )

                Loyer.objects.create(
                    bail=bail,
                    mois=mois,
                    annee=annee,
                    date_echeance=date_echeance,
                    montant_loyer=bail.loyer_mensuel,
                    montant_charges=bail.charges_mensuelles,
                    montant_total=bail.loyer_total,
                )
                loyers_crees += 1

        return JsonResponse({
            'success': True,
            'loyers_crees': loyers_crees,
            'message': f'{loyers_crees} loyers generes pour {mois}/{annee}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required  # CORRECTION #16
@require_GET
def api_statistiques(request):
    """Statistiques de la gerance"""
    try:
        # Statistiques globales
        nb_proprietaires = Proprietaire.objects.filter(actif=True).count()
        nb_biens = BienImmobilier.objects.count()
        nb_biens_loues = BienImmobilier.objects.filter(statut='loue').count()
        nb_baux_actifs = Bail.objects.filter(statut='actif').count()

        # Loyers du mois
        mois = timezone.now().month
        annee = timezone.now().year
        loyers_mois = Loyer.objects.filter(mois=mois, annee=annee)

        total_loyers = loyers_mois.aggregate(total=Sum('montant_total'))['total'] or Decimal('0')
        total_paye = loyers_mois.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')

        # Repartition par type de bien
        repartition_biens = BienImmobilier.objects.values('type_bien').annotate(
            count=Count('id')
        )

        # Incidents en cours
        incidents_ouverts = Incident.objects.filter(statut__in=['signale', 'en_cours']).count()

        return JsonResponse({
            'success': True,
            'proprietaires': nb_proprietaires,
            'biens': nb_biens,
            'biens_loues': nb_biens_loues,
            'taux_occupation': round((nb_biens_loues / nb_biens * 100) if nb_biens > 0 else 0, 1),
            'baux_actifs': nb_baux_actifs,
            'total_loyers_mois': str(total_loyers),
            'total_paye_mois': str(total_paye),
            'incidents_ouverts': incidents_ouverts,
            'repartition_biens': list(repartition_biens),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================================================
# CORRECTION #25: API renouvellement de bail
# ==========================================================================
@login_required
@require_POST
def api_renouveler_bail(request):
    """Renouveler un bail existant"""
    try:
        data = json.loads(request.body)
        bail = get_object_or_404(Bail, id=data.get('bail_id'))

        # Calculer nouvelle date de fin
        duree_mois = int(data.get('duree_mois', 12))
        nouvelle_date_debut = bail.date_fin + timedelta(days=1)

        # Calculer la nouvelle date de fin
        annee_fin = nouvelle_date_debut.year + (nouvelle_date_debut.month + duree_mois - 1) // 12
        mois_fin = (nouvelle_date_debut.month + duree_mois - 1) % 12 + 1
        _, dernier_jour = calendar.monthrange(annee_fin, mois_fin)
        jour_fin = min(nouvelle_date_debut.day, dernier_jour)
        nouvelle_date_fin = nouvelle_date_debut.replace(year=annee_fin, month=mois_fin, day=jour_fin)

        # Mettre a jour le bail
        bail.date_debut = nouvelle_date_debut
        bail.date_fin = nouvelle_date_fin
        bail.duree_mois = duree_mois

        nouveau_loyer = data.get('loyer_mensuel')
        if nouveau_loyer:
            bail.loyer_mensuel = Decimal(str(nouveau_loyer))

        bail.save()

        return JsonResponse({
            'success': True,
            'message': f'Bail renouvele jusqu\'au {nouvelle_date_fin.strftime("%d/%m/%Y")}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================================================
# CORRECTION #26: API resiliation de bail
# ==========================================================================
@login_required
@require_POST
def api_resilier_bail(request):
    """Resilier un bail"""
    try:
        data = json.loads(request.body)
        bail = get_object_or_404(Bail, id=data.get('bail_id'))

        bail.statut = 'resilie'
        bail.date_fin = data.get('date_resiliation', timezone.now().date())
        bail.motif_fin = data.get('motif', '')
        bail.save()

        # Liberer le bien
        bail.bien.statut = 'libre'
        bail.bien.save()

        return JsonResponse({
            'success': True,
            'message': 'Bail resilie avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================================================
# CORRECTION #24: Vue calcul automatique des reversements
# ==========================================================================
@login_required
@require_POST
def api_calculer_reversements(request):
    """Calculer les reversements pour un mois donne"""
    try:
        data = json.loads(request.body)
        mois = int(data.get('mois', timezone.now().month))
        annee = int(data.get('annee', timezone.now().year))

        reversements_crees = 0

        # Pour chaque proprietaire avec des biens loues
        proprietaires = Proprietaire.objects.filter(actif=True, biens__statut='loue').distinct()

        for proprietaire in proprietaires:
            # Verifier si le reversement existe deja
            if ReversementProprietaire.objects.filter(
                proprietaire=proprietaire, mois=mois, annee=annee
            ).exists():
                continue

            # Calculer le total des loyers encaisses pour ce proprietaire
            total_loyers = Loyer.objects.filter(
                bail__bien__proprietaire=proprietaire,
                mois=mois,
                annee=annee,
                statut='paye'
            ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')

            if total_loyers > 0:
                # Calculer les honoraires
                honoraires = total_loyers * (proprietaire.taux_honoraires / 100)
                montant_reverse = total_loyers - honoraires

                ReversementProprietaire.objects.create(
                    proprietaire=proprietaire,
                    mois=mois,
                    annee=annee,
                    total_loyers=total_loyers,
                    honoraires=honoraires,
                    autres_deductions=Decimal('0'),
                    montant_reverse=montant_reverse,
                )
                reversements_crees += 1

        return JsonResponse({
            'success': True,
            'reversements_crees': reversements_crees,
            'message': f'{reversements_crees} reversements calcules pour {mois}/{annee}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_effectuer_reversement(request):
    """Marquer un reversement comme effectue"""
    try:
        data = json.loads(request.body)
        reversement = get_object_or_404(ReversementProprietaire, id=data.get('reversement_id'))

        reversement.statut = 'effectue'
        reversement.date_reversement = data.get('date_reversement', timezone.now().date())
        reversement.mode_reversement = data.get('mode_reversement', 'virement')
        reversement.reference_paiement = data.get('reference_paiement', '')
        reversement.notes = data.get('notes', '')
        reversement.save()

        return JsonResponse({
            'success': True,
            'message': 'Reversement effectue avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================================================
# CORRECTION #23: API Etats des lieux
# ==========================================================================
@login_required
@require_POST
def api_creer_etat_lieux(request):
    """Creer un etat des lieux"""
    try:
        data = json.loads(request.body)
        bail = get_object_or_404(Bail, id=data.get('bail_id'))

        etat = EtatDesLieux.objects.create(
            bail=bail,
            type_etat=data.get('type_etat', 'entree'),
            date_etat=data.get('date_etat', timezone.now().date()),
            compteur_eau=data.get('compteur_eau'),
            compteur_electricite=data.get('compteur_electricite'),
            compteur_gaz=data.get('compteur_gaz'),
            observations=data.get('observations', {}),
            nombre_cles=data.get('nombre_cles', 0),
            detail_cles=data.get('detail_cles', ''),
            etat_general=data.get('etat_general', 'bon'),
            notes=data.get('notes', ''),
        )

        return JsonResponse({
            'success': True,
            'etat_id': str(etat.id),
            'message': 'Etat des lieux cree avec succes'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================================================
# CORRECTION #27: Export PDF (quittances, baux)
# ==========================================================================
@login_required
def export_quittance_pdf(request):
    """Exporter une quittance en PDF"""
    loyer_id = request.GET.get('loyer_id')
    loyer = get_object_or_404(Loyer, id=loyer_id)

    # Pour l'instant, retourner un HTML imprimable
    context = get_default_context(request)
    context['loyer'] = loyer
    context['quittance'] = loyer.quittances.first()

    return render(request, 'gerance/quittance_print.html', context)


@login_required
def export_bail_pdf(request):
    """Exporter un bail en PDF"""
    bail_id = request.GET.get('bail_id')
    bail = get_object_or_404(Bail, id=bail_id)

    context = get_default_context(request)
    context['bail'] = bail

    return render(request, 'gerance/bail_print.html', context)


@login_required
def export_baux_pdf(request):
    """Exporter la liste des baux en PDF"""
    baux = Bail.objects.filter(statut='actif').select_related('bien', 'locataire')

    context = get_default_context(request)
    context['baux'] = baux

    return render(request, 'gerance/baux_print.html', context)


@login_required
def export_releve_pdf(request):
    """Exporter un releve de compte proprietaire en PDF"""
    reversement_id = request.GET.get('reversement_id')
    reversement = get_object_or_404(ReversementProprietaire, id=reversement_id)

    context = get_default_context(request)
    context['reversement'] = reversement

    return render(request, 'gerance/releve_print.html', context)


# ==========================================================================
# CORRECTION #28: Export Excel (loyers, reversements)
# ==========================================================================
@login_required
def export_loyers_excel(request):
    """Exporter les loyers en Excel (CSV)"""
    import csv

    mois = int(request.GET.get('mois', timezone.now().month))
    annee = int(request.GET.get('annee', timezone.now().year))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="loyers_{mois}_{annee}.csv"'
    response.write('\ufeff')  # BOM UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Bien', 'Locataire', 'Montant Total', 'Paye', 'Reste', 'Statut', 'Echeance'])

    loyers = Loyer.objects.filter(mois=mois, annee=annee).select_related('bail', 'bail__bien', 'bail__locataire')

    for loyer in loyers:
        writer.writerow([
            loyer.bail.bien.designation,
            str(loyer.bail.locataire),
            loyer.montant_total,
            loyer.montant_paye,
            loyer.reste_a_payer,
            loyer.get_statut_display(),
            loyer.date_echeance.strftime('%d/%m/%Y')
        ])

    return response


@login_required
def export_reversements_excel(request):
    """Exporter les reversements en Excel (CSV)"""
    import csv

    mois = int(request.GET.get('mois', timezone.now().month))
    annee = int(request.GET.get('annee', timezone.now().year))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reversements_{mois}_{annee}.csv"'
    response.write('\ufeff')  # BOM UTF-8

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Proprietaire', 'Total Loyers', 'Honoraires', 'Deductions', 'Net a Reverser', 'Statut'])

    reversements = ReversementProprietaire.objects.filter(mois=mois, annee=annee).select_related('proprietaire')

    for rev in reversements:
        writer.writerow([
            str(rev.proprietaire),
            rev.total_loyers,
            rev.honoraires,
            rev.autres_deductions,
            rev.montant_reverse,
            rev.get_statut_display()
        ])

    return response

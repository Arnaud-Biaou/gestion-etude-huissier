"""
Vues du module Gérance Immobilière
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Proprietaire, BienImmobilier, Locataire, Bail, Loyer,
    Quittance, EtatDesLieux, Incident, ReversementProprietaire
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
        'active_module': 'gerance',
    }


@login_required
def dashboard(request):
    """Vue principale du module Gérance"""
    context = get_default_context(request)
    context['page_title'] = 'Gérance Immobilière'

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

    # Baux expirant bientôt (dans 60 jours)
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
    """Liste des propriétaires"""
    context = get_default_context(request)
    context['page_title'] = 'Propriétaires'

    proprietaires_list = Proprietaire.objects.filter(actif=True).annotate(
        nb_biens=Count('biens')
    )
    context['proprietaires'] = proprietaires_list

    return render(request, 'gerance/proprietaires.html', context)


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


@login_required
def locataires(request):
    """Liste des locataires"""
    context = get_default_context(request)
    context['page_title'] = 'Locataires'

    locataires_list = Locataire.objects.filter(actif=True)
    context['locataires'] = locataires_list

    return render(request, 'gerance/locataires.html', context)


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
    """Reversements aux propriétaires"""
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


# ==========================================================================
# API ENDPOINTS
# ==========================================================================

@require_POST
def api_creer_proprietaire(request):
    """Créer un nouveau propriétaire"""
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
            'message': 'Propriétaire créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_bien(request):
    """Créer un nouveau bien immobilier"""
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
            'message': 'Bien créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_locataire(request):
    """Créer un nouveau locataire"""
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
            'message': 'Locataire créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_creer_bail(request):
    """Créer un nouveau bail"""
    try:
        data = json.loads(request.body)
        bien = get_object_or_404(BienImmobilier, id=data.get('bien_id'))
        locataire = get_object_or_404(Locataire, id=data.get('locataire_id'))

        # Générer référence du bail
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

        # Mettre à jour le statut du bien
        bien.statut = 'loue'
        bien.save()

        return JsonResponse({
            'success': True,
            'bail_id': str(bail.id),
            'reference': reference,
            'message': 'Bail créé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


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

        # Générer quittance si paiement complet
        if loyer.statut == 'paye':
            annee = timezone.now().year
            count = Quittance.objects.filter(numero__startswith=f"QUIT-{annee}").count() + 1
            Quittance.objects.create(
                loyer=loyer,
                numero=f"QUIT-{annee}-{count:05d}",
                montant=loyer.montant_total,
                periode_debut=timezone.now().date().replace(day=1),
                periode_fin=timezone.now().date(),
            )

        return JsonResponse({
            'success': True,
            'message': 'Paiement enregistré avec succès',
            'statut': loyer.statut,
            'reste_a_payer': str(loyer.reste_a_payer)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


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
            'message': 'Incident signalé avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_resoudre_incident(request, incident_id):
    """Résoudre un incident"""
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
            'message': 'Incident résolu avec succès'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_generer_loyers(request):
    """Générer les loyers pour un mois donné"""
    try:
        data = json.loads(request.body)
        mois = int(data.get('mois', timezone.now().month))
        annee = int(data.get('annee', timezone.now().year))

        baux_actifs = Bail.objects.filter(statut='actif')
        loyers_crees = 0

        for bail in baux_actifs:
            # Vérifier si le loyer existe déjà
            if not Loyer.objects.filter(bail=bail, mois=mois, annee=annee).exists():
                # Calculer la date d'échéance
                date_echeance = timezone.now().date().replace(
                    year=annee, month=mois, day=bail.jour_paiement
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
            'message': f'{loyers_crees} loyers générés pour {mois}/{annee}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_GET
def api_statistiques(request):
    """Statistiques de la gérance"""
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

        # Répartition par type de bien
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

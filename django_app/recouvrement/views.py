"""
Vues du module Recouvrement de Créances
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg
from django.contrib import messages
from django.urls import reverse

from .models import (
    PointGlobalCreancier,
    DossierRecouvrement,
    EnvoiAutomatiquePoint,
    PaiementRecouvrement,
    HistoriqueActionRecouvrement,
    ImputationManuelle,
)
from .services.pdf_point_global import generer_pdf_point_global
from .services.paiement_service import ServicePaiement
from .services.baremes import (
    calculer_honoraires_amiable,
    calculer_emoluments_force,
    detail_calcul_droit_recette,
    BAREME_RECOUVREMENT_AMIABLE,
    BAREME_RECOUVREMENT_FORCE
)
from gestion.models import Creancier, Partie

import json
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


@login_required
def point_global_creancier(request):
    """Vue principale Point Global Créancier"""
    creanciers = Creancier.objects.filter(actif=True).order_by('nom')
    points = PointGlobalCreancier.objects.select_related('creancier').all()[:20]

    return render(request, 'recouvrement/point_global.html', {
        'creanciers': creanciers,
        'points': points,
    })


@login_required
@require_POST
def api_generer_point_global(request):
    """API pour générer un point global"""
    try:
        data = json.loads(request.body)

        creancier_id = data.get('creancier_id')
        periode_debut = data.get('periode_debut')
        periode_fin = data.get('periode_fin')

        if not creancier_id:
            return JsonResponse({'success': False, 'error': 'Créancier requis'}, status=400)

        if not periode_debut or not periode_fin:
            return JsonResponse({'success': False, 'error': 'Période requise'}, status=400)

        # Vérifier que le créancier existe
        creancier = get_object_or_404(Creancier, id=creancier_id)

        # Créer le point global
        point = PointGlobalCreancier.objects.create(
            creancier=creancier,
            periode_debut=datetime.strptime(periode_debut, '%Y-%m-%d').date(),
            periode_fin=datetime.strptime(periode_fin, '%Y-%m-%d').date(),
            inclure_tous_dossiers=data.get('inclure_tous', True),
            inclure_en_cours=data.get('inclure_en_cours', True),
            inclure_clotures=data.get('inclure_clotures', True),
            inclure_amiable=data.get('inclure_amiable', True),
            inclure_force=data.get('inclure_force', True),
            observations=data.get('observations', ''),
            genere_par=request.user if hasattr(request.user, 'id') else None,
        )

        # Sélection manuelle de dossiers
        dossiers_ids = data.get('dossiers_ids', [])
        if dossiers_ids:
            point.inclure_tous_dossiers = False
            point.dossiers_selectionnes.set(dossiers_ids)
            point.save()

        # Calculer les statistiques
        point.calculer_statistiques()

        # Générer le PDF
        try:
            pdf_buffer = generer_pdf_point_global(point)
            point.document_pdf.save(
                f'point_global_{point.id}.pdf',
                ContentFile(pdf_buffer.read())
            )
            point.statut = 'genere'
            point.save()
        except Exception as e:
            # Si la génération PDF échoue, on garde le point sans PDF
            point.statut = 'brouillon'
            point.save()
            return JsonResponse({
                'success': True,
                'point_id': str(point.id),
                'pdf_url': None,
                'warning': f'Point créé mais PDF non généré: {str(e)}'
            })

        return JsonResponse({
            'success': True,
            'point_id': str(point.id),
            'pdf_url': point.document_pdf.url if point.document_pdf else None,
            'stats': point.to_dict()
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_telecharger_point_global(request, point_id):
    """Télécharger le PDF d'un point global"""
    try:
        point = get_object_or_404(PointGlobalCreancier, id=point_id)

        if point.document_pdf:
            response = FileResponse(
                point.document_pdf.open('rb'),
                as_attachment=True,
                filename=f'Point_Global_{point.creancier.nom}_{point.date_generation.strftime("%Y%m%d")}.pdf'
            )
            return response
        else:
            return JsonResponse({'error': 'PDF non disponible'}, status=404)

    except PointGlobalCreancier.DoesNotExist:
        return JsonResponse({'error': 'Point global non trouvé'}, status=404)


@login_required
@require_GET
def api_dossiers_creancier(request, creancier_id):
    """Liste des dossiers d'un créancier pour sélection"""
    dossiers = DossierRecouvrement.objects.filter(creancier_id=creancier_id)

    # Filtres optionnels
    statut = request.GET.get('statut')
    if statut:
        dossiers = dossiers.filter(statut=statut)

    type_rec = request.GET.get('type')
    if type_rec:
        dossiers = dossiers.filter(type_recouvrement=type_rec)

    data = [{
        'id': str(d.id),
        'reference': d.reference,
        'debiteur': d.debiteur.get_nom_complet() if d.debiteur else '-',
        'montant': str(d.montant_principal),
        'statut': d.get_statut_display() if hasattr(d, 'get_statut_display') else d.statut,
        'type': d.type_recouvrement,
        'encaisse': str(d.montant_encaisse or 0),
        'reste_du': str(d.montant_principal - (d.montant_encaisse or 0)),
    } for d in dossiers]

    return JsonResponse({'dossiers': data})


@login_required
@require_GET
def api_liste_points_globaux(request, creancier_id=None):
    """Liste des points globaux générés"""
    points = PointGlobalCreancier.objects.select_related('creancier')

    if creancier_id:
        points = points.filter(creancier_id=creancier_id)

    # Pagination basique
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))

    total = points.count()
    points = points[offset:offset + limit]

    data = [p.to_dict() for p in points]

    return JsonResponse({
        'points': data,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@login_required
@require_GET
def api_detail_point_global(request, point_id):
    """Détail d'un point global"""
    point = get_object_or_404(PointGlobalCreancier, id=point_id)
    return JsonResponse(point.to_dict())


@login_required
@require_POST
def api_regenerer_pdf(request, point_id):
    """Régénérer le PDF d'un point global"""
    try:
        point = get_object_or_404(PointGlobalCreancier, id=point_id)

        # Régénérer le PDF
        pdf_buffer = generer_pdf_point_global(point)
        point.document_pdf.save(
            f'point_global_{point.id}.pdf',
            ContentFile(pdf_buffer.read())
        )
        point.statut = 'genere'
        point.save()

        return JsonResponse({
            'success': True,
            'pdf_url': point.document_pdf.url
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_supprimer_point_global(request, point_id):
    """Supprimer un point global"""
    try:
        point = get_object_or_404(PointGlobalCreancier, id=point_id)

        # Supprimer le fichier PDF s'il existe
        if point.document_pdf:
            point.document_pdf.delete(save=False)

        point.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════
# APIs CALCUL BARÈMES
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_GET
def api_calculer_honoraires(request):
    """Calcule les honoraires selon le barème applicable"""
    try:
        montant = request.GET.get('montant')
        type_bareme = request.GET.get('type', 'amiable')

        if not montant:
            return JsonResponse({'error': 'Montant requis'}, status=400)

        montant = Decimal(montant)

        if type_bareme == 'amiable':
            bareme = BAREME_RECOUVREMENT_AMIABLE
            result = detail_calcul_droit_recette(montant, bareme, 'Recouvrement amiable')
        else:
            bareme = BAREME_RECOUVREMENT_FORCE
            result = detail_calcul_droit_recette(montant, bareme, 'Recouvrement forcé')

        return JsonResponse(result)

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Montant invalide: {str(e)}'}, status=400)


# ═══════════════════════════════════════════════════════════════════
# APIs STATISTIQUES CRÉANCIER
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_GET
def api_statistiques_creancier(request, creancier_id):
    """Statistiques globales d'un créancier"""

    creancier = get_object_or_404(Creancier, id=creancier_id)

    dossiers = DossierRecouvrement.objects.filter(creancier=creancier)

    stats = dossiers.aggregate(
        total_creances=Sum('montant_principal'),
        total_encaisse=Sum('montant_encaisse'),
        total_reverse=Sum('montant_reverse'),
        nombre_dossiers=Count('id'),
        nombre_en_cours=Count('id', filter=Q(statut='en_cours')),
        nombre_clotures=Count('id', filter=Q(statut='cloture')),
        nombre_amiable=Count('id', filter=Q(type_recouvrement='amiable')),
        nombre_force=Count('id', filter=Q(type_recouvrement='force')),
    )

    # Calculer le taux de recouvrement
    total_creances = stats['total_creances'] or 0
    total_encaisse = stats['total_encaisse'] or 0

    if total_creances > 0:
        taux_recouvrement = (total_encaisse / total_creances) * 100
    else:
        taux_recouvrement = 0

    return JsonResponse({
        'creancier': {
            'id': creancier.id,
            'code': creancier.code,
            'nom': creancier.nom,
        },
        'statistiques': {
            'total_creances': str(total_creances),
            'total_encaisse': str(total_encaisse),
            'total_reverse': str(stats['total_reverse'] or 0),
            'total_reste_du': str(total_creances - total_encaisse),
            'taux_recouvrement': f"{taux_recouvrement:.2f}",
            'nombre_dossiers': stats['nombre_dossiers'],
            'nombre_en_cours': stats['nombre_en_cours'],
            'nombre_clotures': stats['nombre_clotures'],
            'nombre_amiable': stats['nombre_amiable'],
            'nombre_force': stats['nombre_force'],
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
# VUES CRUD - DOSSIER DE RECOUVREMENT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def liste_dossiers_recouvrement(request):
    """Liste des dossiers de recouvrement avec filtres"""
    dossiers = DossierRecouvrement.objects.select_related('creancier', 'debiteur').all()

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        dossiers = dossiers.filter(statut=statut)

    type_recouvrement = request.GET.get('type')
    if type_recouvrement:
        dossiers = dossiers.filter(type_recouvrement=type_recouvrement)

    creancier_id = request.GET.get('creancier')
    if creancier_id:
        dossiers = dossiers.filter(creancier_id=creancier_id)

    recherche = request.GET.get('q')
    if recherche:
        dossiers = dossiers.filter(
            Q(reference__icontains=recherche) |
            Q(creancier__nom__icontains=recherche) |
            Q(debiteur__nom__icontains=recherche)
        )

    # Tri
    tri = request.GET.get('tri', '-date_ouverture')
    dossiers = dossiers.order_by(tri)

    # Pagination
    paginator = Paginator(dossiers, 25)
    page = request.GET.get('page', 1)
    dossiers_page = paginator.get_page(page)

    # Données pour les filtres
    creanciers = Creancier.objects.filter(actif=True).order_by('nom')

    # Statistiques rapides
    stats = DossierRecouvrement.objects.aggregate(
        total=Count('id'),
        en_cours=Count('id', filter=Q(statut='en_cours')),
        suspendus=Count('id', filter=Q(statut='suspendu')),
        clotures=Count('id', filter=Q(statut='cloture')),
    )

    return render(request, 'recouvrement/liste_dossiers.html', {
        'dossiers': dossiers_page,
        'creanciers': creanciers,
        'stats': stats,
        'filtres': {
            'statut': statut,
            'type': type_recouvrement,
            'creancier': creancier_id,
            'q': recherche,
            'tri': tri,
        }
    })


@login_required
def detail_dossier_recouvrement(request, dossier_id):
    """Détail complet d'un dossier de recouvrement"""
    dossier = get_object_or_404(
        DossierRecouvrement.objects.select_related('creancier', 'debiteur', 'dossier_principal', 'cree_par'),
        id=dossier_id
    )

    # Récupérer les paiements
    paiements = dossier.paiements.all().order_by('-date_paiement')

    # Récupérer l'historique
    historique = dossier.historique_actions.all().order_by('-date_action')[:20]

    # Calculer la situation complète
    situation = ServicePaiement.calculer_situation_dossier(dossier)

    return render(request, 'recouvrement/detail_dossier.html', {
        'dossier': dossier,
        'paiements': paiements,
        'historique': historique,
        'situation': situation,
    })


@login_required
def creer_dossier_recouvrement(request):
    """Formulaire de création d'un dossier de recouvrement"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            reference = request.POST.get('reference', '').strip()
            creancier_id = request.POST.get('creancier')
            debiteur_id = request.POST.get('debiteur')
            type_recouvrement = request.POST.get('type_recouvrement', 'amiable')
            mode_facturation = request.POST.get('mode_facturation', 'standard')
            montant_principal = request.POST.get('montant_principal', 0)
            montant_interets = request.POST.get('montant_interets', 0)
            frais_engages = request.POST.get('frais_engages', 0)
            date_ouverture = request.POST.get('date_ouverture')
            observations = request.POST.get('observations', '')

            # Validation
            if not reference:
                messages.error(request, "La référence est obligatoire.")
                return redirect('recouvrement:creer_dossier_recouvrement')

            if not creancier_id:
                messages.error(request, "Le créancier est obligatoire.")
                return redirect('recouvrement:creer_dossier_recouvrement')

            # Vérifier unicité de la référence
            if DossierRecouvrement.objects.filter(reference=reference).exists():
                messages.error(request, f"Un dossier avec la référence '{reference}' existe déjà.")
                return redirect('recouvrement:creer_dossier_recouvrement')

            # Créer le dossier
            dossier = DossierRecouvrement(
                reference=reference,
                creancier_id=creancier_id,
                type_recouvrement=type_recouvrement,
                mode_facturation=mode_facturation,
                montant_principal=Decimal(str(montant_principal)) if montant_principal else 0,
                montant_interets=Decimal(str(montant_interets)) if montant_interets else 0,
                frais_engages=Decimal(str(frais_engages)) if frais_engages else 0,
                observations=observations,
                cree_par=request.user,
            )

            if debiteur_id:
                dossier.debiteur_id = debiteur_id

            if date_ouverture:
                dossier.date_ouverture = datetime.strptime(date_ouverture, '%Y-%m-%d').date()

            # Calculer les émoluments
            if type_recouvrement == 'force':
                dossier.emoluments_calcules = Decimal(str(
                    calculer_emoluments_force(float(dossier.montant_principal))
                ))
            else:
                dossier.honoraires_amiable = Decimal(str(
                    calculer_honoraires_amiable(float(dossier.montant_principal))
                ))

            dossier.save()

            # Historique de création
            HistoriqueActionRecouvrement.objects.create(
                dossier=dossier,
                type_action='creation',
                description=f"Création du dossier de recouvrement {type_recouvrement}",
                cree_par=request.user,
            )

            messages.success(request, f"Dossier {reference} créé avec succès.")
            return redirect('recouvrement:detail_dossier_recouvrement', dossier_id=dossier.id)

        except (ValueError, InvalidOperation) as e:
            messages.error(request, f"Erreur de données: {str(e)}")
            return redirect('recouvrement:creer_dossier_recouvrement')

    # GET - Afficher le formulaire
    creanciers = Creancier.objects.filter(actif=True).order_by('nom')
    parties = Partie.objects.all().order_by('nom')

    return render(request, 'recouvrement/form_dossier.html', {
        'creanciers': creanciers,
        'parties': parties,
        'dossier': None,
        'action': 'creer',
    })


@login_required
def modifier_dossier_recouvrement(request, dossier_id):
    """Formulaire de modification d'un dossier de recouvrement"""
    dossier = get_object_or_404(DossierRecouvrement, id=dossier_id)

    if request.method == 'POST':
        try:
            # Récupérer les données
            dossier.type_recouvrement = request.POST.get('type_recouvrement', dossier.type_recouvrement)
            dossier.mode_facturation = request.POST.get('mode_facturation', dossier.mode_facturation)
            dossier.statut = request.POST.get('statut', dossier.statut)

            montant_principal = request.POST.get('montant_principal')
            if montant_principal:
                dossier.montant_principal = Decimal(str(montant_principal))

            montant_interets = request.POST.get('montant_interets')
            if montant_interets is not None:
                dossier.montant_interets = Decimal(str(montant_interets)) if montant_interets else 0

            frais_engages = request.POST.get('frais_engages')
            if frais_engages is not None:
                dossier.frais_engages = Decimal(str(frais_engages)) if frais_engages else 0

            debiteur_id = request.POST.get('debiteur')
            if debiteur_id:
                dossier.debiteur_id = debiteur_id
            else:
                dossier.debiteur = None

            dossier.observations = request.POST.get('observations', '')
            dossier.derniere_action = request.POST.get('derniere_action', '')
            dossier.prochaine_etape = request.POST.get('prochaine_etape', '')

            # Gérer la clôture
            if dossier.statut == 'cloture':
                dossier.motif_cloture = request.POST.get('motif_cloture', '')
                date_cloture = request.POST.get('date_cloture')
                if date_cloture:
                    dossier.date_cloture = datetime.strptime(date_cloture, '%Y-%m-%d').date()
                elif not dossier.date_cloture:
                    dossier.date_cloture = date.today()

            # Recalculer les émoluments si le montant ou type change
            if dossier.type_recouvrement == 'force':
                dossier.emoluments_calcules = Decimal(str(
                    calculer_emoluments_force(float(dossier.montant_principal))
                ))
            else:
                dossier.honoraires_amiable = Decimal(str(
                    calculer_honoraires_amiable(float(dossier.montant_principal))
                ))

            dossier.save()

            messages.success(request, "Dossier modifié avec succès.")
            return redirect('recouvrement:detail_dossier_recouvrement', dossier_id=dossier.id)

        except (ValueError, InvalidOperation) as e:
            messages.error(request, f"Erreur de données: {str(e)}")

    # GET - Afficher le formulaire
    creanciers = Creancier.objects.filter(actif=True).order_by('nom')
    parties = Partie.objects.all().order_by('nom')

    return render(request, 'recouvrement/form_dossier.html', {
        'creanciers': creanciers,
        'parties': parties,
        'dossier': dossier,
        'action': 'modifier',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# APIS PAIEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def api_enregistrer_paiement(request):
    """API pour enregistrer un paiement sur un dossier"""
    try:
        data = json.loads(request.body)

        dossier_id = data.get('dossier_id')
        if not dossier_id:
            return JsonResponse({'success': False, 'error': 'dossier_id requis'}, status=400)

        dossier = get_object_or_404(DossierRecouvrement, id=dossier_id)

        montant = data.get('montant')
        if not montant or Decimal(str(montant)) <= 0:
            return JsonResponse({'success': False, 'error': 'Montant invalide'}, status=400)

        # Date du paiement
        date_paiement = None
        if data.get('date_paiement'):
            date_paiement = datetime.strptime(data['date_paiement'], '%Y-%m-%d').date()

        # Imputation manuelle optionnelle
        imputation_manuelle = None
        if data.get('imputation'):
            imputation_manuelle = {
                'frais': data['imputation'].get('frais', 0),
                'emoluments': data['imputation'].get('emoluments', 0),
                'interets': data['imputation'].get('interets', 0),
                'principal': data['imputation'].get('principal', 0),
                'reserve': data['imputation'].get('reserve', 0),
                'reverser': data['imputation'].get('reverser', 0),
            }

        # Créer le paiement
        paiement = ServicePaiement.enregistrer_paiement(
            dossier=dossier,
            montant=Decimal(str(montant)),
            date_paiement=date_paiement,
            mode_paiement=data.get('mode_paiement', 'especes'),
            reference_paiement=data.get('reference_paiement', ''),
            observations=data.get('observations', ''),
            utilisateur=request.user,
            imputation_manuelle=imputation_manuelle,
        )

        return JsonResponse({
            'success': True,
            'paiement': paiement.to_dict(),
            'message': f"Paiement de {paiement.montant:,.0f} FCFA enregistré"
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_liste_paiements(request, dossier_id):
    """API pour lister les paiements d'un dossier"""
    dossier = get_object_or_404(DossierRecouvrement, id=dossier_id)

    paiements = dossier.paiements.all().order_by('-date_paiement')

    # Pagination optionnelle
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))

    total = paiements.count()
    paiements = paiements[offset:offset + limit]

    data = [p.to_dict() for p in paiements]

    # Totaux
    totaux = dossier.paiements.aggregate(
        total_paye=Sum('montant'),
        total_frais=Sum('impute_frais'),
        total_emoluments=Sum('impute_emoluments'),
        total_interets=Sum('impute_interets'),
        total_principal=Sum('impute_principal'),
        total_reserve=Sum('montant_reserve'),
        total_a_reverser=Sum('montant_a_reverser'),
    )

    # Total reversé
    total_reverse = dossier.paiements.filter(est_reverse=True).aggregate(
        total=Sum('montant_a_reverser')
    )['total'] or 0

    return JsonResponse({
        'success': True,
        'dossier_id': str(dossier.id),
        'dossier_reference': dossier.reference,
        'paiements': data,
        'total': total,
        'limit': limit,
        'offset': offset,
        'totaux': {
            'paye': str(totaux['total_paye'] or 0),
            'frais': str(totaux['total_frais'] or 0),
            'emoluments': str(totaux['total_emoluments'] or 0),
            'interets': str(totaux['total_interets'] or 0),
            'principal': str(totaux['total_principal'] or 0),
            'reserve': str(totaux['total_reserve'] or 0),
            'a_reverser': str(totaux['total_a_reverser'] or 0),
            'reverse': str(total_reverse),
        }
    })


@login_required
@require_POST
def api_effectuer_reversement(request, paiement_id):
    """API pour marquer un paiement comme reversé au créancier"""
    try:
        data = json.loads(request.body) if request.body else {}

        paiement = get_object_or_404(PaiementRecouvrement, id=paiement_id)

        date_reversement = None
        if data.get('date_reversement'):
            date_reversement = datetime.strptime(data['date_reversement'], '%Y-%m-%d').date()

        paiement = ServicePaiement.effectuer_reversement(
            paiement=paiement,
            date_reversement=date_reversement,
            reference_reversement=data.get('reference_reversement', ''),
            utilisateur=request.user,
        )

        return JsonResponse({
            'success': True,
            'paiement': paiement.to_dict(),
            'message': f"Reversement de {paiement.montant_a_reverser:,.0f} FCFA effectué"
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_imputer_reserve(request, paiement_id):
    """API pour imputer manuellement un montant réservé"""
    try:
        data = json.loads(request.body)

        paiement = get_object_or_404(PaiementRecouvrement, id=paiement_id)

        type_imputation = data.get('type_imputation')
        if type_imputation not in ['frais', 'emoluments', 'interets', 'principal']:
            return JsonResponse({
                'success': False,
                'error': 'type_imputation invalide (frais, emoluments, interets, principal)'
            }, status=400)

        montant = data.get('montant')
        if not montant or Decimal(str(montant)) <= 0:
            return JsonResponse({'success': False, 'error': 'Montant invalide'}, status=400)

        imputation = ServicePaiement.imputer_montant_reserve(
            paiement=paiement,
            type_imputation=type_imputation,
            montant=Decimal(str(montant)),
            observations=data.get('observations', ''),
            utilisateur=request.user,
        )

        return JsonResponse({
            'success': True,
            'imputation': imputation.to_dict(),
            'paiement': paiement.to_dict(),
            'message': f"Imputation de {montant:,.0f} FCFA sur {type_imputation}"
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_GET
def api_situation_dossier(request, dossier_id):
    """API pour obtenir la situation complète d'un dossier"""
    dossier = get_object_or_404(DossierRecouvrement, id=dossier_id)

    situation = ServicePaiement.calculer_situation_dossier(dossier)

    # Convertir les Decimal en str pour JSON
    def decimal_to_str(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: decimal_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [decimal_to_str(i) for i in obj]
        return obj

    return JsonResponse({
        'success': True,
        'dossier_id': str(dossier.id),
        'dossier_reference': dossier.reference,
        'situation': decimal_to_str(situation)
    })


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD RECOUVREMENT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_recouvrement(request):
    """Tableau de bord du module recouvrement avec statistiques globales"""

    # Statistiques globales des dossiers
    stats_dossiers = DossierRecouvrement.objects.aggregate(
        total=Count('id'),
        en_cours=Count('id', filter=Q(statut='en_cours')),
        suspendus=Count('id', filter=Q(statut='suspendu')),
        clotures=Count('id', filter=Q(statut='cloture')),
        amiables=Count('id', filter=Q(type_recouvrement='amiable')),
        forces=Count('id', filter=Q(type_recouvrement='force')),
    )

    # Statistiques financières
    stats_financieres = DossierRecouvrement.objects.aggregate(
        total_creances=Sum('montant_principal'),
        total_interets=Sum('montant_interets'),
        total_frais=Sum('frais_engages'),
        total_encaisse=Sum('montant_encaisse'),
        total_reverse=Sum('total_reverse'),
    )

    total_creances = stats_financieres['total_creances'] or 0
    total_encaisse = stats_financieres['total_encaisse'] or 0

    if total_creances > 0:
        taux_recouvrement_global = (total_encaisse / total_creances) * 100
    else:
        taux_recouvrement_global = 0

    # Paiements du mois en cours
    debut_mois = date.today().replace(day=1)
    paiements_mois = PaiementRecouvrement.objects.filter(
        date_paiement__gte=debut_mois
    ).aggregate(
        nombre=Count('id'),
        total=Sum('montant'),
    )

    # Reversements en attente
    reversements_en_attente = PaiementRecouvrement.objects.filter(
        est_reverse=False,
        montant_a_reverser__gt=0
    ).aggregate(
        nombre=Count('id'),
        total=Sum('montant_a_reverser'),
    )

    # Top 5 créanciers par volume
    top_creanciers = DossierRecouvrement.objects.values(
        'creancier__nom', 'creancier_id'
    ).annotate(
        nombre_dossiers=Count('id'),
        total_creances=Sum('montant_principal'),
        total_encaisse=Sum('montant_encaisse'),
    ).order_by('-total_creances')[:5]

    # Derniers dossiers
    derniers_dossiers = DossierRecouvrement.objects.select_related(
        'creancier', 'debiteur'
    ).order_by('-date_creation')[:10]

    # Derniers paiements
    derniers_paiements = PaiementRecouvrement.objects.select_related(
        'dossier', 'dossier__creancier'
    ).order_by('-date_paiement')[:10]

    # Dossiers en cours par mois (6 derniers mois)
    from django.db.models.functions import TruncMonth
    evolution_mensuelle = DossierRecouvrement.objects.filter(
        date_ouverture__gte=date.today().replace(month=1, day=1)
    ).annotate(
        mois=TruncMonth('date_ouverture')
    ).values('mois').annotate(
        nouveaux=Count('id'),
        montant=Sum('montant_principal'),
    ).order_by('mois')

    return render(request, 'recouvrement/dashboard.html', {
        'stats_dossiers': stats_dossiers,
        'stats_financieres': {
            'total_creances': total_creances,
            'total_interets': stats_financieres['total_interets'] or 0,
            'total_frais': stats_financieres['total_frais'] or 0,
            'total_encaisse': total_encaisse,
            'total_reverse': stats_financieres['total_reverse'] or 0,
            'reste_du': total_creances - total_encaisse,
        },
        'taux_recouvrement_global': taux_recouvrement_global,
        'paiements_mois': paiements_mois,
        'reversements_en_attente': reversements_en_attente,
        'top_creanciers': top_creanciers,
        'derniers_dossiers': derniers_dossiers,
        'derniers_paiements': derniers_paiements,
        'evolution_mensuelle': list(evolution_mensuelle),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# API HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_GET
def api_historique_dossier(request, dossier_id):
    """API pour obtenir l'historique des actions d'un dossier"""
    dossier = get_object_or_404(DossierRecouvrement, id=dossier_id)

    # Pagination
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))

    # Filtre par type d'action
    type_action = request.GET.get('type_action')

    historique = dossier.historique_actions.all()

    if type_action:
        historique = historique.filter(type_action=type_action)

    total = historique.count()
    historique = historique.order_by('-date_action')[offset:offset + limit]

    data = [h.to_dict() for h in historique]

    return JsonResponse({
        'success': True,
        'dossier_id': str(dossier.id),
        'dossier_reference': dossier.reference,
        'historique': data,
        'total': total,
        'limit': limit,
        'offset': offset,
    })

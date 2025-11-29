"""
Vues du module Recouvrement de Créances
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

from .models import PointGlobalCreancier, DossierRecouvrement, EnvoiAutomatiquePoint
from .services.pdf_point_global import generer_pdf_point_global
from .services.baremes import (
    calculer_honoraires_amiable,
    calculer_emoluments_force,
    detail_calcul_droit_recette,
    BAREME_RECOUVREMENT_AMIABLE,
    BAREME_RECOUVREMENT_FORCE
)
from gestion.models import Creancier

import json
from datetime import datetime
from decimal import Decimal


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
    from django.db.models import Sum, Count, Q

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

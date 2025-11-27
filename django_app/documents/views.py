"""
Vues et API pour le module Documents
Gestion des fichiers, génération, partage et audit
"""
import json
import os
import mimetypes
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.conf import settings

from .models import (
    Document, DossierVirtuel, ModeleDocument, CloudConnection,
    PartageDocument, AuditDocument, GenerationDocument,
    ConfigurationDocuments, NumeroActe, SignatureElectronique
)
from .services.document_service import DocumentService

# Import conditionnel du module gestion
try:
    from gestion.models import Dossier, Facture
    GESTION_AVAILABLE = True
except ImportError:
    GESTION_AVAILABLE = False


# ==========================================
# VUES PRINCIPALES
# ==========================================

@login_required
def drive_view(request):
    """Vue principale du Drive"""
    context = {
        'current_user': request.user,
        'module': 'drive',
    }
    return render(request, 'documents/drive.html', context)


@login_required
def documents_dossier_view(request, dossier_id):
    """Vue des documents d'un dossier juridique"""
    if GESTION_AVAILABLE:
        dossier = get_object_or_404(Dossier, id=dossier_id)
        documents = Document.objects.filter(
            dossier_juridique=dossier
        ).exclude(statut='supprime').order_by('-date_creation')

        context = {
            'dossier': dossier,
            'documents': documents,
            'current_user': request.user,
        }
        return render(request, 'documents/dossier_documents.html', context)

    return JsonResponse({'error': 'Module gestion non disponible'}, status=400)


# ==========================================
# API - DOCUMENTS
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_documents_liste(request):
    """
    Liste des documents avec filtres et pagination

    GET params:
        - q: Recherche textuelle
        - type: Type de document
        - dossier_juridique: ID du dossier juridique
        - dossier: ID du dossier virtuel
        - statut: Statut du document
        - date_debut: Date de création minimum (YYYY-MM-DD)
        - date_fin: Date de création maximum (YYYY-MM-DD)
        - page: Numéro de page
        - limit: Nombre par page (défaut: 50)
    """
    qs = Document.objects.exclude(statut='supprime')

    # Filtres
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) |
            Q(description__icontains=q) |
            Q(contenu_texte__icontains=q)
        )

    type_doc = request.GET.get('type')
    if type_doc:
        qs = qs.filter(type_document=type_doc)

    dossier_juridique_id = request.GET.get('dossier_juridique')
    if dossier_juridique_id:
        qs = qs.filter(dossier_juridique_id=dossier_juridique_id)

    dossier_id = request.GET.get('dossier')
    if dossier_id:
        qs = qs.filter(dossier_id=dossier_id)

    statut = request.GET.get('statut')
    if statut:
        qs = qs.filter(statut=statut)

    date_debut = request.GET.get('date_debut')
    if date_debut:
        qs = qs.filter(date_creation__date__gte=date_debut)

    date_fin = request.GET.get('date_fin')
    if date_fin:
        qs = qs.filter(date_creation__date__lte=date_fin)

    # Tri
    ordre = request.GET.get('ordre', '-date_creation')
    qs = qs.order_by(ordre)

    # Pagination
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 50)), 100)

    paginator = Paginator(qs, limit)
    page_obj = paginator.get_page(page)

    documents = []
    for doc in page_obj:
        documents.append({
            'id': str(doc.id),
            'nom': doc.nom,
            'nom_original': doc.nom_original,
            'type_document': doc.type_document,
            'type_document_display': doc.get_type_document_display(),
            'description': doc.description,
            'taille': doc.taille,
            'taille_humaine': doc.taille_humaine,
            'extension': doc.extension,
            'mime_type': doc.mime_type,
            'statut': doc.statut,
            'version': doc.version,
            'est_genere': doc.est_genere,
            'dossier_juridique_id': str(doc.dossier_juridique_id) if doc.dossier_juridique_id else None,
            'dossier_id': str(doc.dossier_id) if doc.dossier_id else None,
            'date_creation': doc.date_creation.isoformat(),
            'date_modification': doc.date_modification.isoformat(),
            'url': doc.fichier.url if doc.fichier else None,
        })

    return JsonResponse({
        'success': True,
        'documents': documents,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@login_required
@require_http_methods(["GET"])
def api_document_detail(request, document_id):
    """Détail d'un document"""
    doc = get_object_or_404(Document, id=document_id)

    # Audit lecture
    service = DocumentService(request.user)
    service._audit(doc, 'lecture')

    data = {
        'id': str(doc.id),
        'nom': doc.nom,
        'nom_original': doc.nom_original,
        'type_document': doc.type_document,
        'type_document_display': doc.get_type_document_display(),
        'description': doc.description,
        'taille': doc.taille,
        'taille_humaine': doc.taille_humaine,
        'extension': doc.extension,
        'mime_type': doc.mime_type,
        'hash_md5': doc.hash_md5,
        'hash_sha256': doc.hash_sha256,
        'statut': doc.statut,
        'version': doc.version,
        'est_genere': doc.est_genere,
        'est_modele': doc.est_modele,
        'metadata': doc.metadata,
        'dossier_juridique_id': str(doc.dossier_juridique_id) if doc.dossier_juridique_id else None,
        'dossier_id': str(doc.dossier_id) if doc.dossier_id else None,
        'date_creation': doc.date_creation.isoformat(),
        'date_modification': doc.date_modification.isoformat(),
        'cree_par': doc.cree_par.get_full_name() if doc.cree_par else None,
        'url': doc.fichier.url if doc.fichier else None,
        'versions': list(doc.historique_versions.values(
            'numero_version', 'taille', 'date', 'commentaire'
        )),
        'signatures': list(doc.signatures.values(
            'id', 'signataire_nom', 'type_signature', 'statut', 'date_signature'
        )),
        'partages': list(doc.partages.filter(actif=True).values(
            'id', 'token', 'type_partage', 'date_expiration', 'nombre_acces'
        )),
    }

    return JsonResponse({'success': True, 'document': data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_document_upload(request):
    """
    Upload d'un ou plusieurs documents

    POST (multipart/form-data):
        - fichiers: Fichier(s) à uploader
        - type_document: Type de document
        - dossier_juridique_id: ID du dossier juridique (optionnel)
        - dossier_id: ID du dossier virtuel (optionnel)
        - description: Description
    """
    try:
        service = DocumentService(request.user)

        fichiers = request.FILES.getlist('fichiers')
        if not fichiers:
            fichiers = [request.FILES.get('fichier')]

        type_document = request.POST.get('type_document', 'autre')
        description = request.POST.get('description', '')

        dossier_juridique = None
        dossier_juridique_id = request.POST.get('dossier_juridique_id')
        if dossier_juridique_id and GESTION_AVAILABLE:
            dossier_juridique = Dossier.objects.filter(id=dossier_juridique_id).first()

        dossier = None
        dossier_id = request.POST.get('dossier_id')
        if dossier_id:
            dossier = DossierVirtuel.objects.filter(id=dossier_id).first()

        documents = []
        for fichier in fichiers:
            if fichier:
                doc = service.upload_document(
                    fichier=fichier,
                    type_document=type_document,
                    dossier_juridique=dossier_juridique,
                    dossier=dossier,
                    description=description
                )
                documents.append({
                    'id': str(doc.id),
                    'nom': doc.nom,
                    'taille': doc.taille,
                    'url': doc.fichier.url if doc.fichier else None,
                })

        return JsonResponse({
            'success': True,
            'message': f'{len(documents)} document(s) uploadé(s)',
            'documents': documents
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_document_telecharger(request, document_id):
    """Téléchargement d'un document"""
    doc = get_object_or_404(Document, id=document_id)

    # Audit
    service = DocumentService(request.user)
    service._audit(doc, 'telechargement')

    if not doc.fichier:
        return JsonResponse({'error': 'Fichier non trouvé'}, status=404)

    response = FileResponse(doc.fichier, as_attachment=True, filename=doc.nom_original)
    response['Content-Type'] = doc.mime_type or 'application/octet-stream'
    return response


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_document_supprimer(request):
    """
    Suppression d'un document

    POST (JSON):
        - document_id: ID du document
        - definitif: Si true, suppression définitive
    """
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')
        definitif = data.get('definitif', False)

        doc = get_object_or_404(Document, id=document_id)
        service = DocumentService(request.user)
        service.supprimer_document(doc, definitif=definitif)

        return JsonResponse({
            'success': True,
            'message': 'Document supprimé définitivement' if definitif else 'Document déplacé dans la corbeille'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_document_restaurer(request):
    """Restauration d'un document de la corbeille"""
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')

        doc = get_object_or_404(Document, id=document_id, statut='supprime')
        service = DocumentService(request.user)
        service.restaurer_document(doc)

        return JsonResponse({
            'success': True,
            'message': 'Document restauré'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_document_deplacer(request):
    """Déplacement d'un document"""
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')
        dossier_id = data.get('dossier_id')

        doc = get_object_or_404(Document, id=document_id)
        dossier = get_object_or_404(DossierVirtuel, id=dossier_id)

        service = DocumentService(request.user)
        service.deplacer_document(doc, dossier)

        return JsonResponse({
            'success': True,
            'message': 'Document déplacé'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_document_renommer(request):
    """Renommage d'un document"""
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')
        nouveau_nom = data.get('nom')

        doc = get_object_or_404(Document, id=document_id)
        doc.nom = nouveau_nom
        doc.save()

        service = DocumentService(request.user)
        service._audit(doc, 'modification', {'action': 'renommage', 'nouveau_nom': nouveau_nom})

        return JsonResponse({
            'success': True,
            'message': 'Document renommé'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# API - GÉNÉRATION DE DOCUMENTS
# ==========================================

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generer_fiche_dossier(request):
    """
    Génère la fiche d'un dossier

    POST (JSON):
        - dossier_id: ID du dossier juridique
    """
    try:
        if not GESTION_AVAILABLE:
            return JsonResponse({'error': 'Module gestion non disponible'}, status=400)

        data = json.loads(request.body)
        dossier_id = data.get('dossier_id')

        dossier = get_object_or_404(Dossier, id=dossier_id)
        service = DocumentService(request.user)
        document = service.generer_fiche_dossier(dossier)

        return JsonResponse({
            'success': True,
            'message': 'Fiche du dossier générée',
            'document': {
                'id': str(document.id),
                'nom': document.nom,
                'url': document.fichier.url if document.fichier else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generer_acte(request):
    """
    Génère un acte de procédure

    POST (JSON):
        - dossier_id: ID du dossier juridique
        - type_acte: Type d'acte (commandement, signification, etc.)
        - titre: Titre de l'acte
        - contenu: Contenu de l'acte
        - modele_id: ID du modèle (optionnel)
    """
    try:
        if not GESTION_AVAILABLE:
            return JsonResponse({'error': 'Module gestion non disponible'}, status=400)

        data = json.loads(request.body)
        dossier_id = data.get('dossier_id')
        type_acte = data.get('type_acte', 'autre')

        dossier = get_object_or_404(Dossier, id=dossier_id)

        modele = None
        modele_id = data.get('modele_id')
        if modele_id:
            modele = ModeleDocument.objects.filter(id=modele_id).first()

        acte_data = {
            'titre': data.get('titre', ''),
            'contenu': data.get('contenu', ''),
            'date_acte': datetime.now(),
        }

        # Ajouter les données du dossier
        if dossier.demandeurs.exists():
            demandeur = dossier.demandeurs.first()
            acte_data['creancier_nom'] = demandeur.nom
            acte_data['creancier_adresse'] = demandeur.domicile or demandeur.siege_social or ''

        if dossier.defendeurs.exists():
            debiteur = dossier.defendeurs.first()
            acte_data['debiteur_nom'] = debiteur.nom
            acte_data['debiteur_adresse'] = debiteur.domicile or debiteur.siege_social or ''

        acte_data['montant_principal'] = float(dossier.montant_creance or 0)
        acte_data['reference_dossier'] = dossier.reference

        service = DocumentService(request.user)
        document = service.generer_acte(dossier, type_acte, acte_data, modele)

        return JsonResponse({
            'success': True,
            'message': 'Acte généré',
            'document': {
                'id': str(document.id),
                'nom': document.nom,
                'numero_acte': document.metadata.get('numero_acte'),
                'url': document.fichier.url if document.fichier else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generer_facture_pdf(request):
    """
    Génère le PDF d'une facture

    POST (JSON):
        - facture_id: ID de la facture
    """
    try:
        if not GESTION_AVAILABLE:
            return JsonResponse({'error': 'Module gestion non disponible'}, status=400)

        data = json.loads(request.body)
        facture_id = data.get('facture_id')

        facture = get_object_or_404(Facture, id=facture_id)
        service = DocumentService(request.user)
        document = service.generer_facture_pdf(facture)

        return JsonResponse({
            'success': True,
            'message': 'Facture PDF générée',
            'document': {
                'id': str(document.id),
                'nom': document.nom,
                'url': document.fichier.url if document.fichier else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generer_decompte(request):
    """
    Génère un décompte de recouvrement

    POST (JSON):
        - calcul_data: Données du calcul OHADA
        - dossier_id: ID du dossier juridique (optionnel)
    """
    try:
        data = json.loads(request.body)
        calcul_data = data.get('calcul_data', {})

        dossier = None
        dossier_id = data.get('dossier_id')
        if dossier_id and GESTION_AVAILABLE:
            dossier = Dossier.objects.filter(id=dossier_id).first()

        service = DocumentService(request.user)
        document = service.generer_decompte(calcul_data, dossier)

        return JsonResponse({
            'success': True,
            'message': 'Décompte généré',
            'document': {
                'id': str(document.id),
                'nom': document.nom,
                'url': document.fichier.url if document.fichier else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_generer_lettre(request):
    """
    Génère une lettre (mise en demeure, relance, etc.)

    POST (JSON):
        - type_lettre: Type de lettre
        - objet: Objet de la lettre
        - destinataire: {nom, adresse, ville}
        - contenu: Corps de la lettre
        - dossier_id: ID du dossier juridique (optionnel)
        - modele_id: ID du modèle (optionnel)
    """
    try:
        data = json.loads(request.body)

        dossier = None
        dossier_id = data.get('dossier_id')
        if dossier_id and GESTION_AVAILABLE:
            dossier = Dossier.objects.filter(id=dossier_id).first()

        modele = None
        modele_id = data.get('modele_id')
        if modele_id:
            modele = ModeleDocument.objects.filter(id=modele_id).first()

        lettre_data = {
            'type_lettre': data.get('type_lettre', 'courrier'),
            'objet': data.get('objet', ''),
            'destinataire': data.get('destinataire', {}),
            'contenu': data.get('contenu', ''),
            'reference': dossier.reference if dossier else None,
        }

        service = DocumentService(request.user)
        document = service.generer_lettre(lettre_data, dossier, modele)

        return JsonResponse({
            'success': True,
            'message': 'Lettre générée',
            'document': {
                'id': str(document.id),
                'nom': document.nom,
                'url': document.fichier.url if document.fichier else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# API - DOSSIERS VIRTUELS
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_dossiers_liste(request):
    """
    Liste des dossiers virtuels

    GET params:
        - parent_id: ID du dossier parent
        - dossier_juridique_id: ID du dossier juridique
    """
    qs = DossierVirtuel.objects.all()

    parent_id = request.GET.get('parent_id')
    if parent_id:
        qs = qs.filter(parent_id=parent_id)
    elif not request.GET.get('all'):
        qs = qs.filter(parent__isnull=True)

    dossier_juridique_id = request.GET.get('dossier_juridique_id')
    if dossier_juridique_id:
        qs = qs.filter(dossier_juridique_id=dossier_juridique_id)

    dossiers = []
    for d in qs.order_by('nom'):
        nb_docs = d.documents.exclude(statut='supprime').count()
        nb_sous_dossiers = d.sous_dossiers.count()

        dossiers.append({
            'id': str(d.id),
            'nom': d.nom,
            'type_dossier': d.type_dossier,
            'chemin': d.chemin,
            'parent_id': str(d.parent_id) if d.parent_id else None,
            'dossier_juridique_id': str(d.dossier_juridique_id) if d.dossier_juridique_id else None,
            'couleur': d.couleur,
            'icone': d.icone,
            'est_systeme': d.est_systeme,
            'nb_documents': nb_docs,
            'nb_sous_dossiers': nb_sous_dossiers,
            'date_creation': d.date_creation.isoformat(),
        })

    return JsonResponse({'success': True, 'dossiers': dossiers})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_dossier_creer(request):
    """
    Création d'un dossier virtuel

    POST (JSON):
        - nom: Nom du dossier
        - parent_id: ID du dossier parent (optionnel)
        - dossier_juridique_id: ID du dossier juridique (optionnel)
        - couleur: Couleur (optionnel)
        - icone: Icône (optionnel)
    """
    try:
        data = json.loads(request.body)

        parent = None
        if data.get('parent_id'):
            parent = get_object_or_404(DossierVirtuel, id=data['parent_id'])

        dossier_juridique = None
        if data.get('dossier_juridique_id') and GESTION_AVAILABLE:
            dossier_juridique = Dossier.objects.filter(id=data['dossier_juridique_id']).first()

        dossier = DossierVirtuel.objects.create(
            nom=data['nom'],
            type_dossier=data.get('type_dossier', 'personnel'),
            parent=parent,
            dossier_juridique=dossier_juridique,
            couleur=data.get('couleur', '#1a365d'),
            icone=data.get('icone', 'folder'),
            cree_par=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Dossier créé',
            'dossier': {
                'id': str(dossier.id),
                'nom': dossier.nom,
                'chemin': dossier.chemin,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_dossier_supprimer(request):
    """Suppression d'un dossier virtuel"""
    try:
        data = json.loads(request.body)
        dossier_id = data.get('dossier_id')

        dossier = get_object_or_404(DossierVirtuel, id=dossier_id)

        if dossier.est_systeme:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de supprimer un dossier système'
            }, status=400)

        # Vérifier si vide
        if dossier.documents.exclude(statut='supprime').exists() or dossier.sous_dossiers.exists():
            return JsonResponse({
                'success': False,
                'error': 'Le dossier n\'est pas vide'
            }, status=400)

        dossier.delete()

        return JsonResponse({
            'success': True,
            'message': 'Dossier supprimé'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# API - MODÈLES DE DOCUMENTS
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_modeles_liste(request):
    """Liste des modèles de documents"""
    type_modele = request.GET.get('type')

    qs = ModeleDocument.objects.filter(actif=True)
    if type_modele:
        qs = qs.filter(type_modele=type_modele)

    modeles = []
    for m in qs.order_by('ordre_affichage', 'nom'):
        modeles.append({
            'id': str(m.id),
            'nom': m.nom,
            'code': m.code,
            'type_modele': m.type_modele,
            'type_modele_display': m.get_type_modele_display(),
            'description': m.description,
            'format_sortie': m.format_sortie,
            'variables': m.variables,
            'est_systeme': m.est_systeme,
        })

    return JsonResponse({'success': True, 'modeles': modeles})


@login_required
@require_http_methods(["GET"])
def api_modele_detail(request, modele_id):
    """Détail d'un modèle"""
    modele = get_object_or_404(ModeleDocument, id=modele_id)

    data = {
        'id': str(modele.id),
        'nom': modele.nom,
        'code': modele.code,
        'type_modele': modele.type_modele,
        'description': modele.description,
        'contenu_template': modele.contenu_template,
        'format_sortie': modele.format_sortie,
        'variables': modele.variables,
        'variables_exemple': modele.variables_exemple,
        'avec_entete': modele.avec_entete,
        'avec_pied_page': modele.avec_pied_page,
        'orientation': modele.orientation,
        'marges': {
            'haut': modele.marge_haut,
            'bas': modele.marge_bas,
            'gauche': modele.marge_gauche,
            'droite': modele.marge_droite,
        },
        'est_systeme': modele.est_systeme,
        'variables_disponibles': modele.get_variables_disponibles(),
    }

    return JsonResponse({'success': True, 'modele': data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_modele_sauvegarder(request):
    """Création ou modification d'un modèle"""
    try:
        data = json.loads(request.body)

        modele_id = data.get('id')
        if modele_id:
            modele = get_object_or_404(ModeleDocument, id=modele_id)
            if modele.est_systeme:
                return JsonResponse({
                    'success': False,
                    'error': 'Impossible de modifier un modèle système'
                }, status=400)
        else:
            modele = ModeleDocument(cree_par=request.user)

        modele.nom = data.get('nom', modele.nom)
        modele.code = data.get('code', modele.code)
        modele.type_modele = data.get('type_modele', modele.type_modele)
        modele.description = data.get('description', modele.description)
        modele.contenu_template = data.get('contenu_template', modele.contenu_template)
        modele.format_sortie = data.get('format_sortie', modele.format_sortie)
        modele.variables = data.get('variables', modele.variables)
        modele.variables_exemple = data.get('variables_exemple', modele.variables_exemple)
        modele.avec_entete = data.get('avec_entete', modele.avec_entete)
        modele.avec_pied_page = data.get('avec_pied_page', modele.avec_pied_page)
        modele.orientation = data.get('orientation', modele.orientation)

        if data.get('marges'):
            modele.marge_haut = data['marges'].get('haut', modele.marge_haut)
            modele.marge_bas = data['marges'].get('bas', modele.marge_bas)
            modele.marge_gauche = data['marges'].get('gauche', modele.marge_gauche)
            modele.marge_droite = data['marges'].get('droite', modele.marge_droite)

        modele.save()

        return JsonResponse({
            'success': True,
            'message': 'Modèle sauvegardé',
            'modele': {
                'id': str(modele.id),
                'nom': modele.nom,
                'code': modele.code,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# API - PARTAGE
# ==========================================

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_partage_creer(request):
    """
    Création d'un lien de partage

    POST (JSON):
        - document_id: ID du document (optionnel)
        - dossier_id: ID du dossier (optionnel)
        - type_partage: lecture, telechargement, modification
        - mot_de_passe: Mot de passe (optionnel)
        - duree_jours: Durée de validité en jours
        - destinataire_email: Email du destinataire
        - destinataire_nom: Nom du destinataire
    """
    try:
        data = json.loads(request.body)

        document = None
        if data.get('document_id'):
            document = get_object_or_404(Document, id=data['document_id'])

        dossier = None
        if data.get('dossier_id'):
            dossier = get_object_or_404(DossierVirtuel, id=data['dossier_id'])

        service = DocumentService(request.user)
        partage = service.creer_partage(
            document=document,
            dossier=dossier,
            type_partage=data.get('type_partage', 'lecture'),
            mot_de_passe=data.get('mot_de_passe'),
            duree_jours=data.get('duree_jours'),
            destinataire_email=data.get('destinataire_email'),
            destinataire_nom=data.get('destinataire_nom')
        )

        return JsonResponse({
            'success': True,
            'message': 'Lien de partage créé',
            'partage': {
                'id': str(partage.id),
                'token': partage.token,
                'lien': partage.lien,
                'date_expiration': partage.date_expiration.isoformat() if partage.date_expiration else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_partage_revoquer(request):
    """Révocation d'un partage"""
    try:
        data = json.loads(request.body)
        partage_id = data.get('partage_id')

        partage = get_object_or_404(PartageDocument, id=partage_id)
        service = DocumentService(request.user)
        service.revoquer_partage(partage)

        return JsonResponse({
            'success': True,
            'message': 'Partage révoqué'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# Vue publique de partage
@require_http_methods(["GET", "POST"])
def partage_public_view(request, token):
    """Vue publique pour accéder à un document partagé"""
    partage = get_object_or_404(PartageDocument, token=token, actif=True)

    # Vérifier expiration
    if partage.est_expire:
        return render(request, 'documents/partage_expire.html')

    # Vérifier mot de passe si nécessaire
    if partage.mot_de_passe_hash:
        if request.method == 'POST':
            mot_de_passe = request.POST.get('mot_de_passe', '')
            if not partage.verifier_mot_de_passe(mot_de_passe):
                return render(request, 'documents/partage_password.html', {
                    'error': 'Mot de passe incorrect',
                    'token': token
                })
        else:
            return render(request, 'documents/partage_password.html', {'token': token})

    # Enregistrer l'accès
    partage.enregistrer_acces(
        ip=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Afficher le document ou dossier
    if partage.document:
        if partage.type_partage == 'telechargement':
            return FileResponse(
                partage.document.fichier,
                as_attachment=True,
                filename=partage.document.nom_original
            )
        return render(request, 'documents/partage_document.html', {
            'partage': partage,
            'document': partage.document
        })
    else:
        documents = partage.dossier.documents.exclude(statut='supprime')
        return render(request, 'documents/partage_dossier.html', {
            'partage': partage,
            'dossier': partage.dossier,
            'documents': documents
        })


# ==========================================
# API - STATISTIQUES ET AUDIT
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_statistiques(request):
    """Statistiques du module Documents"""
    dossier_juridique_id = request.GET.get('dossier_juridique_id')

    dossier_juridique = None
    if dossier_juridique_id and GESTION_AVAILABLE:
        dossier_juridique = Dossier.objects.filter(id=dossier_juridique_id).first()

    service = DocumentService(request.user)
    stats = service.obtenir_statistiques(dossier_juridique)

    # Formater les données pour le frontend
    stats['espace_utilise_humain'] = _format_taille(stats['espace_utilise'])

    return JsonResponse({'success': True, 'statistiques': stats})


@login_required
@require_http_methods(["GET"])
def api_audit_document(request, document_id):
    """Historique d'audit d'un document"""
    doc = get_object_or_404(Document, id=document_id)

    audits = AuditDocument.objects.filter(document=doc).order_by('-date')[:100]

    data = []
    for audit in audits:
        data.append({
            'id': str(audit.id),
            'action': audit.action,
            'action_display': audit.get_action_display(),
            'details': audit.details,
            'utilisateur': audit.utilisateur.get_full_name() if audit.utilisateur else None,
            'date': audit.date.isoformat(),
            'ip': audit.ip,
        })

    return JsonResponse({'success': True, 'audits': data})


@login_required
@require_http_methods(["GET"])
def api_activite_recente(request):
    """Activité récente sur les documents"""
    limit = int(request.GET.get('limit', 20))

    audits = AuditDocument.objects.select_related(
        'document', 'utilisateur'
    ).order_by('-date')[:limit]

    data = []
    for audit in audits:
        data.append({
            'id': str(audit.id),
            'action': audit.action,
            'action_display': audit.get_action_display(),
            'document_id': str(audit.document_id) if audit.document_id else None,
            'document_nom': audit.document.nom if audit.document else None,
            'utilisateur': audit.utilisateur.get_full_name() if audit.utilisateur else None,
            'date': audit.date.isoformat(),
        })

    return JsonResponse({'success': True, 'activites': data})


# ==========================================
# API - CORBEILLE
# ==========================================

@login_required
@require_http_methods(["GET"])
def api_corbeille_liste(request):
    """Liste des documents dans la corbeille"""
    documents = Document.objects.filter(statut='supprime').order_by('-date_suppression')

    data = []
    for doc in documents:
        jours_restants = 0
        config = ConfigurationDocuments.get_instance()
        if doc.date_suppression:
            date_suppression_definitive = doc.date_suppression + timedelta(
                days=config.duree_retention_corbeille
            )
            jours_restants = (date_suppression_definitive - timezone.now()).days

        data.append({
            'id': str(doc.id),
            'nom': doc.nom,
            'type_document': doc.type_document,
            'taille_humaine': doc.taille_humaine,
            'date_suppression': doc.date_suppression.isoformat() if doc.date_suppression else None,
            'jours_restants': max(0, jours_restants),
        })

    return JsonResponse({'success': True, 'documents': data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_corbeille_vider(request):
    """Vide la corbeille"""
    service = DocumentService(request.user)
    count = service.vider_corbeille(jours_retention=0)

    return JsonResponse({
        'success': True,
        'message': f'{count} document(s) supprimé(s) définitivement'
    })


# ==========================================
# HELPERS
# ==========================================

def _format_taille(taille):
    """Formate une taille en octets vers une forme lisible"""
    for unite in ['o', 'Ko', 'Mo', 'Go']:
        if taille < 1024:
            return f"{taille:.1f} {unite}"
        taille /= 1024
    return f"{taille:.1f} To"

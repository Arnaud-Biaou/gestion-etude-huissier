"""
Vues pour le module MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES DE CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES DE CITATIONS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Localite, BaremeTarifaire, AutoriteRequerante, CeduleReception,
    DestinataireCedule, ActeSignification, FraisSignification,
    Memoire, LigneMemoire, ValidationMemoire, RegistreParquet,
    ConfigurationCitations
)

# Importer le modÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨le Utilisateur depuis gestion
from gestion.models import Utilisateur, Collaborateur


# =============================================================================
# CONTEXTE PAR DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂFAUT
# =============================================================================

def get_default_context(request):
    """Contexte par dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©faut pour tous les templates"""
    current_user = {
        'id': 1,
        'nom': 'BIAOU Martial Arnaud',
        'role': 'admin',
        'email': 'mab@etude-biaou.bj',
        'initials': 'MA'
    }

    modules = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'home', 'category': 'main', 'url': 'dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'dossiers'},
        {'id': 'citations', 'label': 'Citations', 'icon': 'file-signature', 'category': 'main', 'url': 'citations:dashboard'},
        {'id': 'facturation', 'label': 'Facturation & MECeF', 'icon': 'file-text', 'category': 'main', 'url': 'facturation'},
        {'id': 'calcul', 'label': 'Calcul Recouvrement', 'icon': 'calculator', 'category': 'main', 'url': 'calcul'},
        {'id': 'tresorerie', 'label': 'TrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sorerie', 'icon': 'piggy-bank', 'category': 'finance', 'url': 'tresorerie'},
        {'id': 'comptabilite', 'label': 'ComptabilitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©', 'icon': 'book-open', 'category': 'finance', 'url': 'comptabilite:dashboard'},
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh:dashboard'},
        {'id': 'drive', 'label': 'Drive', 'icon': 'hard-drive', 'category': 'gestion', 'url': 'drive'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda'},
        {'id': 'parametres', 'label': 'Parametres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres'},
        {'id': 'securite', 'label': 'Securite & Acces', 'icon': 'shield', 'category': 'admin', 'url': 'securite'},
    ]

    collaborateurs = list(Collaborateur.objects.filter(actif=True).values('id', 'nom', 'role'))
    if not collaborateurs:
        collaborateurs = [
            {'id': 1, 'nom': 'Me BIAOU Martial', 'role': 'Huissier'},
            {'id': 2, 'nom': 'ADJOVI Carine', 'role': 'Clerc Principal'},
        ]

    return {
        'current_user': current_user,
        'modules': modules,
        'collaborateurs': collaborateurs,
        'active_module': 'citations',
    }


# =============================================================================
# TABLEAU DE BORD
# =============================================================================

def dashboard(request):
    """Tableau de bord du module Citations"""
    context = get_default_context(request)
    context['page_title'] = 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires de CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules de Citations'

    # Statistiques
    today = timezone.now().date()
    debut_mois = today.replace(day=1)

    # CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules
    cedules_recues = CeduleReception.objects.filter(date_reception__gte=debut_mois).count()
    cedules_en_cours = CeduleReception.objects.filter(statut='en_cours').count()
    cedules_urgentes = CeduleReception.objects.filter(
        statut__in=['recue', 'en_cours'],
        urgence__in=['urgente', 'tres_urgente']
    ).count()

    # Actes signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s ce mois
    actes_signifies = ActeSignification.objects.filter(
        date_signification__gte=debut_mois
    ).count()

    # MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires
    memoires_brouillon = Memoire.objects.filter(statut='brouillon').count()
    memoires_en_attente = Memoire.objects.filter(
        statut__in=['certifie', 'soumis', 'vise', 'taxe', 'en_paiement']
    ).count()

    # Montants
    montant_en_attente = Memoire.objects.filter(
        statut__in=['taxe', 'en_paiement']
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    montant_paye_mois = Memoire.objects.filter(
        statut='paye',
        date_paiement__gte=debut_mois
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    context['stats'] = {
        'cedules_recues': cedules_recues,
        'cedules_en_cours': cedules_en_cours,
        'cedules_urgentes': cedules_urgentes,
        'actes_signifies': actes_signifies,
        'memoires_brouillon': memoires_brouillon,
        'memoires_en_attente': memoires_en_attente,
        'montant_en_attente': montant_en_attente,
        'montant_paye_mois': montant_paye_mois,
    }

    # CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules urgentes non traitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©es
    context['cedules_urgentes_list'] = CeduleReception.objects.filter(
        statut__in=['recue', 'en_cours'],
        urgence__in=['urgente', 'tres_urgente']
    ).select_related('autorite_requerante').order_by('date_audience')[:5]

    # Derniers mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires
    context['derniers_memoires'] = Memoire.objects.select_related(
        'autorite_requerante'
    ).order_by('-date_creation')[:5]

    # DerniÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨res cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules
    context['dernieres_cedules'] = CeduleReception.objects.select_related(
        'autorite_requerante'
    ).order_by('-date_reception')[:5]

    return render(request, 'citations/dashboard.html', context)


# =============================================================================
# GESTION DES CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES
# =============================================================================

def cedules(request):
    """Liste des cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules de citation"""
    context = get_default_context(request)
    context['page_title'] = 'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules de Citations'

    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    urgence = request.GET.get('urgence', '')
    autorite = request.GET.get('autorite', '')

    # Query de base
    cedules_qs = CeduleReception.objects.select_related(
        'autorite_requerante'
    ).prefetch_related('destinataires').order_by('-date_reception')

    # Appliquer les filtres
    if search:
        cedules_qs = cedules_qs.filter(
            Q(reference__icontains=search) |
            Q(numero_parquet__icontains=search) |
            Q(nature_infraction__icontains=search)
        )
    if statut:
        cedules_qs = cedules_qs.filter(statut=statut)
    if urgence:
        cedules_qs = cedules_qs.filter(urgence=urgence)
    if autorite:
        cedules_qs = cedules_qs.filter(autorite_requerante_id=autorite)

    # Pagination
    paginator = Paginator(cedules_qs, 20)
    page = request.GET.get('page', 1)
    cedules_page = paginator.get_page(page)

    context['cedules'] = cedules_page
    context['autorites'] = AutoriteRequerante.objects.filter(actif=True)
    context['filters'] = {
        'search': search,
        'statut': statut,
        'urgence': urgence,
        'autorite': autorite,
    }

    # Compteurs par statut
    context['counts'] = {
        'total': CeduleReception.objects.count(),
        'recues': CeduleReception.objects.filter(statut='recue').count(),
        'en_cours': CeduleReception.objects.filter(statut='en_cours').count(),
        'signifiees': CeduleReception.objects.filter(statut='signifiee').count(),
    }

    return render(request, 'citations/cedules.html', context)


def cedule_detail(request, cedule_id):
    """DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail d'une cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    context = get_default_context(request)
    cedule = get_object_or_404(
        CeduleReception.objects.select_related('autorite_requerante'),
        pk=cedule_id
    )
    context['cedule'] = cedule
    context['page_title'] = f'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule {cedule.reference}'

    # Destinataires avec leurs actes
    destinataires = cedule.destinataires.select_related(
        'localite', 'acte_signification'
    ).all()
    context['destinataires'] = destinataires

    # LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s pour le formulaire
    context['localites'] = Localite.objects.filter(actif=True).order_by('nom')

    return render(request, 'citations/cedule_detail.html', context)


def nouvelle_cedule(request):
    """CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ation d'une nouvelle cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    context = get_default_context(request)
    context['page_title'] = 'Nouvelle CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'

    if request.method == 'POST':
        # Traitement du formulaire via API
        return redirect('citations:cedules')

    # GÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer une nouvelle rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence
    context['reference'] = CeduleReception.generer_reference()
    context['autorites'] = AutoriteRequerante.objects.filter(actif=True)
    context['localites'] = Localite.objects.filter(actif=True).order_by('nom')

    return render(request, 'citations/nouvelle_cedule.html', context)


# =============================================================================
# GESTION DES MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES
# =============================================================================

def memoires(request):
    """Liste des mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires de frais"""
    context = get_default_context(request)
    context['page_title'] = 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires de Frais'

    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    annee = request.GET.get('annee', '')
    autorite = request.GET.get('autorite', '')

    # Query de base
    memoires_qs = Memoire.objects.select_related(
        'autorite_requerante'
    ).order_by('-annee', '-mois', '-date_creation')

    # Appliquer les filtres
    if search:
        memoires_qs = memoires_qs.filter(
            Q(numero_memoire__icontains=search) |
            Q(nom_huissier__icontains=search)
        )
    if statut:
        memoires_qs = memoires_qs.filter(statut=statut)
    if annee:
        memoires_qs = memoires_qs.filter(annee=annee)
    if autorite:
        memoires_qs = memoires_qs.filter(autorite_requerante_id=autorite)

    # Pagination
    paginator = Paginator(memoires_qs, 20)
    page = request.GET.get('page', 1)
    memoires_page = paginator.get_page(page)

    context['memoires'] = memoires_page
    context['autorites'] = AutoriteRequerante.objects.filter(actif=True)
    context['annees'] = Memoire.objects.values_list('annee', flat=True).distinct().order_by('-annee')
    context['filters'] = {
        'search': search,
        'statut': statut,
        'annee': annee,
        'autorite': autorite,
    }

    # Statistiques
    context['stats'] = {
        'total': Memoire.objects.count(),
        'brouillon': Memoire.objects.filter(statut='brouillon').count(),
        'en_cours': Memoire.objects.filter(statut__in=['certifie', 'soumis', 'vise', 'taxe']).count(),
        'payes': Memoire.objects.filter(statut='paye').count(),
    }

    return render(request, 'citations/memoires.html', context)


def memoire_detail(request, memoire_id):
    """DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail d'un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    context = get_default_context(request)
    memoire = get_object_or_404(
        Memoire.objects.select_related('autorite_requerante'),
        pk=memoire_id
    )
    context['memoire'] = memoire
    context['page_title'] = f'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire {memoire.numero_memoire}'

    # Lignes du mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire
    lignes = memoire.lignes.select_related(
        'cedule', 'destinataire', 'acte'
    ).order_by('numero_ordre')
    context['lignes'] = lignes

    # Historique des validations
    context['validations'] = memoire.validations.order_by('-date_validation')

    return render(request, 'citations/memoire_detail.html', context)


def nouveau_memoire(request):
    """CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ation d'un nouveau mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    context = get_default_context(request)
    context['page_title'] = 'Nouveau MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'

    now = timezone.now()
    context['mois_courant'] = now.month
    context['annee_courante'] = now.year
    context['autorites'] = AutoriteRequerante.objects.filter(actif=True)

    # CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©es non encore incluses dans un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire
    context['cedules_disponibles'] = CeduleReception.objects.filter(
        statut__in=['signifiee', 'partielle']
    ).exclude(
        lignes_memoire__memoire__statut__in=['certifie', 'soumis', 'vise', 'taxe', 'en_paiement', 'paye']
    ).select_related('autorite_requerante').order_by('-date_reception')

    return render(request, 'citations/nouveau_memoire.html', context)


# =============================================================================
# BARÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMES ET LOCALITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS
# =============================================================================

def baremes(request):
    """Affichage des barÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes tarifaires"""
    context = get_default_context(request)
    context['page_title'] = 'BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes Tarifaires'

    # Grouper les barÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes par type
    context['baremes_signification'] = BaremeTarifaire.objects.filter(
        type_bareme='signification', actif=True
    )
    context['baremes_copie'] = BaremeTarifaire.objects.filter(
        type_bareme='copie', actif=True
    )
    context['baremes_transport'] = BaremeTarifaire.objects.filter(
        type_bareme='transport', actif=True
    )
    context['baremes_mission'] = BaremeTarifaire.objects.filter(
        type_bareme='mission', actif=True
    )

    # Configuration
    context['config'] = ConfigurationCitations.get_instance()

    return render(request, 'citations/baremes.html', context)


def localites(request):
    """Liste des localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s"""
    context = get_default_context(request)
    context['page_title'] = 'LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s'

    search = request.GET.get('search', '')
    departement = request.GET.get('departement', '')

    localites_qs = Localite.objects.filter(actif=True).order_by('departement', 'nom')

    if search:
        localites_qs = localites_qs.filter(
            Q(nom__icontains=search) |
            Q(commune__icontains=search)
        )
    if departement:
        localites_qs = localites_qs.filter(departement=departement)

    # Pagination
    paginator = Paginator(localites_qs, 50)
    page = request.GET.get('page', 1)
    context['localites'] = paginator.get_page(page)

    # Liste des dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©partements
    context['departements'] = Localite.objects.values_list(
        'departement', flat=True
    ).distinct().order_by('departement')

    context['filters'] = {
        'search': search,
        'departement': departement,
    }

    return render(request, 'citations/localites.html', context)


# =============================================================================
# REGISTRE PARQUET
# =============================================================================

def registre_parquet(request):
    """Registre au parquet (Article 75)"""
    context = get_default_context(request)
    context['page_title'] = 'Registre au Parquet'

    # Filtres
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    registre_qs = RegistreParquet.objects.order_by('-date_acte')

    if date_debut:
        registre_qs = registre_qs.filter(date_acte__gte=date_debut)
    if date_fin:
        registre_qs = registre_qs.filter(date_acte__lte=date_fin)

    # Pagination
    paginator = Paginator(registre_qs, 50)
    page = request.GET.get('page', 1)
    context['registre'] = paginator.get_page(page)

    # Total des ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moluments
    context['total_emoluments'] = registre_qs.aggregate(
        total=Sum('montant_emoluments')
    )['total'] or 0

    return render(request, 'citations/registre_parquet.html', context)


# =============================================================================
# API ENDPOINTS - CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES
# =============================================================================

@require_POST
def api_cedule_creer(request):
    """CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er une nouvelle cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    try:
        data = json.loads(request.body)

        cedule = CeduleReception(
            date_reception=data.get('date_reception', timezone.now().date()),
            autorite_requerante_id=data['autorite_requerante_id'],
            numero_parquet=data['numero_parquet'],
            nature_infraction=data.get('nature_infraction', ''),
            nature_acte=data.get('nature_acte', 'citation_correctionnelle'),
            juridiction=data.get('juridiction', ''),
            date_audience=data.get('date_audience'),
            heure_audience=data.get('heure_audience'),
            urgence=data.get('urgence', 'normale'),
            nombre_pieces_jointes=data.get('nombre_pieces_jointes', 0),
            observations=data.get('observations', ''),
        )
        cedule.save()

        # CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er les destinataires
        for dest_data in data.get('destinataires', []):
            destinataire = DestinataireCedule(
                cedule=cedule,
                type_destinataire=dest_data.get('type_destinataire', 'prevenu'),
                type_personne=dest_data.get('type_personne', 'physique'),
                nom=dest_data.get('nom', ''),
                prenoms=dest_data.get('prenoms', ''),
                raison_sociale=dest_data.get('raison_sociale', ''),
                sigle=dest_data.get('sigle', ''),
                representant_legal=dest_data.get('representant_legal', ''),
                adresse=dest_data.get('adresse', ''),
                localite_id=dest_data.get('localite_id'),
                localite_texte=dest_data.get('localite_texte', ''),
                distance_km=dest_data.get('distance_km', 0),
                telephone=dest_data.get('telephone', ''),
                email=dest_data.get('email', ''),
            )
            destinataire.save()

        return JsonResponse({
            'success': True,
            'cedule_id': cedule.id,
            'reference': cedule.reference,
            'message': 'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule crÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_cedule_modifier(request, cedule_id):
    """Modifier une cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    try:
        cedule = get_object_or_404(CeduleReception, pk=cedule_id)
        data = json.loads(request.body)

        # Mettre ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  jour les champs
        for field in ['date_reception', 'numero_parquet', 'nature_infraction',
                      'nature_acte', 'juridiction', 'date_audience', 'heure_audience',
                      'urgence', 'statut', 'nombre_pieces_jointes', 'observations']:
            if field in data:
                setattr(cedule, field, data[field])

        if 'autorite_requerante_id' in data:
            cedule.autorite_requerante_id = data['autorite_requerante_id']

        cedule.save()

        return JsonResponse({
            'success': True,
            'message': 'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule modifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_cedule_detail(request, cedule_id):
    """RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cupÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer les dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tails d'une cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    cedule = get_object_or_404(CeduleReception, pk=cedule_id)

    destinataires = []
    for dest in cedule.destinataires.all():
        dest_data = {
            'id': dest.id,
            'type_destinataire': dest.type_destinataire,
            'type_personne': dest.type_personne,
            'nom': dest.nom,
            'prenoms': dest.prenoms,
            'raison_sociale': dest.raison_sociale,
            'nom_complet': dest.get_nom_complet(),
            'adresse': dest.adresse,
            'localite_id': dest.localite_id,
            'localite_nom': dest.localite.nom if dest.localite else dest.localite_texte,
            'distance_km': float(dest.distance_km),
            'signifie': hasattr(dest, 'acte_signification') and dest.acte_signification is not None,
        }
        if hasattr(dest, 'acte_signification') and dest.acte_signification:
            dest_data['acte'] = {
                'date_signification': dest.acte_signification.date_signification.isoformat(),
                'modalite_remise': dest.acte_signification.modalite_remise,
                'montant': float(dest.acte_signification.get_montant_total()),
            }
        destinataires.append(dest_data)

    return JsonResponse({
        'success': True,
        'cedule': {
            'id': cedule.id,
            'reference': cedule.reference,
            'date_reception': cedule.date_reception.isoformat(),
            'autorite_requerante': cedule.autorite_requerante.nom,
            'numero_parquet': cedule.numero_parquet,
            'nature_infraction': cedule.nature_infraction,
            'nature_acte': cedule.nature_acte,
            'juridiction': cedule.juridiction,
            'date_audience': cedule.date_audience.isoformat() if cedule.date_audience else None,
            'urgence': cedule.urgence,
            'statut': cedule.statut,
            'nb_destinataires': cedule.get_nb_destinataires(),
            'nb_signifies': cedule.get_nb_signifies(),
            'montant_total': float(cedule.calculer_montant_total()),
            'destinataires': destinataires,
        }
    })


# =============================================================================
# API ENDPOINTS - DESTINATAIRES
# =============================================================================

@require_POST
def api_destinataire_ajouter(request, cedule_id):
    """Ajouter un destinataire ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  une cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    try:
        cedule = get_object_or_404(CeduleReception, pk=cedule_id)
        data = json.loads(request.body)

        destinataire = DestinataireCedule(
            cedule=cedule,
            type_destinataire=data.get('type_destinataire', 'prevenu'),
            type_personne=data.get('type_personne', 'physique'),
            nom=data.get('nom', ''),
            prenoms=data.get('prenoms', ''),
            raison_sociale=data.get('raison_sociale', ''),
            sigle=data.get('sigle', ''),
            representant_legal=data.get('representant_legal', ''),
            adresse=data.get('adresse', ''),
            localite_id=data.get('localite_id'),
            localite_texte=data.get('localite_texte', ''),
            distance_km=data.get('distance_km', 0),
            telephone=data.get('telephone', ''),
            email=data.get('email', ''),
            observations=data.get('observations', ''),
        )
        destinataire.save()

        return JsonResponse({
            'success': True,
            'destinataire_id': destinataire.id,
            'message': 'Destinataire ajoutÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_destinataire_supprimer(request, destinataire_id):
    """Supprimer un destinataire"""
    try:
        destinataire = get_object_or_404(DestinataireCedule, pk=destinataire_id)

        # VÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rifier qu'il n'y a pas d'acte de signification
        if hasattr(destinataire, 'acte_signification') and destinataire.acte_signification:
            return JsonResponse({
                'success': False,
                'error': 'Impossible de supprimer un destinataire dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
            }, status=400)

        destinataire.delete()

        return JsonResponse({
            'success': True,
            'message': 'Destinataire supprimÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# API ENDPOINTS - SIGNIFICATION
# =============================================================================

@require_POST
def api_signification_creer(request, destinataire_id):
    """Enregistrer une signification"""
    try:
        destinataire = get_object_or_404(DestinataireCedule, pk=destinataire_id)

        # VÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rifier qu'il n'y a pas dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  une signification
        if hasattr(destinataire, 'acte_signification') and destinataire.acte_signification:
            return JsonResponse({
                'success': False,
                'error': 'Ce destinataire a dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
            }, status=400)

        data = json.loads(request.body)

        # CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er l'acte de signification
        acte = ActeSignification(
            destinataire=destinataire,
            date_signification=data.get('date_signification', timezone.now().date()),
            heure_signification=data.get('heure_signification'),
            modalite_remise=data.get('modalite_remise', 'personne'),
            recepteur_nom=data.get('recepteur_nom', ''),
            recepteur_qualite=data.get('recepteur_qualite', ''),
            lieu_signification=data.get('lieu_signification', ''),
            nombre_copies=data.get('nombre_copies', 1),
            nombre_roles=data.get('nombre_roles', 0),
            observations=data.get('observations', ''),
            difficultes=data.get('difficultes', ''),
        )
        acte.save()

        # CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er les frais de signification
        config = ConfigurationCitations.get_instance()
        frais = FraisSignification(
            acte=acte,
            premier_original=config.tarif_premier_original,
            deuxieme_original=config.tarif_deuxieme_original,
            copies_supplementaires=Decimal(max(0, acte.nombre_copies - 1)) * config.tarif_copie,
            mention_repertoire=config.tarif_mention_repertoire,
            vacation=config.tarif_vacation,
            tarif_km=config.tarif_km,
            type_mission=data.get('type_mission', 'aucune'),
        )
        frais.save()  # Le save() calcule automatiquement les frais

        # Mettre ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  jour le statut de la cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule
        cedule = destinataire.cedule
        nb_destinataires = cedule.get_nb_destinataires()
        nb_signifies = cedule.get_nb_signifies()

        if nb_signifies >= nb_destinataires:
            cedule.statut = 'signifiee'
        elif nb_signifies > 0:
            cedule.statut = 'partielle'
        else:
            cedule.statut = 'en_cours'
        cedule.save()

        # CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er une entrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e dans le registre parquet
        RegistreParquet.objects.create(
            reference_affaire=cedule.numero_parquet,
            nature_diligence=f"Signification {cedule.get_nature_acte_display()}",
            date_acte=acte.date_signification,
            montant_emoluments=frais.total_general,
            acte_signification=acte,
        )

        return JsonResponse({
            'success': True,
            'acte_id': acte.id,
            'montant_total': float(frais.total_general),
            'detail_frais': frais.detail_calcul,
            'message': 'Signification enregistrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_calculer_frais(request):
    """Calculer les frais de signification (preview)"""
    try:
        distance_km = Decimal(request.GET.get('distance_km', 0))
        nombre_copies = int(request.GET.get('nombre_copies', 1))
        nombre_roles = int(request.GET.get('nombre_roles', 0))

        config = ConfigurationCitations.get_instance()

        # Frais de signification (Art. 81)
        premier_original = config.tarif_premier_original
        deuxieme_original = config.tarif_deuxieme_original
        copies_supplementaires = Decimal(max(0, nombre_copies - 1)) * config.tarif_copie
        mention_repertoire = config.tarif_mention_repertoire
        vacation = config.tarif_vacation

        sous_total_signification = (
            premier_original + deuxieme_original +
            copies_supplementaires + mention_repertoire + vacation
        )

        # Frais de copie (Art. 82)
        frais_copie = Decimal(nombre_roles * 1000)

        # Frais de transport (Art. 45 + 89)
        frais_transport = Decimal('0')
        if distance_km > config.seuil_transport_km:
            frais_transport = distance_km * config.tarif_km * 2

        # Frais de mission (DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret 2007-155)
        frais_mission = Decimal('0')
        type_mission = 'aucune'
        if distance_km >= config.seuil_mission_km:
            if distance_km >= 200:
                type_mission = 'journee'
                frais_mission = config.frais_mission_journee
            elif distance_km >= 150:
                type_mission = '2_repas'
                frais_mission = config.frais_mission_2_repas
            else:
                type_mission = '1_repas'
                frais_mission = config.frais_mission_1_repas

        total_general = sous_total_signification + frais_copie + frais_transport + frais_mission

        return JsonResponse({
            'success': True,
            'frais': {
                'signification': {
                    'premier_original': float(premier_original),
                    'deuxieme_original': float(deuxieme_original),
                    'copies_supplementaires': float(copies_supplementaires),
                    'mention_repertoire': float(mention_repertoire),
                    'vacation': float(vacation),
                    'sous_total': float(sous_total_signification),
                },
                'copie': {
                    'nombre_roles': nombre_roles,
                    'tarif_role': 1000,
                    'total': float(frais_copie),
                },
                'transport': {
                    'distance_km': float(distance_km),
                    'tarif_km': float(config.tarif_km),
                    'seuil_km': float(config.seuil_transport_km),
                    'applicable': distance_km > config.seuil_transport_km,
                    'total': float(frais_transport),
                },
                'mission': {
                    'type': type_mission,
                    'seuil_km': float(config.seuil_mission_km),
                    'applicable': distance_km >= config.seuil_mission_km,
                    'total': float(frais_mission),
                },
                'total_general': float(total_general),
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# API ENDPOINTS - MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES
# =============================================================================

@require_POST
def api_memoire_creer(request):
    """CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er un nouveau mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    try:
        data = json.loads(request.body)

        # VÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rifier qu'il n'existe pas dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire pour cette pÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©riode/autoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©
        existing = Memoire.objects.filter(
            mois=data['mois'],
            annee=data['annee'],
            autorite_requerante_id=data['autorite_requerante_id'],
            statut__in=['certifie', 'soumis', 'vise', 'taxe', 'en_paiement', 'paye']
        ).exists()

        if existing:
            return JsonResponse({
                'success': False,
                'error': 'Un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire existe dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  pour cette pÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©riode et cette autoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
            }, status=400)

        # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cupÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer l'utilisateur huissier (simulÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© pour l'instant)
        huissier = Utilisateur.objects.filter(role='huissier').first()
        if not huissier:
            huissier = Utilisateur.objects.first()

        memoire = Memoire(
            mois=data['mois'],
            annee=data['annee'],
            huissier=huissier,
            nom_huissier=data.get('nom_huissier', 'MaÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ®tre BIAOU Martial Arnaud'),
            juridiction_huissier=data.get('juridiction_huissier', 'TPI Parakou'),
            autorite_requerante_id=data['autorite_requerante_id'],
            observations=data.get('observations', ''),
        )
        memoire.save()

        # Ajouter les lignes
        lignes_data = data.get('lignes', [])
        for i, ligne_data in enumerate(lignes_data, start=1):
            LigneMemoire.objects.create(
                memoire=memoire,
                numero_ordre=i,
                cedule_id=ligne_data['cedule_id'],
                destinataire_id=ligne_data['destinataire_id'],
                acte_id=ligne_data.get('acte_id'),
            )

        # Calculer le total
        memoire.calculer_total()

        # CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©er l'historique de validation
        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='creation',
            validateur_nom='SystÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me',
            observations='CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ation du mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
        )

        return JsonResponse({
            'success': True,
            'memoire_id': memoire.id,
            'numero_memoire': memoire.numero_memoire,
            'montant_total': float(memoire.montant_total),
            'message': 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire crÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_memoire_detail(request, memoire_id):
    """RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cupÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer les dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tails d'un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    memoire = get_object_or_404(Memoire, pk=memoire_id)

    lignes = []
    for ligne in memoire.lignes.select_related('cedule', 'destinataire', 'acte').all():
        lignes.append({
            'numero_ordre': ligne.numero_ordre,
            'reference_parquet': ligne.cedule.numero_parquet,
            'destinataire': ligne.destinataire.get_nom_complet(),
            'qualite': ligne.destinataire.get_type_destinataire_display(),
            'nature_acte': ligne.cedule.get_nature_acte_display(),
            'date_signification': ligne.acte.date_signification.isoformat() if ligne.acte else None,
            'montant': float(ligne.montant_ligne),
            'details': ligne.details_calcul,
        })

    return JsonResponse({
        'success': True,
        'memoire': {
            'id': memoire.id,
            'numero_memoire': memoire.numero_memoire,
            'periode': f"{memoire.get_mois_display()} {memoire.annee}",
            'nom_huissier': memoire.nom_huissier,
            'juridiction_huissier': memoire.juridiction_huissier,
            'autorite_requerante': memoire.autorite_requerante.nom,
            'montant_total': float(memoire.montant_total),
            'montant_en_lettres': memoire.montant_en_lettres,
            'statut': memoire.statut,
            'statut_display': memoire.get_statut_display(),
            'date_certification': memoire.date_certification.isoformat() if memoire.date_certification else None,
            'date_soumission': memoire.date_soumission.isoformat() if memoire.date_soumission else None,
            'date_visa': memoire.date_visa.isoformat() if memoire.date_visa else None,
            'vise_par': memoire.vise_par,
            'date_taxe': memoire.date_taxe.isoformat() if memoire.date_taxe else None,
            'taxe_par': memoire.taxe_par,
            'date_paiement': memoire.date_paiement.isoformat() if memoire.date_paiement else None,
            'nb_lignes': memoire.lignes.count(),
            'lignes': lignes,
        }
    })


@require_POST
def api_memoire_certifier(request, memoire_id):
    """Certifier un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)

        if memoire.statut != 'brouillon':
            return JsonResponse({
                'success': False,
                'error': 'Seul un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire en brouillon peut ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªtre certifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
            }, status=400)

        memoire.certifier()

        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='certification',
            validateur_nom='MaÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ®tre BIAOU Martial Arnaud',
            observations='Certification sincÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re et vÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ritable'
        )

        return JsonResponse({
            'success': True,
            'message': 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire certifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avec succÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_memoire_soumettre(request, memoire_id):
    """Soumettre un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire au Parquet"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)
        memoire.soumettre()

        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='soumission',
            validateur_nom='SystÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me',
            observations='Soumission au Parquet'
        )

        return JsonResponse({
            'success': True,
            'message': 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire soumis au Parquet'
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_memoire_viser(request, memoire_id):
    """Visa du Procureur"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)
        data = json.loads(request.body)

        procureur = data.get('procureur', 'Le Procureur de la RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©publique')
        memoire.viser(procureur)

        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='visa',
            validateur_nom=procureur,
            observations='Visa accordÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
        )

        return JsonResponse({
            'success': True,
            'message': 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire visÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par le Procureur'
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_memoire_taxer(request, memoire_id):
    """Taxation par le PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)
        data = json.loads(request.body)

        president = data.get('president', 'Le PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident du Tribunal')
        memoire.taxer(president)

        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='taxe',
            validateur_nom=president,
            observations='TaxÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© exÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cutoire'
        )

        return JsonResponse({
            'success': True,
            'message': 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire taxÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par le PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident'
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_POST
def api_memoire_payer(request, memoire_id):
    """Marquer le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire comme payÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©"""
    try:
        memoire = get_object_or_404(Memoire, pk=memoire_id)
        memoire.marquer_paye()

        ValidationMemoire.objects.create(
            memoire=memoire,
            type_validation='paiement',
            validateur_nom='TrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sor Public',
            observations='Paiement effectuÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
        )

        return JsonResponse({
            'success': True,
            'message': 'Paiement enregistrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# API ENDPOINTS - LOCALITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS
# =============================================================================

def api_localites_liste(request):
    """Liste des localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s"""
    search = request.GET.get('search', '')
    localites_qs = Localite.objects.filter(actif=True)

    if search:
        localites_qs = localites_qs.filter(
            Q(nom__icontains=search) |
            Q(commune__icontains=search)
        )

    localites = [{
        'id': loc.id,
        'nom': loc.nom,
        'commune': loc.commune,
        'departement': loc.departement,
        'distance_parakou': float(loc.distance_parakou),
        'distance_cotonou': float(loc.distance_cotonou),
    } for loc in localites_qs[:50]]

    return JsonResponse({
        'success': True,
        'localites': localites
    })


def api_localite_distance(request, localite_id):
    """RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cupÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer la distance d'une localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©"""
    localite = get_object_or_404(Localite, pk=localite_id)

    return JsonResponse({
        'success': True,
        'localite': {
            'id': localite.id,
            'nom': localite.nom,
            'distance_parakou': float(localite.distance_parakou),
            'distance_cotonou': float(localite.distance_cotonou),
        }
    })


# =============================================================================
# API ENDPOINTS - STATISTIQUES
# =============================================================================

def api_statistiques(request):
    """Statistiques globales du module"""
    annee = int(request.GET.get('annee', timezone.now().year))

    # Statistiques par mois
    stats_mensuelles = []
    for mois in range(1, 13):
        debut_mois = timezone.datetime(annee, mois, 1).date()
        if mois == 12:
            fin_mois = timezone.datetime(annee + 1, 1, 1).date()
        else:
            fin_mois = timezone.datetime(annee, mois + 1, 1).date()

        cedules = CeduleReception.objects.filter(
            date_reception__gte=debut_mois,
            date_reception__lt=fin_mois
        ).count()

        actes = ActeSignification.objects.filter(
            date_signification__gte=debut_mois,
            date_signification__lt=fin_mois
        ).count()

        montant = Memoire.objects.filter(
            mois=mois,
            annee=annee,
            statut='paye'
        ).aggregate(total=Sum('montant_total'))['total'] or 0

        stats_mensuelles.append({
            'mois': mois,
            'cedules': cedules,
            'actes': actes,
            'montant_paye': float(montant),
        })

    # Totaux annuels
    total_cedules = CeduleReception.objects.filter(
        date_reception__year=annee
    ).count()

    total_actes = ActeSignification.objects.filter(
        date_signification__year=annee
    ).count()

    total_paye = Memoire.objects.filter(
        annee=annee,
        statut='paye'
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    total_en_attente = Memoire.objects.filter(
        annee=annee,
        statut__in=['taxe', 'en_paiement']
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    return JsonResponse({
        'success': True,
        'annee': annee,
        'stats_mensuelles': stats_mensuelles,
        'totaux': {
            'cedules': total_cedules,
            'actes': total_actes,
            'montant_paye': float(total_paye),
            'montant_en_attente': float(total_en_attente),
        }
    })

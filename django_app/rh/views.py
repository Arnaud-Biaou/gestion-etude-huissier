"""
Vues du module Ressources Humaines
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Sum, Count, Avg, Q
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from decimal import Decimal
import json
import datetime
import logging

logger = logging.getLogger(__name__)

from .models import (
    Employe, DocumentEmploye, CategorieEmploye, Poste, Site,
    Contrat, AvenantContrat,
    PeriodePaie, BulletinPaie, LigneBulletinPaie, ElementPaie,
    TypeConge, Conge, SoldeConge, TypeAbsence, Absence, Pointage,
    Pret, EcheancePret,
    DeclarationSociale,
    CritereEvaluation, Evaluation, NoteCritereEvaluation,
    Formation, ParticipationFormation,
    TypeSanction, Sanction,
    FinContrat,
    ConfigurationRH,
    SMIG_BENIN, PLAFOND_CNSS
)


def get_default_context(request):
    """Retourne le contexte par défaut pour tous les templates RH"""
    user = request.user

    modules = [
        # Principal
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard', 'category': 'main', 'url': 'gestion:dashboard'},
        {'id': 'dossiers', 'label': 'Dossiers', 'icon': 'folder-open', 'category': 'main', 'url': 'gestion:dossiers'},
        {'id': 'facturation', 'label': 'Facturation', 'icon': 'file-text', 'category': 'main', 'url': 'gestion:facturation'},
        {'id': 'calcul', 'label': 'Calcul Recouvrement', 'icon': 'calculator', 'category': 'main', 'url': 'gestion:calcul'},
        {'id': 'creanciers', 'label': 'Recouvrement Créances', 'icon': 'landmark', 'category': 'main', 'url': 'gestion:creanciers'},
        # Finance
        {'id': 'tresorerie', 'label': 'Trésorerie', 'icon': 'wallet', 'category': 'finance', 'url': 'tresorerie:dashboard'},
        {'id': 'comptabilite', 'label': 'Comptabilité', 'icon': 'book-open', 'category': 'finance', 'url': 'comptabilite:dashboard'},
        # Gestion
        {'id': 'rh', 'label': 'Ressources Humaines', 'icon': 'users', 'category': 'gestion', 'url': 'rh:dashboard'},
        {'id': 'drive', 'label': 'Drive', 'icon': 'hard-drive', 'category': 'gestion', 'url': 'documents:drive'},
        {'id': 'gerance', 'label': 'Gérance Immobilière', 'icon': 'building-2', 'category': 'gestion', 'url': 'gerance:dashboard'},
        {'id': 'agenda', 'label': 'Agenda', 'icon': 'calendar', 'category': 'gestion', 'url': 'agenda:home'},
        # Admin
        {'id': 'parametres', 'label': 'Paramètres', 'icon': 'settings', 'category': 'admin', 'url': 'parametres:index'},
        {'id': 'securite', 'label': 'Sécurité & Accès', 'icon': 'shield', 'category': 'admin', 'url': 'gestion:securite'},
    ]

    return {
        'current_user': {
            'id': user.id if user.is_authenticated else None,
            'nom': user.get_full_name() if user.is_authenticated else 'Invité',
            'role': user.role if user.is_authenticated and hasattr(user, 'role') else '',
            'initials': user.get_initials() if user.is_authenticated and hasattr(user, 'get_initials') else 'XX',
        },
        'modules': modules,
        'active_module': 'rh',
    }


# =============================================================================
# TABLEAU DE BORD RH
# =============================================================================

@login_required
def dashboard(request):
    """Tableau de bord RH"""
    context = get_default_context(request)
    context['page_title'] = 'Ressources Humaines'
    context['active_submenu'] = 'dashboard'

    # Statistiques employés
    employes = Employe.objects.filter(statut='actif')
    context['stats'] = {
        'total_employes': employes.count(),
        'employes_cdi': employes.filter(type_contrat='cdi').count(),
        'employes_cdd': employes.filter(type_contrat='cdd').count(),
        'employes_stage': employes.filter(type_contrat__in=['stage', 'apprentissage']).count(),
        'en_conge': Employe.objects.filter(statut='en_conge').count(),
    }

    # Masse salariale du mois courant
    periode = PeriodePaie.get_periode_courante()
    bulletins = BulletinPaie.objects.filter(periode=periode)
    context['masse_salariale'] = bulletins.aggregate(total=Sum('salaire_brut'))['total'] or 0

    # Alertes
    today = timezone.now().date()
    alertes = []

    # Fins de CDD dans les 30 prochains jours
    fins_cdd = Employe.objects.filter(
        type_contrat='cdd',
        statut='actif',
        date_fin_contrat__lte=today + datetime.timedelta(days=30),
        date_fin_contrat__gte=today
    )
    for emp in fins_cdd:
        jours_restants = (emp.date_fin_contrat - today).days
        alertes.append({
            'type': 'warning',
            'icon': 'clock',
            'message': f"Fin de CDD de {emp.get_nom_complet()} dans {jours_restants} jours",
            'date': emp.date_fin_contrat,
        })

    # Fins de période d'essai dans les 15 prochains jours
    contrats_essai = Contrat.objects.filter(
        statut='actif',
        date_fin_essai__lte=today + datetime.timedelta(days=15),
        date_fin_essai__gte=today
    )
    for contrat in contrats_essai:
        jours_restants = (contrat.date_fin_essai - today).days
        alertes.append({
            'type': 'info',
            'icon': 'user-check',
            'message': f"Fin période d'essai de {contrat.employe.get_nom_complet()} dans {jours_restants} jours",
            'date': contrat.date_fin_essai,
        })

    # Congés en cours
    conges_en_cours = Conge.objects.filter(
        statut='en_cours',
        date_debut__lte=today,
        date_fin__gte=today
    ).select_related('employe', 'type_conge')
    for conge in conges_en_cours:
        jours_restants = (conge.date_fin - today).days
        alertes.append({
            'type': 'success',
            'icon': 'palm-tree',
            'message': f"{conge.employe.get_nom_complet()} en {conge.type_conge.libelle} ({jours_restants} jours restants)",
            'date': conge.date_fin,
        })

    # Anniversaires du mois
    anniversaires = Employe.objects.filter(
        statut='actif',
        date_naissance__month=today.month
    )
    for emp in anniversaires:
        date_anniversaire = emp.date_naissance.replace(year=today.year)
        if date_anniversaire >= today:
            alertes.append({
                'type': 'info',
                'icon': 'cake',
                'message': f"Anniversaire de {emp.get_nom_complet()} ({emp.age + 1} ans)",
                'date': date_anniversaire,
            })

    context['alertes'] = sorted(alertes, key=lambda x: x['date'])[:10]

    # Derniers bulletins de paie
    context['derniers_bulletins'] = BulletinPaie.objects.select_related(
        'employe', 'periode'
    ).order_by('-date_creation')[:5]

    # Demandes de congés en attente
    context['conges_en_attente'] = Conge.objects.filter(
        statut='en_attente'
    ).select_related('employe', 'type_conge').order_by('-date_demande')[:5]

    # Répartition par type de contrat pour graphique
    context['repartition_contrats'] = {
        'labels': ['CDI', 'CDD', 'Stage', 'Apprentissage'],
        'data': [
            employes.filter(type_contrat='cdi').count(),
            employes.filter(type_contrat='cdd').count(),
            employes.filter(type_contrat='stage').count(),
            employes.filter(type_contrat='apprentissage').count(),
        ]
    }

    return render(request, 'rh/dashboard.html', context)


# =============================================================================
# GESTION DES EMPLOYÉS
# =============================================================================

@login_required
def liste_employes(request):
    """Liste des employés"""
    context = get_default_context(request)
    context['page_title'] = 'Liste des employés'
    context['active_submenu'] = 'employes'

    # Filtres
    statut = request.GET.get('statut', 'actif')
    type_contrat = request.GET.get('type_contrat', '')
    site_id = request.GET.get('site', '')
    recherche = request.GET.get('q', '')

    employes = Employe.objects.select_related('poste', 'categorie', 'site')

    if statut:
        employes = employes.filter(statut=statut)
    if type_contrat:
        employes = employes.filter(type_contrat=type_contrat)
    if site_id:
        employes = employes.filter(site_id=site_id)
    if recherche:
        employes = employes.filter(
            Q(nom__icontains=recherche) |
            Q(prenoms__icontains=recherche) |
            Q(matricule__icontains=recherche)
        )

    # Pagination
    paginator = Paginator(employes, 20)
    page = request.GET.get('page', 1)
    context['employes'] = paginator.get_page(page)

    # Données pour filtres
    context['sites'] = Site.objects.filter(actif=True)
    context['types_contrat'] = Employe.TYPE_CONTRAT_CHOICES
    context['statuts'] = Employe.STATUT_CHOICES

    # Filtres actuels
    context['filtres'] = {
        'statut': statut,
        'type_contrat': type_contrat,
        'site': site_id,
        'q': recherche,
    }

    return render(request, 'rh/employes.html', context)


@login_required
def detail_employe(request, employe_id):
    """Détail d'un employé"""
    context = get_default_context(request)
    employe = get_object_or_404(Employe.objects.select_related(
        'poste', 'categorie', 'site', 'superieur'
    ), pk=employe_id)

    context['page_title'] = f'Fiche employé - {employe.get_nom_complet()}'
    context['active_submenu'] = 'employes'
    context['employe'] = employe

    # Contrats
    context['contrats'] = employe.contrats.select_related('poste', 'categorie').order_by('-date_debut')

    # Bulletins de paie (12 derniers mois)
    context['bulletins'] = employe.bulletins.select_related('periode').order_by('-periode__annee', '-periode__mois')[:12]

    # Congés
    context['conges'] = employe.conges.select_related('type_conge').order_by('-date_debut')[:10]

    # Solde congés année en cours
    try:
        context['solde_conges'] = SoldeConge.objects.get(
            employe=employe,
            annee=timezone.now().year
        )
    except SoldeConge.DoesNotExist:
        context['solde_conges'] = None

    # Absences récentes
    context['absences'] = employe.absences.select_related('type_absence').order_by('-date_debut')[:10]

    # Prêts en cours
    context['prets'] = employe.prets.filter(statut__in=['en_cours', 'approuve']).order_by('-date_demande')

    # Évaluations
    context['evaluations'] = employe.evaluations.select_related('evaluateur').order_by('-date_evaluation')[:5]

    # Formations
    context['formations'] = employe.formations_suivies.select_related('formation').order_by('-formation__date_debut')[:5]

    # Sanctions
    context['sanctions'] = employe.sanctions.select_related('type_sanction').order_by('-date_faits')[:5]

    # Documents
    context['documents'] = employe.documents.order_by('-date_upload')[:10]

    return render(request, 'rh/employe_detail.html', context)


@login_required
def nouveau_employe(request):
    """Création d'un nouvel employé"""
    context = get_default_context(request)
    context['page_title'] = 'Nouvel employé'
    context['active_submenu'] = 'employes'

    context['categories'] = CategorieEmploye.objects.all()
    context['postes'] = Poste.objects.filter(actif=True)
    context['sites'] = Site.objects.filter(actif=True)
    context['superieurs'] = Employe.objects.filter(statut='actif')
    context['types_contrat'] = Employe.TYPE_CONTRAT_CHOICES
    context['sexes'] = Employe.SEXE_CHOICES
    context['situations_matrimoniales'] = Employe.SITUATION_MATRIMONIALE_CHOICES

    # Générer le prochain matricule
    context['prochain_matricule'] = Employe.generer_matricule()

    return render(request, 'rh/employe_form.html', context)


@login_required
@require_POST
@transaction.atomic
def sauvegarder_employe(request):
    """Sauvegarde d'un employé (création ou modification)"""
    try:
        data = json.loads(request.body)
        employe_id = data.get('id')

        if employe_id:
            employe = get_object_or_404(Employe, pk=employe_id)
        else:
            employe = Employe()
            employe.matricule = Employe.generer_matricule()

        # Informations personnelles
        employe.nom = data.get('nom', '')
        employe.prenoms = data.get('prenoms', '')
        employe.date_naissance = data.get('date_naissance')
        employe.lieu_naissance = data.get('lieu_naissance', '')
        employe.sexe = data.get('sexe', 'M')
        employe.situation_matrimoniale = data.get('situation_matrimoniale', 'celibataire')
        employe.nombre_enfants = int(data.get('nombre_enfants', 0))
        employe.nationalite = data.get('nationalite', 'Béninoise')
        employe.numero_cni = data.get('numero_cni', '')

        # Contacts
        employe.adresse = data.get('adresse', '')
        employe.telephone = data.get('telephone', '')
        employe.telephone_secondaire = data.get('telephone_secondaire', '')
        employe.email = data.get('email', '')

        # Contact urgence
        employe.contact_urgence_nom = data.get('contact_urgence_nom', '')
        employe.contact_urgence_telephone = data.get('contact_urgence_telephone', '')
        employe.contact_urgence_relation = data.get('contact_urgence_relation', '')

        # Informations professionnelles
        employe.date_embauche = data.get('date_embauche')
        employe.type_contrat = data.get('type_contrat', 'cdi')
        if data.get('date_fin_contrat'):
            employe.date_fin_contrat = data.get('date_fin_contrat')
        employe.salaire_base = Decimal(str(data.get('salaire_base', SMIG_BENIN)))

        if data.get('categorie'):
            employe.categorie_id = data.get('categorie')
        if data.get('poste'):
            employe.poste_id = data.get('poste')
        if data.get('site'):
            employe.site_id = data.get('site')
        if data.get('superieur'):
            employe.superieur_id = data.get('superieur')

        employe.statut = data.get('statut', 'actif')

        # Informations légales
        employe.numero_cnss = data.get('numero_cnss', '')
        employe.numero_ifu = data.get('numero_ifu', '')
        employe.numero_cip = data.get('numero_cip', '')

        # RIB
        employe.banque = data.get('banque', '')
        employe.rib_code_banque = data.get('rib_code_banque', '')
        employe.rib_code_guichet = data.get('rib_code_guichet', '')
        employe.rib_numero_compte = data.get('rib_numero_compte', '')
        employe.rib_cle = data.get('rib_cle', '')

        employe.full_clean()
        employe.save()

        # Créer le contrat initial si nouvel employé
        if not employe_id:
            contrat = Contrat.objects.create(
                employe=employe,
                reference=Contrat.generer_reference(),
                type_contrat=employe.type_contrat,
                date_debut=employe.date_embauche,
                date_fin=employe.date_fin_contrat,
                poste=employe.poste,
                categorie=employe.categorie,
                salaire_base=employe.salaire_base,
                site=employe.site,
                periode_essai_mois=employe.categorie.duree_essai_mois if employe.categorie else 1,
            )

            # Créer le solde de congés initial
            SoldeConge.objects.create(
                employe=employe,
                annee=timezone.now().year,
                jours_acquis=0,
                jours_pris=0,
                jours_reportes=0,
            )

        logger.info(f"Employé {'modifié' if employe_id else 'créé'}: {employe.matricule} - {employe.get_nom_complet()}")

        return JsonResponse({
            'success': True,
            'employe_id': employe.id,
            'message': 'Employé enregistré avec succès'
        })

    except ValidationError as e:
        logger.warning(f"Erreur de validation employé: {e}")
        # Gérer les erreurs de validation Django
        if hasattr(e, 'message_dict'):
            return JsonResponse({
                'success': False,
                'errors': e.message_dict
            }, status=400)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    except Exception as e:
        logger.exception("Erreur lors de la sauvegarde de l'employé")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue lors de l\'enregistrement'
        }, status=500)


# =============================================================================
# GESTION DES CONTRATS
# =============================================================================

@login_required
def liste_contrats(request):
    """Liste des contrats"""
    context = get_default_context(request)
    context['page_title'] = 'Gestion des contrats'
    context['active_submenu'] = 'contrats'

    contrats = Contrat.objects.select_related(
        'employe', 'poste', 'categorie'
    ).order_by('-date_debut')

    # Filtres
    statut = request.GET.get('statut', 'actif')
    type_contrat = request.GET.get('type', '')

    if statut:
        contrats = contrats.filter(statut=statut)
    if type_contrat:
        contrats = contrats.filter(type_contrat=type_contrat)

    paginator = Paginator(contrats, 20)
    page = request.GET.get('page', 1)
    context['contrats'] = paginator.get_page(page)

    context['types_contrat'] = Contrat.TYPE_CONTRAT_CHOICES
    context['statuts'] = Contrat.STATUT_CHOICES

    return render(request, 'rh/contrats.html', context)


@login_required
@require_POST
def creer_avenant(request):
    """Création d'un avenant au contrat"""
    try:
        data = json.loads(request.body)
        contrat = get_object_or_404(Contrat, pk=data.get('contrat_id'))

        avenant = AvenantContrat.objects.create(
            contrat=contrat,
            reference=f"AVT-{contrat.reference}-{contrat.avenants.count() + 1:02d}",
            type_avenant=data.get('type_avenant'),
            date_effet=data.get('date_effet'),
            description=data.get('description', ''),
            ancien_salaire=data.get('ancien_salaire'),
            nouveau_salaire=data.get('nouveau_salaire'),
        )

        # Mettre à jour le contrat et l'employé si nécessaire
        if avenant.type_avenant == 'salaire' and avenant.nouveau_salaire:
            contrat.salaire_base = avenant.nouveau_salaire
            contrat.save()
            contrat.employe.salaire_base = avenant.nouveau_salaire
            contrat.employe.save()

        return JsonResponse({
            'success': True,
            'avenant_id': avenant.id,
            'message': 'Avenant créé avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# GESTION DE LA PAIE
# =============================================================================

@login_required
def paie_dashboard(request):
    """Dashboard de la paie"""
    context = get_default_context(request)
    context['page_title'] = 'Gestion de la paie'
    context['active_submenu'] = 'paie'

    # Période courante
    periode = PeriodePaie.get_periode_courante()
    context['periode'] = periode

    # Bulletins du mois
    bulletins = BulletinPaie.objects.filter(periode=periode).select_related('employe')
    context['bulletins'] = bulletins

    # Statistiques
    context['stats'] = {
        'nb_bulletins': bulletins.count(),
        'nb_valides': bulletins.filter(statut='valide').count(),
        'nb_payes': bulletins.filter(statut='paye').count(),
        'total_brut': bulletins.aggregate(total=Sum('salaire_brut'))['total'] or 0,
        'total_net': bulletins.aggregate(total=Sum('net_a_payer'))['total'] or 0,
        'total_cnss_salariale': bulletins.aggregate(total=Sum('cnss_salariale'))['total'] or 0,
        'total_cnss_patronale': bulletins.aggregate(total=Sum('cnss_patronale'))['total'] or 0,
        'total_ipts': bulletins.aggregate(total=Sum('ipts'))['total'] or 0,
    }

    # Périodes disponibles
    context['periodes'] = PeriodePaie.objects.all()[:12]

    return render(request, 'rh/paie.html', context)


@login_required
@require_POST
@transaction.atomic
def generer_bulletins(request):
    """Génère les bulletins de paie pour la période"""
    try:
        data = json.loads(request.body)
        periode_id = data.get('periode_id')

        if periode_id:
            periode = get_object_or_404(PeriodePaie, pk=periode_id)
        else:
            periode = PeriodePaie.get_periode_courante()

        # Employés actifs sans bulletin pour cette période
        employes = Employe.objects.filter(statut='actif').exclude(
            bulletins__periode=periode
        )

        bulletins_crees = 0
        for employe in employes:
            bulletin = BulletinPaie.objects.create(
                employe=employe,
                periode=periode,
                reference=BulletinPaie.generer_reference(employe, periode),
                salaire_base=employe.salaire_base,
            )
            bulletin.calculer()
            bulletins_crees += 1

        logger.info(f"Génération paie {periode}: {bulletins_crees} bulletins créés")

        return JsonResponse({
            'success': True,
            'bulletins_crees': bulletins_crees,
            'message': f'{bulletins_crees} bulletin(s) généré(s)'
        })

    except Exception as e:
        logger.exception("Erreur lors de la génération des bulletins")
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la génération des bulletins'
        }, status=500)


@login_required
def detail_bulletin(request, bulletin_id):
    """Détail d'un bulletin de paie"""
    context = get_default_context(request)
    bulletin = get_object_or_404(BulletinPaie.objects.select_related(
        'employe', 'employe__poste', 'employe__categorie', 'periode'
    ), pk=bulletin_id)

    context['page_title'] = f'Bulletin de paie - {bulletin.employe.get_nom_complet()}'
    context['active_submenu'] = 'paie'
    context['bulletin'] = bulletin
    context['lignes'] = bulletin.lignes.select_related('element').all()

    # Configuration employeur
    config = ConfigurationRH.get_instance()
    context['config'] = config

    return render(request, 'rh/bulletin_detail.html', context)


@login_required
def imprimer_bulletin(request, bulletin_id):
    """Version imprimable du bulletin"""
    bulletin = get_object_or_404(BulletinPaie.objects.select_related(
        'employe', 'employe__poste', 'employe__categorie', 'periode'
    ), pk=bulletin_id)

    config = ConfigurationRH.get_instance()

    context = {
        'bulletin': bulletin,
        'lignes': bulletin.lignes.select_related('element').all(),
        'config': config,
    }

    return render(request, 'rh/bulletin_print.html', context)


@login_required
@require_POST
def valider_bulletin(request, bulletin_id):
    """Valide un bulletin de paie"""
    try:
        bulletin = get_object_or_404(BulletinPaie, pk=bulletin_id)
        bulletin.statut = 'valide'
        bulletin.valide_par = request.user
        bulletin.save()

        return JsonResponse({
            'success': True,
            'message': 'Bulletin validé avec succès'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def payer_bulletin(request, bulletin_id):
    """Marque un bulletin comme payé"""
    try:
        bulletin = get_object_or_404(BulletinPaie, pk=bulletin_id)
        bulletin.statut = 'paye'
        bulletin.date_paiement = timezone.now().date()
        bulletin.save()

        return JsonResponse({
            'success': True,
            'message': 'Bulletin marqué comme payé'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# GESTION DES CONGÉS
# =============================================================================

@login_required
def conges_dashboard(request):
    """Dashboard des congés"""
    context = get_default_context(request)
    context['page_title'] = 'Gestion des congés'
    context['active_submenu'] = 'conges'

    # Demandes en attente
    context['demandes_en_attente'] = Conge.objects.filter(
        statut='en_attente'
    ).select_related('employe', 'type_conge').order_by('-date_demande')

    # Congés en cours
    today = timezone.now().date()
    context['conges_en_cours'] = Conge.objects.filter(
        statut='en_cours',
        date_debut__lte=today,
        date_fin__gte=today
    ).select_related('employe', 'type_conge')

    # Calendrier des congés (30 prochains jours)
    date_fin = today + datetime.timedelta(days=30)
    context['conges_planifies'] = Conge.objects.filter(
        statut__in=['approuve', 'en_cours'],
        date_debut__lte=date_fin,
        date_fin__gte=today
    ).select_related('employe', 'type_conge').order_by('date_debut')

    # Types de congés
    context['types_conge'] = TypeConge.objects.filter(actif=True)

    # Soldes de congés des employés
    context['soldes'] = SoldeConge.objects.filter(
        annee=today.year
    ).select_related('employe').order_by('employe__nom')

    return render(request, 'rh/conges.html', context)


@login_required
@require_POST
def demander_conge(request):
    """Création d'une demande de congé"""
    try:
        data = json.loads(request.body)

        employe = get_object_or_404(Employe, pk=data.get('employe_id'))
        type_conge = get_object_or_404(TypeConge, pk=data.get('type_conge_id'))

        conge = Conge.objects.create(
            employe=employe,
            type_conge=type_conge,
            date_debut=data.get('date_debut'),
            date_fin=data.get('date_fin'),
            motif=data.get('motif', ''),
        )

        return JsonResponse({
            'success': True,
            'conge_id': conge.id,
            'message': 'Demande de congé enregistrée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def approuver_conge(request, conge_id):
    """Approbation d'une demande de congé"""
    try:
        data = json.loads(request.body)
        conge = get_object_or_404(Conge, pk=conge_id)
        action = data.get('action')  # 'approuver' ou 'refuser'

        if action == 'approuver':
            conge.statut = 'approuve'
            conge.approuve_par = request.user
            conge.date_approbation = timezone.now()

            # Déduire du solde de congés
            if conge.type_conge.decompte_solde:
                try:
                    solde = SoldeConge.objects.get(
                        employe=conge.employe,
                        annee=conge.date_debut.year
                    )
                    solde.jours_pris += conge.nombre_jours
                    solde.save()
                except SoldeConge.DoesNotExist:
                    pass

            message = 'Congé approuvé'
        else:
            conge.statut = 'refuse'
            conge.motif_refus = data.get('motif_refus', '')
            message = 'Congé refusé'

        conge.save()

        return JsonResponse({
            'success': True,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# GESTION DES ABSENCES
# =============================================================================

@login_required
def absences_dashboard(request):
    """Dashboard des absences"""
    context = get_default_context(request)
    context['page_title'] = 'Gestion des absences'
    context['active_submenu'] = 'absences'

    # Filtres
    mois = int(request.GET.get('mois', timezone.now().month))
    annee = int(request.GET.get('annee', timezone.now().year))

    context['mois_courant'] = mois
    context['annee_courante'] = annee

    # Absences du mois
    date_debut = datetime.date(annee, mois, 1)
    if mois == 12:
        date_fin = datetime.date(annee + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        date_fin = datetime.date(annee, mois + 1, 1) - datetime.timedelta(days=1)

    context['absences'] = Absence.objects.filter(
        date_debut__gte=date_debut,
        date_debut__lte=date_fin
    ).select_related('employe', 'type_absence').order_by('-date_debut')

    # Statistiques
    context['stats'] = {
        'total_absences': context['absences'].count(),
        'absences_justifiees': context['absences'].filter(justifie=True).count(),
        'absences_non_justifiees': context['absences'].filter(justifie=False).count(),
        'total_jours': context['absences'].aggregate(total=Sum('nombre_jours'))['total'] or 0,
    }

    # Types d'absence
    context['types_absence'] = TypeAbsence.objects.filter(actif=True)

    return render(request, 'rh/absences.html', context)


@login_required
@require_POST
def enregistrer_absence(request):
    """Enregistrement d'une absence"""
    try:
        data = json.loads(request.body)

        employe = get_object_or_404(Employe, pk=data.get('employe_id'))
        type_absence = get_object_or_404(TypeAbsence, pk=data.get('type_absence_id'))

        absence = Absence.objects.create(
            employe=employe,
            type_absence=type_absence,
            date_debut=data.get('date_debut'),
            date_fin=data.get('date_fin'),
            justifie=data.get('justifie', False),
            motif=data.get('motif', ''),
        )

        return JsonResponse({
            'success': True,
            'absence_id': absence.id,
            'retenue': float(absence.retenue_calculee),
            'message': 'Absence enregistrée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# GESTION DES PRÊTS
# =============================================================================

@login_required
def prets_dashboard(request):
    """Dashboard des prêts et avances"""
    context = get_default_context(request)
    context['page_title'] = 'Prêts et avances'
    context['active_submenu'] = 'prets'

    # Demandes en attente
    context['demandes_en_attente'] = Pret.objects.filter(
        statut='en_attente'
    ).select_related('employe').order_by('-date_demande')

    # Prêts en cours
    context['prets_en_cours'] = Pret.objects.filter(
        statut='en_cours'
    ).select_related('employe').order_by('-date_accord')

    # Statistiques
    prets_en_cours = Pret.objects.filter(statut='en_cours')
    context['stats'] = {
        'nb_prets_en_cours': prets_en_cours.count(),
        'total_prete': prets_en_cours.aggregate(total=Sum('montant'))['total'] or 0,
        'total_rembourse': prets_en_cours.aggregate(total=Sum('montant_rembourse'))['total'] or 0,
        'total_restant': (prets_en_cours.aggregate(total=Sum('montant'))['total'] or 0) -
                         (prets_en_cours.aggregate(total=Sum('montant_rembourse'))['total'] or 0),
    }

    return render(request, 'rh/prets.html', context)


@login_required
@require_POST
def demander_pret(request):
    """Création d'une demande de prêt/avance"""
    try:
        data = json.loads(request.body)

        employe = get_object_or_404(Employe, pk=data.get('employe_id'))
        type_pret = data.get('type_pret', 'avance')

        pret = Pret(
            employe=employe,
            reference=Pret.generer_reference(type_pret),
            type_pret=type_pret,
            montant=Decimal(str(data.get('montant', 0))),
            motif=data.get('motif', ''),
            date_demande=timezone.now().date(),
            nombre_echeances=int(data.get('nombre_echeances', 1)),
        )

        # Calcul montant par échéance
        pret.montant_echeance = pret.montant / pret.nombre_echeances

        pret.full_clean()
        pret.save()

        return JsonResponse({
            'success': True,
            'pret_id': pret.id,
            'message': 'Demande enregistrée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def approuver_pret(request, pret_id):
    """Approbation d'une demande de prêt"""
    try:
        data = json.loads(request.body)
        pret = get_object_or_404(Pret, pk=pret_id)
        action = data.get('action')

        if action == 'approuver':
            pret.statut = 'approuve'
            pret.date_accord = timezone.now().date()
            pret.approuve_par = request.user

            # Créer les échéances
            date_echeance = timezone.now().date().replace(day=28)
            if date_echeance <= timezone.now().date():
                if date_echeance.month == 12:
                    date_echeance = date_echeance.replace(year=date_echeance.year + 1, month=1)
                else:
                    date_echeance = date_echeance.replace(month=date_echeance.month + 1)

            pret.date_premiere_echeance = date_echeance

            for i in range(pret.nombre_echeances):
                EcheancePret.objects.create(
                    pret=pret,
                    numero=i + 1,
                    date_echeance=date_echeance,
                    montant=pret.montant_echeance,
                )
                if date_echeance.month == 12:
                    date_echeance = date_echeance.replace(year=date_echeance.year + 1, month=1)
                else:
                    date_echeance = date_echeance.replace(month=date_echeance.month + 1)

            message = 'Prêt approuvé'
        else:
            pret.statut = 'refuse'
            pret.motif_refus = data.get('motif_refus', '')
            message = 'Prêt refusé'

        pret.save()

        return JsonResponse({
            'success': True,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# DÉCLARATIONS SOCIALES ET FISCALES
# =============================================================================

@login_required
def declarations_dashboard(request):
    """Dashboard des déclarations"""
    context = get_default_context(request)
    context['page_title'] = 'Déclarations sociales et fiscales'
    context['active_submenu'] = 'declarations'

    annee = int(request.GET.get('annee', timezone.now().year))
    context['annee'] = annee

    # Déclarations de l'année
    context['declarations'] = DeclarationSociale.objects.filter(
        annee=annee
    ).order_by('-periode_debut')

    # Prochaines échéances
    today = timezone.now().date()
    config = ConfigurationRH.get_instance()

    echeances = []

    # DNS mensuelle
    date_limite_dns = today.replace(day=config.date_limite_dns)
    if date_limite_dns < today:
        if today.month == 12:
            date_limite_dns = date_limite_dns.replace(year=today.year + 1, month=1)
        else:
            date_limite_dns = date_limite_dns.replace(month=today.month + 1)
    echeances.append({
        'type': 'DNS Mensuelle',
        'date_limite': date_limite_dns,
        'jours_restants': (date_limite_dns - today).days,
    })

    # IPTS mensuel
    date_limite_ipts = today.replace(day=config.date_limite_ipts)
    if date_limite_ipts < today:
        if today.month == 12:
            date_limite_ipts = date_limite_ipts.replace(year=today.year + 1, month=1)
        else:
            date_limite_ipts = date_limite_ipts.replace(month=today.month + 1)
    echeances.append({
        'type': 'IPTS Mensuel',
        'date_limite': date_limite_ipts,
        'jours_restants': (date_limite_ipts - today).days,
    })

    context['echeances'] = echeances

    # Statistiques annuelles
    declarations_annee = DeclarationSociale.objects.filter(annee=annee)
    context['stats'] = {
        'total_cotisations_cnss': declarations_annee.aggregate(
            total=Sum('total_cotisations')
        )['total'] or 0,
        'total_ipts': declarations_annee.aggregate(total=Sum('total_ipts'))['total'] or 0,
        'total_vps': declarations_annee.aggregate(total=Sum('total_vps'))['total'] or 0,
    }

    return render(request, 'rh/declarations.html', context)


@login_required
@require_POST
def generer_declaration(request):
    """Génère une déclaration"""
    try:
        data = json.loads(request.body)

        type_declaration = data.get('type_declaration')
        annee = int(data.get('annee', timezone.now().year))
        mois = data.get('mois')
        trimestre = data.get('trimestre')

        # Calculer les dates de période
        if mois:
            mois = int(mois)
            date_debut = datetime.date(annee, mois, 1)
            if mois == 12:
                date_fin = datetime.date(annee + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                date_fin = datetime.date(annee, mois + 1, 1) - datetime.timedelta(days=1)
        elif trimestre:
            trimestre = int(trimestre)
            mois_debut = (trimestre - 1) * 3 + 1
            date_debut = datetime.date(annee, mois_debut, 1)
            mois_fin = trimestre * 3
            if mois_fin == 12:
                date_fin = datetime.date(annee + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                date_fin = datetime.date(annee, mois_fin + 1, 1) - datetime.timedelta(days=1)
        else:
            date_debut = datetime.date(annee, 1, 1)
            date_fin = datetime.date(annee, 12, 31)

        declaration = DeclarationSociale.objects.create(
            type_declaration=type_declaration,
            periode_debut=date_debut,
            periode_fin=date_fin,
            annee=annee,
            mois=mois,
            trimestre=trimestre,
        )

        declaration.generer()

        return JsonResponse({
            'success': True,
            'declaration_id': declaration.id,
            'message': 'Déclaration générée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# ÉVALUATIONS
# =============================================================================

@login_required
def evaluations_dashboard(request):
    """Dashboard des évaluations"""
    context = get_default_context(request)
    context['page_title'] = 'Évaluations'
    context['active_submenu'] = 'evaluations'

    # Évaluations récentes
    context['evaluations_recentes'] = Evaluation.objects.select_related(
        'employe', 'evaluateur'
    ).order_by('-date_evaluation')[:20]

    # Évaluations planifiées
    today = timezone.now().date()
    context['evaluations_planifiees'] = Evaluation.objects.filter(
        statut='planifiee',
        date_evaluation__gte=today
    ).select_related('employe', 'evaluateur').order_by('date_evaluation')

    # Critères d'évaluation
    context['criteres'] = CritereEvaluation.objects.filter(actif=True)

    return render(request, 'rh/evaluations.html', context)


@login_required
@require_POST
def creer_evaluation(request):
    """Création d'une évaluation"""
    try:
        data = json.loads(request.body)

        employe = get_object_or_404(Employe, pk=data.get('employe_id'))
        evaluateur = None
        if data.get('evaluateur_id'):
            evaluateur = get_object_or_404(Employe, pk=data.get('evaluateur_id'))

        evaluation = Evaluation.objects.create(
            employe=employe,
            evaluateur=evaluateur,
            date_evaluation=data.get('date_evaluation'),
            periode_debut=data.get('periode_debut'),
            periode_fin=data.get('periode_fin'),
        )

        return JsonResponse({
            'success': True,
            'evaluation_id': evaluation.id,
            'message': 'Évaluation créée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# FORMATIONS
# =============================================================================

@login_required
def formations_dashboard(request):
    """Dashboard des formations"""
    context = get_default_context(request)
    context['page_title'] = 'Formations'
    context['active_submenu'] = 'formations'

    # Formations à venir
    today = timezone.now().date()
    context['formations_a_venir'] = Formation.objects.filter(
        date_debut__gte=today,
        statut='planifiee'
    ).order_by('date_debut')

    # Formations en cours
    context['formations_en_cours'] = Formation.objects.filter(
        statut='en_cours'
    ).order_by('date_debut')

    # Formations passées
    context['formations_passees'] = Formation.objects.filter(
        statut='terminee'
    ).order_by('-date_fin')[:10]

    # Budget formation
    annee = timezone.now().year
    context['budget'] = {
        'total_depense': Formation.objects.filter(
            date_debut__year=annee,
            statut='terminee'
        ).aggregate(total=Sum('cout'))['total'] or 0,
        'nb_formations': Formation.objects.filter(
            date_debut__year=annee
        ).count(),
        'nb_participants': ParticipationFormation.objects.filter(
            formation__date_debut__year=annee
        ).count(),
    }

    return render(request, 'rh/formations.html', context)


# =============================================================================
# DISCIPLINE
# =============================================================================

@login_required
def discipline_dashboard(request):
    """Dashboard discipline"""
    context = get_default_context(request)
    context['page_title'] = 'Discipline et sanctions'
    context['active_submenu'] = 'discipline'

    # Sanctions récentes
    context['sanctions'] = Sanction.objects.select_related(
        'employe', 'type_sanction'
    ).order_by('-date_faits')[:20]

    # Types de sanctions
    context['types_sanction'] = TypeSanction.objects.all()

    # Statistiques
    annee = timezone.now().year
    context['stats'] = {
        'total_sanctions': Sanction.objects.filter(date_faits__year=annee).count(),
        'avertissements': Sanction.objects.filter(
            date_faits__year=annee,
            type_sanction__niveau=1
        ).count(),
        'mises_a_pied': Sanction.objects.filter(
            date_faits__year=annee,
            type_sanction__niveau=3
        ).count(),
    }

    return render(request, 'rh/discipline.html', context)


# =============================================================================
# FINS DE CONTRAT
# =============================================================================

@login_required
def fins_contrat_dashboard(request):
    """Dashboard fins de contrat"""
    context = get_default_context(request)
    context['page_title'] = 'Fins de contrat'
    context['active_submenu'] = 'fins_contrat'

    # Fins de contrat récentes
    context['fins_contrat'] = FinContrat.objects.select_related(
        'employe', 'contrat'
    ).order_by('-date_fin_effective')[:20]

    # Procédures en cours
    context['procedures_en_cours'] = FinContrat.objects.filter(
        statut__in=['en_cours', 'notifie', 'preavis']
    ).select_related('employe', 'contrat')

    return render(request, 'rh/fins_contrat.html', context)


@login_required
@require_POST
def initier_fin_contrat(request):
    """Initie une procédure de fin de contrat"""
    try:
        data = json.loads(request.body)

        employe = get_object_or_404(Employe, pk=data.get('employe_id'))
        contrat = employe.contrats.filter(statut='actif').first()

        if not contrat:
            return JsonResponse({
                'success': False,
                'error': 'Aucun contrat actif trouvé'
            }, status=400)

        fin_contrat = FinContrat.objects.create(
            employe=employe,
            contrat=contrat,
            type_rupture=data.get('type_rupture'),
            date_notification=data.get('date_notification'),
            date_fin_effective=data.get('date_fin_effective'),
            motif=data.get('motif', ''),
        )

        # Calculer les indemnités
        fin_contrat.calculer_indemnites()

        return JsonResponse({
            'success': True,
            'fin_contrat_id': fin_contrat.id,
            'indemnites': {
                'preavis': float(fin_contrat.indemnite_preavis),
                'licenciement': float(fin_contrat.indemnite_licenciement),
                'conges': float(fin_contrat.indemnite_conges),
                'total': float(fin_contrat.total_solde_compte),
            },
            'message': 'Procédure initiée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# CONFIGURATION
# =============================================================================

@login_required
def configuration(request):
    """Page de configuration RH"""
    context = get_default_context(request)
    context['page_title'] = 'Configuration RH'
    context['active_submenu'] = 'configuration'

    context['config'] = ConfigurationRH.get_instance()
    context['categories'] = CategorieEmploye.objects.all()
    context['postes'] = Poste.objects.all()
    context['sites'] = Site.objects.all()
    context['types_conge'] = TypeConge.objects.all()
    context['types_absence'] = TypeAbsence.objects.all()
    context['elements_paie'] = ElementPaie.objects.all()

    # Constantes légales
    context['constantes'] = {
        'smig': SMIG_BENIN,
        'plafond_cnss': PLAFOND_CNSS,
    }

    return render(request, 'rh/configuration.html', context)


@login_required
@require_POST
def sauvegarder_configuration(request):
    """Sauvegarde la configuration RH"""
    try:
        data = json.loads(request.body)
        config = ConfigurationRH.get_instance()

        config.nom_entreprise = data.get('nom_entreprise', config.nom_entreprise)
        config.adresse_entreprise = data.get('adresse_entreprise', config.adresse_entreprise)
        config.telephone_entreprise = data.get('telephone_entreprise', config.telephone_entreprise)
        config.email_entreprise = data.get('email_entreprise', config.email_entreprise)
        config.numero_cnss_employeur = data.get('numero_cnss_employeur', config.numero_cnss_employeur)
        config.numero_ifu_employeur = data.get('numero_ifu_employeur', config.numero_ifu_employeur)
        config.jour_paiement_salaire = int(data.get('jour_paiement_salaire', config.jour_paiement_salaire))
        config.taux_risques_professionnels = Decimal(str(data.get('taux_risques_professionnels',
                                                                    config.taux_risques_professionnels)))

        config.est_configure = True
        config.date_configuration = timezone.now()
        config.save()

        return JsonResponse({
            'success': True,
            'message': 'Configuration sauvegardée'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# =============================================================================
# RAPPORTS
# =============================================================================

@login_required
def registre_employeur(request):
    """Génère le registre de l'employeur"""
    context = get_default_context(request)
    context['page_title'] = 'Registre de l\'employeur'

    context['employes'] = Employe.objects.select_related(
        'poste', 'categorie', 'site'
    ).order_by('date_embauche')
    context['config'] = ConfigurationRH.get_instance()

    return render(request, 'rh/rapports/registre_employeur.html', context)


@login_required
def livre_paie(request):
    """Génère le livre de paie"""
    context = get_default_context(request)
    context['page_title'] = 'Livre de paie'

    annee = int(request.GET.get('annee', timezone.now().year))
    mois = request.GET.get('mois')

    context['annee'] = annee
    context['mois'] = mois

    bulletins = BulletinPaie.objects.filter(
        periode__annee=annee,
        statut__in=['valide', 'paye']
    ).select_related('employe', 'periode')

    if mois:
        bulletins = bulletins.filter(periode__mois=int(mois))

    context['bulletins'] = bulletins.order_by('periode__mois', 'employe__nom')

    # Totaux
    context['totaux'] = bulletins.aggregate(
        total_brut=Sum('salaire_brut'),
        total_cnss_salariale=Sum('cnss_salariale'),
        total_cnss_patronale=Sum('cnss_patronale'),
        total_ipts=Sum('ipts'),
        total_net=Sum('net_a_payer'),
    )

    context['config'] = ConfigurationRH.get_instance()

    return render(request, 'rh/rapports/livre_paie.html', context)


# =============================================================================
# API - Endpoints JSON
# =============================================================================

@login_required
@require_GET
def api_employes(request):
    """API - Liste des employés"""
    employes = Employe.objects.filter(statut='actif').values(
        'id', 'matricule', 'nom', 'prenoms', 'salaire_base'
    )
    return JsonResponse({'employes': list(employes)})


@login_required
@require_GET
def api_solde_conges(request, employe_id):
    """API - Solde de congés d'un employé"""
    try:
        solde = SoldeConge.objects.get(
            employe_id=employe_id,
            annee=timezone.now().year
        )
        return JsonResponse({
            'success': True,
            'solde': {
                'jours_acquis': float(solde.jours_acquis),
                'jours_pris': float(solde.jours_pris),
                'jours_reportes': float(solde.jours_reportes),
                'solde_disponible': float(solde.solde_disponible),
            }
        })
    except SoldeConge.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Solde non trouvé'
        }, status=404)


@login_required
@require_GET
def api_statistiques_rh(request):
    """API - Statistiques RH globales"""
    employes = Employe.objects.filter(statut='actif')

    stats = {
        'effectif_total': employes.count(),
        'par_type_contrat': {
            'cdi': employes.filter(type_contrat='cdi').count(),
            'cdd': employes.filter(type_contrat='cdd').count(),
            'stage': employes.filter(type_contrat='stage').count(),
            'apprentissage': employes.filter(type_contrat='apprentissage').count(),
        },
        'par_sexe': {
            'masculin': employes.filter(sexe='M').count(),
            'feminin': employes.filter(sexe='F').count(),
        },
        'anciennete_moyenne': employes.aggregate(
            avg=Avg('date_embauche')
        ),
        'age_moyen': None,  # À calculer
    }

    # Masse salariale
    periode = PeriodePaie.get_periode_courante()
    bulletins = BulletinPaie.objects.filter(periode=periode)
    stats['masse_salariale_mensuelle'] = float(
        bulletins.aggregate(total=Sum('salaire_brut'))['total'] or 0
    )

    return JsonResponse({'success': True, 'stats': stats})

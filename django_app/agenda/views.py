"""
Vues et API pour le module Agenda
Gestion des rendez-vous, tâches et délégations pour une étude d'huissier

Auteur: Maître Martial Arnaud BIAOU
"""

import json
from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType

from .models import (
    RendezVous, Tache, Etiquette, ParticipantExterne,
    DocumentRdv, DocumentTache, RappelRdv, RappelTache,
    CommentaireTache, SousTacheChecklist, Notification,
    JourneeAgenda, ReportTache, ConfigurationAgenda,
    StatistiquesAgenda, HistoriqueAgenda,
    TypeRendezVous, TypeTache, StatutRendezVous, StatutTache,
    StatutDelegation, Priorite, TypeRecurrence,
    VueSauvegardee, ParticipationRdv
)


# =============================================================================
# CONTEXTE PAR DÉFAUT
# =============================================================================

def get_default_context(request):
    """Retourne le contexte par défaut pour tous les templates Agenda"""
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
        {'id': 'import_donnees', 'label': 'Import données', 'icon': 'database', 'category': 'admin', 'url': 'gestion:import_accueil'},
        {'id': 'harmonisation', 'label': 'Harmonisation parties', 'icon': 'sparkles', 'category': 'admin', 'url': 'gestion:admin_suggestions_parties'},
    ]

    return {
        'current_user': {
            'id': user.id if user.is_authenticated else None,
            'nom': user.get_full_name() if user.is_authenticated else 'Invité',
            'role': user.role if user.is_authenticated and hasattr(user, 'role') else '',
            'initials': user.get_initials() if user.is_authenticated and hasattr(user, 'get_initials') else 'XX',
        },
        'modules': modules,
        'active_module': 'agenda',
    }


# =============================================================================
# HELPERS
# =============================================================================

def get_user_from_request(request):
    """Récupère l'utilisateur depuis la requête"""
    if request.user.is_authenticated:
        return request.user
    return None


def user_is_admin(user):
    """Vérifie si l'utilisateur est admin ou huissier"""
    if not user:
        return False
    return user.role in ['admin', 'huissier']


def filter_by_user_permissions(queryset, user, model_type='rdv'):
    """
    Filtre les résultats selon les permissions de l'utilisateur
    Admin/Huissier: voit tout
    Collaborateurs: voit seulement leurs éléments
    """
    if user_is_admin(user):
        return queryset

    if model_type == 'rdv':
        return queryset.filter(
            Q(createur=user) |
            Q(collaborateurs_assignes__utilisateur=user)
        ).distinct()
    elif model_type == 'tache':
        return queryset.filter(
            Q(createur=user) |
            Q(responsable=user) |
            Q(co_responsables=user)
        ).distinct()

    return queryset


def log_action(request, objet, action, details=None, anciennes_valeurs=None, nouvelles_valeurs=None):
    """Enregistre une action dans l'historique"""
    user = get_user_from_request(request)

    type_objet_map = {
        'RendezVous': 'rendez_vous',
        'Tache': 'tache',
        'CommentaireTache': 'commentaire',
    }

    HistoriqueAgenda.objects.create(
        type_objet=type_objet_map.get(objet.__class__.__name__, 'tache'),
        content_type=ContentType.objects.get_for_model(objet),
        object_id=str(objet.id),
        action=action,
        utilisateur=user,
        details=details,
        anciennes_valeurs=anciennes_valeurs,
        nouvelles_valeurs=nouvelles_valeurs,
        adresse_ip=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def creer_notification(destinataire, titre, message, type_notification, objet=None):
    """Crée une notification pour un utilisateur"""
    notif = Notification.objects.create(
        destinataire=destinataire,
        titre=titre,
        message=message,
        type_notification=type_notification,
    )

    if objet:
        notif.content_type = ContentType.objects.get_for_model(objet)
        notif.object_id = str(objet.id)
        notif.save()

    return notif


# =============================================================================
# VUES PRINCIPALES - PAGE AGENDA
# =============================================================================

@login_required
def agenda_home(request):
    """Page principale de l'agenda"""
    user = request.user
    context = get_default_context(request)
    context['page_title'] = 'Agenda'
    context['is_admin'] = user_is_admin(user)
    context['types_rdv'] = TypeRendezVous.choices
    context['types_tache'] = TypeTache.choices
    context['priorites'] = Priorite.choices
    context['statuts_rdv'] = StatutRendezVous.choices
    context['statuts_tache'] = StatutTache.choices
    return render(request, 'agenda/home.html', context)


# =============================================================================
# API RENDEZ-VOUS
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_liste_rdv(request):
    """
    Liste des rendez-vous avec filtres
    GET params: date_debut, date_fin, type_rdv, statut, collaborateur, dossier
    """
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        # Paramètres de filtre
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        type_rdv = request.GET.get('type_rdv')
        statut = request.GET.get('statut')
        collaborateur_id = request.GET.get('collaborateur')
        dossier_id = request.GET.get('dossier')
        vue = request.GET.get('vue', 'mois')  # jour, semaine, mois

        # Base queryset
        queryset = RendezVous.objects.filter(est_actif=True)

        # Appliquer les permissions
        queryset = filter_by_user_permissions(queryset, user, 'rdv')

        # Filtres de date
        if date_debut:
            queryset = queryset.filter(date_debut__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_fin__lte=date_fin)

        # Autres filtres
        if type_rdv:
            queryset = queryset.filter(type_rdv=type_rdv)
        if statut:
            queryset = queryset.filter(statut=statut)
        if collaborateur_id:
            queryset = queryset.filter(collaborateurs_assignes__id=collaborateur_id)
        if dossier_id:
            queryset = queryset.filter(dossiers__id=dossier_id)

        # Sérialisation
        rdv_list = []
        for rdv in queryset.select_related('createur').prefetch_related(
            'collaborateurs_assignes', 'dossiers', 'participants_externes'
        ):
            rdv_list.append({
                'id': str(rdv.id),
                'titre': rdv.titre,
                'type_rdv': rdv.type_rdv,
                'type_rdv_display': rdv.get_type_rdv_display(),
                'description': rdv.description,
                'date_debut': rdv.date_debut.isoformat(),
                'date_fin': rdv.date_fin.isoformat(),
                'journee_entiere': rdv.journee_entiere,
                'lieu': rdv.lieu,
                'adresse': rdv.adresse,
                'latitude': float(rdv.latitude) if rdv.latitude else None,
                'longitude': float(rdv.longitude) if rdv.longitude else None,
                'statut': rdv.statut,
                'statut_display': rdv.get_statut_display(),
                'priorite': rdv.priorite,
                'priorite_display': rdv.get_priorite_display(),
                'couleur': rdv.couleur,
                'createur': {
                    'id': rdv.createur.id,
                    'nom': rdv.createur.get_full_name(),
                } if rdv.createur else None,
                'collaborateurs': [
                    {'id': c.id, 'nom': str(c)}
                    for c in rdv.collaborateurs_assignes.all()
                ],
                'dossiers': [
                    {'id': str(d.id), 'reference': d.reference, 'objet': d.objet}
                    for d in rdv.dossiers.all()
                ],
                'participants_externes': [
                    {'id': str(p.id), 'nom': p.nom, 'type': p.type_participant}
                    for p in rdv.participants_externes.all()
                ],
                'duree': rdv.duree,
                'est_passe': rdv.est_passe,
                'est_aujourdhui': rdv.est_aujourdhui,
            })

        return JsonResponse({
            'success': True,
            'data': rdv_list,
            'count': len(rdv_list)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detail_rdv(request, rdv_id):
    """Détail d'un rendez-vous"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)

        # Vérifier les permissions
        if not user_is_admin(user):
            if rdv.createur != user and not rdv.collaborateurs_assignes.filter(utilisateur=user).exists():
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Documents
        documents = [
            {
                'id': str(d.id),
                'nom': d.nom,
                'description': d.description,
                'date_ajout': d.date_ajout.isoformat(),
            }
            for d in rdv.documents.all()
        ]

        # Rappels
        rappels = [
            {
                'id': str(r.id),
                'type': r.type_rappel,
                'type_display': r.get_type_rappel_display(),
                'type_notification': r.type_notification,
                'est_envoye': r.est_envoye,
            }
            for r in rdv.rappels.all()
        ]

        # Parties concernées (via dossiers)
        parties = []
        for dossier in rdv.dossiers.all():
            for partie in dossier.demandeurs.all():
                parties.append({
                    'id': str(partie.id),
                    'nom': str(partie),
                    'type': 'demandeur',
                    'dossier': dossier.reference
                })
            for partie in dossier.defendeurs.all():
                parties.append({
                    'id': str(partie.id),
                    'nom': str(partie),
                    'type': 'defendeur',
                    'dossier': dossier.reference
                })

        data = {
            'id': str(rdv.id),
            'titre': rdv.titre,
            'type_rdv': rdv.type_rdv,
            'type_rdv_display': rdv.get_type_rdv_display(),
            'description': rdv.description,
            'date_debut': rdv.date_debut.isoformat(),
            'date_fin': rdv.date_fin.isoformat(),
            'journee_entiere': rdv.journee_entiere,
            'lieu': rdv.lieu,
            'adresse': rdv.adresse,
            'latitude': float(rdv.latitude) if rdv.latitude else None,
            'longitude': float(rdv.longitude) if rdv.longitude else None,
            'statut': rdv.statut,
            'statut_display': rdv.get_statut_display(),
            'priorite': rdv.priorite,
            'priorite_display': rdv.get_priorite_display(),
            'couleur': rdv.couleur,
            'type_recurrence': rdv.type_recurrence,
            'type_recurrence_display': rdv.get_type_recurrence_display(),
            'jours_semaine': rdv.jours_semaine,
            'jour_mois': rdv.jour_mois,
            'date_fin_recurrence': rdv.date_fin_recurrence.isoformat() if rdv.date_fin_recurrence else None,
            'createur': {
                'id': rdv.createur.id,
                'nom': rdv.createur.get_full_name(),
            } if rdv.createur else None,
            'collaborateurs': [
                {'id': c.id, 'nom': str(c)}
                for c in rdv.collaborateurs_assignes.all()
            ],
            'dossiers': [
                {'id': str(d.id), 'reference': d.reference, 'objet': d.objet}
                for d in rdv.dossiers.all()
            ],
            'participants_externes': [
                {
                    'id': str(p.id),
                    'nom': p.nom,
                    'email': p.email,
                    'telephone': p.telephone,
                    'type': p.type_participant,
                    'type_display': p.get_type_participant_display()
                }
                for p in rdv.participants_externes.all()
            ],
            'documents': documents,
            'rappels': rappels,
            'parties_concernees': parties,
            'duree': rdv.duree,
            'est_passe': rdv.est_passe,
            'est_aujourdhui': rdv.est_aujourdhui,
            'date_creation': rdv.date_creation.isoformat(),
            'date_modification': rdv.date_modification.isoformat(),
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_rdv(request):
    """Créer un nouveau rendez-vous"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        data = json.loads(request.body)

        # Validation des champs obligatoires
        if not data.get('titre'):
            return JsonResponse({'success': False, 'error': 'Le titre est obligatoire'}, status=400)
        if not data.get('date_debut'):
            return JsonResponse({'success': False, 'error': 'La date de début est obligatoire'}, status=400)

        # Créer le RDV
        rdv = RendezVous.objects.create(
            titre=data['titre'],
            type_rdv=data.get('type_rdv', TypeRendezVous.AUTRE),
            description=data.get('description', ''),
            date_debut=datetime.fromisoformat(data['date_debut'].replace('Z', '+00:00')),
            date_fin=datetime.fromisoformat(data['date_fin'].replace('Z', '+00:00')) if data.get('date_fin') else None,
            journee_entiere=data.get('journee_entiere', False),
            lieu=data.get('lieu', ''),
            adresse=data.get('adresse', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            statut=data.get('statut', StatutRendezVous.PLANIFIE),
            priorite=data.get('priorite', Priorite.NORMALE),
            couleur=data.get('couleur', '#3498db'),
            type_recurrence=data.get('type_recurrence', TypeRecurrence.UNIQUE),
            jours_semaine=data.get('jours_semaine'),
            jour_mois=data.get('jour_mois'),
            date_fin_recurrence=datetime.fromisoformat(data['date_fin_recurrence']).date() if data.get('date_fin_recurrence') else None,
            createur=user,
        )

        # Calculer date_fin si non fournie
        if not rdv.date_fin:
            config = ConfigurationAgenda.get_instance() if ConfigurationAgenda.objects.exists() else None
            duree = config.duree_rdv_defaut if config else 60
            rdv.date_fin = rdv.date_debut + timedelta(minutes=duree)
            rdv.save()

        # Ajouter les collaborateurs
        if data.get('collaborateurs'):
            from gestion.models import Collaborateur
            for collab_id in data['collaborateurs']:
                try:
                    collab = Collaborateur.objects.get(id=collab_id)
                    rdv.collaborateurs_assignes.add(collab)
                except Collaborateur.DoesNotExist:
                    pass

        # Ajouter les dossiers liés
        if data.get('dossiers'):
            from gestion.models import Dossier
            for dossier_id in data['dossiers']:
                try:
                    dossier = Dossier.objects.get(id=dossier_id)
                    rdv.dossiers.add(dossier)
                except Dossier.DoesNotExist:
                    pass

        # Ajouter les participants externes
        if data.get('participants_externes'):
            for participant_data in data['participants_externes']:
                if participant_data.get('id'):
                    try:
                        participant = ParticipantExterne.objects.get(id=participant_data['id'])
                        rdv.participants_externes.add(participant)
                    except ParticipantExterne.DoesNotExist:
                        pass
                else:
                    # Créer un nouveau participant
                    participant = ParticipantExterne.objects.create(
                        nom=participant_data.get('nom', 'Inconnu'),
                        email=participant_data.get('email'),
                        telephone=participant_data.get('telephone'),
                        type_participant=participant_data.get('type', 'autre'),
                    )
                    rdv.participants_externes.add(participant)

        # Ajouter les rappels
        if data.get('rappels'):
            for rappel_data in data['rappels']:
                RappelRdv.objects.create(
                    rendez_vous=rdv,
                    type_rappel=rappel_data.get('type', 'heure_1'),
                    delai_personnalise=rappel_data.get('delai_personnalise'),
                    type_notification=rappel_data.get('type_notification', 'application'),
                )

        # Créer les notifications pour les collaborateurs
        for collab in rdv.collaborateurs_assignes.all():
            if collab.utilisateur and collab.utilisateur != user:
                creer_notification(
                    collab.utilisateur,
                    "Nouveau rendez-vous assigné",
                    f"Vous avez été assigné au RDV: {rdv.titre} le {rdv.date_debut.strftime('%d/%m/%Y à %H:%M')}",
                    'nouveau_rdv',
                    rdv
                )

        # Log
        log_action(request, rdv, 'creation', {'titre': rdv.titre})

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous créé avec succès',
            'data': {'id': str(rdv.id)}
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def api_modifier_rdv(request, rdv_id):
    """Modifier un rendez-vous existant"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)

        # Vérifier les permissions
        if not user_is_admin(user) and rdv.createur != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        data = json.loads(request.body)
        anciennes_valeurs = {
            'titre': rdv.titre,
            'statut': rdv.statut,
            'date_debut': rdv.date_debut.isoformat(),
        }

        # Mise à jour des champs
        if 'titre' in data:
            rdv.titre = data['titre']
        if 'type_rdv' in data:
            rdv.type_rdv = data['type_rdv']
        if 'description' in data:
            rdv.description = data['description']
        if 'date_debut' in data:
            rdv.date_debut = datetime.fromisoformat(data['date_debut'].replace('Z', '+00:00'))
        if 'date_fin' in data:
            rdv.date_fin = datetime.fromisoformat(data['date_fin'].replace('Z', '+00:00'))
        if 'journee_entiere' in data:
            rdv.journee_entiere = data['journee_entiere']
        if 'lieu' in data:
            rdv.lieu = data['lieu']
        if 'adresse' in data:
            rdv.adresse = data['adresse']
        if 'latitude' in data:
            rdv.latitude = data['latitude']
        if 'longitude' in data:
            rdv.longitude = data['longitude']
        if 'statut' in data:
            rdv.statut = data['statut']
        if 'priorite' in data:
            rdv.priorite = data['priorite']
        if 'couleur' in data:
            rdv.couleur = data['couleur']
        if 'type_recurrence' in data:
            rdv.type_recurrence = data['type_recurrence']
        if 'jours_semaine' in data:
            rdv.jours_semaine = data['jours_semaine']
        if 'jour_mois' in data:
            rdv.jour_mois = data['jour_mois']
        if 'date_fin_recurrence' in data:
            rdv.date_fin_recurrence = datetime.fromisoformat(data['date_fin_recurrence']).date() if data['date_fin_recurrence'] else None

        rdv.save()

        # Mise à jour des collaborateurs
        if 'collaborateurs' in data:
            from gestion.models import Collaborateur
            rdv.collaborateurs_assignes.clear()
            for collab_id in data['collaborateurs']:
                try:
                    collab = Collaborateur.objects.get(id=collab_id)
                    rdv.collaborateurs_assignes.add(collab)
                except Collaborateur.DoesNotExist:
                    pass

        # Mise à jour des dossiers
        if 'dossiers' in data:
            from gestion.models import Dossier
            rdv.dossiers.clear()
            for dossier_id in data['dossiers']:
                try:
                    dossier = Dossier.objects.get(id=dossier_id)
                    rdv.dossiers.add(dossier)
                except Dossier.DoesNotExist:
                    pass

        nouvelles_valeurs = {
            'titre': rdv.titre,
            'statut': rdv.statut,
            'date_debut': rdv.date_debut.isoformat(),
        }

        log_action(request, rdv, 'modification', None, anciennes_valeurs, nouvelles_valeurs)

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous modifié avec succès',
            'data': {'id': str(rdv.id)}
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_supprimer_rdv(request, rdv_id):
    """Supprimer un rendez-vous (soft delete)"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id)

        # Vérifier les permissions
        if not user_is_admin(user) and rdv.createur != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        # Soft delete
        rdv.est_actif = False
        rdv.save()

        log_action(request, rdv, 'suppression')

        return JsonResponse({
            'success': True,
            'message': 'Rendez-vous supprimé avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API TÂCHES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_liste_taches(request):
    """
    Liste des tâches avec filtres
    GET params: date_debut, date_fin, type_tache, statut, priorite, responsable, dossier, en_retard
    """
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        # Paramètres
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        type_tache = request.GET.get('type_tache')
        statut = request.GET.get('statut')
        priorite = request.GET.get('priorite')
        responsable_id = request.GET.get('responsable')
        dossier_id = request.GET.get('dossier')
        en_retard = request.GET.get('en_retard')
        delegue = request.GET.get('delegue')
        createur_id = request.GET.get('createur')

        # Base queryset
        queryset = Tache.objects.filter(est_active=True, tache_parente__isnull=True)

        # Appliquer les permissions
        queryset = filter_by_user_permissions(queryset, user, 'tache')

        # Filtres de date
        if date_debut:
            queryset = queryset.filter(date_echeance__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_echeance__lte=date_fin)

        # Autres filtres
        if type_tache:
            queryset = queryset.filter(type_tache=type_tache)
        if statut:
            queryset = queryset.filter(statut=statut)
        if priorite:
            queryset = queryset.filter(priorite=priorite)
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
        if dossier_id:
            queryset = queryset.filter(dossier_id=dossier_id)
        if createur_id:
            queryset = queryset.filter(createur_id=createur_id)

        # Filtre tâches en retard
        if en_retard == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                date_echeance__lt=today
            ).exclude(
                statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
            )

        # Filtre tâches déléguées
        if delegue == 'true':
            queryset = queryset.exclude(responsable=F('createur')).filter(responsable__isnull=False)

        # Tri
        ordre = request.GET.get('ordre', 'date_echeance')
        if ordre.startswith('-'):
            queryset = queryset.order_by(ordre)
        else:
            queryset = queryset.order_by(ordre, '-priorite')

        # Sérialisation
        taches_list = []
        for tache in queryset.select_related('createur', 'responsable', 'dossier').prefetch_related(
            'etiquettes', 'co_responsables', 'sous_taches', 'checklist_items'
        ):
            # Calculer sous-tâches
            sous_taches_count = tache.sous_taches.count()
            sous_taches_terminees = tache.sous_taches.filter(statut=StatutTache.TERMINEE).count()
            checklist_count = tache.checklist_items.count()
            checklist_terminees = tache.checklist_items.filter(est_complete=True).count()

            taches_list.append({
                'id': str(tache.id),
                'titre': tache.titre,
                'type_tache': tache.type_tache,
                'type_tache_display': tache.get_type_tache_display(),
                'description': tache.description,
                'date_echeance': tache.date_echeance.isoformat(),
                'heure_echeance': tache.heure_echeance.isoformat() if tache.heure_echeance else None,
                'statut': tache.statut,
                'statut_display': tache.get_statut_display(),
                'priorite': tache.priorite,
                'priorite_display': tache.get_priorite_display(),
                'couleur': tache.couleur,
                'progression': tache.progression_calculee,
                'temps_estime': tache.temps_estime,
                'temps_passe': tache.temps_passe,
                'createur': {
                    'id': tache.createur.id,
                    'nom': tache.createur.get_full_name(),
                } if tache.createur else None,
                'responsable': {
                    'id': tache.responsable.id,
                    'nom': tache.responsable.get_full_name(),
                } if tache.responsable else None,
                'dossier': {
                    'id': str(tache.dossier.id),
                    'reference': tache.dossier.reference,
                } if tache.dossier else None,
                'etiquettes': [
                    {'id': str(e.id), 'nom': e.nom, 'couleur': e.couleur}
                    for e in tache.etiquettes.all()
                ],
                'est_en_retard': tache.est_en_retard,
                'est_aujourdhui': tache.est_aujourdhui,
                'est_delegue': tache.est_delegue,
                'statut_delegation': tache.statut_delegation,
                'sous_taches': {
                    'total': sous_taches_count,
                    'terminees': sous_taches_terminees,
                },
                'checklist': {
                    'total': checklist_count,
                    'terminees': checklist_terminees,
                },
            })

        return JsonResponse({
            'success': True,
            'data': taches_list,
            'count': len(taches_list)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_detail_tache(request, tache_id):
    """Détail d'une tâche"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)

        # Vérifier les permissions
        if not user_is_admin(user):
            if tache.createur != user and tache.responsable != user and not tache.co_responsables.filter(id=user.id).exists():
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Sous-tâches
        sous_taches = [
            {
                'id': str(st.id),
                'titre': st.titre,
                'statut': st.statut,
                'statut_display': st.get_statut_display(),
                'date_echeance': st.date_echeance.isoformat(),
                'progression': st.progression,
            }
            for st in tache.sous_taches.all()
        ]

        # Checklist
        checklist = [
            {
                'id': str(item.id),
                'libelle': item.libelle,
                'est_complete': item.est_complete,
                'ordre': item.ordre,
            }
            for item in tache.checklist_items.all()
        ]

        # Commentaires
        commentaires = [
            {
                'id': str(c.id),
                'auteur': c.auteur.get_full_name(),
                'contenu': c.contenu,
                'type': c.type_commentaire,
                'date': c.date_creation.isoformat(),
            }
            for c in tache.commentaires.all()
            if not c.est_prive or c.auteur == user or user_is_admin(user)
        ]

        # Documents
        documents = [
            {
                'id': str(d.id),
                'nom': d.nom,
                'description': d.description,
                'date_ajout': d.date_ajout.isoformat(),
            }
            for d in tache.documents.all()
        ]

        # Historique des reports
        reports = [
            {
                'date_origine': r.date_origine.isoformat(),
                'nouvelle_date': r.nouvelle_date.isoformat(),
                'raison': r.raison,
                'type': r.type_report,
                'date': r.date_creation.isoformat(),
            }
            for r in tache.historique_reports.all()[:5]
        ]

        data = {
            'id': str(tache.id),
            'titre': tache.titre,
            'type_tache': tache.type_tache,
            'type_tache_display': tache.get_type_tache_display(),
            'description': tache.description,
            'date_echeance': tache.date_echeance.isoformat(),
            'heure_echeance': tache.heure_echeance.isoformat() if tache.heure_echeance else None,
            'date_debut': tache.date_debut.isoformat() if tache.date_debut else None,
            'statut': tache.statut,
            'statut_display': tache.get_statut_display(),
            'priorite': tache.priorite,
            'priorite_display': tache.get_priorite_display(),
            'couleur': tache.couleur,
            'progression': tache.progression,
            'progression_calculee': tache.progression_calculee,
            'temps_estime': tache.temps_estime,
            'temps_passe': tache.temps_passe,
            'type_recurrence': tache.type_recurrence,
            'createur': {
                'id': tache.createur.id,
                'nom': tache.createur.get_full_name(),
            } if tache.createur else None,
            'responsable': {
                'id': tache.responsable.id,
                'nom': tache.responsable.get_full_name(),
            } if tache.responsable else None,
            'co_responsables': [
                {'id': u.id, 'nom': u.get_full_name()}
                for u in tache.co_responsables.all()
            ],
            'date_delegation': tache.date_delegation.isoformat() if tache.date_delegation else None,
            'instructions_delegation': tache.instructions_delegation,
            'demande_compte_rendu': tache.demande_compte_rendu,
            'statut_delegation': tache.statut_delegation,
            'dossier': {
                'id': str(tache.dossier.id),
                'reference': tache.dossier.reference,
                'objet': tache.dossier.objet,
            } if tache.dossier else None,
            'partie_concernee': {
                'id': str(tache.partie_concernee.id),
                'nom': str(tache.partie_concernee),
            } if tache.partie_concernee else None,
            'etiquettes': [
                {'id': str(e.id), 'nom': e.nom, 'couleur': e.couleur}
                for e in tache.etiquettes.all()
            ],
            'sous_taches': sous_taches,
            'checklist': checklist,
            'commentaires': commentaires,
            'documents': documents,
            'historique_reports': reports,
            'est_en_retard': tache.est_en_retard,
            'est_aujourdhui': tache.est_aujourdhui,
            'est_delegue': tache.est_delegue,
            'date_creation': tache.date_creation.isoformat(),
            'date_modification': tache.date_modification.isoformat(),
            'date_terminaison': tache.date_terminaison.isoformat() if tache.date_terminaison else None,
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_tache(request):
    """Créer une nouvelle tâche"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        data = json.loads(request.body)

        # Validation
        if not data.get('titre'):
            return JsonResponse({'success': False, 'error': 'Le titre est obligatoire'}, status=400)
        if not data.get('date_echeance'):
            return JsonResponse({'success': False, 'error': "La date d'échéance est obligatoire"}, status=400)

        # Créer la tâche
        tache = Tache.objects.create(
            titre=data['titre'],
            type_tache=data.get('type_tache', TypeTache.AUTRE),
            description=data.get('description', ''),
            date_echeance=datetime.fromisoformat(data['date_echeance']).date(),
            heure_echeance=datetime.strptime(data['heure_echeance'], '%H:%M').time() if data.get('heure_echeance') else None,
            date_debut=datetime.fromisoformat(data['date_debut']).date() if data.get('date_debut') else None,
            priorite=data.get('priorite', Priorite.NORMALE),
            couleur=data.get('couleur', '#3498db'),
            temps_estime=data.get('temps_estime'),
            type_recurrence=data.get('type_recurrence', TypeRecurrence.UNIQUE),
            jours_semaine=data.get('jours_semaine'),
            jour_mois=data.get('jour_mois'),
            date_fin_recurrence=datetime.fromisoformat(data['date_fin_recurrence']).date() if data.get('date_fin_recurrence') else None,
            createur=user,
            responsable_id=data.get('responsable_id', user.id),
            instructions_delegation=data.get('instructions_delegation'),
            demande_compte_rendu=data.get('demande_compte_rendu', False),
        )

        # Lier au dossier
        if data.get('dossier_id'):
            from gestion.models import Dossier
            try:
                tache.dossier = Dossier.objects.get(id=data['dossier_id'])
                tache.save()
            except Dossier.DoesNotExist:
                pass

        # Lier à la partie concernée
        if data.get('partie_id'):
            from gestion.models import Partie
            try:
                tache.partie_concernee = Partie.objects.get(id=data['partie_id'])
                tache.save()
            except Partie.DoesNotExist:
                pass

        # Ajouter les co-responsables
        if data.get('co_responsables'):
            from gestion.models import Utilisateur
            for user_id in data['co_responsables']:
                try:
                    u = Utilisateur.objects.get(id=user_id)
                    tache.co_responsables.add(u)
                except Utilisateur.DoesNotExist:
                    pass

        # Ajouter les étiquettes
        if data.get('etiquettes'):
            for etiquette_id in data['etiquettes']:
                try:
                    etiquette = Etiquette.objects.get(id=etiquette_id)
                    tache.etiquettes.add(etiquette)
                except Etiquette.DoesNotExist:
                    pass

        # Créer les éléments de checklist
        if data.get('checklist'):
            for i, item in enumerate(data['checklist']):
                SousTacheChecklist.objects.create(
                    tache=tache,
                    libelle=item.get('libelle', item) if isinstance(item, dict) else item,
                    ordre=i,
                )

        # Gérer la délégation
        if tache.responsable and tache.responsable != user:
            tache.date_delegation = timezone.now()
            tache.statut_delegation = StatutDelegation.ASSIGNEE
            tache.save()

            # Notification au responsable
            creer_notification(
                tache.responsable,
                "Nouvelle tâche déléguée",
                f"{user.get_full_name()} vous a assigné la tâche: {tache.titre}",
                'nouvelle_tache',
                tache
            )

        # Ajouter les rappels
        if data.get('rappels'):
            for rappel_data in data['rappels']:
                RappelTache.objects.create(
                    tache=tache,
                    type_rappel=rappel_data.get('type', 'jour_echeance'),
                    delai_personnalise=rappel_data.get('delai_personnalise'),
                    type_notification=rappel_data.get('type_notification', 'application'),
                )

        # Log
        log_action(request, tache, 'creation', {'titre': tache.titre})

        return JsonResponse({
            'success': True,
            'message': 'Tâche créée avec succès',
            'data': {'id': str(tache.id)}
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def api_modifier_tache(request, tache_id):
    """Modifier une tâche existante"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)

        # Vérifier les permissions
        if not user_is_admin(user) and tache.createur != user and tache.responsable != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        data = json.loads(request.body)
        anciennes_valeurs = {
            'titre': tache.titre,
            'statut': tache.statut,
            'date_echeance': tache.date_echeance.isoformat(),
            'responsable_id': tache.responsable_id,
        }

        # Mise à jour des champs
        if 'titre' in data:
            tache.titre = data['titre']
        if 'type_tache' in data:
            tache.type_tache = data['type_tache']
        if 'description' in data:
            tache.description = data['description']
        if 'date_echeance' in data:
            nouvelle_date = datetime.fromisoformat(data['date_echeance']).date()
            if nouvelle_date != tache.date_echeance:
                # Enregistrer le report
                ReportTache.objects.create(
                    tache=tache,
                    date_origine=tache.date_echeance,
                    nouvelle_date=nouvelle_date,
                    raison=data.get('raison_report'),
                    reporte_par=user,
                    type_report='manuel',
                )
            tache.date_echeance = nouvelle_date
        if 'heure_echeance' in data:
            tache.heure_echeance = datetime.strptime(data['heure_echeance'], '%H:%M').time() if data['heure_echeance'] else None
        if 'statut' in data:
            tache.statut = data['statut']
            if data['statut'] == StatutTache.TERMINEE:
                tache.date_terminaison = timezone.now()
                tache.progression = 100
        if 'priorite' in data:
            tache.priorite = data['priorite']
        if 'couleur' in data:
            tache.couleur = data['couleur']
        if 'progression' in data:
            tache.progression = data['progression']
        if 'temps_passe' in data:
            tache.temps_passe = data['temps_passe']

        # Changement de responsable (réassignation)
        if 'responsable_id' in data and data['responsable_id'] != tache.responsable_id:
            ancien_responsable = tache.responsable
            from gestion.models import Utilisateur
            try:
                nouveau_responsable = Utilisateur.objects.get(id=data['responsable_id'])
                tache.responsable = nouveau_responsable
                tache.date_delegation = timezone.now()
                tache.statut_delegation = StatutDelegation.ASSIGNEE

                # Notification au nouveau responsable
                creer_notification(
                    nouveau_responsable,
                    "Tâche réassignée",
                    f"La tâche '{tache.titre}' vous a été assignée",
                    'nouvelle_tache',
                    tache
                )

                # Notification à l'ancien responsable
                if ancien_responsable and ancien_responsable != user:
                    creer_notification(
                        ancien_responsable,
                        "Tâche réassignée",
                        f"La tâche '{tache.titre}' a été réassignée à {nouveau_responsable.get_full_name()}",
                        'autre',
                        tache
                    )

                log_action(request, tache, 'reassignation', {
                    'ancien': ancien_responsable.get_full_name() if ancien_responsable else None,
                    'nouveau': nouveau_responsable.get_full_name()
                })
            except Utilisateur.DoesNotExist:
                pass

        tache.save()

        # Mise à jour des étiquettes
        if 'etiquettes' in data:
            tache.etiquettes.clear()
            for etiquette_id in data['etiquettes']:
                try:
                    etiquette = Etiquette.objects.get(id=etiquette_id)
                    tache.etiquettes.add(etiquette)
                except Etiquette.DoesNotExist:
                    pass

        nouvelles_valeurs = {
            'titre': tache.titre,
            'statut': tache.statut,
            'date_echeance': tache.date_echeance.isoformat(),
            'responsable_id': tache.responsable_id,
        }

        log_action(request, tache, 'modification', None, anciennes_valeurs, nouvelles_valeurs)

        return JsonResponse({
            'success': True,
            'message': 'Tâche modifiée avec succès',
            'data': {'id': str(tache.id)}
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_terminer_tache(request, tache_id):
    """Marquer une tâche comme terminée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)

        # Vérifier les permissions
        if not user_is_admin(user) and tache.createur != user and tache.responsable != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        tache.marquer_terminee(user)

        # Notification au créateur si c'est une délégation
        if tache.est_delegue and tache.createur != user:
            creer_notification(
                tache.createur,
                "Tâche terminée",
                f"{user.get_full_name()} a terminé la tâche: {tache.titre}",
                'tache_terminee',
                tache
            )

        log_action(request, tache, 'completion')

        return JsonResponse({
            'success': True,
            'message': 'Tâche marquée comme terminée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_supprimer_tache(request, tache_id):
    """Supprimer une tâche (soft delete)"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id)

        # Vérifier les permissions
        if not user_is_admin(user) and tache.createur != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        tache.est_active = False
        tache.save()

        log_action(request, tache, 'suppression')

        return JsonResponse({
            'success': True,
            'message': 'Tâche supprimée avec succès'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API DÉLÉGATION
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_deleguer_tache(request, tache_id):
    """Déléguer une tâche à un collaborateur"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        # Seul l'admin/huissier peut déléguer
        if not user_is_admin(user):
            return JsonResponse({'success': False, 'error': 'Seul l\'huissier peut déléguer des tâches'}, status=403)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)
        data = json.loads(request.body)

        if not data.get('responsable_id'):
            return JsonResponse({'success': False, 'error': 'Le responsable est obligatoire'}, status=400)

        from gestion.models import Utilisateur
        try:
            nouveau_responsable = Utilisateur.objects.get(id=data['responsable_id'])
        except Utilisateur.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Utilisateur non trouvé'}, status=404)

        ancien_responsable = tache.responsable

        tache.responsable = nouveau_responsable
        tache.date_delegation = timezone.now()
        tache.statut_delegation = StatutDelegation.ASSIGNEE
        tache.instructions_delegation = data.get('instructions', '')
        tache.demande_compte_rendu = data.get('demande_compte_rendu', False)

        if data.get('date_echeance'):
            tache.date_echeance = datetime.fromisoformat(data['date_echeance']).date()

        tache.save()

        # Notification
        creer_notification(
            nouveau_responsable,
            "Nouvelle tâche déléguée",
            f"{user.get_full_name()} vous a délégué la tâche: {tache.titre}\n\nInstructions: {tache.instructions_delegation or 'Aucune'}",
            'nouvelle_tache',
            tache
        )

        log_action(request, tache, 'delegation', {
            'responsable': nouveau_responsable.get_full_name(),
            'instructions': tache.instructions_delegation,
        })

        return JsonResponse({
            'success': True,
            'message': f'Tâche déléguée à {nouveau_responsable.get_full_name()}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_accepter_delegation(request, tache_id):
    """Accepter une tâche déléguée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, responsable=user, est_active=True)

        if tache.statut_delegation != StatutDelegation.ASSIGNEE:
            return JsonResponse({'success': False, 'error': 'Cette tâche ne peut pas être acceptée'}, status=400)

        tache.statut_delegation = StatutDelegation.ACCEPTEE
        tache.save()

        # Notification au créateur
        creer_notification(
            tache.createur,
            "Délégation acceptée",
            f"{user.get_full_name()} a accepté la tâche: {tache.titre}",
            'autre',
            tache
        )

        return JsonResponse({
            'success': True,
            'message': 'Délégation acceptée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_demander_aide(request, tache_id):
    """Demander de l'aide ou clarification sur une tâche déléguée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, responsable=user, est_active=True)
        data = json.loads(request.body)

        message = data.get('message', 'Besoin de clarification')

        # Créer un commentaire
        CommentaireTache.objects.create(
            tache=tache,
            auteur=user,
            contenu=message,
            type_commentaire='demande_aide',
        )

        # Notification au créateur
        creer_notification(
            tache.createur,
            "Demande d'aide",
            f"{user.get_full_name()} demande de l'aide pour la tâche: {tache.titre}\n\n{message}",
            'demande_aide',
            tache
        )

        return JsonResponse({
            'success': True,
            'message': "Demande d'aide envoyée"
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_valider_delegation(request, tache_id):
    """Valider une tâche terminée par un collaborateur"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, createur=user, est_active=True)

        if tache.statut_delegation != StatutDelegation.TERMINEE:
            return JsonResponse({'success': False, 'error': 'Cette tâche doit être terminée avant validation'}, status=400)

        tache.statut_delegation = StatutDelegation.VALIDEE
        tache.save()

        # Notification au responsable
        if tache.responsable:
            creer_notification(
                tache.responsable,
                "Tâche validée",
                f"Votre travail sur la tâche '{tache.titre}' a été validé",
                'autre',
                tache
            )

        return JsonResponse({
            'success': True,
            'message': 'Tâche validée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_taches_deleguees(request):
    """Liste des tâches déléguées (pour le tableau de bord)"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if user_is_admin(user):
            # Admin: voit toutes les tâches qu'il a déléguées
            queryset = Tache.objects.filter(
                createur=user,
                est_active=True,
                statut_delegation__isnull=False
            ).exclude(responsable=user)
        else:
            # Collaborateur: voit les tâches qui lui sont déléguées
            queryset = Tache.objects.filter(
                responsable=user,
                est_active=True,
                statut_delegation__isnull=False
            ).exclude(createur=user)

        # Filtres
        statut = request.GET.get('statut_delegation')
        if statut:
            queryset = queryset.filter(statut_delegation=statut)

        en_retard = request.GET.get('en_retard')
        if en_retard == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(date_echeance__lt=today).exclude(
                statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
            )

        taches_list = []
        for tache in queryset.select_related('createur', 'responsable', 'dossier'):
            taches_list.append({
                'id': str(tache.id),
                'titre': tache.titre,
                'type_tache': tache.type_tache,
                'type_tache_display': tache.get_type_tache_display(),
                'date_echeance': tache.date_echeance.isoformat(),
                'statut': tache.statut,
                'statut_display': tache.get_statut_display(),
                'priorite': tache.priorite,
                'priorite_display': tache.get_priorite_display(),
                'progression': tache.progression_calculee,
                'statut_delegation': tache.statut_delegation,
                'statut_delegation_display': tache.get_statut_delegation_display() if tache.statut_delegation else None,
                'date_delegation': tache.date_delegation.isoformat() if tache.date_delegation else None,
                'instructions': tache.instructions_delegation,
                'demande_compte_rendu': tache.demande_compte_rendu,
                'createur': {
                    'id': tache.createur.id,
                    'nom': tache.createur.get_full_name(),
                } if tache.createur else None,
                'responsable': {
                    'id': tache.responsable.id,
                    'nom': tache.responsable.get_full_name(),
                } if tache.responsable else None,
                'dossier': {
                    'id': str(tache.dossier.id),
                    'reference': tache.dossier.reference,
                } if tache.dossier else None,
                'est_en_retard': tache.est_en_retard,
            })

        return JsonResponse({
            'success': True,
            'data': taches_list,
            'count': len(taches_list),
            'is_admin': user_is_admin(user)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API COMMENTAIRES ET CHECKLIST
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_ajouter_commentaire(request, tache_id):
    """Ajouter un commentaire à une tâche"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)
        data = json.loads(request.body)

        if not data.get('contenu'):
            return JsonResponse({'success': False, 'error': 'Le contenu est obligatoire'}, status=400)

        commentaire = CommentaireTache.objects.create(
            tache=tache,
            auteur=user,
            contenu=data['contenu'],
            type_commentaire=data.get('type', 'commentaire'),
            est_prive=data.get('est_prive', False),
        )

        # Notification aux autres participants
        destinataires = set()
        if tache.createur and tache.createur != user:
            destinataires.add(tache.createur)
        if tache.responsable and tache.responsable != user:
            destinataires.add(tache.responsable)

        for dest in destinataires:
            creer_notification(
                dest,
                "Nouveau commentaire",
                f"{user.get_full_name()} a commenté la tâche: {tache.titre}",
                'commentaire',
                tache
            )

        return JsonResponse({
            'success': True,
            'message': 'Commentaire ajouté',
            'data': {
                'id': str(commentaire.id),
                'contenu': commentaire.contenu,
                'auteur': user.get_full_name(),
                'date': commentaire.date_creation.isoformat(),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_toggle_checklist_item(request, item_id):
    """Cocher/décocher un élément de checklist"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        item = get_object_or_404(SousTacheChecklist, id=item_id)

        item.est_complete = not item.est_complete
        if item.est_complete:
            item.date_completion = timezone.now()
            item.complete_par = user
        else:
            item.date_completion = None
            item.complete_par = None
        item.save()

        # Mettre à jour la progression de la tâche
        tache = item.tache
        total = tache.checklist_items.count()
        completes = tache.checklist_items.filter(est_complete=True).count()
        tache.progression = int((completes / total) * 100) if total > 0 else 0
        tache.save()

        return JsonResponse({
            'success': True,
            'data': {
                'est_complete': item.est_complete,
                'progression_tache': tache.progression,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_ajouter_checklist_item(request, tache_id):
    """Ajouter un élément à la checklist d'une tâche"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        tache = get_object_or_404(Tache, id=tache_id, est_active=True)
        data = json.loads(request.body)

        if not data.get('libelle'):
            return JsonResponse({'success': False, 'error': 'Le libellé est obligatoire'}, status=400)

        # Déterminer l'ordre
        dernier_ordre = tache.checklist_items.order_by('-ordre').first()
        ordre = (dernier_ordre.ordre + 1) if dernier_ordre else 0

        item = SousTacheChecklist.objects.create(
            tache=tache,
            libelle=data['libelle'],
            ordre=ordre,
        )

        return JsonResponse({
            'success': True,
            'data': {
                'id': str(item.id),
                'libelle': item.libelle,
                'est_complete': item.est_complete,
                'ordre': item.ordre,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API VUES PRINCIPALES (BOUTONS)
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_actions_du_jour(request):
    """
    BOUTON 4: Actions du jour
    RDV et tâches du jour + tâches en retard
    """
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        today = timezone.now().date()
        date_debut_jour = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        date_fin_jour = timezone.make_aware(datetime.combine(today, datetime.max.time()))

        # RDV du jour
        rdv_queryset = RendezVous.objects.filter(
            est_actif=True,
            date_debut__range=[date_debut_jour, date_fin_jour]
        )
        rdv_queryset = filter_by_user_permissions(rdv_queryset, user, 'rdv')

        rdv_list = [
            {
                'id': str(rdv.id),
                'titre': rdv.titre,
                'type_rdv': rdv.type_rdv,
                'type_rdv_display': rdv.get_type_rdv_display(),
                'date_debut': rdv.date_debut.isoformat(),
                'date_fin': rdv.date_fin.isoformat(),
                'lieu': rdv.lieu,
                'statut': rdv.statut,
                'statut_display': rdv.get_statut_display(),
                'priorite': rdv.priorite,
                'couleur': rdv.couleur,
            }
            for rdv in rdv_queryset.order_by('date_debut')
        ]

        # Tâches du jour
        taches_jour_queryset = Tache.objects.filter(
            est_active=True,
            date_echeance=today
        )
        taches_jour_queryset = filter_by_user_permissions(taches_jour_queryset, user, 'tache')

        # Tâches en retard
        taches_retard_queryset = Tache.objects.filter(
            est_active=True,
            date_echeance__lt=today
        ).exclude(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE])
        taches_retard_queryset = filter_by_user_permissions(taches_retard_queryset, user, 'tache')

        def serialize_tache(t):
            return {
                'id': str(t.id),
                'titre': t.titre,
                'type_tache': t.type_tache,
                'type_tache_display': t.get_type_tache_display(),
                'date_echeance': t.date_echeance.isoformat(),
                'statut': t.statut,
                'statut_display': t.get_statut_display(),
                'priorite': t.priorite,
                'priorite_display': t.get_priorite_display(),
                'progression': t.progression_calculee,
                'couleur': t.couleur,
                'est_en_retard': t.est_en_retard,
                'responsable': t.responsable.get_full_name() if t.responsable else None,
            }

        taches_jour = [serialize_tache(t) for t in taches_jour_queryset.order_by('priorite', 'heure_echeance')]
        taches_retard = [serialize_tache(t) for t in taches_retard_queryset.order_by('date_echeance')]

        # Statistiques
        total_rdv = len(rdv_list)
        rdv_termines = len([r for r in rdv_list if r['statut'] == StatutRendezVous.TERMINE])
        total_taches = len(taches_jour)
        taches_terminees = len([t for t in taches_jour if t['statut'] == StatutTache.TERMINEE])

        return JsonResponse({
            'success': True,
            'data': {
                'date': today.isoformat(),
                'rendez_vous': rdv_list,
                'taches_jour': taches_jour,
                'taches_en_retard': taches_retard,
                'statistiques': {
                    'rdv_total': total_rdv,
                    'rdv_termines': rdv_termines,
                    'taches_total': total_taches,
                    'taches_terminees': taches_terminees,
                    'taches_en_retard': len(taches_retard),
                    'progression': round(((rdv_termines + taches_terminees) / (total_rdv + total_taches) * 100), 1) if (total_rdv + total_taches) > 0 else 100,
                }
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_dossiers_en_attente(request):
    """
    BOUTON 3: Dossiers en attente
    Dossiers liés à des RDV ou tâches non terminées
    """
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        from gestion.models import Dossier

        # Récupérer les dossiers avec des RDV non terminés
        rdv_en_cours = RendezVous.objects.filter(
            est_actif=True
        ).exclude(
            statut__in=[StatutRendezVous.TERMINE, StatutRendezVous.ANNULE]
        )
        if not user_is_admin(user):
            rdv_en_cours = rdv_en_cours.filter(
                Q(createur=user) | Q(collaborateurs_assignes__utilisateur=user)
            )
        dossiers_rdv = set(rdv_en_cours.values_list('dossiers__id', flat=True))

        # Récupérer les dossiers avec des tâches non terminées
        taches_en_cours = Tache.objects.filter(
            est_active=True
        ).exclude(
            statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
        )
        if not user_is_admin(user):
            taches_en_cours = taches_en_cours.filter(
                Q(createur=user) | Q(responsable=user)
            )
        dossiers_taches = set(taches_en_cours.values_list('dossier_id', flat=True))

        # Union des deux ensembles
        dossiers_ids = (dossiers_rdv | dossiers_taches) - {None}

        dossiers_list = []
        for dossier in Dossier.objects.filter(id__in=dossiers_ids).select_related('collaborateur'):
            # RDV associés non terminés
            rdv_dossier = RendezVous.objects.filter(
                dossiers=dossier,
                est_actif=True
            ).exclude(statut__in=[StatutRendezVous.TERMINE, StatutRendezVous.ANNULE])

            # Tâches associées non terminées
            taches_dossier = Tache.objects.filter(
                dossier=dossier,
                est_active=True
            ).exclude(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE])

            # Prochaine action
            prochaine_action = None
            prochain_rdv = rdv_dossier.order_by('date_debut').first()
            prochaine_tache = taches_dossier.order_by('date_echeance').first()

            if prochain_rdv and prochaine_tache:
                if prochain_rdv.date_debut.date() <= prochaine_tache.date_echeance:
                    prochaine_action = {
                        'type': 'rdv',
                        'titre': prochain_rdv.titre,
                        'date': prochain_rdv.date_debut.isoformat(),
                        'responsable': prochain_rdv.createur.get_full_name() if prochain_rdv.createur else None
                    }
                else:
                    prochaine_action = {
                        'type': 'tache',
                        'titre': prochaine_tache.titre,
                        'date': prochaine_tache.date_echeance.isoformat(),
                        'responsable': prochaine_tache.responsable.get_full_name() if prochaine_tache.responsable else None
                    }
            elif prochain_rdv:
                prochaine_action = {
                    'type': 'rdv',
                    'titre': prochain_rdv.titre,
                    'date': prochain_rdv.date_debut.isoformat(),
                    'responsable': prochain_rdv.createur.get_full_name() if prochain_rdv.createur else None
                }
            elif prochaine_tache:
                prochaine_action = {
                    'type': 'tache',
                    'titre': prochaine_tache.titre,
                    'date': prochaine_tache.date_echeance.isoformat(),
                    'responsable': prochaine_tache.responsable.get_full_name() if prochaine_tache.responsable else None
                }

            dossiers_list.append({
                'id': str(dossier.id),
                'reference': dossier.reference,
                'objet': dossier.objet,
                'statut': dossier.statut,
                'nb_rdv_en_cours': rdv_dossier.count(),
                'nb_taches_en_cours': taches_dossier.count(),
                'prochaine_action': prochaine_action,
                'collaborateur': str(dossier.collaborateur) if dossier.collaborateur else None,
            })

        # Trier par urgence (prochaine échéance)
        dossiers_list.sort(key=lambda x: x['prochaine_action']['date'] if x['prochaine_action'] else '9999-12-31')

        return JsonResponse({
            'success': True,
            'data': dossiers_list,
            'count': len(dossiers_list)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_vue_ensemble(request):
    """
    BOUTON 5: Vue d'ensemble / Résumé
    Tableau de bord récapitulatif
    """
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        today = timezone.now().date()
        debut_semaine = today - timedelta(days=today.weekday())
        fin_semaine = debut_semaine + timedelta(days=6)
        debut_mois = today.replace(day=1)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        is_admin = user_is_admin(user)

        def get_stats(date_debut, date_fin, filter_user=True):
            # Base querysets
            rdv_filter = Q(est_actif=True, date_debut__date__gte=date_debut, date_debut__date__lte=date_fin)
            tache_filter = Q(est_active=True, date_echeance__gte=date_debut, date_echeance__lte=date_fin)

            if filter_user and not is_admin:
                rdv_filter &= Q(createur=user) | Q(collaborateurs_assignes__utilisateur=user)
                tache_filter &= Q(createur=user) | Q(responsable=user)

            rdv = RendezVous.objects.filter(rdv_filter).distinct()
            taches = Tache.objects.filter(tache_filter).distinct()

            return {
                'nb_rdv': rdv.count(),
                'rdv_termines': rdv.filter(statut=StatutRendezVous.TERMINE).count(),
                'nb_taches': taches.count(),
                'taches_terminees': taches.filter(statut=StatutTache.TERMINEE).count(),
                'taches_en_retard': taches.filter(date_echeance__lt=today).exclude(
                    statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
                ).count(),
            }

        # Stats semaine
        stats_semaine = get_stats(debut_semaine, fin_semaine)

        # Stats mois
        stats_mois = get_stats(debut_mois, fin_mois)

        # Taux de réalisation
        def taux(termines, total):
            return round((termines / total * 100), 1) if total > 0 else 100

        stats_semaine['taux_rdv'] = taux(stats_semaine['rdv_termines'], stats_semaine['nb_rdv'])
        stats_semaine['taux_taches'] = taux(stats_semaine['taches_terminees'], stats_semaine['nb_taches'])
        stats_mois['taux_rdv'] = taux(stats_mois['rdv_termines'], stats_mois['nb_rdv'])
        stats_mois['taux_taches'] = taux(stats_mois['taches_terminees'], stats_mois['nb_taches'])

        result = {
            'semaine': {
                'debut': debut_semaine.isoformat(),
                'fin': fin_semaine.isoformat(),
                **stats_semaine
            },
            'mois': {
                'debut': debut_mois.isoformat(),
                'fin': fin_mois.isoformat(),
                **stats_mois
            },
        }

        # Stats par collaborateur (admin seulement)
        if is_admin:
            from gestion.models import Utilisateur
            collaborateurs_stats = []

            for collab in Utilisateur.objects.filter(is_active=True).exclude(role='admin'):
                taches_collab = Tache.objects.filter(
                    responsable=collab,
                    est_active=True,
                    date_echeance__gte=debut_mois,
                    date_echeance__lte=fin_mois
                )
                collaborateurs_stats.append({
                    'id': collab.id,
                    'nom': collab.get_full_name(),
                    'role': collab.role,
                    'taches_assignees': taches_collab.count(),
                    'taches_terminees': taches_collab.filter(statut=StatutTache.TERMINEE).count(),
                    'taches_en_retard': taches_collab.filter(date_echeance__lt=today).exclude(
                        statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
                    ).count(),
                })

            result['collaborateurs'] = collaborateurs_stats

        # Alertes
        alertes = []

        # Tâches en retard
        taches_retard = Tache.objects.filter(
            est_active=True,
            date_echeance__lt=today
        ).exclude(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE])
        if not is_admin:
            taches_retard = taches_retard.filter(Q(createur=user) | Q(responsable=user))

        for tache in taches_retard[:5]:
            alertes.append({
                'type': 'tache_retard',
                'message': f"Tâche en retard: {tache.titre}",
                'date': tache.date_echeance.isoformat(),
                'priorite': tache.priorite,
                'id': str(tache.id),
            })

        # RDV non confirmés (dans les 3 prochains jours)
        rdv_non_confirmes = RendezVous.objects.filter(
            est_actif=True,
            statut=StatutRendezVous.PLANIFIE,
            date_debut__date__gte=today,
            date_debut__date__lte=today + timedelta(days=3)
        )
        if not is_admin:
            rdv_non_confirmes = rdv_non_confirmes.filter(
                Q(createur=user) | Q(collaborateurs_assignes__utilisateur=user)
            )

        for rdv in rdv_non_confirmes[:5]:
            alertes.append({
                'type': 'rdv_non_confirme',
                'message': f"RDV non confirmé: {rdv.titre}",
                'date': rdv.date_debut.isoformat(),
                'id': str(rdv.id),
            })

        result['alertes'] = alertes

        return JsonResponse({
            'success': True,
            'data': result,
            'is_admin': is_admin
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API CLÔTURE DE JOURNÉE
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_cloturer_journee(request):
    """Clôturer manuellement la journée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        data = json.loads(request.body) if request.body else {}
        date_str = data.get('date', timezone.now().date().isoformat())
        date_cloture = datetime.fromisoformat(date_str).date()
        commentaire = data.get('commentaire')
        date_report = data.get('date_report')  # Pour reporter à une date spécifique

        # Créer ou récupérer la journée
        journee, created = JourneeAgenda.objects.get_or_create(
            date=date_cloture,
            utilisateur=user if not user_is_admin(user) else None
        )

        if journee.est_cloturee:
            return JsonResponse({'success': False, 'error': 'Cette journée est déjà clôturée'}, status=400)

        journee.cloturer(user, 'manuelle', commentaire)

        # Si date de report spécifique
        if date_report:
            date_report_obj = datetime.fromisoformat(date_report).date()
            taches_a_reporter = Tache.objects.filter(
                date_echeance=date_cloture,
                est_active=True
            ).exclude(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE])

            if not user_is_admin(user):
                taches_a_reporter = taches_a_reporter.filter(
                    Q(createur=user) | Q(responsable=user)
                )

            for tache in taches_a_reporter:
                ReportTache.objects.create(
                    tache=tache,
                    date_origine=tache.date_echeance,
                    nouvelle_date=date_report_obj,
                    raison=commentaire,
                    reporte_par=user,
                    type_report='manuel',
                )
                tache.date_echeance = date_report_obj
                tache.statut = StatutTache.REPORTEE
                tache.save()

        return JsonResponse({
            'success': True,
            'message': 'Journée clôturée avec succès',
            'data': {
                'bilan': journee.bilan_json,
                'taux_realisation': journee._calculer_taux_realisation(),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_bilan_journee(request, date_str):
    """Récupérer le bilan d'une journée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        date_obj = datetime.fromisoformat(date_str).date()

        try:
            journee = JourneeAgenda.objects.get(
                date=date_obj,
                utilisateur=user if not user_is_admin(user) else None
            )
        except JourneeAgenda.DoesNotExist:
            # Créer une journée virtuelle pour les stats
            journee = JourneeAgenda(
                date=date_obj,
                utilisateur=user if not user_is_admin(user) else None
            )
            journee.calculer_statistiques()

        return JsonResponse({
            'success': True,
            'data': {
                'date': date_obj.isoformat(),
                'est_cloturee': journee.est_cloturee,
                'date_cloture': journee.date_cloture.isoformat() if journee.date_cloture else None,
                'type_cloture': journee.type_cloture,
                'commentaire': journee.commentaire_cloture,
                'statistiques': {
                    'nb_rdv_prevus': journee.nb_rdv_prevus,
                    'nb_rdv_termines': journee.nb_rdv_termines,
                    'nb_rdv_annules': journee.nb_rdv_annules,
                    'nb_taches_prevues': journee.nb_taches_prevues,
                    'nb_taches_terminees': journee.nb_taches_terminees,
                    'nb_taches_reportees': journee.nb_taches_reportees,
                },
                'bilan': journee.bilan_json,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API NOTIFICATIONS
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_notifications(request):
    """Liste des notifications de l'utilisateur"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        non_lues_seulement = request.GET.get('non_lues') == 'true'
        limit = int(request.GET.get('limit', 20))

        queryset = Notification.objects.filter(destinataire=user)

        if non_lues_seulement:
            queryset = queryset.filter(est_lu=False)

        notifications = [
            {
                'id': str(n.id),
                'titre': n.titre,
                'message': n.message,
                'type': n.type_notification,
                'est_lu': n.est_lu,
                'date': n.date_creation.isoformat(),
                'objet_id': n.object_id,
            }
            for n in queryset[:limit]
        ]

        nb_non_lues = Notification.objects.filter(destinataire=user, est_lu=False).count()

        return JsonResponse({
            'success': True,
            'data': notifications,
            'nb_non_lues': nb_non_lues
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_marquer_notification_lue(request, notif_id):
    """Marquer une notification comme lue"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        notification = get_object_or_404(Notification, id=notif_id, destinataire=user)
        notification.marquer_lu()

        return JsonResponse({'success': True, 'message': 'Notification marquée comme lue'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_marquer_toutes_lues(request):
    """Marquer toutes les notifications comme lues"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        Notification.objects.filter(destinataire=user, est_lu=False).update(
            est_lu=True,
            date_lecture=timezone.now()
        )

        return JsonResponse({'success': True, 'message': 'Toutes les notifications marquées comme lues'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API ÉTIQUETTES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_liste_etiquettes(request):
    """Liste des étiquettes"""
    try:
        etiquettes = [
            {
                'id': str(e.id),
                'nom': e.nom,
                'couleur': e.couleur,
                'description': e.description,
            }
            for e in Etiquette.objects.all()
        ]

        return JsonResponse({'success': True, 'data': etiquettes})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_etiquette(request):
    """Créer une nouvelle étiquette"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        data = json.loads(request.body)

        if not data.get('nom'):
            return JsonResponse({'success': False, 'error': 'Le nom est obligatoire'}, status=400)

        if Etiquette.objects.filter(nom=data['nom']).exists():
            return JsonResponse({'success': False, 'error': 'Cette étiquette existe déjà'}, status=400)

        etiquette = Etiquette.objects.create(
            nom=data['nom'],
            couleur=data.get('couleur', '#3498db'),
            description=data.get('description'),
            createur=user,
        )

        return JsonResponse({
            'success': True,
            'data': {
                'id': str(etiquette.id),
                'nom': etiquette.nom,
                'couleur': etiquette.couleur,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API CONFIGURATION
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_configuration(request):
    """Récupérer la configuration de l'agenda"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        config = ConfigurationAgenda.get_instance() if ConfigurationAgenda.objects.exists() else ConfigurationAgenda()

        return JsonResponse({
            'success': True,
            'data': {
                'heure_debut_journee': config.heure_debut_journee.isoformat(),
                'heure_fin_journee': config.heure_fin_journee.isoformat(),
                'heure_cloture_auto': config.heure_cloture_auto.isoformat(),
                'jours_travail': config.jours_travail,
                'duree_rdv_defaut': config.duree_rdv_defaut,
                'rappel_rdv_defaut': config.rappel_rdv_defaut,
                'rappel_tache_defaut': config.rappel_tache_defaut,
                'envoyer_recapitulatif_quotidien': config.envoyer_recapitulatif_quotidien,
                'activer_notifications_email': config.activer_notifications_email,
                'activer_notifications_sms': config.activer_notifications_sms,
                'activer_cloture_auto': config.activer_cloture_auto,
                'reporter_auto_taches': config.reporter_auto_taches,
                'delai_escalade_retard': config.delai_escalade_retard,
                'couleurs_types_rdv': config.couleurs_types_rdv,
                'couleurs_types_tache': config.couleurs_types_tache,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def api_modifier_configuration(request):
    """Modifier la configuration de l'agenda (admin seulement)"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user_is_admin(user):
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        data = json.loads(request.body)
        config = ConfigurationAgenda.get_instance()

        if 'heure_debut_journee' in data:
            config.heure_debut_journee = datetime.strptime(data['heure_debut_journee'], '%H:%M').time()
        if 'heure_fin_journee' in data:
            config.heure_fin_journee = datetime.strptime(data['heure_fin_journee'], '%H:%M').time()
        if 'heure_cloture_auto' in data:
            config.heure_cloture_auto = datetime.strptime(data['heure_cloture_auto'], '%H:%M').time()
        if 'jours_travail' in data:
            config.jours_travail = data['jours_travail']
        if 'duree_rdv_defaut' in data:
            config.duree_rdv_defaut = data['duree_rdv_defaut']
        if 'rappel_rdv_defaut' in data:
            config.rappel_rdv_defaut = data['rappel_rdv_defaut']
        if 'rappel_tache_defaut' in data:
            config.rappel_tache_defaut = data['rappel_tache_defaut']
        if 'envoyer_recapitulatif_quotidien' in data:
            config.envoyer_recapitulatif_quotidien = data['envoyer_recapitulatif_quotidien']
        if 'activer_notifications_email' in data:
            config.activer_notifications_email = data['activer_notifications_email']
        if 'activer_notifications_sms' in data:
            config.activer_notifications_sms = data['activer_notifications_sms']
        if 'activer_cloture_auto' in data:
            config.activer_cloture_auto = data['activer_cloture_auto']
        if 'reporter_auto_taches' in data:
            config.reporter_auto_taches = data['reporter_auto_taches']
        if 'delai_escalade_retard' in data:
            config.delai_escalade_retard = data['delai_escalade_retard']
        if 'couleurs_types_rdv' in data:
            config.couleurs_types_rdv = data['couleurs_types_rdv']
        if 'couleurs_types_tache' in data:
            config.couleurs_types_tache = data['couleurs_types_tache']

        config.save()

        return JsonResponse({'success': True, 'message': 'Configuration mise à jour'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API UTILITAIRES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_collaborateurs(request):
    """Liste des collaborateurs pour assignation"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        from gestion.models import Collaborateur

        collaborateurs = [
            {
                'id': c.id,
                'nom': str(c),
                'utilisateur_id': c.utilisateur.id if c.utilisateur else None,
                'role': c.utilisateur.role if c.utilisateur else None,
            }
            for c in Collaborateur.objects.filter(actif=True).select_related('utilisateur')
        ]

        return JsonResponse({'success': True, 'data': collaborateurs})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_dossiers_liste(request):
    """Liste des dossiers pour liaison"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        from gestion.models import Dossier

        search = request.GET.get('search', '')
        limit = int(request.GET.get('limit', 20))

        queryset = Dossier.objects.filter(statut__in=['actif', 'urgent'])

        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(objet__icontains=search)
            )

        dossiers = [
            {
                'id': str(d.id),
                'reference': d.reference,
                'objet': d.objet,
                'statut': d.statut,
            }
            for d in queryset[:limit]
        ]

        return JsonResponse({'success': True, 'data': dossiers})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API VUES SAUVEGARDÉES
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_liste_vues_sauvegardees(request):
    """Liste des vues sauvegardées de l'utilisateur"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        vues = VueSauvegardee.objects.filter(utilisateur=user)

        vues_list = [
            {
                'id': str(v.id),
                'nom': v.nom,
                'description': v.description,
                'filtres': v.filtres,
                'est_par_defaut': v.est_par_defaut,
                'ordre': v.ordre,
                'created_at': v.created_at.isoformat(),
                'updated_at': v.updated_at.isoformat(),
            }
            for v in vues
        ]

        return JsonResponse({
            'success': True,
            'data': vues_list,
            'count': len(vues_list)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_creer_vue_sauvegardee(request):
    """Créer une nouvelle vue sauvegardée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        data = json.loads(request.body)

        if not data.get('nom'):
            return JsonResponse({'success': False, 'error': 'Le nom est obligatoire'}, status=400)

        if VueSauvegardee.objects.filter(utilisateur=user, nom=data['nom']).exists():
            return JsonResponse({'success': False, 'error': 'Une vue avec ce nom existe déjà'}, status=400)

        # Déterminer l'ordre
        dernier_ordre = VueSauvegardee.objects.filter(utilisateur=user).order_by('-ordre').first()
        ordre = (dernier_ordre.ordre + 1) if dernier_ordre else 0

        vue = VueSauvegardee.objects.create(
            utilisateur=user,
            nom=data['nom'],
            description=data.get('description', ''),
            filtres=data.get('filtres', {}),
            est_par_defaut=data.get('est_par_defaut', False),
            ordre=ordre,
        )

        return JsonResponse({
            'success': True,
            'message': 'Vue sauvegardée créée',
            'data': {
                'id': str(vue.id),
                'nom': vue.nom,
                'filtres': vue.filtres,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def api_modifier_vue_sauvegardee(request, vue_id):
    """Modifier une vue sauvegardée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        vue = get_object_or_404(VueSauvegardee, id=vue_id, utilisateur=user)
        data = json.loads(request.body)

        if 'nom' in data:
            # Vérifier unicité du nom
            if VueSauvegardee.objects.filter(utilisateur=user, nom=data['nom']).exclude(pk=vue.pk).exists():
                return JsonResponse({'success': False, 'error': 'Une vue avec ce nom existe déjà'}, status=400)
            vue.nom = data['nom']

        if 'description' in data:
            vue.description = data['description']
        if 'filtres' in data:
            vue.filtres = data['filtres']
        if 'est_par_defaut' in data:
            vue.est_par_defaut = data['est_par_defaut']
        if 'ordre' in data:
            vue.ordre = data['ordre']

        vue.save()

        return JsonResponse({
            'success': True,
            'message': 'Vue sauvegardée modifiée',
            'data': {
                'id': str(vue.id),
                'nom': vue.nom,
                'filtres': vue.filtres,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_supprimer_vue_sauvegardee(request, vue_id):
    """Supprimer une vue sauvegardée"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        vue = get_object_or_404(VueSauvegardee, id=vue_id, utilisateur=user)
        nom = vue.nom
        vue.delete()

        return JsonResponse({
            'success': True,
            'message': f'Vue "{nom}" supprimée'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_appliquer_vue_sauvegardee(request, vue_id):
    """Retourne les filtres d'une vue sauvegardée pour les appliquer"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        vue = get_object_or_404(VueSauvegardee, id=vue_id, utilisateur=user)

        return JsonResponse({
            'success': True,
            'data': {
                'id': str(vue.id),
                'nom': vue.nom,
                'filtres': vue.filtres,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# API PARTICIPATION RDV (STATUT PRÉSENCE)
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def api_participations_rdv(request, rdv_id):
    """Liste des participations d'un RDV avec statuts de présence"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)

        participations = []
        for p in rdv.participations.select_related('collaborateur', 'participant_externe'):
            participant_data = None
            if p.collaborateur:
                participant_data = {
                    'type': 'collaborateur',
                    'id': p.collaborateur.id,
                    'nom': str(p.collaborateur),
                }
            elif p.participant_externe:
                participant_data = {
                    'type': 'externe',
                    'id': str(p.participant_externe.id),
                    'nom': p.participant_externe.nom,
                    'email': p.participant_externe.email,
                }

            participations.append({
                'id': str(p.id),
                'participant': participant_data,
                'statut_presence': p.statut_presence,
                'statut_presence_display': p.get_statut_presence_display(),
                'date_reponse': p.date_reponse.isoformat() if p.date_reponse else None,
                'commentaire': p.commentaire,
            })

        return JsonResponse({
            'success': True,
            'data': participations,
            'count': len(participations)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_ajouter_participation(request, rdv_id):
    """Ajouter un participant à un RDV"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)
        data = json.loads(request.body)

        collaborateur = None
        participant_externe = None

        if data.get('collaborateur_id'):
            from gestion.models import Collaborateur
            collaborateur = get_object_or_404(Collaborateur, id=data['collaborateur_id'])
            # Vérifier si déjà participant
            if ParticipationRdv.objects.filter(rdv=rdv, collaborateur=collaborateur).exists():
                return JsonResponse({'success': False, 'error': 'Ce collaborateur est déjà participant'}, status=400)

        elif data.get('participant_externe_id'):
            participant_externe = get_object_or_404(ParticipantExterne, id=data['participant_externe_id'])
            if ParticipationRdv.objects.filter(rdv=rdv, participant_externe=participant_externe).exists():
                return JsonResponse({'success': False, 'error': 'Ce participant est déjà ajouté'}, status=400)

        else:
            return JsonResponse({'success': False, 'error': 'Participant requis'}, status=400)

        participation = ParticipationRdv.objects.create(
            rdv=rdv,
            collaborateur=collaborateur,
            participant_externe=participant_externe,
            statut_presence='invite',
        )

        # Notification si collaborateur
        if collaborateur and collaborateur.utilisateur:
            from .services import NotificationService
            NotificationService.creer_notification(
                collaborateur.utilisateur,
                f"Invitation RDV: {rdv.titre}",
                f"Vous êtes invité au rendez-vous '{rdv.titre}' prévu le {rdv.date_debut.strftime('%d/%m/%Y à %H:%M')}",
                'rappel_rdv',
                rdv
            )
            participation.notifie = True
            participation.date_notification = timezone.now()
            participation.save()

        return JsonResponse({
            'success': True,
            'message': 'Participant ajouté',
            'data': {'id': str(participation.id)}
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_repondre_invitation(request, rdv_id):
    """Confirmer ou décliner une invitation à un RDV"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)
        data = json.loads(request.body)

        reponse = data.get('reponse')  # 'confirme' ou 'decline'
        commentaire = data.get('commentaire', '')

        if reponse not in ['confirme', 'decline']:
            return JsonResponse({'success': False, 'error': "Réponse invalide (confirme/decline)"}, status=400)

        # Trouver la participation de l'utilisateur
        from gestion.models import Collaborateur
        try:
            collaborateur = Collaborateur.objects.get(utilisateur=user)
            participation = ParticipationRdv.objects.get(rdv=rdv, collaborateur=collaborateur)
        except (Collaborateur.DoesNotExist, ParticipationRdv.DoesNotExist):
            return JsonResponse({'success': False, 'error': "Vous n'êtes pas invité à ce RDV"}, status=404)

        if reponse == 'confirme':
            participation.confirmer(commentaire)
            message = 'Participation confirmée'
        else:
            participation.decliner(commentaire)
            message = 'Invitation déclinée'

        # Notification au créateur du RDV
        if rdv.createur and rdv.createur != user:
            from .services import NotificationService
            action = 'confirmé' if reponse == 'confirme' else 'décliné'
            NotificationService.creer_notification(
                rdv.createur,
                f"Réponse invitation: {rdv.titre}",
                f"{user.get_full_name()} a {action} sa participation au RDV '{rdv.titre}'",
                'autre',
                rdv
            )

        return JsonResponse({
            'success': True,
            'message': message,
            'data': {
                'statut_presence': participation.statut_presence,
                'statut_presence_display': participation.get_statut_presence_display(),
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_marquer_presence(request, rdv_id):
    """Marquer la présence/absence des participants après le RDV"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        rdv = get_object_or_404(RendezVous, id=rdv_id, est_actif=True)

        # Vérifier que l'utilisateur peut modifier (créateur ou admin)
        if not user_is_admin(user) and rdv.createur != user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

        data = json.loads(request.body)
        presences = data.get('presences', [])  # [{id, statut: 'present'|'absent'|'excuse'}]

        for p_data in presences:
            participation_id = p_data.get('id')
            statut = p_data.get('statut')

            if statut not in ['present', 'absent', 'excuse']:
                continue

            try:
                participation = ParticipationRdv.objects.get(id=participation_id, rdv=rdv)
                if statut == 'present':
                    participation.marquer_present()
                else:
                    participation.marquer_absent(excuse=(statut == 'excuse'))
            except ParticipationRdv.DoesNotExist:
                pass

        return JsonResponse({
            'success': True,
            'message': 'Présences enregistrées'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_recherche_globale(request):
    """Recherche globale dans RDV et tâches"""
    try:
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        search = request.GET.get('q', '')
        if len(search) < 2:
            return JsonResponse({'success': True, 'data': {'rdv': [], 'taches': []}})

        # Recherche RDV
        rdv_queryset = RendezVous.objects.filter(
            est_actif=True
        ).filter(
            Q(titre__icontains=search) |
            Q(description__icontains=search) |
            Q(lieu__icontains=search)
        )
        rdv_queryset = filter_by_user_permissions(rdv_queryset, user, 'rdv')

        rdv_list = [
            {
                'id': str(r.id),
                'type': 'rdv',
                'titre': r.titre,
                'date': r.date_debut.isoformat(),
                'statut': r.statut,
            }
            for r in rdv_queryset[:10]
        ]

        # Recherche tâches
        tache_queryset = Tache.objects.filter(
            est_active=True
        ).filter(
            Q(titre__icontains=search) |
            Q(description__icontains=search)
        )
        tache_queryset = filter_by_user_permissions(tache_queryset, user, 'tache')

        tache_list = [
            {
                'id': str(t.id),
                'type': 'tache',
                'titre': t.titre,
                'date': t.date_echeance.isoformat(),
                'statut': t.statut,
            }
            for t in tache_queryset[:10]
        ]

        return JsonResponse({
            'success': True,
            'data': {
                'rdv': rdv_list,
                'taches': tache_list
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

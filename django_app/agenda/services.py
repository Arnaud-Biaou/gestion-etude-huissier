"""
Services métier pour le module Agenda
Logique de notification, récurrence, clôture automatique, etc.

Auteur: Maître Martial Arnaud BIAOU
"""

from datetime import datetime, timedelta, date, time
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    RendezVous, Tache, Notification, RappelRdv, RappelTache,
    JourneeAgenda, ReportTache, ConfigurationAgenda,
    StatistiquesAgenda, StatutRendezVous, StatutTache,
    StatutDelegation, TypeRecurrence, TypeNotification
)


class NotificationService:
    """Service de gestion des notifications"""

    @staticmethod
    def creer_notification(destinataire, titre, message, type_notification, objet=None, canal='application'):
        """Crée une notification pour un utilisateur"""
        notif = Notification.objects.create(
            destinataire=destinataire,
            titre=titre,
            message=message,
            type_notification=type_notification,
            canal=canal,
        )

        if objet:
            notif.content_type = ContentType.objects.get_for_model(objet)
            notif.object_id = str(objet.id)
            notif.save()

        # Envoi email si configuré
        if canal in ['email', 'tous']:
            NotificationService.envoyer_email(destinataire, titre, message)

        return notif

    @staticmethod
    def envoyer_email(destinataire, titre, message):
        """Envoie un email de notification"""
        try:
            config = ConfigurationAgenda.get_instance()
            if not config.activer_notifications_email:
                return False

            if destinataire.email:
                send_mail(
                    subject=f"[Agenda Étude] {titre}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                    recipient_list=[destinataire.email],
                    fail_silently=True,
                )
                return True
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        return False

    @staticmethod
    def notifier_nouvelle_delegation(tache, createur, responsable):
        """Notifie le responsable d'une nouvelle délégation"""
        message = f"""
Vous avez une nouvelle tâche assignée par {createur.get_full_name()}.

Tâche: {tache.titre}
Date d'échéance: {tache.date_echeance.strftime('%d/%m/%Y')}
Priorité: {tache.get_priorite_display()}

{f'Instructions: {tache.instructions_delegation}' if tache.instructions_delegation else ''}
        """.strip()

        return NotificationService.creer_notification(
            responsable,
            "Nouvelle tâche déléguée",
            message,
            'nouvelle_tache',
            tache,
            'tous'
        )

    @staticmethod
    def notifier_tache_terminee(tache, utilisateur):
        """Notifie le créateur qu'une tâche déléguée est terminée"""
        if tache.createur and tache.createur != utilisateur:
            message = f"""
{utilisateur.get_full_name()} a terminé la tâche que vous lui aviez assignée.

Tâche: {tache.titre}
Date de terminaison: {timezone.now().strftime('%d/%m/%Y à %H:%M')}

{f'Compte-rendu attendu: Oui' if tache.demande_compte_rendu else ''}
            """.strip()

            return NotificationService.creer_notification(
                tache.createur,
                "Tâche déléguée terminée",
                message,
                'tache_terminee',
                tache,
                'tous'
            )
        return None

    @staticmethod
    def notifier_tache_en_retard(tache):
        """Notifie les responsables d'une tâche en retard"""
        responsables = [tache.responsable] if tache.responsable else []
        if tache.createur and tache.createur not in responsables:
            responsables.append(tache.createur)

        jours_retard = (timezone.now().date() - tache.date_echeance).days

        message = f"""
La tâche suivante est en retard de {jours_retard} jour(s):

Tâche: {tache.titre}
Date d'échéance: {tache.date_echeance.strftime('%d/%m/%Y')}
Responsable: {tache.responsable.get_full_name() if tache.responsable else 'Non assigné'}
        """.strip()

        for user in responsables:
            if user:
                NotificationService.creer_notification(
                    user,
                    f"Tâche en retard ({jours_retard}j)",
                    message,
                    'tache_retard',
                    tache,
                    'application'
                )


class RappelService:
    """Service de gestion des rappels"""

    @staticmethod
    def traiter_rappels_rdv():
        """Traite les rappels de rendez-vous à envoyer"""
        now = timezone.now()

        rappels = RappelRdv.objects.filter(
            est_envoye=False,
            rendez_vous__est_actif=True,
            rendez_vous__date_debut__gt=now
        ).select_related('rendez_vous')

        for rappel in rappels:
            date_rappel = rappel.get_date_rappel()
            if date_rappel <= now:
                RappelService._envoyer_rappel_rdv(rappel)

    @staticmethod
    def _envoyer_rappel_rdv(rappel):
        """Envoie un rappel de RDV"""
        rdv = rappel.rendez_vous

        # Destinataires
        destinataires = list(rappel.destinataires.all())
        if not destinataires:
            destinataires = [rdv.createur]
            for collab in rdv.collaborateurs_assignes.all():
                if collab.utilisateur:
                    destinataires.append(collab.utilisateur)

        message = f"""
Rappel de rendez-vous:

{rdv.titre}
Date: {rdv.date_debut.strftime('%d/%m/%Y à %H:%M')}
{f'Lieu: {rdv.lieu}' if rdv.lieu else ''}
{f'Description: {rdv.description}' if rdv.description else ''}
        """.strip()

        for dest in set(destinataires):
            NotificationService.creer_notification(
                dest,
                f"Rappel: {rdv.titre}",
                message,
                'rappel_rdv',
                rdv,
                rappel.type_notification
            )

        rappel.est_envoye = True
        rappel.date_envoi = timezone.now()
        rappel.save()

    @staticmethod
    def traiter_rappels_tache():
        """Traite les rappels de tâches à envoyer"""
        today = timezone.now().date()

        rappels = RappelTache.objects.filter(
            est_envoye=False,
            tache__est_active=True
        ).exclude(
            tache__statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
        ).select_related('tache')

        for rappel in rappels:
            date_rappel = RappelService._calculer_date_rappel_tache(rappel)
            if date_rappel and date_rappel <= today:
                RappelService._envoyer_rappel_tache(rappel)

    @staticmethod
    def _calculer_date_rappel_tache(rappel):
        """Calcule la date d'envoi d'un rappel de tâche"""
        tache = rappel.tache
        delais = {
            'jour_echeance': 0,
            'veille': 1,
            '2jours': 2,
            'semaine': 7,
        }

        if rappel.type_rappel == 'personnalise':
            jours = rappel.delai_personnalise or 0
        else:
            jours = delais.get(rappel.type_rappel, 0)

        return tache.date_echeance - timedelta(days=jours)

    @staticmethod
    def _envoyer_rappel_tache(rappel):
        """Envoie un rappel de tâche"""
        tache = rappel.tache

        destinataires = []
        if tache.responsable:
            destinataires.append(tache.responsable)
        if tache.createur and tache.createur not in destinataires:
            destinataires.append(tache.createur)

        message = f"""
Rappel de tâche:

{tache.titre}
Date d'échéance: {tache.date_echeance.strftime('%d/%m/%Y')}
{f'Heure: {tache.heure_echeance.strftime("%H:%M")}' if tache.heure_echeance else ''}
Priorité: {tache.get_priorite_display()}
{f'Description: {tache.description}' if tache.description else ''}
        """.strip()

        for dest in destinataires:
            NotificationService.creer_notification(
                dest,
                f"Rappel: {tache.titre}",
                message,
                'rappel_tache',
                tache,
                rappel.type_notification
            )

        rappel.est_envoye = True
        rappel.date_envoi = timezone.now()
        rappel.save()


class RecurrenceService:
    """Service de gestion des récurrences"""

    @staticmethod
    def generer_occurrences_rdv(rdv_parent, date_limite=None):
        """Génère les occurrences d'un RDV récurrent"""
        if rdv_parent.type_recurrence == TypeRecurrence.UNIQUE:
            return []

        if not date_limite:
            date_limite = rdv_parent.date_fin_recurrence or (timezone.now().date() + timedelta(days=90))

        occurrences = []
        current_date = rdv_parent.date_debut.date()
        duree = rdv_parent.date_fin - rdv_parent.date_debut

        while current_date <= date_limite:
            # Calculer la prochaine date
            next_date = RecurrenceService._calculer_prochaine_date(
                current_date,
                rdv_parent.type_recurrence,
                rdv_parent.jours_semaine,
                rdv_parent.jour_mois
            )

            if next_date and next_date <= date_limite:
                # Vérifier si l'occurrence existe déjà
                existe = RendezVous.objects.filter(
                    rdv_parent=rdv_parent,
                    date_debut__date=next_date
                ).exists()

                if not existe:
                    # Créer l'occurrence
                    heure_debut = rdv_parent.date_debut.time()
                    nouvelle_date_debut = timezone.make_aware(
                        datetime.combine(next_date, heure_debut)
                    )

                    occurrence = RendezVous.objects.create(
                        titre=rdv_parent.titre,
                        type_rdv=rdv_parent.type_rdv,
                        description=rdv_parent.description,
                        date_debut=nouvelle_date_debut,
                        date_fin=nouvelle_date_debut + duree,
                        journee_entiere=rdv_parent.journee_entiere,
                        lieu=rdv_parent.lieu,
                        adresse=rdv_parent.adresse,
                        latitude=rdv_parent.latitude,
                        longitude=rdv_parent.longitude,
                        statut=StatutRendezVous.PLANIFIE,
                        priorite=rdv_parent.priorite,
                        couleur=rdv_parent.couleur,
                        type_recurrence=TypeRecurrence.UNIQUE,
                        createur=rdv_parent.createur,
                        rdv_parent=rdv_parent,
                    )

                    # Copier les relations
                    occurrence.dossiers.set(rdv_parent.dossiers.all())
                    occurrence.collaborateurs_assignes.set(rdv_parent.collaborateurs_assignes.all())
                    occurrence.participants_externes.set(rdv_parent.participants_externes.all())

                    occurrences.append(occurrence)

            current_date = next_date if next_date else date_limite + timedelta(days=1)

        return occurrences

    @staticmethod
    def generer_occurrences_tache(tache_parent, date_limite=None):
        """Génère les occurrences d'une tâche récurrente"""
        if tache_parent.type_recurrence == TypeRecurrence.UNIQUE:
            return []

        if not date_limite:
            date_limite = tache_parent.date_fin_recurrence or (timezone.now().date() + timedelta(days=90))

        occurrences = []
        current_date = tache_parent.date_echeance

        while current_date <= date_limite:
            next_date = RecurrenceService._calculer_prochaine_date(
                current_date,
                tache_parent.type_recurrence,
                tache_parent.jours_semaine,
                tache_parent.jour_mois
            )

            if next_date and next_date <= date_limite:
                existe = Tache.objects.filter(
                    tache_parent=tache_parent,
                    date_echeance=next_date
                ).exists()

                if not existe:
                    occurrence = Tache.objects.create(
                        titre=tache_parent.titre,
                        type_tache=tache_parent.type_tache,
                        description=tache_parent.description,
                        date_echeance=next_date,
                        heure_echeance=tache_parent.heure_echeance,
                        priorite=tache_parent.priorite,
                        couleur=tache_parent.couleur,
                        temps_estime=tache_parent.temps_estime,
                        type_recurrence=TypeRecurrence.UNIQUE,
                        createur=tache_parent.createur,
                        responsable=tache_parent.responsable,
                        dossier=tache_parent.dossier,
                        tache_parent=tache_parent,
                    )

                    occurrence.etiquettes.set(tache_parent.etiquettes.all())
                    occurrence.co_responsables.set(tache_parent.co_responsables.all())

                    occurrences.append(occurrence)

            current_date = next_date if next_date else date_limite + timedelta(days=1)

        return occurrences

    @staticmethod
    def _calculer_prochaine_date(date_courante, type_recurrence, jours_semaine=None, jour_mois=None):
        """Calcule la prochaine date selon le type de récurrence"""
        if type_recurrence == TypeRecurrence.QUOTIDIEN:
            return date_courante + timedelta(days=1)

        elif type_recurrence == TypeRecurrence.HEBDOMADAIRE:
            if jours_semaine:
                # Trouver le prochain jour dans la liste
                jour_actuel = date_courante.weekday()
                jours_tries = sorted(jours_semaine)

                for jour in jours_tries:
                    if jour > jour_actuel:
                        return date_courante + timedelta(days=jour - jour_actuel)

                # Si aucun jour restant cette semaine, prendre le premier de la semaine suivante
                return date_courante + timedelta(days=7 - jour_actuel + jours_tries[0])
            else:
                return date_courante + timedelta(weeks=1)

        elif type_recurrence == TypeRecurrence.MENSUEL:
            # Prochain mois
            annee = date_courante.year
            mois = date_courante.month + 1
            if mois > 12:
                mois = 1
                annee += 1

            if jour_mois:
                jour = min(jour_mois, 28)  # Sécurité pour les mois courts
            else:
                jour = date_courante.day

            try:
                return date(annee, mois, jour)
            except ValueError:
                # Jour invalide pour ce mois, prendre le dernier jour
                from calendar import monthrange
                dernier_jour = monthrange(annee, mois)[1]
                return date(annee, mois, dernier_jour)

        return None


class ClotureJourneeService:
    """Service de clôture automatique des journées"""

    @staticmethod
    def cloturer_automatique(date_cloture=None, utilisateur=None):
        """Clôture automatique d'une journée"""
        if not date_cloture:
            date_cloture = timezone.now().date() - timedelta(days=1)

        # Vérifier si la journée est déjà clôturée
        journee, created = JourneeAgenda.objects.get_or_create(
            date=date_cloture,
            utilisateur=utilisateur,
            defaults={'est_cloturee': False}
        )

        if journee.est_cloturee:
            return journee

        config = ConfigurationAgenda.get_instance() if ConfigurationAgenda.objects.exists() else None

        # Calculer les statistiques
        journee.calculer_statistiques()

        # Clôturer
        journee.cloturer(utilisateur, 'automatique')

        # Reporter les tâches si configuré
        if not config or config.reporter_auto_taches:
            ClotureJourneeService._reporter_taches(date_cloture, utilisateur)

        # Envoyer le bilan
        ClotureJourneeService._envoyer_bilan(journee)

        return journee

    @staticmethod
    def _reporter_taches(date_origine, utilisateur=None):
        """Reporte les tâches non terminées"""
        tache_filter = Q(date_echeance=date_origine, est_active=True)
        tache_filter &= ~Q(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE])

        if utilisateur:
            tache_filter &= Q(createur=utilisateur) | Q(responsable=utilisateur)

        taches = Tache.objects.filter(tache_filter)
        lendemain = date_origine + timedelta(days=1)

        for tache in taches:
            # Créer l'historique de report
            ReportTache.objects.create(
                tache=tache,
                date_origine=date_origine,
                nouvelle_date=lendemain,
                raison="Clôture automatique de journée",
                type_report='automatique'
            )

            # Mettre à jour la tâche
            tache.date_echeance = lendemain
            tache.statut = StatutTache.REPORTEE
            tache.save()

            # Notifier le responsable
            if tache.responsable:
                NotificationService.creer_notification(
                    tache.responsable,
                    "Tâche reportée automatiquement",
                    f"La tâche '{tache.titre}' a été reportée au {lendemain.strftime('%d/%m/%Y')}",
                    'report',
                    tache
                )

    @staticmethod
    def _envoyer_bilan(journee):
        """Envoie le bilan de la journée"""
        if journee.utilisateur:
            destinataires = [journee.utilisateur]
        else:
            # Envoyer aux admins
            from gestion.models import Utilisateur
            destinataires = Utilisateur.objects.filter(role__in=['admin', 'huissier'], is_active=True)

        bilan = journee.bilan_json or {}
        taux = bilan.get('taux_realisation', 0)

        message = f"""
Bilan de la journée du {journee.date.strftime('%d/%m/%Y')}:

Rendez-vous:
- Prévus: {journee.nb_rdv_prevus}
- Terminés: {journee.nb_rdv_termines}
- Annulés: {journee.nb_rdv_annules}

Tâches:
- Prévues: {journee.nb_taches_prevues}
- Terminées: {journee.nb_taches_terminees}
- Reportées: {journee.nb_taches_reportees}

Taux de réalisation: {taux}%
        """.strip()

        for dest in destinataires:
            NotificationService.creer_notification(
                dest,
                f"Bilan du {journee.date.strftime('%d/%m/%Y')}",
                message,
                'bilan_journee',
                None,
                'application'
            )


class StatistiquesService:
    """Service de calcul des statistiques"""

    @staticmethod
    def calculer_stats_periode(type_periode, date_debut, date_fin, utilisateur=None):
        """Calcule les statistiques pour une période donnée"""
        stats, created = StatistiquesAgenda.objects.get_or_create(
            type_periode=type_periode,
            date_debut=date_debut,
            utilisateur=utilisateur,
            defaults={'date_fin': date_fin}
        )

        # Filtres de base
        rdv_filter = Q(est_actif=True, date_debut__date__gte=date_debut, date_debut__date__lte=date_fin)
        tache_filter = Q(est_active=True, date_echeance__gte=date_debut, date_echeance__lte=date_fin)

        if utilisateur:
            rdv_filter &= Q(createur=utilisateur) | Q(collaborateurs_assignes__utilisateur=utilisateur)
            tache_filter &= Q(createur=utilisateur) | Q(responsable=utilisateur)

        # Stats RDV
        rdv = RendezVous.objects.filter(rdv_filter).distinct()
        stats.nb_rdv_total = rdv.count()
        stats.nb_rdv_termines = rdv.filter(statut=StatutRendezVous.TERMINE).count()
        stats.nb_rdv_annules = rdv.filter(statut=StatutRendezVous.ANNULE).count()
        stats.nb_rdv_reportes = rdv.filter(statut=StatutRendezVous.REPORTE).count()

        # Répartition par type
        stats.repartition_types_rdv = dict(
            rdv.values('type_rdv').annotate(count=models.Count('id')).values_list('type_rdv', 'count')
        )

        # Stats Tâches
        taches = Tache.objects.filter(tache_filter).distinct()
        stats.nb_taches_total = taches.count()
        stats.nb_taches_terminees = taches.filter(statut=StatutTache.TERMINEE).count()
        stats.nb_taches_en_retard = taches.filter(
            date_echeance__lt=date_fin
        ).exclude(statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]).count()
        stats.nb_taches_reportees = taches.filter(statut=StatutTache.REPORTEE).count()

        # Répartition par type
        stats.repartition_types_tache = dict(
            taches.values('type_tache').annotate(count=models.Count('id')).values_list('type_tache', 'count')
        )

        # Taux de réalisation
        if stats.nb_rdv_total > 0:
            stats.taux_realisation_rdv = (stats.nb_rdv_termines / stats.nb_rdv_total) * 100
        else:
            stats.taux_realisation_rdv = 100

        if stats.nb_taches_total > 0:
            stats.taux_realisation_taches = (stats.nb_taches_terminees / stats.nb_taches_total) * 100
        else:
            stats.taux_realisation_taches = 100

        # Délégations
        delegations = taches.filter(statut_delegation__isnull=False)
        stats.nb_taches_deleguees = delegations.count()
        delegations_terminees = delegations.filter(statut_delegation=StatutDelegation.VALIDEE).count()
        if stats.nb_taches_deleguees > 0:
            stats.taux_completion_delegations = (delegations_terminees / stats.nb_taches_deleguees) * 100
        else:
            stats.taux_completion_delegations = 100

        stats.save()
        return stats


class EscaladeService:
    """Service de gestion des escalades pour tâches en retard"""

    @staticmethod
    def verifier_escalades():
        """Vérifie et déclenche les escalades nécessaires"""
        config = ConfigurationAgenda.get_instance() if ConfigurationAgenda.objects.exists() else None
        delai_escalade = config.delai_escalade_retard if config else 2

        date_limite = timezone.now().date() - timedelta(days=delai_escalade)

        taches_a_escalader = Tache.objects.filter(
            est_active=True,
            date_echeance__lte=date_limite
        ).exclude(
            statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
        )

        from gestion.models import Utilisateur
        admins = Utilisateur.objects.filter(role__in=['admin', 'huissier'], is_active=True)

        for tache in taches_a_escalader:
            jours_retard = (timezone.now().date() - tache.date_echeance).days

            # Vérifier si déjà escaladée récemment (dans les 24h)
            notification_recente = Notification.objects.filter(
                type_notification='tache_retard',
                object_id=str(tache.id),
                date_creation__gte=timezone.now() - timedelta(hours=24)
            ).exists()

            if not notification_recente:
                message = f"""
ALERTE: Tâche en retard critique

Tâche: {tache.titre}
Retard: {jours_retard} jours
Responsable: {tache.responsable.get_full_name() if tache.responsable else 'Non assigné'}
{f'Dossier: {tache.dossier.reference}' if tache.dossier else ''}

Cette tâche nécessite votre attention immédiate.
                """.strip()

                for admin in admins:
                    NotificationService.creer_notification(
                        admin,
                        f"URGENT: Tâche en retard de {jours_retard}j",
                        message,
                        'tache_retard',
                        tache,
                        'tous'
                    )


# Import manquant pour les annotations
from django.db import models

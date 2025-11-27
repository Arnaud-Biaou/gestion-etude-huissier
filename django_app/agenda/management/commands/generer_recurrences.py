"""
Commande de gestion pour générer les occurrences de RDV et tâches récurrents

Utilisation: python manage.py generer_recurrences [--jours N]

Cette commande devrait être exécutée quotidiennement pour créer les occurrences
des éléments récurrents pour les N prochains jours.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from agenda.models import RendezVous, Tache, TypeRecurrence
from agenda.services import RecurrenceService


class Command(BaseCommand):
    help = 'Génère les occurrences de RDV et tâches récurrents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jours',
            type=int,
            default=30,
            help='Nombre de jours à l\'avance pour générer les occurrences (défaut: 30)',
        )

    def handle(self, *args, **options):
        jours = options['jours']
        date_limite = timezone.now().date() + timedelta(days=jours)

        self.stdout.write(f'Génération des occurrences jusqu\'au {date_limite}...')

        # RDV récurrents
        rdv_recurrents = RendezVous.objects.filter(
            est_actif=True,
            type_recurrence__in=[
                TypeRecurrence.QUOTIDIEN,
                TypeRecurrence.HEBDOMADAIRE,
                TypeRecurrence.MENSUEL,
                TypeRecurrence.PERSONNALISE
            ],
            rdv_parent__isnull=True  # Seulement les parents
        )

        total_rdv = 0
        for rdv in rdv_recurrents:
            occurrences = RecurrenceService.generer_occurrences_rdv(rdv, date_limite)
            total_rdv += len(occurrences)
            if occurrences:
                self.stdout.write(f'  - {rdv.titre}: {len(occurrences)} occurrence(s) créée(s)')

        self.stdout.write(self.style.SUCCESS(f'{total_rdv} occurrence(s) de RDV créée(s)'))

        # Tâches récurrentes
        taches_recurrentes = Tache.objects.filter(
            est_active=True,
            type_recurrence__in=[
                TypeRecurrence.QUOTIDIEN,
                TypeRecurrence.HEBDOMADAIRE,
                TypeRecurrence.MENSUEL,
                TypeRecurrence.PERSONNALISE
            ],
            tache_parent__isnull=True  # Seulement les parents
        )

        total_taches = 0
        for tache in taches_recurrentes:
            occurrences = RecurrenceService.generer_occurrences_tache(tache, date_limite)
            total_taches += len(occurrences)
            if occurrences:
                self.stdout.write(f'  - {tache.titre}: {len(occurrences)} occurrence(s) créée(s)')

        self.stdout.write(self.style.SUCCESS(f'{total_taches} occurrence(s) de tâche(s) créée(s)'))
        self.stdout.write(self.style.SUCCESS('Génération des récurrences terminée'))

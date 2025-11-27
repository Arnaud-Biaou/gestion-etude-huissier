"""
Commande de gestion pour clôturer automatiquement la journée

Utilisation: python manage.py cloturer_journee [--date YYYY-MM-DD]

Cette commande devrait être exécutée chaque jour après l'heure de clôture (ex: 23h59).
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from agenda.services import ClotureJourneeService


class Command(BaseCommand):
    help = 'Clôture automatiquement la journée et reporte les tâches non terminées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date à clôturer (format: YYYY-MM-DD). Par défaut: hier',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la clôture même si déjà clôturée',
        )

    def handle(self, *args, **options):
        if options['date']:
            try:
                date_cloture = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Format de date invalide. Utilisez YYYY-MM-DD')
        else:
            # Par défaut, clôturer hier
            date_cloture = timezone.now().date() - timedelta(days=1)

        self.stdout.write(f'Clôture de la journée du {date_cloture}...')

        try:
            journee = ClotureJourneeService.cloturer_automatique(date_cloture)

            if journee.bilan_json:
                bilan = journee.bilan_json
                self.stdout.write(f"RDV: {bilan['rdv']['termines']}/{bilan['rdv']['prevus']}")
                self.stdout.write(f"Tâches: {bilan['taches']['terminees']}/{bilan['taches']['prevues']}")
                self.stdout.write(f"Taux de réalisation: {bilan['taux_realisation']}%")

            self.stdout.write(self.style.SUCCESS(f'Journée du {date_cloture} clôturée avec succès'))

        except Exception as e:
            raise CommandError(f'Erreur lors de la clôture: {str(e)}')

"""
Commande de gestion pour calculer les statistiques de l'agenda

Utilisation: python manage.py calculer_statistiques [--periode jour|semaine|mois]

Cette commande calcule et enregistre les statistiques pour les rapports.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from agenda.services import StatistiquesService


class Command(BaseCommand):
    help = 'Calcule les statistiques de l\'agenda'

    def add_arguments(self, parser):
        parser.add_argument(
            '--periode',
            type=str,
            choices=['jour', 'semaine', 'mois'],
            default='jour',
            help='Période pour laquelle calculer les statistiques',
        )

    def handle(self, *args, **options):
        periode = options['periode']
        today = timezone.now().date()

        if periode == 'jour':
            date_debut = today - timedelta(days=1)
            date_fin = date_debut
        elif periode == 'semaine':
            date_debut = today - timedelta(days=today.weekday() + 7)
            date_fin = date_debut + timedelta(days=6)
        else:  # mois
            date_debut = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            date_fin = today.replace(day=1) - timedelta(days=1)

        self.stdout.write(f'Calcul des statistiques {periode} ({date_debut} - {date_fin})...')

        try:
            # Stats globales
            stats = StatistiquesService.calculer_stats_periode(
                periode, date_debut, date_fin
            )

            self.stdout.write(f'RDV: {stats.nb_rdv_total} (terminés: {stats.nb_rdv_termines})')
            self.stdout.write(f'Tâches: {stats.nb_taches_total} (terminées: {stats.nb_taches_terminees})')
            self.stdout.write(f'Taux RDV: {stats.taux_realisation_rdv:.1f}%')
            self.stdout.write(f'Taux tâches: {stats.taux_realisation_taches:.1f}%')

            self.stdout.write(self.style.SUCCESS('Statistiques calculées avec succès'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))

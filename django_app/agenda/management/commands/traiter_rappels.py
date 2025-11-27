"""
Commande de gestion pour traiter les rappels de RDV et tâches

Utilisation: python manage.py traiter_rappels

Cette commande devrait être exécutée régulièrement via cron (toutes les 5-15 minutes).
"""

from django.core.management.base import BaseCommand
from agenda.services import RappelService


class Command(BaseCommand):
    help = 'Traite les rappels de rendez-vous et tâches à envoyer'

    def handle(self, *args, **options):
        self.stdout.write('Traitement des rappels de RDV...')
        RappelService.traiter_rappels_rdv()
        self.stdout.write(self.style.SUCCESS('Rappels RDV traités'))

        self.stdout.write('Traitement des rappels de tâches...')
        RappelService.traiter_rappels_tache()
        self.stdout.write(self.style.SUCCESS('Rappels tâches traités'))

        self.stdout.write(self.style.SUCCESS('Tous les rappels ont été traités'))

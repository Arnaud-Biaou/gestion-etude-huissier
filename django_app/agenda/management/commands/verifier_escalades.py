"""
Commande de gestion pour vérifier les escalades de tâches en retard

Utilisation: python manage.py verifier_escalades

Cette commande devrait être exécutée quotidiennement pour alerter les admins
des tâches en retard critique.
"""

from django.core.management.base import BaseCommand
from agenda.services import EscaladeService


class Command(BaseCommand):
    help = 'Vérifie et déclenche les escalades pour les tâches en retard critique'

    def handle(self, *args, **options):
        self.stdout.write('Vérification des escalades...')

        try:
            EscaladeService.verifier_escalades()
            self.stdout.write(self.style.SUCCESS('Vérification des escalades terminée'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))

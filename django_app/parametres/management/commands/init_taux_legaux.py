"""
Commande pour initialiser les taux d'intérêt légaux UEMOA 2010-2025
"""
from django.core.management.base import BaseCommand
from parametres.models import TauxLegal
from decimal import Decimal


class Command(BaseCommand):
    help = "Initialise les taux d'intérêt légaux UEMOA 2010-2025"

    def handle(self, *args, **options):
        # Données des taux légaux UEMOA par année
        taux_data = [
            (2010, '6.4800'),
            (2011, '6.2500'),
            (2012, '4.2500'),
            (2013, '4.1141'),
            (2014, '3.7274'),
            (2015, '3.5000'),
            (2016, '3.5000'),
            (2017, '3.5437'),
            (2018, '4.5000'),
            (2019, '4.5000'),
            (2020, '4.5000'),
            (2021, '4.2391'),
            (2022, '4.0000'),
            (2023, '4.2205'),
            (2024, '5.0336'),
            (2025, '5.5000'),
        ]

        created_count = 0
        updated_count = 0

        for annee, taux in taux_data:
            obj, created = TauxLegal.objects.update_or_create(
                annee=annee,
                defaults={'taux': Decimal(taux)}
            )
            if created:
                created_count += 1
                self.stdout.write(f"Créé: {annee} - {taux}%")
            else:
                updated_count += 1
                self.stdout.write(f"Mis à jour: {annee} - {taux}%")

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTaux légaux initialisés avec succès: '
                f'{created_count} créés, {updated_count} mis à jour'
            )
        )

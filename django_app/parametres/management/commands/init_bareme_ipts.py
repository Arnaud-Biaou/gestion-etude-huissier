"""
Commande pour initialiser le barème IPTS par défaut (Bénin 2024)

Usage:
    python manage.py init_bareme_ipts
    python manage.py init_bareme_ipts --force  # Réinitialise même si des tranches existent
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from parametres.models import TrancheIPTS


class Command(BaseCommand):
    help = 'Initialise le barème IPTS par défaut du Bénin (2024)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la réinitialisation même si des tranches existent déjà',
        )

    def handle(self, *args, **options):
        # Vérifier si des tranches existent déjà
        existing_count = TrancheIPTS.objects.count()
        if existing_count > 0 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'{existing_count} tranches IPTS existent déjà. '
                    'Utilisez --force pour réinitialiser.'
                )
            )
            return

        # Barème IPTS 2024 du Bénin (officiel)
        bareme_defaut = [
            (1, 0, 50000, Decimal('0')),
            (2, 50001, 130000, Decimal('10')),
            (3, 130001, 280000, Decimal('15')),
            (4, 280001, 480000, Decimal('19')),
            (5, 480001, 730000, Decimal('24')),
            (6, 730001, 1030000, Decimal('28')),
            (7, 1030001, 1380000, Decimal('32')),
            (8, 1380001, 1880000, Decimal('35')),
            (9, 1880001, 3780000, Decimal('37')),
            (10, 3780001, None, Decimal('40')),
        ]

        self.stdout.write(self.style.MIGRATE_HEADING('Initialisation du barème IPTS 2024...'))
        self.stdout.write('')

        for ordre, montant_min, montant_max, taux in bareme_defaut:
            tranche, created = TrancheIPTS.objects.update_or_create(
                ordre=ordre,
                defaults={
                    'montant_min': montant_min,
                    'montant_max': montant_max,
                    'taux': taux,
                    'est_actif': True,
                    'date_debut': '2024-01-01',
                }
            )

            action = 'Créée' if created else 'Mise à jour'
            if montant_max:
                self.stdout.write(
                    f"  [{action}] Tranche {ordre}: {montant_min:>10,} - {montant_max:>10,} FCFA → {taux:>5}%"
                )
            else:
                self.stdout.write(
                    f"  [{action}] Tranche {ordre}: {montant_min:>10,} - {'∞':>10} FCFA → {taux:>5}%"
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Barème IPTS initialisé avec succès !'))
        self.stdout.write('')

        # Afficher un exemple de calcul
        self.stdout.write(self.style.MIGRATE_HEADING('Exemple de calcul IPTS:'))
        exemples = [50000, 100000, 200000, 500000, 1000000]
        for salaire in exemples:
            ipts = TrancheIPTS.calculer_ipts(salaire)
            self.stdout.write(
                f"  Salaire imposable: {salaire:>12,} FCFA → IPTS: {ipts:>10,} FCFA"
            )

from django.core.management.base import BaseCommand
from parametres.models import EnteteJuridiction


class Command(BaseCommand):
    help = 'Initialise les juridictions du Bénin'

    def handle(self, *args, **options):
        # Niveau 1 : République
        republique, _ = EnteteJuridiction.objects.update_or_create(
            code='REP_BENIN',
            defaults={
                'nom': 'République du Bénin',
                'nom_complet': 'RÉPUBLIQUE DU BÉNIN',
                'niveau': 1,
                'devise': 'Fraternité - Justice - Travail',
                'ordre_affichage': 1,
            }
        )
        self.stdout.write(f"✓ {republique}")

        # Niveau 3 : Cours d'Appel
        cours_appel = [
            ('CA_PARAKOU', 'Cour d\'Appel de Parakou', 'COUR D\'APPEL DE PARAKOU'),
            ('CA_COTONOU', 'Cour d\'Appel de Cotonou', 'COUR D\'APPEL DE COTONOU'),
            ('CA_ABOMEY', 'Cour d\'Appel d\'Abomey', 'COUR D\'APPEL D\'ABOMEY'),
        ]

        for code, nom, nom_complet in cours_appel:
            ca, _ = EnteteJuridiction.objects.update_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'nom_complet': nom_complet,
                    'niveau': 3,
                    'juridiction_superieure': republique,
                    'ordre_affichage': 10,
                }
            )
            self.stdout.write(f"  ✓ {ca}")

        # Niveau 4 : TPI
        ca_parakou = EnteteJuridiction.objects.get(code='CA_PARAKOU')

        tpi_parakou, _ = EnteteJuridiction.objects.update_or_create(
            code='TPI_PARAKOU',
            defaults={
                'nom': 'Tribunal de Première Instance de Parakou',
                'nom_complet': 'TRIBUNAL DE PREMIÈRE INSTANCE DE PREMIÈRE CLASSE DE PARAKOU',
                'niveau': 4,
                'juridiction_superieure': ca_parakou,
                'ordre_affichage': 20,
            }
        )
        self.stdout.write(f"    ✓ {tpi_parakou}")

        # Autres TPI sous Parakou
        autres_tpi = [
            ('TPI_NATITINGOU', 'TPI de Natitingou', 'TRIBUNAL DE PREMIÈRE INSTANCE DE NATITINGOU'),
            ('TPI_KANDI', 'TPI de Kandi', 'TRIBUNAL DE PREMIÈRE INSTANCE DE KANDI'),
        ]

        for code, nom, nom_complet in autres_tpi:
            tpi, _ = EnteteJuridiction.objects.update_or_create(
                code=code,
                defaults={
                    'nom': nom,
                    'nom_complet': nom_complet,
                    'niveau': 4,
                    'juridiction_superieure': ca_parakou,
                    'ordre_affichage': 21,
                }
            )
            self.stdout.write(f"    ✓ {tpi}")

        # CRIET
        criet, _ = EnteteJuridiction.objects.update_or_create(
            code='CRIET',
            defaults={
                'nom': 'CRIET',
                'nom_complet': 'COUR DE RÉPRESSION DES INFRACTIONS ÉCONOMIQUES ET DU TERRORISME',
                'niveau': 2,
                'juridiction_superieure': republique,
                'ordre_affichage': 5,
            }
        )
        self.stdout.write(f"  ✓ {criet}")

        self.stdout.write(self.style.SUCCESS('\nJuridictions initialisées avec succès'))

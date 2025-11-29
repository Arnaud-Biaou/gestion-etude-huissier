"""
Commande de gestion pour initialiser les juridictions du Bénin
"""

from django.core.management.base import BaseCommand
from parametres.models import Juridiction


class Command(BaseCommand):
    help = 'Initialise les juridictions du Bénin'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation des juridictions du Bénin...')

        # ===== COURS D'APPEL =====
        ca_cotonou, created = Juridiction.objects.update_or_create(
            nom_court='CA Cotonou',
            defaults={
                'nom': "Cour d'Appel de Cotonou",
                'type_juridiction': 'cour_appel',
                'ville': 'Cotonou',
                'titre_procureur_general': 'Procureur Général',
                'ordre': 1
            }
        )
        self.stdout.write(f"  {'Créée' if created else 'Mise à jour'}: {ca_cotonou.nom}")

        ca_abomey, created = Juridiction.objects.update_or_create(
            nom_court='CA Abomey',
            defaults={
                'nom': "Cour d'Appel d'Abomey",
                'type_juridiction': 'cour_appel',
                'ville': 'Abomey',
                'titre_procureur_general': 'Procureur Général',
                'ordre': 2
            }
        )
        self.stdout.write(f"  {'Créée' if created else 'Mise à jour'}: {ca_abomey.nom}")

        ca_parakou, created = Juridiction.objects.update_or_create(
            nom_court='CA Parakou',
            defaults={
                'nom': "Cour d'Appel de Parakou",
                'type_juridiction': 'cour_appel',
                'ville': 'Parakou',
                'titre_procureur_general': 'Procureur Général',
                'ordre': 3
            }
        )
        self.stdout.write(f"  {'Créée' if created else 'Mise à jour'}: {ca_parakou.nom}")

        # ===== JURIDICTIONS SPÉCIALES =====
        criet, created = Juridiction.objects.update_or_create(
            nom_court='CRIET',
            defaults={
                'nom': "Cour de Répression des Infractions Économiques et du Terrorisme",
                'type_juridiction': 'cour_speciale',
                'ville': 'Porto-Novo',
                'titre_procureur': 'Procureur Spécial',
                'titre_president': 'Président',
                'ordre': 10
            }
        )
        self.stdout.write(f"  {'Créée' if created else 'Mise à jour'}: {criet.nom}")

        csaf, created = Juridiction.objects.update_or_create(
            nom_court='CSAF',
            defaults={
                'nom': "Cour Spéciale des Affaires Foncières",
                'type_juridiction': 'cour_speciale',
                'ville': 'Cotonou',
                'titre_procureur': 'Procureur Spécial',
                'titre_president': 'Président',
                'ordre': 11
            }
        )
        self.stdout.write(f"  {'Créée' if created else 'Mise à jour'}: {csaf.nom}")

        # ===== TPI RATTACHÉS À PARAKOU =====
        tpi_parakou, created = Juridiction.objects.update_or_create(
            nom_court='TPI Parakou',
            defaults={
                'nom': "Tribunal de Première Instance de Première Classe de Parakou",
                'type_juridiction': 'tpi',
                'classe_tpi': 'premiere',
                'ville': 'Parakou',
                'cour_appel_rattachement': ca_parakou,
                'ordre': 20
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_parakou.nom}")

        tpi_djougou, created = Juridiction.objects.update_or_create(
            nom_court='TPI Djougou',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Djougou",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Djougou',
                'cour_appel_rattachement': ca_parakou,
                'ordre': 21
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_djougou.nom}")

        tpi_kandi, created = Juridiction.objects.update_or_create(
            nom_court='TPI Kandi',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Kandi",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Kandi',
                'cour_appel_rattachement': ca_parakou,
                'ordre': 22
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_kandi.nom}")

        tpi_natitingou, created = Juridiction.objects.update_or_create(
            nom_court='TPI Natitingou',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Natitingou",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Natitingou',
                'cour_appel_rattachement': ca_parakou,
                'ordre': 23
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_natitingou.nom}")

        # ===== TPI RATTACHÉS À COTONOU =====
        tpi_cotonou, created = Juridiction.objects.update_or_create(
            nom_court='TPI Cotonou',
            defaults={
                'nom': "Tribunal de Première Instance de Première Classe de Cotonou",
                'type_juridiction': 'tpi',
                'classe_tpi': 'premiere',
                'ville': 'Cotonou',
                'cour_appel_rattachement': ca_cotonou,
                'ordre': 30
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_cotonou.nom}")

        tpi_porto_novo, created = Juridiction.objects.update_or_create(
            nom_court='TPI Porto-Novo',
            defaults={
                'nom': "Tribunal de Première Instance de Première Classe de Porto-Novo",
                'type_juridiction': 'tpi',
                'classe_tpi': 'premiere',
                'ville': 'Porto-Novo',
                'cour_appel_rattachement': ca_cotonou,
                'ordre': 31
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_porto_novo.nom}")

        tpi_ouidah, created = Juridiction.objects.update_or_create(
            nom_court='TPI Ouidah',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Ouidah",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Ouidah',
                'cour_appel_rattachement': ca_cotonou,
                'ordre': 32
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_ouidah.nom}")

        tpi_lokossa, created = Juridiction.objects.update_or_create(
            nom_court='TPI Lokossa',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Lokossa",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Lokossa',
                'cour_appel_rattachement': ca_cotonou,
                'ordre': 33
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_lokossa.nom}")

        tpi_pobé, created = Juridiction.objects.update_or_create(
            nom_court='TPI Pobè',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Pobè",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Pobè',
                'cour_appel_rattachement': ca_cotonou,
                'ordre': 34
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_pobé.nom}")

        # ===== TPI RATTACHÉS À ABOMEY =====
        tpi_abomey, created = Juridiction.objects.update_or_create(
            nom_court='TPI Abomey',
            defaults={
                'nom': "Tribunal de Première Instance de Première Classe d'Abomey",
                'type_juridiction': 'tpi',
                'classe_tpi': 'premiere',
                'ville': 'Abomey',
                'cour_appel_rattachement': ca_abomey,
                'ordre': 40
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_abomey.nom}")

        tpi_bohicon, created = Juridiction.objects.update_or_create(
            nom_court='TPI Bohicon',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Bohicon",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Bohicon',
                'cour_appel_rattachement': ca_abomey,
                'ordre': 41
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_bohicon.nom}")

        tpi_savalou, created = Juridiction.objects.update_or_create(
            nom_court='TPI Savalou',
            defaults={
                'nom': "Tribunal de Première Instance de Deuxième Classe de Savalou",
                'type_juridiction': 'tpi',
                'classe_tpi': 'deuxieme',
                'ville': 'Savalou',
                'cour_appel_rattachement': ca_abomey,
                'ordre': 42
            }
        )
        self.stdout.write(f"  {'Créé' if created else 'Mis à jour'}: {tpi_savalou.nom}")

        self.stdout.write(self.style.SUCCESS('Juridictions initialisées avec succès!'))

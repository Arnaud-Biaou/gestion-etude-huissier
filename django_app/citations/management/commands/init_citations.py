# -*- coding: utf-8 -*-
"""
Commande d'initialisation du module Citations
Crée les données de référence (localités, autorités, barèmes)
"""

from django.core.management.base import BaseCommand
from citations.models import (
    Localite, BaremeTarifaire, AutoriteRequerante, ConfigurationCitations
)


class Command(BaseCommand):
    help = 'Initialise les données de référence du module Citations'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation du module Citations...')

        # 1. Créer la configuration
        self.stdout.write('  - Configuration...')
        config, created = ConfigurationCitations.objects.get_or_create(pk=1)
        if created:
            self.stdout.write(self.style.SUCCESS('    Configuration créée'))
        else:
            self.stdout.write('    Configuration existante')

        # 2. Créer les autorités requérantes
        self.stdout.write('  - Autorités requérantes...')
        autorites_data = [
            {
                'code': 'CRIET',
                'nom': 'Cour de Répression des Infractions Économiques et du Terrorisme',
                'type_autorite': 'parquet_criet',
                'sigle': 'CRIET',
                'ville': 'Cotonou',
            },
            {
                'code': 'PR-COT',
                'nom': 'Parquet de la République près le TPI de Cotonou',
                'type_autorite': 'parquet_tpi',
                'sigle': 'TPI Cotonou',
                'ville': 'Cotonou',
            },
            {
                'code': 'PR-PAR',
                'nom': 'Parquet de la République près le TPI de Parakou',
                'type_autorite': 'parquet_tpi',
                'sigle': 'TPI Parakou',
                'ville': 'Parakou',
            },
            {
                'code': 'PR-ABK',
                'nom': "Parquet de la République près le TPI d'Abomey-Calavi",
                'type_autorite': 'parquet_tpi',
                'sigle': 'TPI Abomey-Calavi',
                'ville': 'Abomey-Calavi',
            },
            {
                'code': 'PR-PAN',
                'nom': 'Parquet de la République près le TPI de Porto-Novo',
                'type_autorite': 'parquet_tpi',
                'sigle': 'TPI Porto-Novo',
                'ville': 'Porto-Novo',
            },
            {
                'code': 'PG-COT',
                'nom': "Parquet Général près la Cour d'Appel de Cotonou",
                'type_autorite': 'parquet_ca',
                'sigle': 'CA Cotonou',
                'ville': 'Cotonou',
            },
            {
                'code': 'PG-PAR',
                'nom': "Parquet Général près la Cour d'Appel de Parakou",
                'type_autorite': 'parquet_ca',
                'sigle': 'CA Parakou',
                'ville': 'Parakou',
            },
        ]

        for data in autorites_data:
            obj, created = AutoriteRequerante.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(f'    + {obj.sigle}')

        # 3. Créer les barèmes tarifaires
        self.stdout.write('  - Barèmes tarifaires...')
        baremes_data = [
            # Article 81 - Signification
            {'code': 'SIG-ORIG1', 'libelle': 'Premier original', 'type_bareme': 'signification', 'montant': 980, 'article_reference': 'Article 81 - Décret n°2012-143'},
            {'code': 'SIG-ORIG2', 'libelle': 'Deuxième original', 'type_bareme': 'signification', 'montant': 980, 'article_reference': 'Article 81 - Décret n°2012-143'},
            {'code': 'SIG-COPIE', 'libelle': 'Copie supplémentaire', 'type_bareme': 'signification', 'montant': 900, 'article_reference': 'Article 81 - Décret n°2012-143'},
            {'code': 'SIG-MENTION', 'libelle': 'Mention sur répertoire', 'type_bareme': 'signification', 'montant': 25, 'article_reference': 'Article 81 - Décret n°2012-143'},
            {'code': 'SIG-VACATION', 'libelle': 'Vacation', 'type_bareme': 'signification', 'montant': 3000, 'article_reference': 'Article 81 - Décret n°2012-143'},
            # Article 82 - Copie
            {'code': 'COPIE-ROLE', 'libelle': 'Par rôle (42 lignes à 20 syllabes)', 'type_bareme': 'copie', 'montant': 1000, 'article_reference': 'Article 82 - Décret n°2012-143'},
            # Articles 45/89 - Transport
            {'code': 'TRANS-KM', 'libelle': 'Tarif kilométrique', 'type_bareme': 'transport', 'montant': 140, 'article_reference': 'Articles 45 & 89 - Décret n°2012-143', 'distance_min': 20},
            # Décret 2007-155 - Mission
            {'code': 'MISSION-1R', 'libelle': 'Mission 1 repas', 'type_bareme': 'mission', 'montant': 15000, 'article_reference': 'Décret n°2007-155 - Groupe II', 'distance_min': 100},
            {'code': 'MISSION-2R', 'libelle': 'Mission 2 repas', 'type_bareme': 'mission', 'montant': 30000, 'article_reference': 'Décret n°2007-155 - Groupe II', 'distance_min': 100},
            {'code': 'MISSION-JC', 'libelle': 'Mission journée complète', 'type_bareme': 'mission', 'montant': 45000, 'article_reference': 'Décret n°2007-155 - Groupe II', 'distance_min': 100},
            # Article 46 - Séjour
            {'code': 'SEJOUR', 'libelle': 'Indemnité de séjour', 'type_bareme': 'sejour', 'montant': 15000, 'article_reference': 'Article 46 - Décret n°2012-143', 'distance_min': 100},
        ]

        for data in baremes_data:
            obj, created = BaremeTarifaire.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(f'    + {obj.code}')

        # 4. Créer les localités principales du Bénin
        self.stdout.write('  - Localités...')
        localites_data = [
            # Département du Borgou
            {'nom': 'Parakou', 'departement': 'Borgou', 'commune': 'Parakou', 'distance_parakou': 0, 'distance_cotonou': 415},
            {'nom': 'Nikki', 'departement': 'Borgou', 'commune': 'Nikki', 'distance_parakou': 55, 'distance_cotonou': 470},
            {'nom': 'Kalalé', 'departement': 'Borgou', 'commune': 'Kalalé', 'distance_parakou': 90, 'distance_cotonou': 505},
            {'nom': 'Pèrèrè', 'departement': 'Borgou', 'commune': 'Pèrèrè', 'distance_parakou': 65, 'distance_cotonou': 480},
            {'nom': 'Tchaourou', 'departement': 'Borgou', 'commune': 'Tchaourou', 'distance_parakou': 45, 'distance_cotonou': 370},
            {'nom': "N'Dali", 'departement': 'Borgou', 'commune': "N'Dali", 'distance_parakou': 30, 'distance_cotonou': 445},
            {'nom': 'Sinendé', 'departement': 'Borgou', 'commune': 'Sinendé', 'distance_parakou': 85, 'distance_cotonou': 500},
            # Département de l'Alibori
            {'nom': 'Kandi', 'departement': 'Alibori', 'commune': 'Kandi', 'distance_parakou': 140, 'distance_cotonou': 555},
            {'nom': 'Malanville', 'departement': 'Alibori', 'commune': 'Malanville', 'distance_parakou': 200, 'distance_cotonou': 615},
            {'nom': 'Banikoara', 'departement': 'Alibori', 'commune': 'Banikoara', 'distance_parakou': 115, 'distance_cotonou': 530},
            {'nom': 'Karimama', 'departement': 'Alibori', 'commune': 'Karimama', 'distance_parakou': 220, 'distance_cotonou': 635},
            {'nom': 'Gogounou', 'departement': 'Alibori', 'commune': 'Gogounou', 'distance_parakou': 100, 'distance_cotonou': 515},
            {'nom': 'Ségbana', 'departement': 'Alibori', 'commune': 'Ségbana', 'distance_parakou': 160, 'distance_cotonou': 575},
            # Département de l'Atacora
            {'nom': 'Natitingou', 'departement': 'Atacora', 'commune': 'Natitingou', 'distance_parakou': 165, 'distance_cotonou': 580},
            {'nom': 'Boukoumbé', 'departement': 'Atacora', 'commune': 'Boukoumbé', 'distance_parakou': 200, 'distance_cotonou': 615},
            {'nom': 'Tanguiéta', 'departement': 'Atacora', 'commune': 'Tanguiéta', 'distance_parakou': 210, 'distance_cotonou': 625},
            {'nom': 'Matéri', 'departement': 'Atacora', 'commune': 'Matéri', 'distance_parakou': 240, 'distance_cotonou': 655},
            {'nom': 'Cobly', 'departement': 'Atacora', 'commune': 'Cobly', 'distance_parakou': 215, 'distance_cotonou': 630},
            {'nom': 'Kouandé', 'departement': 'Atacora', 'commune': 'Kouandé', 'distance_parakou': 130, 'distance_cotonou': 545},
            {'nom': 'Kérou', 'departement': 'Atacora', 'commune': 'Kérou', 'distance_parakou': 95, 'distance_cotonou': 510},
            {'nom': 'Péhunco', 'departement': 'Atacora', 'commune': 'Péhunco', 'distance_parakou': 110, 'distance_cotonou': 525},
            # Département de la Donga
            {'nom': 'Djougou', 'departement': 'Donga', 'commune': 'Djougou', 'distance_parakou': 130, 'distance_cotonou': 460},
            {'nom': 'Copargo', 'departement': 'Donga', 'commune': 'Copargo', 'distance_parakou': 145, 'distance_cotonou': 475},
            {'nom': 'Bassila', 'departement': 'Donga', 'commune': 'Bassila', 'distance_parakou': 175, 'distance_cotonou': 390},
            {'nom': 'Ouaké', 'departement': 'Donga', 'commune': 'Ouaké', 'distance_parakou': 150, 'distance_cotonou': 480},
            # Département des Collines
            {'nom': 'Dassa-Zoumé', 'departement': 'Collines', 'commune': 'Dassa-Zoumé', 'distance_parakou': 195, 'distance_cotonou': 220},
            {'nom': 'Savalou', 'departement': 'Collines', 'commune': 'Savalou', 'distance_parakou': 225, 'distance_cotonou': 190},
            {'nom': 'Savè', 'departement': 'Collines', 'commune': 'Savè', 'distance_parakou': 165, 'distance_cotonou': 250},
            {'nom': 'Bantè', 'departement': 'Collines', 'commune': 'Bantè', 'distance_parakou': 200, 'distance_cotonou': 280},
            {'nom': 'Glazoué', 'departement': 'Collines', 'commune': 'Glazoué', 'distance_parakou': 180, 'distance_cotonou': 235},
            {'nom': 'Ouèssè', 'departement': 'Collines', 'commune': 'Ouèssè', 'distance_parakou': 145, 'distance_cotonou': 270},
            # Département du Zou
            {'nom': 'Abomey', 'departement': 'Zou', 'commune': 'Abomey', 'distance_parakou': 275, 'distance_cotonou': 140},
            {'nom': 'Bohicon', 'departement': 'Zou', 'commune': 'Bohicon', 'distance_parakou': 280, 'distance_cotonou': 135},
            {'nom': 'Covè', 'departement': 'Zou', 'commune': 'Covè', 'distance_parakou': 250, 'distance_cotonou': 165},
            {'nom': 'Zagnanado', 'departement': 'Zou', 'commune': 'Zagnanado', 'distance_parakou': 235, 'distance_cotonou': 180},
            {'nom': 'Zogbodomey', 'departement': 'Zou', 'commune': 'Zogbodomey', 'distance_parakou': 295, 'distance_cotonou': 120},
            # Département du Littoral
            {'nom': 'Cotonou', 'departement': 'Littoral', 'commune': 'Cotonou', 'distance_parakou': 415, 'distance_cotonou': 0},
            # Département de l'Atlantique
            {'nom': 'Abomey-Calavi', 'departement': 'Atlantique', 'commune': 'Abomey-Calavi', 'distance_parakou': 425, 'distance_cotonou': 12},
            {'nom': 'Ouidah', 'departement': 'Atlantique', 'commune': 'Ouidah', 'distance_parakou': 455, 'distance_cotonou': 40},
            {'nom': 'Allada', 'departement': 'Atlantique', 'commune': 'Allada', 'distance_parakou': 385, 'distance_cotonou': 55},
            {'nom': 'Kpomassè', 'departement': 'Atlantique', 'commune': 'Kpomassè', 'distance_parakou': 440, 'distance_cotonou': 50},
            {'nom': 'Tori-Bossito', 'departement': 'Atlantique', 'commune': 'Tori-Bossito', 'distance_parakou': 395, 'distance_cotonou': 45},
            {'nom': 'Zè', 'departement': 'Atlantique', 'commune': 'Zè', 'distance_parakou': 370, 'distance_cotonou': 70},
            {'nom': 'Sô-Ava', 'departement': 'Atlantique', 'commune': 'Sô-Ava', 'distance_parakou': 440, 'distance_cotonou': 25},
            # Département de l'Ouémé
            {'nom': 'Porto-Novo', 'departement': 'Ouémé', 'commune': 'Porto-Novo', 'distance_parakou': 450, 'distance_cotonou': 35},
            {'nom': 'Sèmè-Podji', 'departement': 'Ouémé', 'commune': 'Sèmè-Podji', 'distance_parakou': 430, 'distance_cotonou': 15},
            {'nom': 'Adjarra', 'departement': 'Ouémé', 'commune': 'Adjarra', 'distance_parakou': 455, 'distance_cotonou': 40},
            {'nom': 'Avrankou', 'departement': 'Ouémé', 'commune': 'Avrankou', 'distance_parakou': 440, 'distance_cotonou': 55},
            {'nom': 'Akpro-Missérété', 'departement': 'Ouémé', 'commune': 'Akpro-Missérété', 'distance_parakou': 435, 'distance_cotonou': 60},
            # Département du Plateau
            {'nom': 'Pobè', 'departement': 'Plateau', 'commune': 'Pobè', 'distance_parakou': 410, 'distance_cotonou': 75},
            {'nom': 'Kétou', 'departement': 'Plateau', 'commune': 'Kétou', 'distance_parakou': 320, 'distance_cotonou': 130},
            {'nom': 'Sakété', 'departement': 'Plateau', 'commune': 'Sakété', 'distance_parakou': 380, 'distance_cotonou': 65},
            {'nom': 'Adja-Ouèrè', 'departement': 'Plateau', 'commune': 'Adja-Ouèrè', 'distance_parakou': 350, 'distance_cotonou': 100},
            {'nom': 'Ifangni', 'departement': 'Plateau', 'commune': 'Ifangni', 'distance_parakou': 395, 'distance_cotonou': 55},
            # Département du Mono
            {'nom': 'Lokossa', 'departement': 'Mono', 'commune': 'Lokossa', 'distance_parakou': 350, 'distance_cotonou': 95},
            {'nom': 'Athiémé', 'departement': 'Mono', 'commune': 'Athiémé', 'distance_parakou': 365, 'distance_cotonou': 105},
            {'nom': 'Comé', 'departement': 'Mono', 'commune': 'Comé', 'distance_parakou': 380, 'distance_cotonou': 85},
            {'nom': 'Grand-Popo', 'departement': 'Mono', 'commune': 'Grand-Popo', 'distance_parakou': 420, 'distance_cotonou': 85},
            {'nom': 'Houéyogbé', 'departement': 'Mono', 'commune': 'Houéyogbé', 'distance_parakou': 390, 'distance_cotonou': 70},
            {'nom': 'Bopa', 'departement': 'Mono', 'commune': 'Bopa', 'distance_parakou': 360, 'distance_cotonou': 90},
            # Département du Couffo
            {'nom': 'Aplahoué', 'departement': 'Couffo', 'commune': 'Aplahoué', 'distance_parakou': 330, 'distance_cotonou': 130},
            {'nom': 'Djakotomey', 'departement': 'Couffo', 'commune': 'Djakotomey', 'distance_parakou': 345, 'distance_cotonou': 115},
            {'nom': 'Dogbo', 'departement': 'Couffo', 'commune': 'Dogbo', 'distance_parakou': 355, 'distance_cotonou': 105},
            {'nom': 'Klouékanmè', 'departement': 'Couffo', 'commune': 'Klouékanmè', 'distance_parakou': 340, 'distance_cotonou': 120},
            {'nom': 'Lalo', 'departement': 'Couffo', 'commune': 'Lalo', 'distance_parakou': 325, 'distance_cotonou': 135},
            {'nom': 'Toviklin', 'departement': 'Couffo', 'commune': 'Toviklin', 'distance_parakou': 335, 'distance_cotonou': 125},
        ]

        for data in localites_data:
            obj, created = Localite.objects.get_or_create(
                nom=data['nom'],
                commune=data['commune'],
                defaults=data
            )
            if created:
                self.stdout.write(f'    + {obj.nom} ({obj.departement})')

        self.stdout.write(self.style.SUCCESS('\nModule Citations initialisé avec succès!'))
        self.stdout.write(f'  - {AutoriteRequerante.objects.count()} autorités requérantes')
        self.stdout.write(f'  - {BaremeTarifaire.objects.count()} barèmes tarifaires')
        self.stdout.write(f'  - {Localite.objects.count()} localités')

from django.core.management.base import BaseCommand
from gestion.models import Collaborateur, ActeProcedure, TauxLegal, Utilisateur


class Command(BaseCommand):
    help = 'Initialise les données de base'

    def handle(self, *args, **options):
        # Créer l'utilisateur admin
        if not Utilisateur.objects.filter(username='admin').exists():
            admin = Utilisateur.objects.create_superuser(
                username='admin',
                email='mab@etude-biaou.bj',
                password='admin123',
                first_name='BIAOU',
                last_name='Martial Arnaud',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Utilisateur admin créé'))

        # Créer les collaborateurs
        collaborateurs_data = [
            {'nom': 'Me BIAOU Martial', 'role': 'huissier', 'email': 'biaou.martial@etude-biaou.bj'},
            {'nom': 'ADJOVI Carine', 'role': 'clerc_principal', 'email': 'adjovi.carine@etude-biaou.bj'},
            {'nom': 'HOUNKPATIN Paul', 'role': 'clerc', 'email': 'hounkpatin.paul@etude-biaou.bj'},
            {'nom': 'DOSSOU Marie', 'role': 'secretaire', 'email': 'dossou.marie@etude-biaou.bj'},
        ]

        for data in collaborateurs_data:
            Collaborateur.objects.get_or_create(nom=data['nom'], defaults=data)

        self.stdout.write(self.style.SUCCESS(f'{len(collaborateurs_data)} collaborateurs créés/vérifiés'))

        # Créer les actes de procédure
        actes_data = [
            {'code': 'cmd', 'libelle': 'Commandement de payer', 'tarif': 15000},
            {'code': 'sign_titre', 'libelle': 'Signification de titre exécutoire', 'tarif': 10000},
            {'code': 'pv_saisie', 'libelle': 'PV de Saisie-Vente', 'tarif': 25000},
            {'code': 'pv_carence', 'libelle': 'PV de Carence', 'tarif': 15000},
            {'code': 'denonc', 'libelle': 'Dénonciation de saisie', 'tarif': 12000},
            {'code': 'assign', 'libelle': 'Assignation', 'tarif': 20000},
            {'code': 'sign_ord', 'libelle': 'Signification Ordonnance', 'tarif': 10000},
            {'code': 'certif', 'libelle': 'Certificat de non recours', 'tarif': 5000},
            {'code': 'mainlevee', 'libelle': 'Mainlevée', 'tarif': 15000},
            {'code': 'sommation', 'libelle': 'Sommation interpellative', 'tarif': 12000},
            {'code': 'constat', 'libelle': 'Procès-verbal de constat', 'tarif': 30000},
        ]

        for data in actes_data:
            ActeProcedure.objects.get_or_create(code=data['code'], defaults=data)

        self.stdout.write(self.style.SUCCESS(f'{len(actes_data)} actes de procédure créés/vérifiés'))

        # Créer les taux légaux UEMOA
        taux_data = {
            2010: 6.4800, 2011: 6.2500, 2012: 4.2500, 2013: 4.1141, 2014: 3.7274,
            2015: 3.5000, 2016: 3.5000, 2017: 3.5437, 2018: 4.5000, 2019: 4.5000,
            2020: 4.5000, 2021: 4.2391, 2022: 4.0000, 2023: 4.2205, 2024: 5.0336,
            2025: 5.5000
        }

        for annee, taux in taux_data.items():
            TauxLegal.objects.get_or_create(annee=annee, defaults={'taux': taux})

        self.stdout.write(self.style.SUCCESS(f'{len(taux_data)} taux légaux créés/vérifiés'))

        self.stdout.write(self.style.SUCCESS('Initialisation terminée !'))

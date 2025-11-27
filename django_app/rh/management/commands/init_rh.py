"""
Commande d'initialisation des données RH
Conforme à la législation béninoise
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from rh.models import (
    CategorieEmploye, Poste, Site,
    TypeConge, TypeAbsence, TypeSanction,
    ElementPaie, CritereEvaluation,
    ConfigurationRH
)


class Command(BaseCommand):
    help = 'Initialise les données de base du module RH (catégories, postes, types de congés, etc.)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Initialisation des données RH...'))

        # Configuration RH
        self.init_configuration()

        # Catégories professionnelles
        self.init_categories()

        # Postes
        self.init_postes()

        # Sites
        self.init_sites()

        # Types de congés
        self.init_types_conge()

        # Types d'absences
        self.init_types_absence()

        # Types de sanctions
        self.init_types_sanction()

        # Éléments de paie
        self.init_elements_paie()

        # Critères d'évaluation
        self.init_criteres_evaluation()

        self.stdout.write(self.style.SUCCESS('Initialisation RH terminée avec succès!'))

    def init_configuration(self):
        """Initialise la configuration RH"""
        config, created = ConfigurationRH.objects.get_or_create(pk=1)
        if created:
            config.nom_entreprise = "Étude d'Huissier de Justice BIAOU"
            config.adresse_entreprise = "Cotonou, Bénin"
            config.save()
            self.stdout.write(self.style.SUCCESS('  - Configuration RH créée'))
        else:
            self.stdout.write('  - Configuration RH existante')

    def init_categories(self):
        """Initialise les catégories professionnelles"""
        categories = [
            {'code': 'CAT1', 'libelle': 'Ouvrier/Manoeuvre', 'niveau': 1, 'coefficient': Decimal('100'),
             'salaire_minimum': Decimal('52000'), 'duree_essai_mois': 1},
            {'code': 'CAT2', 'libelle': 'Employé qualifié', 'niveau': 2, 'coefficient': Decimal('120'),
             'salaire_minimum': Decimal('65000'), 'duree_essai_mois': 1},
            {'code': 'CAT3', 'libelle': 'Technicien', 'niveau': 3, 'coefficient': Decimal('150'),
             'salaire_minimum': Decimal('85000'), 'duree_essai_mois': 2},
            {'code': 'CAT4', 'libelle': 'Agent de maîtrise', 'niveau': 4, 'coefficient': Decimal('180'),
             'salaire_minimum': Decimal('120000'), 'duree_essai_mois': 2},
            {'code': 'CAT5', 'libelle': 'Cadre', 'niveau': 5, 'coefficient': Decimal('250'),
             'salaire_minimum': Decimal('180000'), 'duree_essai_mois': 3},
            {'code': 'CAT6', 'libelle': 'Cadre supérieur', 'niveau': 6, 'coefficient': Decimal('350'),
             'salaire_minimum': Decimal('300000'), 'duree_essai_mois': 3},
        ]

        for cat_data in categories:
            cat, created = CategorieEmploye.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"  - Catégorie {cat.code} créée")

    def init_postes(self):
        """Initialise les postes de l'étude"""
        # Récupérer les catégories
        cat1 = CategorieEmploye.objects.filter(code='CAT1').first()
        cat2 = CategorieEmploye.objects.filter(code='CAT2').first()
        cat3 = CategorieEmploye.objects.filter(code='CAT3').first()
        cat4 = CategorieEmploye.objects.filter(code='CAT4').first()
        cat5 = CategorieEmploye.objects.filter(code='CAT5').first()
        cat6 = CategorieEmploye.objects.filter(code='CAT6').first()

        postes = [
            {'code': 'HUISSIER', 'libelle': 'Huissier de Justice', 'categorie': cat6,
             'description': 'Huissier titulaire ou associé'},
            {'code': 'CLERC_PRINC', 'libelle': 'Clerc Principal', 'categorie': cat5,
             'description': 'Clerc responsable de service'},
            {'code': 'CLERC', 'libelle': 'Clerc', 'categorie': cat4,
             'description': 'Clerc d\'huissier'},
            {'code': 'SECRETAIRE', 'libelle': 'Secrétaire', 'categorie': cat3,
             'description': 'Secrétaire de l\'étude'},
            {'code': 'COMPTABLE', 'libelle': 'Comptable', 'categorie': cat4,
             'description': 'Responsable comptabilité'},
            {'code': 'AGENT_REC', 'libelle': 'Agent de recouvrement', 'categorie': cat3,
             'description': 'Agent de terrain pour le recouvrement'},
            {'code': 'CHAUFFEUR', 'libelle': 'Chauffeur', 'categorie': cat2,
             'description': 'Chauffeur de l\'étude'},
            {'code': 'COURSIER', 'libelle': 'Coursier', 'categorie': cat2,
             'description': 'Coursier pour significations'},
            {'code': 'GARDIEN', 'libelle': 'Gardien', 'categorie': cat1,
             'description': 'Agent de sécurité'},
            {'code': 'MENAGE', 'libelle': 'Agent d\'entretien', 'categorie': cat1,
             'description': 'Personnel d\'entretien'},
            {'code': 'STAGIAIRE', 'libelle': 'Stagiaire', 'categorie': cat1,
             'description': 'Stagiaire de l\'étude'},
        ]

        for poste_data in postes:
            if poste_data['categorie']:
                poste, created = Poste.objects.get_or_create(
                    code=poste_data['code'],
                    defaults=poste_data
                )
                if created:
                    self.stdout.write(f"  - Poste {poste.code} créé")

    def init_sites(self):
        """Initialise les sites"""
        sites = [
            {'nom': 'Siège Principal', 'adresse': 'Cotonou, Bénin', 'est_principal': True},
        ]

        for site_data in sites:
            site, created = Site.objects.get_or_create(
                nom=site_data['nom'],
                defaults=site_data
            )
            if created:
                self.stdout.write(f"  - Site {site.nom} créé")

    def init_types_conge(self):
        """Initialise les types de congés selon le Code du travail béninois"""
        types_conge = [
            {'code': 'CP', 'libelle': 'Congé payé annuel', 'duree_max': 30, 'est_paye': True,
             'decompte_solde': True, 'description': '2 jours ouvrables par mois travaillé'},
            {'code': 'MAT', 'libelle': 'Congé de maternité', 'duree_max': 98, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '14 semaines (6 avant + 8 après accouchement)'},
            {'code': 'PAT', 'libelle': 'Congé de paternité', 'duree_max': 3, 'est_paye': True,
             'decompte_solde': False, 'description': '3 jours pour la naissance'},
            {'code': 'MAR', 'libelle': 'Congé mariage employé', 'duree_max': 3, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '3 jours pour le mariage de l\'employé'},
            {'code': 'MAR_ENF', 'libelle': 'Congé mariage enfant', 'duree_max': 1, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '1 jour pour le mariage d\'un enfant'},
            {'code': 'NAIS', 'libelle': 'Congé naissance', 'duree_max': 3, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '3 jours pour la naissance d\'un enfant'},
            {'code': 'DEC_CJ', 'libelle': 'Congé décès conjoint/enfant', 'duree_max': 5, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '5 jours pour le décès du conjoint ou d\'un enfant'},
            {'code': 'DEC_PAR', 'libelle': 'Congé décès parent', 'duree_max': 3, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': '3 jours pour le décès d\'un parent ou beau-parent'},
            {'code': 'MAL', 'libelle': 'Congé maladie', 'duree_max': None, 'est_paye': True,
             'decompte_solde': False, 'justificatif_requis': True,
             'description': 'Congé sur certificat médical'},
            {'code': 'SS', 'libelle': 'Congé sans solde', 'duree_max': None, 'est_paye': False,
             'decompte_solde': False,
             'description': 'Congé non rémunéré sur demande'},
            {'code': 'PERM', 'libelle': 'Permission d\'absence', 'duree_max': 2, 'est_paye': True,
             'decompte_solde': False,
             'description': 'Permission exceptionnelle'},
        ]

        for type_data in types_conge:
            type_conge, created = TypeConge.objects.get_or_create(
                code=type_data['code'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f"  - Type congé {type_conge.code} créé")

    def init_types_absence(self):
        """Initialise les types d'absences"""
        types_absence = [
            {'code': 'MAL_NJ', 'libelle': 'Maladie non justifiée', 'impacte_salaire': True,
             'taux_retenue': Decimal('100')},
            {'code': 'MAL_J', 'libelle': 'Maladie justifiée', 'impacte_salaire': False,
             'taux_retenue': Decimal('0')},
            {'code': 'ABS_NJ', 'libelle': 'Absence injustifiée', 'impacte_salaire': True,
             'taux_retenue': Decimal('100')},
            {'code': 'RETARD', 'libelle': 'Retard', 'impacte_salaire': True,
             'taux_retenue': Decimal('50')},
            {'code': 'AT', 'libelle': 'Accident de travail', 'impacte_salaire': False,
             'taux_retenue': Decimal('0')},
            {'code': 'GREVE', 'libelle': 'Grève', 'impacte_salaire': True,
             'taux_retenue': Decimal('100')},
        ]

        for type_data in types_absence:
            type_abs, created = TypeAbsence.objects.get_or_create(
                code=type_data['code'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f"  - Type absence {type_abs.code} créé")

    def init_types_sanction(self):
        """Initialise les types de sanctions selon le Code du travail béninois"""
        types_sanction = [
            {'code': 'AVERT_VERB', 'libelle': 'Avertissement verbal', 'niveau': 1,
             'duree_max_jours': None, 'description': 'Rappel à l\'ordre oral'},
            {'code': 'AVERT_ECRIT', 'libelle': 'Avertissement écrit', 'niveau': 1,
             'duree_max_jours': None, 'description': 'Rappel à l\'ordre écrit',
             'procedure': 'Notification écrite avec accusé de réception'},
            {'code': 'BLAME', 'libelle': 'Blâme', 'niveau': 2,
             'duree_max_jours': None, 'description': 'Blâme inscrit au dossier',
             'procedure': 'Notification écrite après entretien'},
            {'code': 'MISE_PIED', 'libelle': 'Mise à pied disciplinaire', 'niveau': 3,
             'duree_max_jours': 8, 'description': 'Suspension sans solde (max 8 jours)',
             'procedure': 'Convocation, entretien, notification écrite avec délai de réponse'},
            {'code': 'LIC_SIMPLE', 'libelle': 'Licenciement pour faute simple', 'niveau': 4,
             'duree_max_jours': None, 'description': 'Licenciement avec préavis',
             'procedure': 'Procédure complète de licenciement avec préavis'},
            {'code': 'LIC_GRAVE', 'libelle': 'Licenciement pour faute grave', 'niveau': 4,
             'duree_max_jours': None, 'description': 'Licenciement sans préavis ni indemnités',
             'procedure': 'Procédure de licenciement pour faute grave'},
            {'code': 'LIC_LOURDE', 'libelle': 'Licenciement pour faute lourde', 'niveau': 4,
             'duree_max_jours': None, 'description': 'Licenciement immédiat pour faute intentionnelle',
             'procedure': 'Procédure de licenciement pour faute lourde'},
        ]

        for type_data in types_sanction:
            type_sanc, created = TypeSanction.objects.get_or_create(
                code=type_data['code'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f"  - Type sanction {type_sanc.code} créé")

    def init_elements_paie(self):
        """Initialise les éléments de paie"""
        elements = [
            # Gains
            {'code': 'PRIME_ANC', 'libelle': 'Prime d\'ancienneté', 'type_element': 'gain',
             'nature': 'prime_anciennete', 'est_imposable': True, 'est_cotisable': True},
            {'code': 'PRIME_RESP', 'libelle': 'Prime de responsabilité', 'type_element': 'gain',
             'nature': 'prime_responsabilite', 'est_imposable': True, 'est_cotisable': True},
            {'code': 'PRIME_REND', 'libelle': 'Prime de rendement', 'type_element': 'gain',
             'nature': 'prime_rendement', 'est_imposable': True, 'est_cotisable': True},
            {'code': 'PRIME_DEPL', 'libelle': 'Prime de déplacement', 'type_element': 'gain',
             'nature': 'prime_deplacement', 'est_imposable': True, 'est_cotisable': False},
            {'code': 'PRIME_TRANS', 'libelle': 'Indemnité de transport', 'type_element': 'gain',
             'nature': 'prime_transport', 'est_imposable': False, 'est_cotisable': False},
            {'code': 'HS', 'libelle': 'Heures supplémentaires', 'type_element': 'gain',
             'nature': 'heures_sup', 'est_imposable': True, 'est_cotisable': True},
            {'code': 'IND_LOG', 'libelle': 'Indemnité de logement', 'type_element': 'gain',
             'nature': 'indemnite_logement', 'est_imposable': True, 'est_cotisable': True},
            {'code': 'AVN', 'libelle': 'Avantage en nature', 'type_element': 'gain',
             'nature': 'avantage_nature', 'est_imposable': True, 'est_cotisable': True},
            # Retenues
            {'code': 'CNSS_SAL', 'libelle': 'Cotisation CNSS salariale', 'type_element': 'retenue',
             'nature': 'cnss_salariale', 'est_imposable': False, 'est_cotisable': False,
             'taux': Decimal('3.6')},
            {'code': 'IPTS', 'libelle': 'IPTS', 'type_element': 'retenue',
             'nature': 'ipts', 'est_imposable': False, 'est_cotisable': False},
            {'code': 'AVS', 'libelle': 'Avance sur salaire', 'type_element': 'retenue',
             'nature': 'avance_salaire', 'est_imposable': False, 'est_cotisable': False},
            {'code': 'PRET', 'libelle': 'Remboursement prêt', 'type_element': 'retenue',
             'nature': 'pret', 'est_imposable': False, 'est_cotisable': False},
            {'code': 'RET_ABS', 'libelle': 'Retenue pour absence', 'type_element': 'retenue',
             'nature': 'absence', 'est_imposable': False, 'est_cotisable': False},
        ]

        for elem_data in elements:
            elem, created = ElementPaie.objects.get_or_create(
                code=elem_data['code'],
                defaults=elem_data
            )
            if created:
                self.stdout.write(f"  - Élément paie {elem.code} créé")

    def init_criteres_evaluation(self):
        """Initialise les critères d'évaluation"""
        criteres = [
            {'code': 'PONCT', 'libelle': 'Ponctualité et assiduité', 'coefficient': Decimal('1.0'),
             'description': 'Respect des horaires et présence régulière'},
            {'code': 'QUALITE', 'libelle': 'Qualité du travail', 'coefficient': Decimal('1.5'),
             'description': 'Qualité et rigueur dans l\'exécution des tâches'},
            {'code': 'PRODUC', 'libelle': 'Productivité', 'coefficient': Decimal('1.5'),
             'description': 'Volume de travail accompli'},
            {'code': 'INIT', 'libelle': 'Initiative et autonomie', 'coefficient': Decimal('1.0'),
             'description': 'Capacité à prendre des initiatives'},
            {'code': 'COLLAB', 'libelle': 'Esprit d\'équipe', 'coefficient': Decimal('1.0'),
             'description': 'Collaboration avec les collègues'},
            {'code': 'COMM', 'libelle': 'Communication', 'coefficient': Decimal('1.0'),
             'description': 'Qualité de communication orale et écrite'},
            {'code': 'DISCIP', 'libelle': 'Discipline', 'coefficient': Decimal('1.0'),
             'description': 'Respect des règles et procédures'},
            {'code': 'ADAPT', 'libelle': 'Adaptabilité', 'coefficient': Decimal('0.5'),
             'description': 'Capacité d\'adaptation aux changements'},
        ]

        for critere_data in criteres:
            critere, created = CritereEvaluation.objects.get_or_create(
                code=critere_data['code'],
                defaults=critere_data
            )
            if created:
                self.stdout.write(f"  - Critère {critere.code} créé")

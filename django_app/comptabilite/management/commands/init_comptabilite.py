"""
Commande pour initialiser le plan comptable OHADA et les données de base
pour une étude d'huissier de justice.
"""
from django.core.management.base import BaseCommand
from comptabilite.models import (
    CompteComptable, Journal, TypeOperation, ConfigurationComptable
)


class Command(BaseCommand):
    help = 'Initialise le plan comptable OHADA et les données de base pour le module comptabilité'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation du module comptabilité...\n')

        # Créer les comptes comptables OHADA
        self.creer_plan_comptable()

        # Créer les journaux
        self.creer_journaux()

        # Créer les types d'opérations pour le mode facile
        self.creer_types_operations()

        # Créer la configuration
        ConfigurationComptable.get_instance()

        self.stdout.write(self.style.SUCCESS('\nInitialisation terminée avec succès !'))

    def creer_plan_comptable(self):
        """Crée le plan comptable OHADA adapté pour une étude d'huissier"""
        self.stdout.write('Création du plan comptable OHADA...')

        comptes = [
            # CLASSE 1 - CAPITAUX
            ('10', 'Capital', 'crediteur', 'Capital social et individuel'),
            ('101', 'Capital social', 'crediteur', 'Capital social de l\'étude'),
            ('109', 'Actionnaires, capital souscrit non appelé', 'debiteur', ''),
            ('11', 'Réserves', 'crediteur', 'Réserves légales et statutaires'),
            ('111', 'Réserve légale', 'crediteur', ''),
            ('118', 'Autres réserves', 'crediteur', ''),
            ('12', 'Report à nouveau', 'crediteur', 'Résultats non distribués des exercices antérieurs'),
            ('120', 'Report à nouveau créditeur', 'crediteur', 'Bénéfices antérieurs non distribués'),
            ('129', 'Report à nouveau débiteur', 'debiteur', 'Pertes antérieures'),
            ('13', 'Résultat net de l\'exercice', 'crediteur', 'Résultat de l\'exercice en cours'),
            ('130', 'Résultat net: bénéfice', 'crediteur', ''),
            ('139', 'Résultat net: perte', 'debiteur', ''),
            ('16', 'Emprunts et dettes assimilées', 'crediteur', 'Dettes financières'),
            ('162', 'Emprunts auprès des établissements de crédit', 'crediteur', 'Emprunts bancaires'),
            ('164', 'Dettes financières diverses', 'crediteur', ''),

            # CLASSE 2 - IMMOBILISATIONS
            ('21', 'Immobilisations incorporelles', 'debiteur', 'Actifs incorporels'),
            ('213', 'Logiciels', 'debiteur', 'Logiciels et applications'),
            ('22', 'Terrains', 'debiteur', ''),
            ('23', 'Bâtiments', 'debiteur', 'Constructions'),
            ('231', 'Bâtiments administratifs', 'debiteur', 'Locaux de l\'étude'),
            ('24', 'Matériel', 'debiteur', 'Matériel et outillage'),
            ('241', 'Matériel et outillage', 'debiteur', ''),
            ('244', 'Matériel de bureau', 'debiteur', 'Ordinateurs, imprimantes...'),
            ('245', 'Matériel de transport', 'debiteur', 'Véhicules de l\'étude'),
            ('246', 'Mobilier de bureau', 'debiteur', 'Bureaux, chaises, armoires...'),
            ('28', 'Amortissements', 'crediteur', 'Amortissements des immobilisations'),
            ('281', 'Amortissements des immobilisations incorporelles', 'crediteur', ''),
            ('283', 'Amortissements des bâtiments', 'crediteur', ''),
            ('284', 'Amortissements du matériel', 'crediteur', ''),

            # CLASSE 3 - STOCKS
            ('31', 'Fournitures de bureau', 'debiteur', 'Stock de fournitures'),
            ('32', 'Autres approvisionnements', 'debiteur', ''),

            # CLASSE 4 - TIERS
            ('40', 'Fournisseurs et comptes rattachés', 'crediteur', 'Dettes fournisseurs'),
            ('401', 'Fournisseurs', 'crediteur', 'Dettes envers les fournisseurs'),
            ('4011', 'Fournisseurs - Achats de biens', 'crediteur', ''),
            ('4012', 'Fournisseurs - Prestations de services', 'crediteur', ''),
            ('408', 'Fournisseurs - Factures non parvenues', 'crediteur', ''),
            ('41', 'Clients et comptes rattachés', 'debiteur', 'Créances clients'),
            ('411', 'Clients', 'debiteur', 'Créances sur les clients'),
            ('4111', 'Clients - Honoraires', 'debiteur', 'Créances honoraires'),
            ('4112', 'Clients - Émoluments', 'debiteur', 'Créances émoluments'),
            ('4113', 'Clients - Consignations', 'debiteur', 'Consignations reçues des clients'),
            ('418', 'Clients - Produits à recevoir', 'debiteur', ''),
            ('419', 'Clients créditeurs', 'crediteur', 'Avances et acomptes reçus'),
            ('42', 'Personnel', 'debiteur', 'Comptes du personnel'),
            ('421', 'Personnel - Rémunérations dues', 'crediteur', 'Salaires à payer'),
            ('422', 'Personnel - Avances et acomptes', 'debiteur', ''),
            ('43', 'Organismes sociaux', 'crediteur', 'Charges sociales'),
            ('431', 'CNSS', 'crediteur', 'Cotisations CNSS'),
            ('44', 'État et collectivités', 'crediteur', 'Dettes fiscales'),
            ('441', 'État - Impôt sur les bénéfices', 'crediteur', ''),
            ('442', 'État - Autres impôts et taxes', 'crediteur', ''),
            ('443', 'État - TVA facturée', 'crediteur', 'TVA collectée sur les ventes'),
            ('4431', 'TVA collectée', 'crediteur', ''),
            ('445', 'État - TVA récupérable', 'debiteur', 'TVA déductible sur achats'),
            ('4451', 'TVA récupérable sur immobilisations', 'debiteur', ''),
            ('4452', 'TVA récupérable sur achats', 'debiteur', ''),
            ('4453', 'TVA récupérable sur services', 'debiteur', ''),
            ('447', 'État - Impôts retenus à la source', 'crediteur', 'Retenues à la source'),
            ('449', 'État - Charges à payer et produits à recevoir', 'crediteur', ''),
            ('46', 'Débiteurs et créditeurs divers', 'debiteur', ''),
            ('462', 'Créances sur cessions d\'immobilisations', 'debiteur', ''),
            ('467', 'Débiteurs divers', 'debiteur', ''),
            ('47', 'Comptes transitoires', 'debiteur', ''),
            ('471', 'Comptes d\'attente', 'debiteur', 'Opérations en attente de régularisation'),
            ('472', 'Consignations', 'crediteur', 'Fonds de consignation des clients'),
            ('4721', 'Consignations clients', 'crediteur', 'Fonds consignés par les clients'),
            ('4722', 'Consignations à reverser', 'crediteur', 'Montants à reverser aux créanciers'),

            # CLASSE 5 - TRÉSORERIE
            ('52', 'Banques', 'debiteur', 'Comptes bancaires'),
            ('521', 'Banques locales', 'debiteur', 'Comptes dans les banques locales'),
            ('5211', 'Banque principale', 'debiteur', 'Compte bancaire principal'),
            ('5212', 'Banque secondaire', 'debiteur', ''),
            ('53', 'Établissements financiers', 'debiteur', ''),
            ('54', 'Instruments de trésorerie', 'debiteur', ''),
            ('57', 'Caisse', 'debiteur', 'Caisse de l\'étude'),
            ('571', 'Caisse siège social', 'debiteur', 'Caisse principale'),
            ('58', 'Régies d\'avances et accréditifs', 'debiteur', ''),
            ('585', 'Régies d\'avances', 'debiteur', 'Avances pour frais'),
            ('59', 'Dépréciations et provisions', 'crediteur', ''),

            # CLASSE 6 - CHARGES
            ('60', 'Achats', 'debiteur', 'Achats de biens et services'),
            ('601', 'Achats de fournitures de bureau', 'debiteur', 'Fournitures, papeterie'),
            ('602', 'Achats de petit matériel', 'debiteur', ''),
            ('604', 'Achats de prestations de services', 'debiteur', ''),
            ('605', 'Achats de matières et fournitures', 'debiteur', ''),
            ('608', 'Frais accessoires sur achats', 'debiteur', ''),
            ('61', 'Services extérieurs', 'debiteur', 'Charges externes'),
            ('612', 'Redevances de crédit-bail', 'debiteur', 'Leasing'),
            ('613', 'Locations', 'debiteur', ''),
            ('6131', 'Locations immobilières', 'debiteur', 'Loyer des locaux'),
            ('6132', 'Locations de matériel', 'debiteur', ''),
            ('614', 'Charges locatives', 'debiteur', ''),
            ('615', 'Entretien et réparations', 'debiteur', ''),
            ('6151', 'Entretien des locaux', 'debiteur', ''),
            ('6155', 'Entretien du matériel', 'debiteur', ''),
            ('616', 'Primes d\'assurances', 'debiteur', 'Assurances professionnelles'),
            ('617', 'Études et recherches', 'debiteur', ''),
            ('618', 'Autres services extérieurs', 'debiteur', ''),
            ('62', 'Autres services extérieurs', 'debiteur', ''),
            ('621', 'Personnel extérieur', 'debiteur', 'Intérimaires, sous-traitance'),
            ('622', 'Rémunérations d\'intermédiaires', 'debiteur', 'Honoraires, commissions'),
            ('6221', 'Commissions et courtages', 'debiteur', ''),
            ('6226', 'Honoraires', 'debiteur', 'Honoraires expert-comptable, avocat...'),
            ('623', 'Publicité et relations publiques', 'debiteur', ''),
            ('624', 'Transports', 'debiteur', ''),
            ('6241', 'Transports sur achats', 'debiteur', ''),
            ('6242', 'Transports sur ventes', 'debiteur', ''),
            ('625', 'Déplacements, missions et réceptions', 'debiteur', 'Frais de déplacement'),
            ('6251', 'Voyages et déplacements', 'debiteur', ''),
            ('6252', 'Missions', 'debiteur', ''),
            ('6253', 'Réceptions', 'debiteur', ''),
            ('6254', 'Frais de carburant', 'debiteur', 'Carburant véhicules'),
            ('626', 'Frais postaux et de télécommunications', 'debiteur', ''),
            ('6261', 'Frais postaux', 'debiteur', 'Timbres, envois postaux'),
            ('6262', 'Téléphone', 'debiteur', 'Téléphone, internet'),
            ('627', 'Services bancaires', 'debiteur', 'Frais bancaires'),
            ('628', 'Autres services', 'debiteur', ''),
            ('63', 'Impôts et taxes', 'debiteur', 'Impôts et taxes'),
            ('631', 'Impôts et taxes directs', 'debiteur', ''),
            ('6311', 'Patente', 'debiteur', ''),
            ('6312', 'Taxes foncières', 'debiteur', ''),
            ('632', 'Impôts et taxes indirects', 'debiteur', ''),
            ('635', 'Autres impôts et taxes', 'debiteur', ''),
            ('64', 'Charges de personnel', 'debiteur', 'Salaires et charges sociales'),
            ('641', 'Rémunérations du personnel', 'debiteur', 'Salaires'),
            ('6411', 'Salaires', 'debiteur', ''),
            ('6412', 'Primes et gratifications', 'debiteur', ''),
            ('6413', 'Congés payés', 'debiteur', ''),
            ('645', 'Charges sociales', 'debiteur', ''),
            ('6451', 'Cotisations CNSS', 'debiteur', ''),
            ('6452', 'Cotisations aux caisses de retraite', 'debiteur', ''),
            ('646', 'Rémunérations de l\'exploitant', 'debiteur', 'Rémunération huissier'),
            ('647', 'Autres charges sociales', 'debiteur', ''),
            ('65', 'Autres charges des activités ordinaires', 'debiteur', ''),
            ('651', 'Pertes sur créances clients', 'debiteur', 'Créances irrécouvrables'),
            ('658', 'Charges diverses', 'debiteur', ''),
            ('66', 'Charges financières', 'debiteur', 'Charges financières'),
            ('661', 'Intérêts des emprunts', 'debiteur', ''),
            ('664', 'Pertes de change', 'debiteur', ''),
            ('67', 'Charges HAO', 'debiteur', 'Charges hors activités ordinaires'),
            ('671', 'Intérêts moratoires', 'debiteur', ''),
            ('68', 'Dotations aux amortissements', 'debiteur', 'Amortissements'),
            ('681', 'Dotations aux amortissements', 'debiteur', ''),
            ('6811', 'Dotations aux amortissements des immobilisations', 'debiteur', ''),
            ('69', 'Impôts sur le résultat', 'debiteur', 'Impôt sur les sociétés'),
            ('691', 'Impôts sur les bénéfices', 'debiteur', ''),

            # CLASSE 7 - PRODUITS
            ('70', 'Ventes', 'crediteur', 'Chiffre d\'affaires'),
            ('706', 'Services vendus', 'crediteur', 'Prestations de services'),
            ('7061', 'Honoraires', 'crediteur', 'Honoraires perçus'),
            ('7062', 'Émoluments', 'crediteur', 'Émoluments perçus'),
            ('7063', 'Frais de recouvrement', 'crediteur', 'Frais de recouvrement perçus'),
            ('7064', 'Frais de constat', 'crediteur', 'Honoraires de constat'),
            ('7065', 'Frais de signification', 'crediteur', 'Frais de signification d\'actes'),
            ('7066', 'Droits de greffe', 'crediteur', 'Droits perçus pour dépôt'),
            ('7068', 'Autres prestations', 'crediteur', ''),
            ('71', 'Production stockée', 'crediteur', ''),
            ('72', 'Production immobilisée', 'crediteur', ''),
            ('73', 'Variations des stocks', 'crediteur', ''),
            ('75', 'Autres produits', 'crediteur', 'Autres produits d\'exploitation'),
            ('758', 'Produits divers', 'crediteur', ''),
            ('76', 'Produits financiers', 'crediteur', 'Produits financiers'),
            ('761', 'Intérêts de placements', 'crediteur', ''),
            ('764', 'Gains de change', 'crediteur', ''),
            ('77', 'Produits HAO', 'crediteur', 'Produits hors activités ordinaires'),
            ('771', 'Produits des cessions d\'immobilisations', 'crediteur', ''),
            ('78', 'Reprises sur provisions', 'crediteur', ''),
            ('781', 'Reprises sur provisions d\'exploitation', 'crediteur', ''),
            ('79', 'Reprises sur dépréciations', 'crediteur', ''),

            # CLASSE 8 - COMPTES DES AUTRES CHARGES ET AUTRES PRODUITS
            ('80', 'Comptes de marge', 'crediteur', 'Comptes de marge sur activités ordinaires'),
            ('81', 'Valeurs comptables des cessions d\'immobilisations', 'debiteur', ''),
            ('811', 'Valeurs comptables des cessions d\'immobilisations incorporelles', 'debiteur', ''),
            ('812', 'Valeurs comptables des cessions d\'immobilisations corporelles', 'debiteur', ''),
            ('82', 'Produits des cessions d\'immobilisations', 'crediteur', ''),
            ('821', 'Produits des cessions d\'immobilisations incorporelles', 'crediteur', ''),
            ('822', 'Produits des cessions d\'immobilisations corporelles', 'crediteur', ''),
            ('83', 'Charges hors activités ordinaires', 'debiteur', 'Charges HAO'),
            ('831', 'Charges HAO constatées', 'debiteur', ''),
            ('834', 'Pertes sur créances HAO', 'debiteur', ''),
            ('835', 'Dons et libéralités accordés', 'debiteur', ''),
            ('836', 'Abandons de créances consentis', 'debiteur', ''),
            ('839', 'Charges provisionnées HAO', 'debiteur', ''),
            ('84', 'Produits hors activités ordinaires', 'crediteur', 'Produits HAO'),
            ('841', 'Produits HAO constatés', 'crediteur', ''),
            ('845', 'Dons et libéralités obtenus', 'crediteur', ''),
            ('846', 'Abandons de créances obtenus', 'crediteur', ''),
            ('848', 'Transferts de charges HAO', 'crediteur', ''),
            ('849', 'Reprises de provisions HAO', 'crediteur', ''),
            ('85', 'Dotations HAO', 'debiteur', ''),
            ('851', 'Dotations aux provisions HAO', 'debiteur', ''),
            ('852', 'Dotations aux dépréciations HAO', 'debiteur', ''),
            ('86', 'Reprises HAO', 'crediteur', ''),
            ('861', 'Reprises de provisions HAO', 'crediteur', ''),
            ('862', 'Reprises de dépréciations HAO', 'crediteur', ''),
            ('87', 'Participations des travailleurs', 'debiteur', ''),
            ('871', 'Participation légale aux bénéfices', 'debiteur', ''),
            ('874', 'Participation contractuelle aux bénéfices', 'debiteur', ''),
            ('88', 'Subventions d\'équilibre', 'crediteur', ''),
            ('881', 'Subventions d\'équilibre reçues', 'crediteur', ''),
            ('89', 'Impôts sur le résultat', 'debiteur', 'Impôt sur les bénéfices'),
            ('891', 'Impôts sur les bénéfices de l\'exercice', 'debiteur', ''),
            ('892', 'Rappels d\'impôts sur résultats antérieurs', 'debiteur', ''),
            ('895', 'Impôt minimum forfaitaire (IMF)', 'debiteur', ''),
            ('899', 'Dégrèvements et annulations d\'impôts', 'crediteur', ''),

            # CLASSE 9 - ENGAGEMENTS HORS BILAN ET COMPTES DE LA COMPTABILITÉ ANALYTIQUE
            ('90', 'Engagements obtenus', 'debiteur', 'Engagements reçus de tiers'),
            ('901', 'Avals, cautions et garanties obtenus', 'debiteur', ''),
            ('902', 'Effets escomptés non échus', 'debiteur', ''),
            ('903', 'Créances cédées non échues', 'debiteur', ''),
            ('905', 'Biens détenus en garantie', 'debiteur', ''),
            ('906', 'Engagements reçus sur marchés', 'debiteur', ''),
            ('91', 'Contreparties des engagements obtenus', 'crediteur', ''),
            ('911', 'Contreparties des avals, cautions, garanties', 'crediteur', ''),
            ('92', 'Engagements donnés', 'crediteur', 'Engagements envers les tiers'),
            ('921', 'Avals, cautions et garanties donnés', 'crediteur', ''),
            ('922', 'Biens donnés en garantie', 'crediteur', ''),
            ('923', 'Engagements en matière de retraite', 'crediteur', ''),
            ('924', 'Engagements donnés sur marchés', 'crediteur', ''),
            ('93', 'Contreparties des engagements donnés', 'debiteur', ''),
            ('931', 'Contreparties des avals, cautions, garanties', 'debiteur', ''),
            ('94', 'Engagements réciproques', 'debiteur', ''),
            ('941', 'Redevances de crédit-bail restant à courir', 'debiteur', ''),
            ('942', 'Créances et dettes garanties par nantissement', 'debiteur', ''),
            ('95', 'Contreparties des engagements réciproques', 'crediteur', ''),
            ('951', 'Contreparties des redevances crédit-bail', 'crediteur', ''),
            ('96', 'Engagements spécifiques Étude d\'huissier', 'debiteur', 'Engagements spécifiques'),
            ('961', 'Consignations à recouvrer', 'debiteur', 'Montants à recouvrer pour le compte de tiers'),
            ('962', 'Honoraires à percevoir', 'debiteur', 'Honoraires sur procédures en cours'),
            ('963', 'Garanties détenues sur débiteurs', 'debiteur', ''),
            ('97', 'Contreparties engagements spécifiques', 'crediteur', ''),
            ('971', 'Contreparties consignations', 'crediteur', ''),
        ]

        created_count = 0
        for numero, libelle, solde_normal, description in comptes:
            compte, created = CompteComptable.objects.get_or_create(
                numero=numero,
                defaults={
                    'libelle': libelle,
                    'solde_normal': solde_normal,
                    'description': description,
                    'actif': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  {created_count} comptes créés sur {len(comptes)} définis')

    def creer_journaux(self):
        """Crée les journaux comptables standards"""
        self.stdout.write('Création des journaux comptables...')

        journaux = [
            ('AC', 'Journal des achats', 'AC', 'Enregistrement des factures fournisseurs'),
            ('VE', 'Journal des ventes', 'VE', 'Enregistrement des factures clients et honoraires'),
            ('BQ', 'Journal de banque', 'BQ', 'Mouvements bancaires'),
            ('CA', 'Journal de caisse', 'CA', 'Mouvements de caisse'),
            ('OD', 'Opérations diverses', 'OD', 'Écritures diverses et régularisations'),
            ('AN', 'À nouveau', 'AN', 'Report des soldes d\'ouverture'),
        ]

        created_count = 0
        for code, libelle, type_journal, description in journaux:
            journal, created = Journal.objects.get_or_create(
                code=code,
                defaults={
                    'libelle': libelle,
                    'type_journal': type_journal,
                    'description': description,
                    'actif': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  {created_count} journaux créés sur {len(journaux)} définis')

    def creer_types_operations(self):
        """Crée les types d'opérations pour le mode facile"""
        self.stdout.write('Création des types d\'opérations...')

        # Récupérer les journaux et comptes nécessaires
        try:
            journal_vente = Journal.objects.get(code='VE')
            journal_achat = Journal.objects.get(code='AC')
            journal_banque = Journal.objects.get(code='BQ')
            journal_caisse = Journal.objects.get(code='CA')

            compte_banque = CompteComptable.objects.get(numero='5211')
            compte_caisse = CompteComptable.objects.get(numero='571')
            compte_clients = CompteComptable.objects.get(numero='411')
            compte_honoraires = CompteComptable.objects.get(numero='7061')
            compte_emoluments = CompteComptable.objects.get(numero='7062')
            compte_fournisseurs = CompteComptable.objects.get(numero='401')
            compte_loyer = CompteComptable.objects.get(numero='6131')
            compte_fournitures = CompteComptable.objects.get(numero='601')
            compte_salaires = CompteComptable.objects.get(numero='6411')
            compte_personnel = CompteComptable.objects.get(numero='421')
            compte_consignations = CompteComptable.objects.get(numero='4721')
            compte_carburant = CompteComptable.objects.get(numero='6254')
            compte_telephone = CompteComptable.objects.get(numero='6262')

            operations = [
                ('ENCAISS_HONORAIRES', 'J\'ai encaissé des honoraires',
                 'Enregistre un encaissement d\'honoraires par banque', 'banknote',
                 journal_vente, compte_banque, compte_honoraires, 1),

                ('ENCAISS_HONORAIRES_CAISSE', 'J\'ai encaissé des honoraires en espèces',
                 'Enregistre un encaissement d\'honoraires en caisse', 'wallet',
                 journal_caisse, compte_caisse, compte_honoraires, 2),

                ('ENCAISS_EMOLUMENTS', 'J\'ai encaissé des émoluments',
                 'Enregistre un encaissement d\'émoluments', 'receipt',
                 journal_vente, compte_banque, compte_emoluments, 3),

                ('PAIEMENT_LOYER', 'J\'ai payé le loyer',
                 'Enregistre le paiement du loyer des locaux', 'home',
                 journal_banque, compte_loyer, compte_banque, 10),

                ('ACHAT_FOURNITURES', 'J\'ai acheté des fournitures',
                 'Enregistre un achat de fournitures de bureau', 'package',
                 journal_achat, compte_fournitures, compte_banque, 11),

                ('PAIEMENT_SALAIRE', 'J\'ai payé un salaire',
                 'Enregistre le paiement d\'un salaire', 'users',
                 journal_banque, compte_salaires, compte_banque, 12),

                ('RECU_CONSIGNATION', 'J\'ai reçu une consignation client',
                 'Enregistre une consignation reçue d\'un client', 'shield',
                 journal_banque, compte_banque, compte_consignations, 20),

                ('REVERSER_CONSIGNATION', 'J\'ai reversé au créancier',
                 'Enregistre le reversement d\'une consignation', 'send',
                 journal_banque, compte_consignations, compte_banque, 21),

                ('PAIEMENT_CARBURANT', 'J\'ai payé du carburant',
                 'Enregistre un achat de carburant pour les véhicules', 'fuel',
                 journal_caisse, compte_carburant, compte_caisse, 30),

                ('PAIEMENT_TELEPHONE', 'J\'ai payé le téléphone/internet',
                 'Enregistre le paiement des factures télécom', 'phone',
                 journal_banque, compte_telephone, compte_banque, 31),
            ]

            created_count = 0
            for (code, libelle, description, icone, journal,
                 compte_debit, compte_credit, ordre) in operations:
                op, created = TypeOperation.objects.get_or_create(
                    code=code,
                    defaults={
                        'libelle': libelle,
                        'description': description,
                        'icone': icone,
                        'journal': journal,
                        'compte_debit': compte_debit,
                        'compte_credit': compte_credit,
                        'ordre_affichage': ordre,
                        'actif': True
                    }
                )
                if created:
                    created_count += 1

            self.stdout.write(f'  {created_count} types d\'opérations créés')

        except CompteComptable.DoesNotExist as e:
            self.stdout.write(self.style.WARNING(f'  Certains comptes requis n\'existent pas: {e}'))
        except Journal.DoesNotExist as e:
            self.stdout.write(self.style.WARNING(f'  Certains journaux requis n\'existent pas: {e}'))

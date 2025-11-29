"""
Service d'import de données depuis l'ancienne application.
Parse les références et prépare les données pour validation.
NE MODIFIE PAS les tables principales - utilise uniquement les tables temporaires.
"""
import re
import csv
import json
from decimal import Decimal
from datetime import date
from io import StringIO

from django.db import transaction

from gestion.models_import import SessionImport, DossierImportTemp


class ParseurReference:
    """
    Parse les références de l'ancienne application.
    Format: REF_596_1125_MAB_AFF_YEKINI Djamal Dine_ctr_DJADOO
    """

    # Pattern pour extraire les composants de la référence
    PATTERN_REFERENCE = re.compile(
        r'^REF_(\d+)_(\d{4})_MAB_AFF_(.+?)_ctr_(.+)$',
        re.IGNORECASE
    )

    # Pattern alternatif (plus souple)
    PATTERN_ALTERNATIF = re.compile(
        r'^REF[_-]?(\d+)[_-]?(\d{2,4})[_-]?MAB[_-]?AFF[_-]?(.+?)[_-]?(?:ctr|c/|contre|vs)[_-]?(.+)$',
        re.IGNORECASE
    )

    @classmethod
    def parser_reference(cls, reference):
        """
        Parse une référence et retourne les composants extraits.

        Retourne un dict avec :
        - numero_ordre
        - mois_creation
        - annee_creation
        - date_ouverture (estimée)
        - demandeur_texte
        - defendeur_texte
        - succes (bool)
        - message_erreur (si échec)
        """
        if not reference:
            return {
                'succes': False,
                'message_erreur': 'Référence vide'
            }

        reference = reference.strip()

        # Essayer le pattern principal
        match = cls.PATTERN_REFERENCE.match(reference)

        if not match:
            # Essayer le pattern alternatif
            match = cls.PATTERN_ALTERNATIF.match(reference)

        if not match:
            return {
                'succes': False,
                'message_erreur': f'Format de référence non reconnu: {reference}',
                'reference_originale': reference
            }

        numero_ordre = match.group(1)
        code_date = match.group(2)
        demandeur_texte = match.group(3).strip()
        defendeur_texte = match.group(4).strip()

        # Parser le code date (MMAA ou MMAAAA)
        mois, annee = cls._parser_code_date(code_date)

        # Estimer la date d'ouverture (1er jour du mois)
        date_ouverture = None
        if mois and annee:
            try:
                date_ouverture = date(annee, mois, 1)
            except ValueError:
                pass

        return {
            'succes': True,
            'numero_ordre': numero_ordre,
            'mois_creation': mois,
            'annee_creation': annee,
            'date_ouverture': date_ouverture,
            'demandeur_texte': demandeur_texte,
            'defendeur_texte': defendeur_texte,
            'reference_originale': reference
        }

    @classmethod
    def _parser_code_date(cls, code_date):
        """Parse le code date MMAA ou MMAAAA"""
        if len(code_date) == 4:
            # Format MMAA (ex: 1125 = novembre 2025)
            mois = int(code_date[:2])
            annee = int(code_date[2:])
            # Convertir année sur 2 chiffres
            if annee < 100:
                annee = 2000 + annee if annee < 50 else 1900 + annee
        elif len(code_date) == 6:
            # Format MMAAAA (ex: 112025)
            mois = int(code_date[:2])
            annee = int(code_date[2:])
        else:
            return None, None

        # Validation
        if mois < 1 or mois > 12:
            return None, None
        if annee < 2000 or annee > 2100:
            return None, None

        return mois, annee


class ParseurPartie:
    """Parse les noms de parties pour extraire nom/prénom ou raison sociale"""

    # Indicateurs de personne morale
    INDICATEURS_PM = [
        'SA', 'SARL', 'SAS', 'SARLU', 'SNC', 'ETS', 'GIE', 'SUARL',
        'S.A.', 'S.A.R.L.', 'S.A.S.',
        'BANQUE', 'BANK', 'BOA', 'ECOBANK', 'UBA', 'ORABANK',
        'SOCIETE', 'SOCIÉTÉ', 'ENTREPRISE', 'ETABLISSEMENT',
        'MICRO', 'FINANCE', 'ASSURANCE', 'HOTEL', 'RESTAURANT',
        'COMMERCE', 'TRADING', 'IMPORT', 'EXPORT',
    ]

    @classmethod
    def parser_partie(cls, texte):
        """
        Analyse un texte de partie et détermine s'il s'agit d'une personne
        physique ou morale, puis extrait les informations.

        Retourne un dict avec :
        - est_personne_morale
        - nom
        - prenom (si personne physique)
        - raison_sociale (si personne morale)
        """
        if not texte:
            return {
                'est_personne_morale': False,
                'nom': '',
                'prenom': '',
                'raison_sociale': ''
            }

        texte = texte.strip()
        texte_upper = texte.upper()

        # Vérifier si c'est une personne morale
        est_pm = any(ind in texte_upper for ind in cls.INDICATEURS_PM)

        if est_pm:
            return {
                'est_personne_morale': True,
                'nom': '',
                'prenom': '',
                'raison_sociale': texte
            }
        else:
            # Personne physique - essayer de séparer nom et prénom
            nom, prenom = cls._separer_nom_prenom(texte)
            return {
                'est_personne_morale': False,
                'nom': nom,
                'prenom': prenom,
                'raison_sociale': ''
            }

    @classmethod
    def _separer_nom_prenom(cls, texte):
        """
        Sépare le nom et le prénom.
        Convention: NOM en majuscules, Prénom en minuscules/capitalisé
        Ou: NOM Prénom (séparés par espace)
        """
        parties = texte.split()

        if len(parties) == 0:
            return '', ''
        elif len(parties) == 1:
            return parties[0], ''
        else:
            # Stratégie 1: Tout en majuscules = NOM, sinon = prénom
            noms = []
            prenoms = []

            for partie in parties:
                if partie.isupper():
                    noms.append(partie)
                else:
                    prenoms.append(partie)

            if noms and prenoms:
                return ' '.join(noms), ' '.join(prenoms)

            # Stratégie 2: Premier mot = NOM, reste = prénoms
            return parties[0].upper(), ' '.join(parties[1:])


class ServiceImport:
    """Service principal d'import des données"""

    def __init__(self, session):
        self.session = session
        self.rapport = {
            'total_lignes': 0,
            'dossiers_crees': 0,
            'erreurs_parsing': [],
            'doublons_detectes': [],
            'parties_nouvelles': 0,
            'parties_existantes': 0,
        }

    def importer_csv(self, contenu_csv, colonnes_mapping=None):
        """
        Importe des données depuis un contenu CSV.

        colonnes_mapping: dict optionnel pour mapper les colonnes
        Ex: {'reference': 'REF', 'date': 'DATE_OUVERTURE', ...}
        """
        if colonnes_mapping is None:
            colonnes_mapping = {
                'reference': 'reference',
                'date_ouverture': 'date_ouverture',
                'demandeur_adresse': 'demandeur_adresse',
                'demandeur_telephone': 'demandeur_telephone',
                'demandeur_email': 'demandeur_email',
                'defendeur_adresse': 'defendeur_adresse',
                'defendeur_telephone': 'defendeur_telephone',
                'defendeur_email': 'defendeur_email',
                'montant_principal': 'montant_principal',
                'montant_interets': 'montant_interets',
                'montant_frais': 'montant_frais',
            }

        reader = csv.DictReader(StringIO(contenu_csv), delimiter=';')

        dossiers_temp = []

        for i, row in enumerate(reader):
            self.rapport['total_lignes'] += 1

            try:
                dossier_temp = self._traiter_ligne(row, colonnes_mapping, i + 1)
                if dossier_temp:
                    dossiers_temp.append(dossier_temp)
            except Exception as e:
                self.rapport['erreurs_parsing'].append({
                    'ligne': i + 1,
                    'erreur': str(e),
                    'donnees': dict(row)
                })

        # Sauvegarder en masse
        with transaction.atomic():
            DossierImportTemp.objects.bulk_create(dossiers_temp)

        # Mettre à jour la session
        self.session.total_lignes = self.rapport['total_lignes']
        self.session.dossiers_trouves = len(dossiers_temp)
        self.session.erreurs_detectees = len(self.rapport['erreurs_parsing'])
        self.session.statut = 'analyse'
        self.session.set_rapport(self.rapport)
        self.session.save()

        return self.rapport

    def _traiter_ligne(self, row, mapping, numero_ligne):
        """Traite une ligne du CSV et crée un DossierImportTemp"""

        # Extraire la référence
        col_ref = mapping.get('reference', 'reference')
        reference = row.get(col_ref, '').strip()

        if not reference:
            raise ValueError(f"Référence manquante à la ligne {numero_ligne}")

        # Parser la référence
        parsed = ParseurReference.parser_reference(reference)

        if not parsed['succes']:
            raise ValueError(parsed['message_erreur'])

        # Parser les parties
        demandeur_info = ParseurPartie.parser_partie(parsed['demandeur_texte'])
        defendeur_info = ParseurPartie.parser_partie(parsed['defendeur_texte'])

        # Créer le dossier temporaire
        dossier_temp = DossierImportTemp(
            session=self.session,
            reference_originale=reference,
            donnees_brutes_json=json.dumps(dict(row), ensure_ascii=False),

            # Données parsées
            numero_ordre=parsed['numero_ordre'],
            mois_creation=parsed['mois_creation'],
            annee_creation=parsed['annee_creation'],
            date_ouverture_parsee=parsed['date_ouverture'],

            # Demandeur
            demandeur_texte_brut=parsed['demandeur_texte'],
            demandeur_nom=demandeur_info['nom'],
            demandeur_prenom=demandeur_info['prenom'],
            demandeur_est_personne_morale=demandeur_info['est_personne_morale'],
            demandeur_raison_sociale=demandeur_info['raison_sociale'],
            demandeur_adresse=row.get(mapping.get('demandeur_adresse', ''), ''),
            demandeur_telephone=row.get(mapping.get('demandeur_telephone', ''), ''),
            demandeur_email=row.get(mapping.get('demandeur_email', ''), ''),

            # Défendeur
            defendeur_texte_brut=parsed['defendeur_texte'],
            defendeur_nom=defendeur_info['nom'],
            defendeur_prenom=defendeur_info['prenom'],
            defendeur_est_personne_morale=defendeur_info['est_personne_morale'],
            defendeur_raison_sociale=defendeur_info['raison_sociale'],
            defendeur_adresse=row.get(mapping.get('defendeur_adresse', ''), ''),
            defendeur_telephone=row.get(mapping.get('defendeur_telephone', ''), ''),
            defendeur_email=row.get(mapping.get('defendeur_email', ''), ''),

            # Intitulé généré
            intitule_genere=f"{parsed['demandeur_texte']} c/ {parsed['defendeur_texte']}",

            statut='en_attente'
        )

        # Montants (si disponibles)
        try:
            mp = row.get(mapping.get('montant_principal', ''), '')
            if mp:
                dossier_temp.montant_principal = Decimal(str(mp).replace(' ', '').replace(',', '.'))
        except:
            pass

        self.rapport['dossiers_crees'] += 1
        return dossier_temp

    def analyser_doublons(self):
        """
        Analyse les doublons potentiels avec les données existantes.
        NE MODIFIE PAS les tables principales - lecture seule.
        """
        from gestion.models import Dossier, Partie
        from gestion.services.suggestions_parties import calculer_similarite

        dossiers_temp = self.session.dossiers_temp.filter(statut='en_attente')

        for dossier_temp in dossiers_temp:
            # Chercher demandeur similaire
            if dossier_temp.demandeur_est_personne_morale:
                nom_cherche = dossier_temp.demandeur_raison_sociale
            else:
                nom_cherche = f"{dossier_temp.demandeur_nom} {dossier_temp.demandeur_prenom}".strip()

            if nom_cherche:
                parties_similaires = Partie.objects.all()[:500]  # Limiter pour performance
                meilleur_score = 0
                meilleure_partie = None

                for partie in parties_similaires:
                    nom_partie = partie.raison_sociale or f"{partie.nom} {partie.prenom or ''}".strip()
                    score = calculer_similarite(nom_cherche, nom_partie)
                    if score > meilleur_score and score >= 0.85:
                        meilleur_score = score
                        meilleure_partie = partie

                if meilleure_partie:
                    dossier_temp.demandeur_existant_id = meilleure_partie.pk
                    dossier_temp.demandeur_existant_nom = str(meilleure_partie)
                    dossier_temp.demandeur_score_similarite = meilleur_score
                    self.rapport['parties_existantes'] += 1
                else:
                    self.rapport['parties_nouvelles'] += 1

            # Même logique pour défendeur
            if dossier_temp.defendeur_est_personne_morale:
                nom_cherche = dossier_temp.defendeur_raison_sociale
            else:
                nom_cherche = f"{dossier_temp.defendeur_nom} {dossier_temp.defendeur_prenom}".strip()

            if nom_cherche:
                parties_similaires = Partie.objects.all()[:500]
                meilleur_score = 0
                meilleure_partie = None

                for partie in parties_similaires:
                    nom_partie = partie.raison_sociale or f"{partie.nom} {partie.prenom or ''}".strip()
                    score = calculer_similarite(nom_cherche, nom_partie)
                    if score > meilleur_score and score >= 0.85:
                        meilleur_score = score
                        meilleure_partie = partie

                if meilleure_partie:
                    dossier_temp.defendeur_existant_id = meilleure_partie.pk
                    dossier_temp.defendeur_existant_nom = str(meilleure_partie)
                    dossier_temp.defendeur_score_similarite = meilleur_score

            dossier_temp.save()

        # Mettre à jour le rapport
        self.session.doublons_detectes = self.rapport['parties_existantes']
        self.session.set_rapport(self.rapport)
        self.session.save()

        return self.rapport

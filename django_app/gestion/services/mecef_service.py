"""
Service d'intégration avec l'API e-MECeF (DGI Bénin)

Documentation officielle: https://emecef.dgi.bj
MECeF = Machine Enregistreuse Certifiée électronique Fiscale

Ce service permet de:
- Certifier les factures électroniquement auprès de la DGI
- Obtenir un NIM (Numéro d'Identification MECeF) pour chaque facture
- Générer les QR codes de vérification
- Annuler des factures certifiées

Configuration requise dans settings.py:

    # Mode test (sandbox)
    MECEF_API_URL = 'https://sandbox.emecef.dgi.bj/api/v1'
    MECEF_NIM = 'votre_nim_machine'
    MECEF_TOKEN = 'votre_token_api'
    MECEF_MODE = 'test'

    # Mode production
    MECEF_API_URL = 'https://api.emecef.dgi.bj/api/v1'
    MECEF_NIM = 'votre_nim_machine'
    MECEF_TOKEN = 'votre_token_api'
    MECEF_MODE = 'production'

Groupes de taxation MECeF:
    - Groupe A: Exonéré (0%) - pour les débours
    - Groupe B: TVA 18% - taux standard
    - Groupe E: TPS 5% - Taxe sur Prestations de Services
"""
import requests
import hashlib
import json
import logging
from decimal import Decimal
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class MECeFError(Exception):
    """
    Exception personnalisée pour les erreurs MECeF

    Attributes:
        message: Description de l'erreur
        code: Code d'erreur MECeF (si disponible)
        response: Réponse HTTP brute (si disponible)
    """
    def __init__(self, message, code=None, response=None):
        self.message = message
        self.code = code
        self.response = response
        super().__init__(self.message)


class MECeFService:
    """
    Service pour l'intégration avec l'API e-MECeF de la DGI Bénin

    Usage:
        from gestion.services.mecef_service import mecef_service

        # Vérifier la configuration
        if mecef_service.is_configured():
            # Certifier une facture
            result = mecef_service.normaliser_facture(facture)
            print(f"NIM: {result['nim']}")

        # Ou instancier directement
        service = MECeFService()
        service.normaliser_facture(facture)
    """

    # Groupes de taxation selon la norme MECeF
    GROUPE_TAXATION = {
        'A': {'code': 'A', 'libelle': 'Exonéré', 'taux': Decimal('0')},
        'B': {'code': 'B', 'libelle': 'TVA 18%', 'taux': Decimal('18')},
        'E': {'code': 'E', 'libelle': 'TPS 5%', 'taux': Decimal('5')},
    }

    # Types de factures MECeF
    TYPE_FACTURE = {
        'FV': 'Facture de Vente',
        'FA': 'Facture d\'Avoir',
        'EV': 'Export de Vente',
    }

    def __init__(self):
        """Initialise le service avec la configuration depuis settings.py"""
        self.api_url = getattr(settings, 'MECEF_API_URL', None)
        self.nim = getattr(settings, 'MECEF_NIM', None)
        self.token = getattr(settings, 'MECEF_TOKEN', None)
        self.mode = getattr(settings, 'MECEF_MODE', 'test')

    def is_configured(self):
        """
        Vérifie si le service est correctement configuré

        Returns:
            bool: True si tous les paramètres requis sont présents
        """
        return all([self.api_url, self.nim, self.token])

    def _get_headers(self):
        """
        Retourne les headers pour les requêtes API

        Returns:
            dict: Headers HTTP pour l'authentification
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-NIM': self.nim,
        }

    def _build_invoice_payload(self, facture):
        """
        Construit le payload JSON pour la certification d'une facture

        Args:
            facture: Instance du modèle Facture

        Returns:
            dict: Payload formaté pour l'API MECeF
        """
        lignes = []
        for ligne in facture.lignes.all():
            groupe = self.GROUPE_TAXATION.get(ligne.groupe_taxation, self.GROUPE_TAXATION['E'])
            lignes.append({
                'designation': ligne.description[:100],  # Limite MECeF
                'quantite': float(ligne.quantite),
                'prix_unitaire': float(ligne.prix_unitaire),
                'montant_ht': float(ligne.total),
                'groupe_taxation': groupe['code'],
                'taux_taxe': float(groupe['taux']),
                'montant_taxe': float(ligne.montant_tva_ligne),
                'montant_ttc': float(ligne.montant_ttc_ligne),
            })

        # Date de facture
        if hasattr(facture, 'date_emission') and facture.date_emission:
            date_facture = facture.date_emission.isoformat()
        else:
            date_facture = datetime.now().date().isoformat()

        payload = {
            'nim': self.nim,
            'type_facture': 'FV',  # Facture de Vente
            'numero_facture': facture.numero,
            'date_facture': date_facture,
            'client': {
                'nom': facture.client[:100] if facture.client else 'Client',
                'ifu': facture.ifu or '',
                'adresse': '',
                'telephone': '',
            },
            'lignes': lignes,
            'montant_ht': float(facture.montant_ht or 0),
            'montant_tva': float(facture.montant_tva or 0),
            'montant_ttc': float(facture.montant_ttc or 0),
            'mode_paiement': 'ESPECES',  # Par défaut
        }

        return payload

    def _build_avoir_payload(self, avoir, facture_origine):
        """
        Construit le payload JSON pour un avoir (note de crédit)

        Args:
            avoir: Instance du modèle Avoir
            facture_origine: Facture d'origine liée à l'avoir

        Returns:
            dict: Payload formaté pour l'API MECeF
        """
        payload = self._build_invoice_payload(avoir)
        payload['type_facture'] = 'FA'  # Facture d'Avoir
        payload['facture_origine'] = {
            'numero': facture_origine.numero,
            'nim': facture_origine.nim,
        }
        return payload

    def normaliser_facture(self, facture):
        """
        Envoie une facture à l'API MECeF pour certification (normalisation)

        Cette méthode:
        1. Vérifie la configuration
        2. Construit le payload
        3. Envoie la requête à l'API
        4. Met à jour la facture avec les infos MECeF

        Args:
            facture: Instance du modèle Facture

        Returns:
            dict: Réponse contenant nim, signature, qr_code, etc.
            {
                'success': True,
                'nim': 'NIM123456789',
                'signature': 'ABC123...',
                'code_verification': 'VERIF123',
                'qr_code': 'base64_encoded_qr...',
            }

        Raises:
            MECeFError: En cas d'erreur de l'API ou de configuration
        """
        if not self.is_configured():
            raise MECeFError(
                "Service MECeF non configuré. "
                "Vérifiez les paramètres MECEF_API_URL, MECEF_NIM et MECEF_TOKEN dans settings.py"
            )

        # Vérifier si déjà certifiée
        statut_mecef = getattr(facture, 'statut_mecef', None)
        if statut_mecef == 'certifiee':
            raise MECeFError(
                "Cette facture est déjà certifiée",
                code='ALREADY_CERTIFIED'
            )

        payload = self._build_invoice_payload(facture)

        try:
            logger.info(f"Envoi facture {facture.numero} à MECeF (mode: {self.mode})...")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.api_url}/invoices/normalize",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            logger.debug(f"Réponse MECeF: {response.status_code} - {response.text[:500]}")

            if response.status_code == 200:
                data = response.json()

                # Mettre à jour la facture avec les infos MECeF
                facture.nim = data.get('nim')
                facture.signature_mecef = data.get('signature')
                facture.code_mecef = data.get('code_verification')
                facture.statut_mecef = 'certifiee'
                facture.date_certification_mecef = datetime.now()
                facture.save()

                logger.info(f"Facture {facture.numero} certifiée avec succès. NIM: {facture.nim}")

                return {
                    'success': True,
                    'nim': data.get('nim'),
                    'signature': data.get('signature'),
                    'code_verification': data.get('code_verification'),
                    'qr_code': data.get('qr_code'),
                    'url_verification': data.get('url_verification'),
                }
            else:
                # Gérer les erreurs HTTP
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = {}

                error_message = error_data.get('message', f'Erreur HTTP {response.status_code}')
                error_code = error_data.get('code', f'HTTP_{response.status_code}')

                logger.error(f"Erreur MECeF pour facture {facture.numero}: {error_message}")

                raise MECeFError(
                    error_message,
                    code=error_code,
                    response=response
                )

        except requests.Timeout:
            logger.error(f"Timeout lors de la certification de la facture {facture.numero}")
            raise MECeFError("Délai d'attente dépassé. L'API MECeF ne répond pas.")

        except requests.ConnectionError as e:
            logger.error(f"Erreur de connexion MECeF: {str(e)}")
            raise MECeFError(f"Impossible de se connecter à l'API MECeF: {str(e)}")

        except requests.RequestException as e:
            logger.error(f"Erreur réseau MECeF: {str(e)}")
            raise MECeFError(f"Erreur de connexion à l'API MECeF: {str(e)}")

    def verifier_statut(self, nim):
        """
        Vérifie le statut d'une facture certifiée auprès de MECeF

        Args:
            nim: Numéro d'Identification MECeF de la facture

        Returns:
            dict: Statut de la facture
            {
                'nim': 'NIM123456789',
                'statut': 'VALIDE',
                'date_certification': '2024-01-15T10:30:00',
                ...
            }

        Raises:
            MECeFError: En cas d'erreur
        """
        if not self.is_configured():
            raise MECeFError("Service MECeF non configuré")

        if not nim:
            raise MECeFError("NIM requis pour la vérification")

        try:
            logger.info(f"Vérification du statut MECeF pour NIM: {nim}")

            response = requests.get(
                f"{self.api_url}/invoices/{nim}/status",
                headers=self._get_headers(),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise MECeFError(f"Facture non trouvée pour le NIM: {nim}", code='NOT_FOUND')
            else:
                raise MECeFError(f"Erreur lors de la vérification: HTTP {response.status_code}")

        except requests.RequestException as e:
            raise MECeFError(f"Erreur de connexion: {str(e)}")

    def annuler_facture(self, facture, motif):
        """
        Demande l'annulation d'une facture certifiée auprès de MECeF

        Note: L'annulation MECeF est irréversible et soumise à des règles strictes.
        Une facture ne peut être annulée que dans certains délais et conditions.

        Args:
            facture: Instance du modèle Facture (doit avoir un NIM)
            motif: Raison de l'annulation (obligatoire)

        Returns:
            dict: Confirmation de l'annulation

        Raises:
            MECeFError: En cas d'erreur ou de refus
        """
        if not self.is_configured():
            raise MECeFError("Service MECeF non configuré")

        if not facture.nim:
            raise MECeFError("Cette facture n'a pas de NIM. Elle n'a pas été certifiée.")

        if not motif or len(motif.strip()) < 10:
            raise MECeFError("Le motif d'annulation doit être détaillé (min. 10 caractères)")

        try:
            logger.info(f"Demande d'annulation MECeF pour facture {facture.numero} (NIM: {facture.nim})")

            response = requests.post(
                f"{self.api_url}/invoices/{facture.nim}/cancel",
                headers=self._get_headers(),
                json={
                    'motif': motif,
                    'date_annulation': datetime.now().isoformat(),
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Mettre à jour le statut local
                facture.statut_mecef = 'annulee'
                facture.save()

                logger.info(f"Facture {facture.numero} annulée avec succès auprès de MECeF")

                return {
                    'success': True,
                    'message': data.get('message', 'Facture annulée'),
                    **data
                }
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                raise MECeFError(
                    error_data.get('message', "Annulation refusée par MECeF"),
                    code=error_data.get('code', 'CANCEL_REFUSED')
                )
            else:
                raise MECeFError(f"Erreur lors de l'annulation: HTTP {response.status_code}")

        except requests.RequestException as e:
            raise MECeFError(f"Erreur de connexion: {str(e)}")

    def generer_avoir(self, avoir, facture_origine):
        """
        Génère et certifie un avoir (note de crédit) auprès de MECeF

        Args:
            avoir: Instance de l'avoir à certifier
            facture_origine: Facture d'origine liée à l'avoir

        Returns:
            dict: Réponse de certification de l'avoir

        Raises:
            MECeFError: En cas d'erreur
        """
        if not self.is_configured():
            raise MECeFError("Service MECeF non configuré")

        if not facture_origine.nim:
            raise MECeFError("La facture d'origine doit être certifiée avant de créer un avoir")

        payload = self._build_avoir_payload(avoir, facture_origine)

        try:
            logger.info(f"Envoi avoir pour facture {facture_origine.numero} à MECeF...")

            response = requests.post(
                f"{self.api_url}/invoices/normalize",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Mettre à jour l'avoir avec les infos MECeF
                if hasattr(avoir, 'nim'):
                    avoir.nim = data.get('nim')
                    avoir.statut_mecef = 'certifiee'
                    avoir.save()

                logger.info(f"Avoir certifié avec NIM: {data.get('nim')}")

                return {
                    'success': True,
                    'nim': data.get('nim'),
                    'signature': data.get('signature'),
                    **data
                }
            else:
                error_data = response.json() if response.content else {}
                raise MECeFError(
                    error_data.get('message', f'Erreur HTTP {response.status_code}'),
                    code=error_data.get('code')
                )

        except requests.RequestException as e:
            raise MECeFError(f"Erreur de connexion: {str(e)}")

    def test_connexion(self):
        """
        Teste la connexion à l'API MECeF

        Returns:
            dict: Résultat du test
            {
                'success': True/False,
                'message': 'Description',
                'mode': 'test/production',
            }
        """
        if not self.is_configured():
            return {
                'success': False,
                'message': "Service non configuré. Paramètres MECEF_* manquants.",
                'mode': self.mode,
            }

        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': "Connexion à l'API MECeF réussie",
                    'mode': self.mode,
                    'api_url': self.api_url,
                }
            else:
                return {
                    'success': False,
                    'message': f"API accessible mais erreur: HTTP {response.status_code}",
                    'mode': self.mode,
                }

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f"Impossible de se connecter: {str(e)}",
                'mode': self.mode,
            }


# Instance singleton pour utilisation facile
mecef_service = MECeFService()

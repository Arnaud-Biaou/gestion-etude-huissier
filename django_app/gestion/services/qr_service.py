"""
Service de génération et gestion des QR codes pour la sécurisation des actes.
Étude Me Martial Arnaud BIAOU - Huissier de Justice
"""

import hashlib
import io
import base64
from typing import Optional, Tuple

# Import conditionnel de qrcode (à installer: pip install qrcode[pil])
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("⚠️ Module qrcode non installé. Exécutez: pip install qrcode[pil]")


class QRCodeService:
    """
    Service pour générer des QR codes de vérification des actes.
    """

    # Configuration par défaut
    DEFAULT_BOX_SIZE = 10
    DEFAULT_BORDER = 4
    DEFAULT_VERSION = 1

    @classmethod
    def est_disponible(cls) -> bool:
        """Vérifie si le module qrcode est disponible."""
        return QR_AVAILABLE

    @classmethod
    def generer_qr_image(
        cls,
        data: str,
        box_size: int = DEFAULT_BOX_SIZE,
        border: int = DEFAULT_BORDER
    ) -> Optional[io.BytesIO]:
        """
        Génère une image QR code à partir de données.

        Args:
            data: Les données à encoder (URL de vérification)
            box_size: Taille de chaque "boîte" du QR
            border: Taille de la bordure blanche

        Returns:
            BytesIO contenant l'image PNG, ou None si erreur
        """
        if not QR_AVAILABLE:
            return None

        try:
            qr = qrcode.QRCode(
                version=cls.DEFAULT_VERSION,
                error_correction=ERROR_CORRECT_M,
                box_size=box_size,
                border=border,
            )

            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return buffer

        except Exception as e:
            print(f"Erreur génération QR: {e}")
            return None

    @classmethod
    def generer_qr_base64(cls, data: str, **kwargs) -> Optional[str]:
        """
        Génère un QR code et le retourne en base64.
        Utile pour l'intégration directe dans HTML/PDF.

        Returns:
            String base64 de l'image PNG, ou None si erreur
        """
        buffer = cls.generer_qr_image(data, **kwargs)

        if buffer is None:
            return None

        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @classmethod
    def generer_qr_data_uri(cls, data: str, **kwargs) -> Optional[str]:
        """
        Génère un QR code et le retourne en data URI.
        Peut être utilisé directement dans une balise <img src="...">.

        Returns:
            Data URI de l'image, ou None si erreur
        """
        b64 = cls.generer_qr_base64(data, **kwargs)

        if b64 is None:
            return None

        return f"data:image/png;base64,{b64}"


class ActeSecuriseService:
    """
    Service pour créer et gérer les actes sécurisés.
    """

    @staticmethod
    def calculer_hash_fichier(fichier) -> str:
        """
        Calcule le hash SHA-256 d'un fichier uploadé.

        Args:
            fichier: Fichier Django (UploadedFile) ou file-like object

        Returns:
            Hash SHA-256 en hexadécimal
        """
        sha256 = hashlib.sha256()

        # Support pour différents types de fichiers
        if hasattr(fichier, 'chunks'):
            # Fichier Django uploadé
            for chunk in fichier.chunks():
                sha256.update(chunk)
        elif hasattr(fichier, 'read'):
            # File-like object
            fichier.seek(0)
            while True:
                chunk = fichier.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
            fichier.seek(0)
        elif isinstance(fichier, bytes):
            # Bytes directement
            sha256.update(fichier)
        else:
            raise ValueError("Type de fichier non supporté")

        return sha256.hexdigest()

    @staticmethod
    def calculer_hash_contenu(contenu: str) -> str:
        """
        Calcule le hash SHA-256 d'un contenu texte.

        Args:
            contenu: Texte à hasher

        Returns:
            Hash SHA-256 en hexadécimal
        """
        return hashlib.sha256(contenu.encode('utf-8')).hexdigest()

    @classmethod
    def creer_acte_securise(
        cls,
        dossier,
        type_acte: str,
        titre_acte: str,
        date_acte,
        parties_resume: str,
        contenu_ou_fichier,
        cree_par=None,
        document=None
    ):
        """
        Crée un nouvel acte sécurisé avec génération automatique du code.

        Args:
            dossier: Instance du modèle Dossier
            type_acte: Type d'acte (signification, constat, etc.)
            titre_acte: Titre descriptif
            date_acte: Date de l'acte
            parties_resume: Résumé des parties (ex: "X c/ Y")
            contenu_ou_fichier: Contenu texte ou fichier pour calculer le hash
            cree_par: Collaborateur qui crée l'acte (optionnel)
            document: Document associé (optionnel)

        Returns:
            Instance ActeSecurise créée
        """
        from gestion.models import ActeSecurise

        # Calculer le hash
        if isinstance(contenu_ou_fichier, str):
            hash_contenu = cls.calculer_hash_contenu(contenu_ou_fichier)
        else:
            hash_contenu = cls.calculer_hash_fichier(contenu_ou_fichier)

        # Générer le code unique
        code = ActeSecurise.generer_code_verification()

        # Créer l'acte sécurisé
        acte = ActeSecurise.objects.create(
            code_verification=code,
            dossier=dossier,
            type_acte=type_acte,
            titre_acte=titre_acte,
            date_acte=date_acte,
            parties_resume=parties_resume,
            hash_contenu=hash_contenu,
            cree_par=cree_par,
            document=document,
        )

        return acte

    @classmethod
    def generer_qr_pour_acte(cls, acte_securise) -> Optional[str]:
        """
        Génère le QR code pour un acte sécurisé.

        Args:
            acte_securise: Instance ActeSecurise

        Returns:
            Data URI de l'image QR, ou None si erreur
        """
        qr_data = acte_securise.get_qr_data()
        return QRCodeService.generer_qr_data_uri(qr_data)

    @classmethod
    def verifier_acte(cls, code_verification: str) -> Tuple[bool, Optional[dict]]:
        """
        Vérifie l'authenticité d'un acte par son code.

        Args:
            code_verification: Code à vérifier

        Returns:
            Tuple (est_valide, infos_acte ou None)
        """
        from gestion.models import ActeSecurise

        try:
            acte = ActeSecurise.objects.select_related(
                'dossier', 'cree_par'
            ).get(code_verification=code_verification)

            if not acte.est_actif:
                return False, {
                    'raison': 'Acte désactivé ou annulé',
                    'code': code_verification,
                }

            # Incrémenter le compteur
            acte.incrementer_verification()

            return True, {
                'code': acte.code_verification,
                'type_acte': acte.get_type_acte_display(),
                'titre': acte.titre_acte,
                'date_acte': acte.date_acte,
                'parties': acte.parties_resume,
                'reference_dossier': acte.dossier.reference,
                'cree_le': acte.cree_le,
                'nombre_verifications': acte.nombre_verifications,
            }

        except ActeSecurise.DoesNotExist:
            return False, None

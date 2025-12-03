"""
Service pour incruster un QR code de sécurité sur les PDF d'actes.
Étude Me Martial Arnaud BIAOU - Huissier de Justice

Permet de générer :
- Version ORIGINAL
- Version SECOND ORIGINAL
- Version COPIE

Chaque version porte le même QR code de vérification avec mention du type.
"""

import io
import qrcode
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class PDFQRService:
    """Service pour incruster un QR code sur un PDF"""

    # Types de documents disponibles
    TYPE_ORIGINAL = 'ORIGINAL'
    TYPE_SECOND_ORIGINAL = 'SECOND ORIGINAL'
    TYPE_COPIE = 'COPIE'

    @classmethod
    def generer_qr_image(cls, data, size=150):
        """
        Génère une image QR code.

        Args:
            data: Données à encoder (URL de vérification)
            size: Taille en pixels

        Returns:
            Image PIL du QR code
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir en mode RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionner
        img = img.resize((size, size), Image.LANCZOS)
        return img

    @classmethod
    def creer_overlay_qr(cls, qr_image, page_width, page_height,
                          position='bottom-right', type_document='ORIGINAL',
                          code_verification=''):
        """
        Crée un PDF overlay avec le QR code et le texte.

        Args:
            qr_image: Image PIL du QR code
            page_width: Largeur de la page en points
            page_height: Hauteur de la page en points
            position: 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            type_document: 'ORIGINAL', 'SECOND ORIGINAL', 'COPIE'
            code_verification: Code unique de l'acte

        Returns:
            BytesIO contenant le PDF overlay
        """

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Dimensions du QR (25mm x 25mm)
        qr_size = 25 * mm
        margin = 10 * mm

        # Position selon le choix
        if position == 'bottom-right':
            x = page_width - qr_size - margin
            y = margin
        elif position == 'bottom-left':
            x = margin
            y = margin
        elif position == 'top-right':
            x = page_width - qr_size - margin
            y = page_height - qr_size - margin - 15 * mm
        else:  # top-left
            x = margin
            y = page_height - qr_size - margin - 15 * mm

        # Sauvegarder le QR en buffer temporaire
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Dessiner un rectangle blanc de fond avec bordure
        c.setFillColorRGB(1, 1, 1)  # Blanc
        c.setStrokeColorRGB(0.7, 0.7, 0.7)  # Gris clair
        c.setLineWidth(0.5)
        c.rect(x - 3*mm, y - 10*mm, qr_size + 6*mm, qr_size + 22*mm, fill=True, stroke=True)

        # Dessiner le QR code
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(qr_buffer), x, y, width=qr_size, height=qr_size)

        # Ajouter le type de document au-dessus du QR (en gras)
        c.setFillColorRGB(0, 0, 0)  # Noir
        c.setFont("Helvetica-Bold", 7)

        # Centrer le texte au-dessus du QR
        text_width = c.stringWidth(type_document, "Helvetica-Bold", 7)
        text_x = x + (qr_size - text_width) / 2
        c.drawString(text_x, y + qr_size + 4*mm, type_document)

        # Ajouter le code en dessous du QR
        c.setFont("Helvetica", 5)
        code_width = c.stringWidth(code_verification, "Helvetica", 5)
        code_x = x + (qr_size - code_width) / 2
        c.drawString(code_x, y - 6*mm, code_verification)

        # Ajouter "Scannez pour vérifier" en petit
        c.setFont("Helvetica", 4)
        scan_text = "Scannez pour vérifier"
        scan_width = c.stringWidth(scan_text, "Helvetica", 4)
        scan_x = x + (qr_size - scan_width) / 2
        c.drawString(scan_x, y - 9*mm, scan_text)

        c.save()
        buffer.seek(0)
        return buffer

    @classmethod
    def incruster_qr_sur_pdf(cls, pdf_bytes, code_verification, url_verification,
                              type_document='ORIGINAL', position='bottom-right',
                              page='all'):
        """
        Incruste le QR code sur le PDF.

        Args:
            pdf_bytes: Contenu du PDF original (bytes)
            code_verification: Code unique de l'acte (ex: ACT-2025-1130-7F3B2)
            url_verification: URL complète pour vérification
            type_document: 'ORIGINAL', 'SECOND ORIGINAL', ou 'COPIE'
            position: 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            page: 'last', 'first', ou 'all'

        Returns:
            bytes: PDF modifié avec QR incrusté
        """

        # Lire le PDF original
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        pdf_writer = PdfWriter()

        # Générer le QR code
        qr_image = cls.generer_qr_image(url_verification)

        # Traiter chaque page
        total_pages = len(pdf_reader.pages)

        for i, page_obj in enumerate(pdf_reader.pages):
            # Déterminer si on ajoute le QR sur cette page
            ajouter_qr = False
            if page == 'all':
                ajouter_qr = True
            elif page == 'first' and i == 0:
                ajouter_qr = True
            elif page == 'last' and i == total_pages - 1:
                ajouter_qr = True

            if ajouter_qr:
                # Obtenir les dimensions de la page
                page_width = float(page_obj.mediabox.width)
                page_height = float(page_obj.mediabox.height)

                # Créer l'overlay avec le QR
                overlay_buffer = cls.creer_overlay_qr(
                    qr_image, page_width, page_height,
                    position, type_document, code_verification
                )

                # Fusionner l'overlay sur la page
                overlay_reader = PdfReader(overlay_buffer)
                page_obj.merge_page(overlay_reader.pages[0])

            pdf_writer.add_page(page_obj)

        # Écrire le PDF final
        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        return output_buffer.getvalue()

    @classmethod
    def generer_toutes_versions(cls, pdf_bytes, code_verification, url_verification,
                                 position='bottom-right', page='all'):
        """
        Génère les 3 versions du document : Original, Second Original, Copie.

        Args:
            pdf_bytes: PDF original en bytes
            code_verification: Code unique de l'acte
            url_verification: URL de vérification
            position: Position du QR
            page: Page(s) où ajouter le QR

        Returns:
            dict: {
                'original': bytes,
                'second_original': bytes,
                'copie': bytes
            }
        """
        return {
            'original': cls.incruster_qr_sur_pdf(
                pdf_bytes, code_verification, url_verification,
                type_document=cls.TYPE_ORIGINAL,
                position=position, page=page
            ),
            'second_original': cls.incruster_qr_sur_pdf(
                pdf_bytes, code_verification, url_verification,
                type_document=cls.TYPE_SECOND_ORIGINAL,
                position=position, page=page
            ),
            'copie': cls.incruster_qr_sur_pdf(
                pdf_bytes, code_verification, url_verification,
                type_document=cls.TYPE_COPIE,
                position=position, page=page
            ),
        }

    @classmethod
    def valider_pdf(cls, pdf_bytes):
        """
        Valide qu'un fichier est bien un PDF valide.

        Args:
            pdf_bytes: Contenu du fichier

        Returns:
            tuple: (is_valid, error_message, page_count)
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(reader.pages)

            if page_count == 0:
                return False, "Le PDF ne contient aucune page", 0

            return True, None, page_count

        except Exception as e:
            return False, f"Fichier PDF invalide: {str(e)}", 0

"""
Service de génération de documents PDF
Utilise ReportLab pour la génération et QRCode pour les codes QR
"""
import io
import os
import re
from datetime import datetime, date
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

# Import conditionnel de ReportLab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, KeepTogether, HRFlowable
    )
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Import conditionnel de QRCode
try:
    import qrcode
    from qrcode.image.pil import PilImage
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class PDFGenerator:
    """Générateur de documents PDF professionnels"""

    # Couleurs de l'étude
    COLORS = {
        'primary': colors.HexColor('#1a365d'),
        'accent': colors.HexColor('#c6a962'),
        'success': colors.HexColor('#2f855a'),
        'warning': colors.HexColor('#c05621'),
        'danger': colors.HexColor('#c53030'),
        'text': colors.HexColor('#2d3748'),
        'text_light': colors.HexColor('#718096'),
        'border': colors.HexColor('#e2e8f0'),
        'background': colors.HexColor('#f7fafc'),
    }

    def __init__(self, config=None):
        """Initialise le générateur avec la configuration"""
        self.config = config or self._get_default_config()
        self.styles = self._create_styles()

    def _get_default_config(self):
        """Configuration par défaut"""
        return {
            'nom_etude': 'ÉTUDE D\'HUISSIER DE JUSTICE',
            'adresse_etude': 'Cotonou, République du Bénin',
            'telephone_etude': '+229 XX XX XX XX',
            'email_etude': 'contact@etude.bj',
            'ifu_etude': '',
            'rccm_etude': '',
            'nom_huissier': 'Maître [NOM]',
            'qualite_huissier': 'Huissier de Justice',
            'logo_path': None,
            'signature_path': None,
            'cachet_path': None,
        }

    def _create_styles(self):
        """Crée les styles personnalisés"""
        styles = getSampleStyleSheet()

        # Titre principal
        styles.add(ParagraphStyle(
            name='TitreDocument',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=6,
        ))

        # Sous-titre
        styles.add(ParagraphStyle(
            name='SousTitre',
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=self.COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=12,
        ))

        # Corps de texte
        styles.add(ParagraphStyle(
            name='CorpsTexte',
            fontName='Helvetica',
            fontSize=10,
            textColor=self.COLORS['text'],
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14,
        ))

        # Texte important
        styles.add(ParagraphStyle(
            name='TexteImportant',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=self.COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=4,
        ))

        # En-tête tableau
        styles.add(ParagraphStyle(
            name='EnTeteTableau',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))

        # Cellule tableau
        styles.add(ParagraphStyle(
            name='CelluleTableau',
            fontName='Helvetica',
            fontSize=9,
            textColor=self.COLORS['text'],
            alignment=TA_LEFT,
        ))

        # Montant
        styles.add(ParagraphStyle(
            name='Montant',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=self.COLORS['accent'],
            alignment=TA_RIGHT,
        ))

        # Pied de page
        styles.add(ParagraphStyle(
            name='PiedPage',
            fontName='Helvetica',
            fontSize=8,
            textColor=self.COLORS['text_light'],
            alignment=TA_CENTER,
        ))

        # Référence
        styles.add(ParagraphStyle(
            name='Reference',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=self.COLORS['accent'],
            alignment=TA_RIGHT,
        ))

        return styles

    def generate_qr_code(self, data, size=100):
        """Génère un code QR"""
        if not QRCODE_AVAILABLE:
            return None

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1a365d", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return Image(buffer, width=size, height=size)

    def _add_header(self, elements, titre=None):
        """Ajoute l'en-tête de l'étude"""
        # Logo et informations de l'étude
        header_data = [
            [
                Paragraph(self.config['nom_etude'], self.styles['TitreDocument']),
            ],
            [
                Paragraph(self.config['nom_huissier'], self.styles['TexteImportant']),
            ],
            [
                Paragraph(self.config['qualite_huissier'], self.styles['CorpsTexte']),
            ],
            [
                Paragraph(self.config['adresse_etude'], self.styles['CorpsTexte']),
            ],
            [
                Paragraph(f"Tél: {self.config['telephone_etude']}", self.styles['CorpsTexte']),
            ],
        ]

        header_table = Table(header_data, colWidths=[170*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(header_table)

        # Ligne de séparation
        elements.append(Spacer(1, 6*mm))
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.COLORS['accent'],
            spaceBefore=0,
            spaceAfter=6*mm
        ))

        # Titre du document
        if titre:
            elements.append(Paragraph(titre, self.styles['TitreDocument']))
            elements.append(Spacer(1, 6*mm))

    def _add_footer(self, canvas_obj, doc):
        """Ajoute le pied de page"""
        canvas_obj.saveState()
        canvas_obj.setStrokeColor(self.COLORS['accent'])
        canvas_obj.setLineWidth(1)
        canvas_obj.line(20*mm, 20*mm, 190*mm, 20*mm)

        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(self.COLORS['text_light'])

        # Informations de l'étude
        footer_text = f"{self.config['nom_etude']} - {self.config['adresse_etude']}"
        if self.config['ifu_etude']:
            footer_text += f" - IFU: {self.config['ifu_etude']}"

        canvas_obj.drawCentredString(105*mm, 14*mm, footer_text)

        # Numéro de page
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawRightString(190*mm, 10*mm, f"Page {page_num}")

        # Date d'impression
        date_impression = datetime.now().strftime("%d/%m/%Y à %H:%M")
        canvas_obj.drawString(20*mm, 10*mm, f"Imprimé le {date_impression}")

        canvas_obj.restoreState()

    def _format_montant(self, montant):
        """Formate un montant en FCFA"""
        if montant is None:
            return "0 FCFA"
        if isinstance(montant, str):
            try:
                montant = Decimal(montant)
            except:
                return f"{montant} FCFA"
        return f"{montant:,.0f} FCFA".replace(",", " ")

    def _format_date(self, date_obj, format_type='long'):
        """Formate une date"""
        if date_obj is None:
            return ""
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return date_obj

        mois = [
            '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]

        if format_type == 'long':
            return f"{date_obj.day} {mois[date_obj.month]} {date_obj.year}"
        elif format_type == 'court':
            return date_obj.strftime("%d/%m/%Y")
        else:
            return str(date_obj)

    def generer_fiche_dossier(self, dossier, output_path=None):
        """
        Génère la fiche complète d'un dossier (carte du dossier)

        Args:
            dossier: Instance du modèle Dossier
            output_path: Chemin de sortie (optionnel, retourne bytes si non spécifié)
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # En-tête
        self._add_header(elements, "FICHE DU DOSSIER")

        # Référence et statut
        ref_statut_data = [
            [
                Paragraph(f"Référence: <b>{dossier.reference}</b>", self.styles['Reference']),
                Paragraph(f"Statut: <b>{dossier.get_statut_display()}</b>", self.styles['TexteImportant']),
            ]
        ]
        ref_table = Table(ref_statut_data, colWidths=[85*mm, 85*mm])
        ref_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(ref_table)
        elements.append(Spacer(1, 6*mm))

        # Informations générales
        elements.append(Paragraph("INFORMATIONS GÉNÉRALES", self.styles['SousTitre']))

        info_data = [
            ["Nature de l'affaire:", dossier.get_type_dossier_display()],
            ["Type:", "Contentieux" if dossier.is_contentieux else "Non contentieux"],
            ["Date d'ouverture:", self._format_date(dossier.date_creation, 'long')],
            ["Affecté à:", str(dossier.affecte_a) if dossier.affecte_a else "Non affecté"],
        ]

        info_table = Table(info_data, colWidths=[50*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['primary']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLORS['text']),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6*mm))

        # Parties - Créancier(s)
        elements.append(Paragraph("CRÉANCIER(S) / DEMANDEUR(S)", self.styles['SousTitre']))

        if dossier.demandeurs.exists():
            for partie in dossier.demandeurs.all():
                partie_info = self._format_partie(partie)
                elements.append(Paragraph(partie_info, self.styles['CorpsTexte']))
        else:
            elements.append(Paragraph("Aucun créancier enregistré", self.styles['CorpsTexte']))

        elements.append(Spacer(1, 4*mm))

        # Parties - Débiteur(s)
        elements.append(Paragraph("DÉBITEUR(S) / DÉFENDEUR(S)", self.styles['SousTitre']))

        if dossier.defendeurs.exists():
            for partie in dossier.defendeurs.all():
                partie_info = self._format_partie(partie)
                elements.append(Paragraph(partie_info, self.styles['CorpsTexte']))
        else:
            elements.append(Paragraph("Aucun débiteur enregistré", self.styles['CorpsTexte']))

        elements.append(Spacer(1, 6*mm))

        # Montants
        elements.append(Paragraph("SITUATION FINANCIÈRE", self.styles['SousTitre']))

        montants_data = [
            ["Principal de la créance:", self._format_montant(dossier.montant_creance)],
            ["Date de la créance:", self._format_date(dossier.date_creance, 'long') if dossier.date_creance else "Non précisée"],
        ]

        montants_table = Table(montants_data, colWidths=[70*mm, 100*mm])
        montants_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['primary']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLORS['accent']),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['background']),
            ('BOX', (0, 0), (-1, -1), 1, self.COLORS['border']),
        ]))
        elements.append(montants_table)
        elements.append(Spacer(1, 6*mm))

        # QR Code
        qr_data = f"DOSSIER:{dossier.reference}|DATE:{dossier.date_creation}|STATUT:{dossier.statut}"
        qr_image = self.generate_qr_code(qr_data, size=80)
        if qr_image:
            qr_section = [
                [
                    Paragraph("Scannez pour accéder au dossier", self.styles['PiedPage']),
                    qr_image
                ]
            ]
            qr_table = Table(qr_section, colWidths=[90*mm, 80*mm])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(qr_table)

        # Construction du document
        doc.build(elements, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return output_path

        return buffer.getvalue()

    def _format_partie(self, partie):
        """Formate les informations d'une partie"""
        if partie.type_personne == 'physique':
            info = f"<b>{partie.nom} {partie.prenoms or ''}</b>"
            if partie.profession:
                info += f", {partie.profession}"
            if partie.domicile:
                info += f"<br/>Domicilié(e) à: {partie.domicile}"
        else:
            info = f"<b>{partie.denomination}</b>"
            if partie.forme_juridique:
                info += f" ({partie.forme_juridique})"
            if partie.siege_social:
                info += f"<br/>Siège social: {partie.siege_social}"
            if partie.representant:
                info += f"<br/>Représentée par: {partie.representant}"

        if partie.telephone:
            info += f"<br/>Tél: {partie.telephone}"
        if partie.ifu:
            info += f" | IFU: {partie.ifu}"

        return info

    def generer_acte_procedure(self, acte_data, modele, output_path=None):
        """
        Génère un acte de procédure à partir d'un modèle

        Args:
            acte_data: Dictionnaire avec les données de l'acte
            modele: Instance de ModeleDocument ou contenu HTML
            output_path: Chemin de sortie (optionnel)
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # En-tête
        titre = acte_data.get('titre', 'ACTE DE PROCÉDURE')
        self._add_header(elements, titre)

        # Numéro d'acte et date
        numero_acte = acte_data.get('numero_acte', '')
        date_acte = acte_data.get('date_acte', datetime.now())

        ref_data = [
            [
                Paragraph(f"Acte N° {numero_acte}", self.styles['Reference']),
                Paragraph(f"Le {self._format_date(date_acte, 'long')}", self.styles['TexteImportant']),
            ]
        ]
        ref_table = Table(ref_data, colWidths=[85*mm, 85*mm])
        ref_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(ref_table)
        elements.append(Spacer(1, 8*mm))

        # Contenu de l'acte
        contenu = acte_data.get('contenu', '')
        if hasattr(modele, 'contenu_template'):
            contenu = self._process_template(modele.contenu_template, acte_data)

        # Diviser le contenu en paragraphes
        paragraphes = contenu.split('\n\n')
        for para in paragraphes:
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['CorpsTexte']))
                elements.append(Spacer(1, 3*mm))

        elements.append(Spacer(1, 10*mm))

        # Signature
        signature_section = [
            [
                Paragraph("Fait à Cotonou,", self.styles['CorpsTexte']),
            ],
            [
                Paragraph(f"Le {self._format_date(date_acte, 'long')}", self.styles['CorpsTexte']),
            ],
            [
                Spacer(1, 15*mm),
            ],
            [
                Paragraph(f"<b>{self.config['nom_huissier']}</b>", self.styles['TexteImportant']),
            ],
            [
                Paragraph(self.config['qualite_huissier'], self.styles['CorpsTexte']),
            ],
        ]

        sig_table = Table(signature_section, colWidths=[170*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ]))
        elements.append(sig_table)

        # Construction
        doc.build(elements, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return output_path

        return buffer.getvalue()

    def generer_facture(self, facture, output_path=None):
        """
        Génère une facture PDF conforme MECeF

        Args:
            facture: Instance du modèle Facture
            output_path: Chemin de sortie (optionnel)
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )

        elements = []

        # En-tête avec logo
        self._add_header(elements, "FACTURE")

        # Informations facture
        info_facture = [
            [
                Paragraph(f"<b>Facture N°</b> {facture.numero}", self.styles['Reference']),
                Paragraph(f"<b>Date:</b> {self._format_date(facture.date_emission, 'long')}", self.styles['TexteImportant']),
            ],
            [
                Paragraph(f"<b>Échéance:</b> {self._format_date(facture.date_echeance, 'court')}", self.styles['CorpsTexte']),
                Paragraph(f"<b>Statut:</b> {facture.get_statut_display()}", self.styles['CorpsTexte']),
            ],
        ]

        info_table = Table(info_facture, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6*mm))

        # Client
        elements.append(Paragraph("CLIENT", self.styles['SousTitre']))
        client_info = f"<b>{facture.client}</b>"
        if facture.ifu:
            client_info += f"<br/>IFU: {facture.ifu}"
        elements.append(Paragraph(client_info, self.styles['CorpsTexte']))
        elements.append(Spacer(1, 6*mm))

        # Tableau des lignes
        elements.append(Paragraph("DÉTAIL DES PRESTATIONS", self.styles['SousTitre']))

        # En-tête du tableau
        table_data = [[
            Paragraph("Description", self.styles['EnTeteTableau']),
            Paragraph("Qté", self.styles['EnTeteTableau']),
            Paragraph("P.U. (FCFA)", self.styles['EnTeteTableau']),
            Paragraph("Total (FCFA)", self.styles['EnTeteTableau']),
        ]]

        # Lignes de facture
        for ligne in facture.lignes.all():
            total_ligne = ligne.quantite * ligne.prix_unitaire
            table_data.append([
                Paragraph(ligne.description, self.styles['CelluleTableau']),
                str(ligne.quantite),
                self._format_montant(ligne.prix_unitaire).replace(' FCFA', ''),
                self._format_montant(total_ligne).replace(' FCFA', ''),
            ])

        col_widths = [90*mm, 20*mm, 35*mm, 35*mm]
        lignes_table = Table(table_data, colWidths=col_widths)
        lignes_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            # Corps
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            # Alternance couleurs
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['background']]),
        ]))
        elements.append(lignes_table)
        elements.append(Spacer(1, 4*mm))

        # Totaux
        totaux_data = [
            ["Total HT:", self._format_montant(facture.montant_ht)],
            [f"TVA (18%):", self._format_montant(facture.montant_tva)],
            ["Total TTC:", self._format_montant(facture.montant_ttc)],
        ]

        totaux_table = Table(totaux_data, colWidths=[130*mm, 50*mm])
        totaux_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, -1), (-1, -1), self.COLORS['primary']),
            ('BACKGROUND', (0, -1), (-1, -1), self.COLORS['background']),
            ('BOX', (0, -1), (-1, -1), 1, self.COLORS['primary']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(totaux_table)
        elements.append(Spacer(1, 6*mm))

        # MECeF si disponible
        if facture.mecef_numero:
            elements.append(Paragraph("INFORMATIONS MECeF", self.styles['SousTitre']))
            mecef_info = f"""
            <b>Numéro MECeF:</b> {facture.mecef_numero}<br/>
            <b>NIM:</b> {facture.nim or 'N/A'}<br/>
            <b>Date MECeF:</b> {self._format_date(facture.date_mecef, 'court') if facture.date_mecef else 'N/A'}
            """
            elements.append(Paragraph(mecef_info, self.styles['CorpsTexte']))

            # QR Code MECeF
            if facture.mecef_qr:
                qr_image = self.generate_qr_code(facture.mecef_qr, size=80)
                if qr_image:
                    elements.append(qr_image)

        # Construction
        doc.build(elements, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return output_path

        return buffer.getvalue()

    def generer_decompte_recouvrement(self, calcul_data, dossier=None, output_path=None):
        """
        Génère un décompte de recouvrement OHADA

        Args:
            calcul_data: Données du calcul (résultats)
            dossier: Instance du dossier associé
            output_path: Chemin de sortie (optionnel)
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )

        elements = []

        # En-tête
        self._add_header(elements, "DÉCOMPTE DE RECOUVREMENT")
        elements.append(Paragraph("(Conformément aux dispositions de l'OHADA)", self.styles['PiedPage']))
        elements.append(Spacer(1, 6*mm))

        # Référence dossier si disponible
        if dossier:
            elements.append(Paragraph(f"Dossier: {dossier.reference}", self.styles['Reference']))
            elements.append(Spacer(1, 4*mm))

        # Principal
        elements.append(Paragraph("PRINCIPAL", self.styles['SousTitre']))
        montant_principal = calcul_data.get('montant_principal', 0)
        elements.append(Paragraph(
            f"Montant de la créance: <b>{self._format_montant(montant_principal)}</b>",
            self.styles['CorpsTexte']
        ))
        elements.append(Spacer(1, 4*mm))

        # Intérêts
        elements.append(Paragraph("INTÉRÊTS", self.styles['SousTitre']))
        interets = calcul_data.get('interets', {})

        interets_data = [
            ["Type d'intérêts:", interets.get('type_taux', 'Légal OHADA')],
            ["Taux appliqué:", f"{interets.get('taux', 6)}%"],
            ["Période:", f"Du {interets.get('date_debut', '')} au {interets.get('date_fin', '')}"],
            ["Montant des intérêts:", self._format_montant(interets.get('montant', 0))],
        ]

        int_table = Table(interets_data, colWidths=[70*mm, 100*mm])
        int_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['primary']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(int_table)
        elements.append(Spacer(1, 4*mm))

        # Frais et émoluments
        if calcul_data.get('emoluments'):
            elements.append(Paragraph("FRAIS ET ÉMOLUMENTS", self.styles['SousTitre']))

            emoluments = calcul_data.get('emoluments', {})
            frais_data = []

            for item in emoluments.get('details', []):
                frais_data.append([item.get('libelle', ''), self._format_montant(item.get('montant', 0))])

            if frais_data:
                frais_table = Table(frais_data, colWidths=[120*mm, 50*mm])
                frais_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
                ]))
                elements.append(frais_table)

            elements.append(Spacer(1, 4*mm))
            elements.append(Paragraph(
                f"Total émoluments: <b>{self._format_montant(emoluments.get('total', 0))}</b>",
                self.styles['Montant']
            ))

        elements.append(Spacer(1, 8*mm))

        # Total général
        total_general = calcul_data.get('total_general', 0)
        elements.append(HRFlowable(
            width="100%", thickness=2, color=self.COLORS['primary']
        ))
        elements.append(Spacer(1, 4*mm))

        total_data = [[
            Paragraph("TOTAL GÉNÉRAL À RECOUVRER:", self.styles['TexteImportant']),
            Paragraph(f"<b>{self._format_montant(total_general)}</b>", self.styles['Montant']),
        ]]
        total_table = Table(total_data, colWidths=[120*mm, 50*mm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['background']),
            ('BOX', (0, 0), (-1, -1), 2, self.COLORS['primary']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(total_table)

        elements.append(Spacer(1, 15*mm))

        # Signature
        elements.append(Paragraph(
            f"Fait à Cotonou, le {self._format_date(datetime.now(), 'long')}",
            self.styles['CorpsTexte']
        ))
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(
            f"<b>{self.config['nom_huissier']}</b><br/>{self.config['qualite_huissier']}",
            self.styles['TexteImportant']
        ))

        # Construction
        doc.build(elements, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return output_path

        return buffer.getvalue()

    def generer_lettre(self, lettre_data, modele=None, output_path=None):
        """
        Génère une lettre (mise en demeure, relance, etc.)

        Args:
            lettre_data: Dictionnaire avec les données de la lettre
            modele: Instance de ModeleDocument (optionnel)
            output_path: Chemin de sortie (optionnel)
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab n'est pas installé")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # En-tête
        self._add_header(elements)

        # Date et lieu
        elements.append(Paragraph(
            f"Cotonou, le {self._format_date(lettre_data.get('date', datetime.now()), 'long')}",
            self.styles['CorpsTexte']
        ))
        elements.append(Spacer(1, 6*mm))

        # Référence
        if lettre_data.get('reference'):
            elements.append(Paragraph(
                f"<b>Réf:</b> {lettre_data['reference']}",
                self.styles['Reference']
            ))
            elements.append(Spacer(1, 4*mm))

        # Destinataire
        destinataire = lettre_data.get('destinataire', {})
        dest_text = f"""
        <b>{destinataire.get('nom', '')}</b><br/>
        {destinataire.get('adresse', '')}<br/>
        {destinataire.get('ville', '')}
        """
        elements.append(Paragraph(dest_text, self.styles['CorpsTexte']))
        elements.append(Spacer(1, 8*mm))

        # Objet
        objet = lettre_data.get('objet', '')
        elements.append(Paragraph(f"<b>Objet:</b> {objet}", self.styles['TexteImportant']))
        elements.append(Spacer(1, 6*mm))

        # Corps de la lettre
        contenu = lettre_data.get('contenu', '')
        if modele and hasattr(modele, 'contenu_template'):
            contenu = self._process_template(modele.contenu_template, lettre_data)

        paragraphes = contenu.split('\n\n')
        for para in paragraphes:
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['CorpsTexte']))
                elements.append(Spacer(1, 3*mm))

        elements.append(Spacer(1, 10*mm))

        # Formule de politesse
        formule = lettre_data.get('formule_politesse', "Veuillez agréer l'expression de mes salutations distinguées.")
        elements.append(Paragraph(formule, self.styles['CorpsTexte']))

        elements.append(Spacer(1, 15*mm))

        # Signature
        elements.append(Paragraph(
            f"<b>{self.config['nom_huissier']}</b><br/>{self.config['qualite_huissier']}",
            self.styles['TexteImportant']
        ))

        # Construction
        doc.build(elements, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return output_path

        return buffer.getvalue()

    def _process_template(self, template_content, variables):
        """
        Remplace les variables dans un template

        Variables supportées: {{nom_variable}}
        """
        result = template_content

        # Variables standards
        now = datetime.now()
        standard_vars = {
            'date_jour': self._format_date(now, 'long'),
            'date_court': self._format_date(now, 'court'),
            'heure': now.strftime("%H:%M"),
            'etude_nom': self.config['nom_etude'],
            'etude_adresse': self.config['adresse_etude'],
            'etude_telephone': self.config['telephone_etude'],
            'huissier_nom': self.config['nom_huissier'],
        }

        # Fusionner avec les variables passées
        all_vars = {**standard_vars, **variables}

        # Remplacer les variables
        for key, value in all_vars.items():
            pattern = r'\{\{\s*' + key + r'\s*\}\}'
            if value is not None:
                result = re.sub(pattern, str(value), result)

        # Supprimer les variables non remplacées
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        return result


# Fonction utilitaire pour la génération rapide
def generer_document_rapide(type_document, data, output_path=None):
    """
    Fonction utilitaire pour générer rapidement un document

    Args:
        type_document: 'fiche_dossier', 'acte', 'facture', 'decompte', 'lettre'
        data: Données appropriées selon le type
        output_path: Chemin de sortie (optionnel)

    Returns:
        Bytes du PDF ou chemin du fichier
    """
    generator = PDFGenerator()

    if type_document == 'fiche_dossier':
        return generator.generer_fiche_dossier(data, output_path)
    elif type_document == 'acte':
        return generator.generer_acte_procedure(data, data.get('modele'), output_path)
    elif type_document == 'facture':
        return generator.generer_facture(data, output_path)
    elif type_document == 'decompte':
        return generator.generer_decompte_recouvrement(data, data.get('dossier'), output_path)
    elif type_document == 'lettre':
        return generator.generer_lettre(data, data.get('modele'), output_path)
    else:
        raise ValueError(f"Type de document inconnu: {type_document}")

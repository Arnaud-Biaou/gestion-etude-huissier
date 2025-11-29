"""
Génération PDF complète des mémoires de cédules
- Page 1 (portrait) : En-tête + RÉQUISITION + Signatures/Visas
- Page 2 (portrait) : EXÉCUTOIRE + Signatures/Visas
- Page 3+ (paysage) : Tableau des coûts + Certification + Signature huissier
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from decimal import Decimal
from datetime import datetime


def nombre_en_lettres(nombre):
    """Convertit un nombre en lettres (FCFA)"""
    unites = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
              'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf']
    dizaines = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 'soixante', 'quatre-vingt', 'quatre-vingt']

    def convertir_bloc(n):
        if n == 0:
            return ''
        elif n < 20:
            return unites[n]
        elif n < 100:
            q, r = divmod(n, 10)
            if q == 7 or q == 9:
                q -= 1
                r += 10
            base = dizaines[q]
            if q == 8 and r == 0:
                base = 'quatre-vingts'
            if r == 1 and q != 8:
                return base + ' et un'
            return base + (' ' + unites[r] if r else '')
        elif n < 1000:
            q, r = divmod(n, 100)
            if q == 1:
                return 'cent' + (' ' + convertir_bloc(r) if r else '')
            return unites[q] + ' cent' + ('s' if r == 0 else ' ' + convertir_bloc(r))
        elif n < 1000000:
            q, r = divmod(n, 1000)
            mille = 'mille' if q == 1 else convertir_bloc(q) + ' mille'
            return mille + (' ' + convertir_bloc(r) if r else '')
        elif n < 1000000000:
            q, r = divmod(n, 1000000)
            million = 'un million' if q == 1 else convertir_bloc(q) + ' millions'
            return million + (' ' + convertir_bloc(r) if r else '')
        else:
            q, r = divmod(n, 1000000000)
            milliard = 'un milliard' if q == 1 else convertir_bloc(q) + ' milliards'
            return milliard + (' ' + convertir_bloc(r) if r else '')

    nombre_int = int(nombre)
    if nombre_int == 0:
        return 'zéro franc CFA'

    return convertir_bloc(nombre_int).strip().upper() + ' FRANCS CFA'


def generer_pdf_memoire_complet(memoire):
    """
    Génère le PDF complet du mémoire :
    - Page 1 (portrait) : En-tête + RÉQUISITION + Signatures/Visas
    - Page 2 (portrait) : EXÉCUTOIRE + Signatures/Visas
    - Page 3+ (paysage) : Tableau des coûts + Certification + Signature huissier
    """
    buffer = BytesIO()

    # Récupérer les infos de juridiction
    juridiction = memoire.juridiction
    if not juridiction:
        # Fallback si pas de juridiction définie
        autorite_req = {
            'titre': 'Procureur de la République',
            'nom': '',
            'juridiction': memoire.autorite_requerante.nom if memoire.autorite_requerante else 'Non défini',
            'ville': memoire.autorite_requerante.ville if memoire.autorite_requerante else 'Parakou',
            'avec_visa': False
        }
        autorite_exec = {
            'titre': 'Président du Tribunal',
            'nom': '',
            'juridiction': memoire.autorite_requerante.nom if memoire.autorite_requerante else 'Non défini',
            'ville': memoire.autorite_requerante.ville if memoire.autorite_requerante else 'Parakou',
            'avec_visa': False
        }
        juridiction_nom = memoire.autorite_requerante.nom if memoire.autorite_requerante else 'Non défini'
        juridiction_ville = memoire.autorite_requerante.ville if memoire.autorite_requerante else 'Parakou'
        type_juridiction = 'tpi'
    else:
        autorite_req = juridiction.get_autorite_requisition()
        autorite_exec = juridiction.get_autorite_executoire()
        juridiction_nom = juridiction.nom
        juridiction_ville = juridiction.ville
        type_juridiction = juridiction.type_juridiction

    # Montant en lettres
    montant_lettres = nombre_en_lettres(memoire.montant_total)
    montant_chiffres = f"{int(memoire.montant_total):,}".replace(',', ' ')

    # Configuration étude
    try:
        from parametres.models import ConfigurationEtude
        config = ConfigurationEtude.get_instance()
        huissier_nom = config.nom_etude or "Martial Arnaud BIAOU"
        juridiction_competence = config.juridiction or "Tribunal de Première Instance de Première Classe et la Cour d'Appel de Parakou"
        ville_huissier = config.adresse_ville if config.adresse_ville else 'Parakou'
    except Exception:
        huissier_nom = "Martial Arnaud BIAOU"
        juridiction_competence = "Tribunal de Première Instance de Première Classe et la Cour d'Appel de Parakou"
        ville_huissier = 'Parakou'

    huissier_titre = f"Huissier de Justice près le {juridiction_competence}"

    # Mois en toutes lettres
    mois_noms = [
        '', 'JANVIER', 'FÉVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN',
        'JUILLET', 'AOÛT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DÉCEMBRE'
    ]
    mois_nom = mois_noms[memoire.mois] if 1 <= memoire.mois <= 12 else ''

    # Styles
    styles = getSampleStyleSheet()

    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )

    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=10
    )

    style_normal = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    )

    style_signature_droite = ParagraphStyle(
        'SignatureDroite',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_RIGHT
    )

    style_signature_gauche = ParagraphStyle(
        'SignatureGauche',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT
    )

    style_centre = ParagraphStyle(
        'Centre',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER
    )

    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=10,
        spaceBefore=20,
        textDecoration='underline',
        fontName='Helvetica-Bold'
    )

    # Document portrait pour pages 1 et 2
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    elements = []

    # ============================================================
    # PAGE 1 : EN-TÊTE + RÉQUISITION
    # ============================================================

    # En-tête
    elements.append(Paragraph(f"<b>Mémoire N° {memoire.numero}</b>", style_titre))
    elements.append(Paragraph(f"du mois de {mois_nom} {memoire.annee}", style_sous_titre))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>ÉTAT DES INDEMNITÉS DUES À</b>", style_centre))
    elements.append(Paragraph(f"<b>Maître {huissier_nom}</b>", style_centre))
    elements.append(Paragraph(huissier_titre, style_centre))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Autorité requérante :</b> {juridiction_nom}", style_normal))
    elements.append(Spacer(1, 30))

    # RÉQUISITION
    elements.append(Paragraph("<b><u>RÉQUISITION</u></b>", style_titre))
    elements.append(Spacer(1, 15))

    # Texte de la réquisition
    texte_requisition = f"Nous ……………………………………………………………………………………………., {autorite_req['titre']} près la {juridiction_nom} ;"
    elements.append(Paragraph(texte_requisition, style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Vu le présent mémoire, les pièces jointes ;", style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Vu le décret N° 2012-143 du 07 juin 2012 portant réglementation des frais de justice criminelle, "
        "correctionnelle et de police en ses articles 81 et suivants ;",
        style_normal
    ))
    elements.append(Spacer(1, 10))

    # Requérons selon le type de juridiction
    if type_juridiction == 'tpi':
        titre_exec = f"Monsieur le Président du {juridiction_nom}"
    elif type_juridiction == 'cour_appel':
        titre_exec = f"Monsieur le Président de la {juridiction_nom}"
    else:  # cour_speciale
        titre_exec = f"Monsieur le Président de la {juridiction.nom_court if juridiction else juridiction_nom}"

    elements.append(Paragraph(f"Requérons qu'il soit délivré exécutoire par {titre_exec} ;", style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"Sur la caisse du Trésor public, chapitre des frais de justice, pour paiement de la somme de "
        f"<b>FCFA {montant_lettres.upper()} ({montant_chiffres})</b>.",
        style_normal
    ))
    elements.append(Spacer(1, 40))

    # Date et lieu - aligné à droite
    elements.append(Paragraph(f"{juridiction_ville}, le ……..……………………………….. {memoire.annee}", style_signature_droite))
    elements.append(Spacer(1, 20))

    # Signatures réquisition selon type de juridiction
    if autorite_req.get('avec_visa', False):
        # TPI : Visa Procureur Général à gauche, Signature Procureur République à droite
        data_sig = [
            [
                Paragraph("<b>Vu :</b>", style_signature_gauche),
                Paragraph(f"<b>Le {autorite_req['titre']}</b>", style_signature_droite)
            ],
            [
                Paragraph(f"Le {autorite_req.get('visa_titre', 'Procureur Général')}", style_signature_gauche),
                ""
            ],
            ["", ""],
            ["", ""],
            ["", ""],
        ]
        table_sig = Table(data_sig, colWidths=[8*cm, 8*cm])
        table_sig.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(table_sig)
    else:
        # Cour d'Appel ou Spéciale : Signature seule à droite
        elements.append(Paragraph(f"<b>Le {autorite_req['titre']}</b>", style_signature_droite))
        elements.append(Spacer(1, 60))

    # Saut de page
    elements.append(PageBreak())

    # ============================================================
    # PAGE 2 : EXÉCUTOIRE
    # ============================================================

    elements.append(Paragraph("<b><u>EXÉCUTOIRE</u></b>", style_titre))
    elements.append(Spacer(1, 20))

    # Texte de l'exécutoire
    if type_juridiction == 'tpi':
        titre_nous = f"Président du {juridiction_nom}"
    elif type_juridiction == 'cour_appel':
        titre_nous = f"Président de la {juridiction_nom}"
    else:  # cour_speciale
        titre_nous = f"Président de la {juridiction.nom_court if juridiction else juridiction_nom}"

    texte_executoire = f"Nous ………………………………………………………………………………………………………., {titre_nous} ;"
    elements.append(Paragraph(texte_executoire, style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Vu la réquisition ci-dessus, les pièces jointes et le texte ci-dessus visé ;", style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"Avons arrêté et rendu exécutoire le mémoire ci-contre pour la somme de "
        f"<b>FCFA {montant_lettres.upper()} ({montant_chiffres})</b>.",
        style_normal
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Montant de la taxe que nous avons fait par application des articles susvisés ;", style_normal))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"Et attendu qu'il n'y a pas de partie civile en cause, ordonnons que ladite somme soit payée à "
        f"Maître {huissier_nom}, {huissier_titre}, par les soins de l'Administration.",
        style_normal
    ))
    elements.append(Spacer(1, 40))

    # Date et lieu - aligné à droite
    elements.append(Paragraph(f"{juridiction_ville}, le ……………………………………….. {memoire.annee}", style_signature_droite))
    elements.append(Spacer(1, 20))

    # Signatures exécutoire selon type de juridiction
    if autorite_exec.get('avec_visa', False):
        # TPI : Visa Président Cour d'Appel à gauche, Signature Président TPI à droite
        data_sig = [
            [
                Paragraph("<b>Vu :</b>", style_signature_gauche),
                Paragraph("<b>Le Président</b>", style_signature_droite)
            ],
            [
                Paragraph(f"Le {autorite_exec.get('visa_titre', 'Président de la Cour')}", style_signature_gauche),
                ""
            ],
            ["", ""],
            ["", ""],
            ["", ""],
        ]
        table_sig = Table(data_sig, colWidths=[8*cm, 8*cm])
        table_sig.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(table_sig)
    else:
        # Cour d'Appel ou Spéciale : Signature seule à droite
        elements.append(Paragraph("<b>Le Président</b>", style_signature_droite))
        elements.append(Spacer(1, 60))

    # Saut de page vers le tableau
    elements.append(PageBreak())

    # ============================================================
    # PAGE 3+ : TABLEAU DES COÛTS
    # ============================================================

    # Encadré références légales
    ref_legales = """
    <b>Références légales :</b><br/>
    • Décret N° 2012-143 du 07 juin 2012 - Frais de justice criminelle, correctionnelle et de police (Art. 81 et suivants)<br/>
    • Décret N° 2012-435 du 19 novembre 2012 - Modification article 43<br/>
    • Décret N° 2007-155 du 03 avril 2007 - Frais de mission à l'intérieur du territoire (Groupe II)
    """
    elements.append(Paragraph(ref_legales, style_normal))
    elements.append(Spacer(1, 20))

    # Titre du tableau
    elements.append(Paragraph(f"<b>DÉTAIL DES ACTES - MÉMOIRE N° {memoire.numero}</b>", style_titre))
    elements.append(Paragraph(f"{mois_nom} {memoire.annee} - {juridiction_nom}", style_sous_titre))
    elements.append(Spacer(1, 15))

    # Tableau des affaires
    for affaire in memoire.affaires.all().prefetch_related('destinataires__actes'):
        # Titre affaire
        elements.append(Paragraph(
            f"<b>Affaire : {affaire.numero_parquet}</b> - {affaire.intitule_affaire}",
            style_normal
        ))
        elements.append(Spacer(1, 5))

        # Tableau des destinataires et actes
        table_data = [['Destinataire', 'Acte', 'Date', 'Base', 'Copies', 'Pièces', 'Transport', 'Mission', 'Total']]

        for dest in affaire.destinataires.all():
            first_row = True
            dest_nom = f"{dest.get_nom_complet()}\n{dest.localite}"
            if dest.distance_km > 0:
                dest_nom += f" ({dest.distance_km} km)"

            for acte in dest.actes.all():
                row = [
                    dest_nom if first_row else '',
                    acte.get_type_acte_display()[:20],
                    acte.date_acte.strftime('%d/%m/%Y') if acte.date_acte else '',
                    f"{int(acte.montant_base):,}",
                    f"{int(acte.montant_copies):,}" if acte.montant_copies else '-',
                    f"{int(acte.montant_pieces):,}" if acte.montant_pieces else '-',
                    f"{int(dest.frais_transport):,}" if first_row and dest.frais_transport else '-',
                    f"{int(dest.frais_mission):,}" if first_row and dest.frais_mission else '-',
                    f"{int(acte.montant_total_acte):,}" if first_row else ''
                ]
                table_data.append(row)
                first_row = False

            # Sous-total destinataire
            table_data.append([
                '', '', '', '', '', '', '', 'Sous-total:',
                f"{int(dest.montant_total_destinataire):,}"
            ])

        # Total affaire
        table_data.append([
            '', '', '', '', '', '', '', f'TOTAL {affaire.numero_parquet}:',
            f"{int(affaire.montant_total_affaire):,}"
        ])

        # Créer le tableau
        table = Table(table_data, colWidths=[4*cm, 2.5*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#c6a962')),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 15))

    # Total général
    elements.append(Spacer(1, 20))
    total_data = [
        ['TOTAL GÉNÉRAL DU MÉMOIRE', f"{int(memoire.montant_total):,} FCFA"]
    ]
    total_table = Table(total_data, colWidths=[12*cm, 5*cm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(total_table)

    # Montant en lettres
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        f"<i>Arrêté le présent mémoire à la somme de : <b>{montant_lettres}</b></i>",
        style_normal
    ))

    # ============================================================
    # FIN DU MÉMOIRE - CERTIFICATION ET SIGNATURE HUISSIER
    # ============================================================

    elements.append(Spacer(1, 40))

    # Texte de certification
    texte_certification = f"Je soussigné certifie véritable le présent mémoire pour la somme de <b>FRANCS CFA {montant_lettres.upper()} ({montant_chiffres})</b>"
    elements.append(Paragraph(texte_certification, style_normal))
    elements.append(Spacer(1, 20))

    # Date et lieu - aligné à droite
    if memoire.date_certification:
        date_certification = memoire.date_certification.strftime('%d %B %Y')
    else:
        date_certification = datetime.now().strftime('%d %B %Y')

    # Traduire le mois en français
    mois_fr = {
        'January': 'janvier', 'February': 'février', 'March': 'mars',
        'April': 'avril', 'May': 'mai', 'June': 'juin',
        'July': 'juillet', 'August': 'août', 'September': 'septembre',
        'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
    }
    for en, fr in mois_fr.items():
        date_certification = date_certification.replace(en, fr)

    elements.append(Paragraph(f"{ville_huissier}, le {date_certification}", style_signature_droite))
    elements.append(Spacer(1, 50))  # Espace pour signature manuscrite

    # Nom de l'huissier - aligné à droite
    elements.append(Paragraph(f"<b>Me {huissier_nom}</b>", style_signature_droite))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

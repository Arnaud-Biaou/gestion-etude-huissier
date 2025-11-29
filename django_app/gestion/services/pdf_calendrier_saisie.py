"""
Génération du PDF du calendrier de saisie immobilière
Format paysage avec tableau des étapes
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO


def generer_pdf_calendrier_saisie(calendrier):
    """
    Génère le PDF du calendrier de saisie immobilière

    Format :
    - En-tête : Juridiction
    - Titre : CALENDRIER D'EXECUTION AUX FINS DE SAISIE IMMOBILIERE
    - Affaire : Créancier c/ Débiteur(s)
    - Tableau des étapes
    """
    buffer = BytesIO()

    # Document en mode paysage pour le tableau
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    # Styles
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceAfter=12
    )
    style_affaire = ParagraphStyle(
        'Affaire',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica'
    )
    style_cell = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        leading=10
    )

    elements = []

    # ═══════════════════════════════════════════════════════════════
    # EN-TÊTE
    # ═══════════════════════════════════════════════════════════════
    elements.append(Paragraph(calendrier.juridiction.upper(), style_titre))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "<u>CALENDRIER D'EXECUTION AUX FINS DE SAISIE IMMOBILIERE</u>",
        style_sous_titre
    ))
    elements.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════════════════════
    # AFFAIRE
    # ═══════════════════════════════════════════════════════════════
    # Formater les débiteurs avec tirets
    debiteurs_liste = calendrier.debiteurs.split('\n')
    debiteurs_formates = '<br/>'.join([f"- {d.strip()}" for d in debiteurs_liste if d.strip()])

    affaire_text = f"<b>AFF :</b> {calendrier.creancier} <b>C/</b><br/>{debiteurs_formates}"
    elements.append(Paragraph(affaire_text, style_affaire))
    elements.append(Spacer(1, 15))

    # ═══════════════════════════════════════════════════════════════
    # TABLEAU DES ÉTAPES
    # ═══════════════════════════════════════════════════════════════

    # En-tête du tableau
    header = [
        Paragraph("<b>N° d'ordre</b>", style_cell),
        Paragraph("<b>Nature de l'acte</b>", style_cell),
        Paragraph("<b>Délai requis</b>", style_cell),
        Paragraph("<b>Date proposée</b>", style_cell),
        Paragraph("<b>Date butoir</b>", style_cell),
    ]

    data = [header]

    # Calculer les étapes
    etapes = calendrier.calculer_calendrier()

    for etape in etapes:
        numero = str(etape['numero'])
        nature = Paragraph(etape['nature'], style_cell)
        delai = Paragraph(etape['delai_requis'], style_cell)

        # Date proposée
        date_prop = etape.get('date_proposee')
        if date_prop is None:
            date_prop_str = ""
        elif isinstance(date_prop, tuple):
            date_prop_str = f"Entre le {date_prop[0].strftime('%d/%m/%Y')}<br/>et le {date_prop[1].strftime('%d/%m/%Y')}"
        else:
            date_prop_str = date_prop.strftime('%d/%m/%Y') if date_prop else ""

        # Date butoir
        date_but = etape.get('date_butoir')
        if date_but is None:
            date_but_str = ""
        elif isinstance(date_but, tuple):
            date_but_str = f"Pas avant le {date_but[0].strftime('%d/%m/%Y')}<br/>Et pas après le {date_but[1].strftime('%d/%m/%Y')}"
        else:
            date_but_str = date_but.strftime('%d/%m/%Y') if date_but else ""

        # Note spéciale pour certaines étapes
        note = etape.get('note', '')
        if note:
            date_but_str = note

        # Détails supplémentaires
        details = etape.get('details', [])
        if details:
            date_prop_str += '<br/>' + '<br/>'.join([f"- {d}" for d in details])

        data.append([
            numero,
            nature,
            Paragraph(etape['delai_requis'], style_cell),
            Paragraph(date_prop_str, style_cell),
            Paragraph(date_but_str, style_cell),
        ])

    # Créer le tableau
    col_widths = [1.5*cm, 6*cm, 7*cm, 5.5*cm, 5.5*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),

        # Grille
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        # Alignement
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),

        # Couleurs alternées pour les lignes
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))

    elements.append(table)

    # ═══════════════════════════════════════════════════════════════
    # PIED DE PAGE - Légende
    # ═══════════════════════════════════════════════════════════════
    elements.append(Spacer(1, 20))

    legende = """
    <b>LÉGENDE :</b><br/>
    - Les délais sont calculés en jours francs conformément aux Articles 1-13 à 1-15 de l'Acte uniforme OHADA<br/>
    - La date butoir est la date limite à respecter sous peine de sanction (caducité, déchéance, nullité)<br/>
    - La date proposée est une recommandation tenant compte des contraintes pratiques
    """
    style_legende = ParagraphStyle(
        'Legende',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666')
    )
    elements.append(Paragraph(legende, style_legende))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_pdf_calendrier_detail(calendrier):
    """
    Génère un PDF plus détaillé avec immeuble et observations
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    style_sous_titre = ParagraphStyle(
        'SousTitre',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceAfter=12
    )
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=4
    )
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica'
    )
    style_cell = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        leading=10
    )

    elements = []

    # En-tête
    elements.append(Paragraph(calendrier.juridiction.upper(), style_titre))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"<u>CALENDRIER D'EXECUTION AUX FINS DE SAISIE IMMOBILIERE</u><br/>Référence : {calendrier.reference}",
        style_sous_titre
    ))
    elements.append(Spacer(1, 12))

    # Parties
    elements.append(Paragraph("<b>PARTIES :</b>", style_section))
    debiteurs_liste = calendrier.debiteurs.split('\n')
    debiteurs_formates = '<br/>'.join([f"    - {d.strip()}" for d in debiteurs_liste if d.strip()])
    elements.append(Paragraph(f"<b>Créancier poursuivant :</b> {calendrier.creancier}", style_normal))
    elements.append(Paragraph(f"<b>Débiteur(s) saisi(s) :</b><br/>{debiteurs_formates}", style_normal))
    elements.append(Spacer(1, 8))

    # Immeuble
    elements.append(Paragraph("<b>IMMEUBLE :</b>", style_section))
    elements.append(Paragraph(calendrier.designation_immeuble, style_normal))
    if calendrier.titre_foncier:
        elements.append(Paragraph(f"<b>Titre foncier N° :</b> {calendrier.titre_foncier}", style_normal))
    elements.append(Spacer(1, 12))

    # Tableau des étapes
    elements.append(Paragraph("<b>CALENDRIER DES ÉTAPES :</b>", style_section))

    header = [
        Paragraph("<b>N°</b>", style_cell),
        Paragraph("<b>Nature de l'acte</b>", style_cell),
        Paragraph("<b>Article</b>", style_cell),
        Paragraph("<b>Délai requis</b>", style_cell),
        Paragraph("<b>Date proposée</b>", style_cell),
        Paragraph("<b>Date butoir</b>", style_cell),
    ]

    data = [header]
    etapes = calendrier.calculer_calendrier()

    for etape in etapes:
        numero = str(etape['numero'])
        nature = Paragraph(etape['nature'], style_cell)
        article = Paragraph(etape.get('article', ''), style_cell)
        delai = Paragraph(etape['delai_requis'], style_cell)

        date_prop = etape.get('date_proposee')
        if date_prop is None:
            date_prop_str = ""
        elif isinstance(date_prop, tuple):
            date_prop_str = f"Du {date_prop[0].strftime('%d/%m/%Y')}<br/>au {date_prop[1].strftime('%d/%m/%Y')}"
        else:
            date_prop_str = date_prop.strftime('%d/%m/%Y')

        date_but = etape.get('date_butoir')
        if date_but is None:
            date_but_str = ""
        elif isinstance(date_but, tuple):
            date_but_str = f"Min: {date_but[0].strftime('%d/%m/%Y')}<br/>Max: {date_but[1].strftime('%d/%m/%Y')}"
        else:
            date_but_str = date_but.strftime('%d/%m/%Y')

        note = etape.get('note', '')
        if note:
            date_but_str = note

        sanction = etape.get('sanction', '')
        if sanction:
            date_but_str += f"<br/><b>Sanction: {sanction}</b>"

        data.append([
            numero,
            nature,
            article,
            Paragraph(etape['delai_requis'], style_cell),
            Paragraph(date_prop_str, style_cell),
            Paragraph(date_but_str, style_cell),
        ])

    col_widths = [1*cm, 5*cm, 2*cm, 6*cm, 4.5*cm, 5*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))

    elements.append(table)

    # Observations
    if calendrier.observations:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>OBSERVATIONS :</b>", style_section))
        elements.append(Paragraph(calendrier.observations, style_normal))

    # Légende
    elements.append(Spacer(1, 20))
    legende = """
    <b>RÉFÉRENCES LÉGALES :</b> Acte uniforme OHADA portant organisation des procédures simplifiées
    de recouvrement et des voies d'exécution (révision du 17 octobre 2023) - Articles 246 à 335<br/>
    <b>Computation des délais :</b> Articles 1-13 à 1-15 (jours francs, prorogation si jour non ouvrable)
    """
    style_legende = ParagraphStyle(
        'Legende',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#666666')
    )
    elements.append(Paragraph(legende, style_legende))

    doc.build(elements)
    buffer.seek(0)
    return buffer

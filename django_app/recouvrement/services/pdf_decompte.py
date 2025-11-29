"""
Service de génération PDF pour le Décompte de Créance OHADA
Conforme aux exigences OHADA (Articles 92, 153, 184)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from decimal import Decimal
from datetime import datetime


def format_montant(montant):
    """Formate un montant avec séparateurs de milliers"""
    if montant is None:
        return "0"
    try:
        return f"{int(float(montant)):,}".replace(',', ' ')
    except (ValueError, TypeError):
        return "0"


def generer_pdf_decompte(decompte_data):
    """
    Génère un PDF du décompte conforme OHADA

    Args:
        decompte_data: dict avec toutes les données du calcul
            {
                'mode': 'complet' ou 'emoluments',
                'principal': montant,
                'interets_echus': {'total': x, 'periodes': [...]},
                'interets_echoir': {'total': x, 'periodes': [...]},
                'emoluments': {'total': x, 'details': [...], 'type_titre': '...'},
                'base_emoluments': x,
                'frais_justice': x,
                'actes': x (total) ou [{libelle, montant}, ...],
                'actes_detail': [{libelle, montant}, ...] (optionnel),
                'total': x,
                'date_debut': 'dd/mm/yyyy',
                'date_fin': 'dd/mm/yyyy',
                'majoration': bool,
                'date_limite_majoration': 'dd/mm/yyyy' ou None,
                'type_calcul': 'simple' ou 'compose',
                'type_taux': 'legal' ou 'cima' ou 'conventionnel',
                'reference_dossier': 'xxx' (optionnel),
                'creancier': 'xxx' (optionnel),
                'debiteur': 'xxx' (optionnel)
            }

    Returns:
        BytesIO: Buffer PDF
    """
    from parametres.models import ConfigurationEtude

    buffer = BytesIO()

    try:
        config = ConfigurationEtude.get_instance()
    except Exception:
        config = None

    # Styles
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        'Titre',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        fontName='Helvetica-Bold',
        spaceAfter=20
    )
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#1a365d')
    )
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3
    )
    style_droite = ParagraphStyle(
        'Droite',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    style_centre = ParagraphStyle(
        'Centre',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER
    )
    style_total = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    style_note = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        leftIndent=20
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )
    elements = []

    # ═══════════════════════════════════════════════════════════
    # EN-TÊTE
    # ═══════════════════════════════════════════════════════════

    nom_huissier = config.nom_etude if config else "ÉTUDE DE MAÎTRE"
    juridiction = config.juridiction if config else "Tribunal de Première Instance"

    # Ligne décorative
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Paragraph(f"<b>{nom_huissier.upper()}</b>", style_centre))
    elements.append(Paragraph(f"Huissier de Justice {juridiction}", style_centre))
    if config and config.adresse:
        elements.append(Paragraph(config.adresse, style_centre))
    if config and config.telephone:
        elements.append(Paragraph(f"Tél : {config.telephone}", style_centre))
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Spacer(1, 15))

    # Titre du document
    elements.append(Paragraph("<b>DÉCOMPTE DE CRÉANCE</b>", style_titre))
    elements.append(Paragraph("<i>Conforme aux règles OHADA (Articles 92, 153, 184)</i>", style_centre))
    elements.append(Paragraph(f"Établi le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", style_centre))
    elements.append(Paragraph("─" * 70, style_centre))
    elements.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════
    # INFORMATIONS GÉNÉRALES
    # ═══════════════════════════════════════════════════════════

    # Référence dossier (si disponible)
    if decompte_data.get('reference_dossier'):
        elements.append(Paragraph(f"<b>Référence :</b> {decompte_data['reference_dossier']}", style_normal))

    # Parties (si disponibles)
    if decompte_data.get('creancier'):
        elements.append(Paragraph(f"<b>Créancier :</b> {decompte_data['creancier']}", style_normal))
    if decompte_data.get('debiteur'):
        elements.append(Paragraph(f"<b>Débiteur :</b> {decompte_data['debiteur']}", style_normal))

    if decompte_data.get('reference_dossier') or decompte_data.get('creancier'):
        elements.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════════════════
    # MODE EMOLUMENTS SEULS
    # ═══════════════════════════════════════════════════════════

    if decompte_data.get('mode') == 'emoluments':
        elements.append(Paragraph("<b>I. CALCUL DES ÉMOLUMENTS PROPORTIONNELS</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        base = decompte_data.get('base', 0)
        elements.append(Paragraph(f"Base de calcul : <b>{format_montant(base)} FCFA</b>", style_normal))

        emol = decompte_data.get('emoluments', {})
        type_titre = emol.get('type_titre', 'sans')
        type_label = "Avec titre exécutoire" if type_titre == 'avec' else "Sans titre exécutoire"
        elements.append(Paragraph(f"Type de barème : <b>{type_label}</b>", style_normal))
        elements.append(Spacer(1, 10))

        # Détail par tranche
        if emol.get('details'):
            elements.append(Paragraph("<b>Détail par tranche (Décret 2017-066) :</b>", style_normal))
            table_data = [['Tranche', 'Taux', 'Base', 'Émolument']]
            for d in emol['details']:
                table_data.append([
                    d.get('tranche', '-'),
                    f"{d.get('taux', 0)}%",
                    f"{format_montant(d.get('base', 0))} F",
                    f"{format_montant(d.get('emolument', 0))} F"
                ])

            table = Table(table_data, colWidths=[5*cm, 2*cm, 4*cm, 4*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ]))
            elements.append(table)

        elements.append(Spacer(1, 15))
        elements.append(Paragraph("═" * 70, style_centre))
        elements.append(Paragraph(
            f"<b>TOTAL ÉMOLUMENTS : {format_montant(decompte_data.get('total', 0))} FCFA</b>",
            style_total
        ))
        elements.append(Paragraph("═" * 70, style_centre))

    else:
        # ═══════════════════════════════════════════════════════════
        # MODE COMPLET - DÉCOMPTE DE CRÉANCE
        # ═══════════════════════════════════════════════════════════

        # I. PRINCIPAL
        elements.append(Paragraph("<b>I. PRINCIPAL</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        principal_table = [
            ['Montant principal de la créance :', f"{format_montant(decompte_data.get('principal', 0))} FCFA"]
        ]
        table = Table(principal_table, colWidths=[10*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        # II. INTÉRÊTS ÉCHUS
        elements.append(Paragraph("<b>II. INTÉRÊTS ÉCHUS</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        date_debut = decompte_data.get('date_debut', '-')
        date_fin = decompte_data.get('date_fin', '-')
        elements.append(Paragraph(f"Période : du <b>{date_debut}</b> au <b>{date_fin}</b>", style_normal))

        type_calcul = decompte_data.get('type_calcul', 'simple')
        type_calcul_label = "Intérêts composés" if type_calcul == 'compose' else "Intérêts simples"
        elements.append(Paragraph(f"Mode de calcul : {type_calcul_label}", style_normal))

        type_taux = decompte_data.get('type_taux', 'legal')
        if type_taux == 'legal':
            taux_label = "Taux légaux UEMOA/BCEAO"
        elif type_taux == 'cima':
            taux_label = "Taux CIMA (5%/mois)"
        else:
            taux_label = "Taux conventionnel"
        elements.append(Paragraph(f"Type de taux : {taux_label}", style_normal))
        elements.append(Spacer(1, 8))

        # Détail par période/année
        interets_echus = decompte_data.get('interets_echus', {})
        periodes = interets_echus.get('periodes', [])

        if periodes:
            elements.append(Paragraph("<b>Détail par année :</b>", style_normal))
            table_data = [['Période', 'Jours', 'Taux', 'Intérêts']]
            for p in periodes:
                taux_info = f"{p.get('taux', 0):.4f}%"
                if p.get('majore'):
                    taux_info = f"{p.get('taux_applique', p.get('taux', 0)):.4f}% (majoré +50%)"
                table_data.append([
                    f"{p.get('annee', '-')} ({p.get('debut', '-')} au {p.get('fin', '-')})",
                    str(p.get('jours', 0)),
                    taux_info,
                    f"{format_montant(p.get('interet', 0))} F"
                ])

            table = Table(table_data, colWidths=[7*cm, 2*cm, 3.5*cm, 3*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ]))
            elements.append(table)

        # Note majoration si applicable
        if decompte_data.get('majoration') and decompte_data.get('date_limite_majoration'):
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(
                f"<i>* Majoration de 50% du taux légal appliquée après le {decompte_data['date_limite_majoration']} "
                f"(Loi 2024-10, Article 3)</i>",
                style_note
            ))

        total_echus = interets_echus.get('total', 0)
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(
            f"<b>SOUS-TOTAL INTÉRÊTS ÉCHUS : {format_montant(total_echus)} FCFA</b>",
            style_droite
        ))
        elements.append(Spacer(1, 10))

        # III. INTÉRÊTS À ÉCHOIR
        elements.append(Paragraph("<b>III. INTÉRÊTS À ÉCHOIR</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))
        elements.append(Paragraph(
            "<i>Intérêts pour 1 mois à compter de la date de saisie (conformément à l'OHADA pour saisie-attribution)</i>",
            style_note
        ))

        interets_echoir = decompte_data.get('interets_echoir', {})
        total_echoir = interets_echoir.get('total', 0)
        elements.append(Paragraph(
            f"<b>INTÉRÊTS À ÉCHOIR (30 jours) : {format_montant(total_echoir)} FCFA</b>",
            style_droite
        ))
        elements.append(Spacer(1, 10))

        # IV. FRAIS DE JUSTICE (si applicable)
        frais_justice = decompte_data.get('frais_justice', 0)
        if frais_justice > 0:
            elements.append(Paragraph("<b>IV. FRAIS DE JUSTICE</b>", style_section))
            elements.append(Paragraph("─" * 70, style_normal))
            elements.append(Paragraph(
                f"<b>FRAIS DE JUSTICE : {format_montant(frais_justice)} FCFA</b>",
                style_droite
            ))
            elements.append(Spacer(1, 10))

        # V. ÉMOLUMENTS PROPORTIONNELS (si applicable)
        emoluments = decompte_data.get('emoluments')
        if emoluments:
            section_num = "V" if frais_justice > 0 else "IV"
            elements.append(Paragraph(f"<b>{section_num}. ÉMOLUMENTS PROPORTIONNELS</b>", style_section))
            elements.append(Paragraph("─" * 70, style_normal))

            base_emol = decompte_data.get('base_emoluments', 0)
            elements.append(Paragraph(f"Base de calcul : {format_montant(base_emol)} FCFA", style_normal))

            type_titre = emoluments.get('type_titre', 'sans')
            type_label = "Avec titre exécutoire" if type_titre == 'avec' else "Sans titre exécutoire"
            elements.append(Paragraph(f"Type : {type_label} (Décret 2017-066)", style_normal))

            if emoluments.get('details'):
                elements.append(Spacer(1, 5))
                table_data = [['Tranche', 'Taux', 'Émolument']]
                for d in emoluments['details']:
                    table_data.append([
                        d.get('tranche', '-'),
                        f"{d.get('taux', 0)}%",
                        f"{format_montant(d.get('emolument', 0))} F"
                    ])

                table = Table(table_data, colWidths=[6*cm, 3*cm, 4*cm])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ]))
                elements.append(table)

            elements.append(Paragraph(
                f"<b>ÉMOLUMENTS : {format_montant(emoluments.get('total', 0))} FCFA</b>",
                style_droite
            ))
            elements.append(Spacer(1, 10))

        # VI. COÛTS DES ACTES DE PROCÉDURE (si applicable)
        actes = decompte_data.get('actes', 0)
        actes_detail = decompte_data.get('actes_detail', [])

        if (isinstance(actes, (int, float)) and actes > 0) or actes_detail:
            section_num = "VI" if emoluments else ("V" if frais_justice > 0 else "IV")
            elements.append(Paragraph(f"<b>{section_num}. COÛTS DES ACTES DE PROCÉDURE</b>", style_section))
            elements.append(Paragraph("─" * 70, style_normal))

            if actes_detail:
                for acte in actes_detail:
                    elements.append(Paragraph(
                        f"- {acte.get('libelle', 'Acte')} : {format_montant(acte.get('montant', 0))} FCFA",
                        style_normal
                    ))

            total_actes = actes if isinstance(actes, (int, float)) else sum(a.get('montant', 0) for a in actes_detail)
            elements.append(Paragraph(
                f"<b>TOTAL ACTES : {format_montant(total_actes)} FCFA</b>",
                style_droite
            ))
            elements.append(Spacer(1, 10))

        # ═══════════════════════════════════════════════════════════
        # TOTAL GÉNÉRAL
        # ═══════════════════════════════════════════════════════════

        elements.append(Paragraph("═" * 70, style_centre))
        elements.append(Spacer(1, 5))

        # Récapitulatif
        recap_data = [
            ['Principal :', f"{format_montant(decompte_data.get('principal', 0))} FCFA"],
            ['Intérêts échus :', f"{format_montant(total_echus)} FCFA"],
            ['Intérêts à échoir :', f"{format_montant(total_echoir)} FCFA"],
        ]

        if frais_justice > 0:
            recap_data.append(['Frais de justice :', f"{format_montant(frais_justice)} FCFA"])

        if emoluments:
            recap_data.append(['Émoluments :', f"{format_montant(emoluments.get('total', 0))} FCFA"])

        actes_total = actes if isinstance(actes, (int, float)) else sum(a.get('montant', 0) for a in (actes_detail or []))
        if actes_total > 0:
            recap_data.append(['Actes de procédure :', f"{format_montant(actes_total)} FCFA"])

        recap_data.append(['', '─' * 15])
        recap_data.append(['TOTAL GÉNÉRAL :', f"{format_montant(decompte_data.get('total', 0))} FCFA"])

        table = Table(recap_data, colWidths=[10*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, -1), (-1, -1), 13),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a365d')),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 5))
        elements.append(Paragraph("═" * 70, style_centre))

    # ═══════════════════════════════════════════════════════════
    # MENTIONS LÉGALES
    # ═══════════════════════════════════════════════════════════

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>MENTIONS LÉGALES</b>", style_section))
    elements.append(Paragraph("─" * 70, style_normal))

    mentions = [
        "• Ce décompte est établi conformément aux règles de l'OHADA (Articles 92, 153, 184)",
        "• Les intérêts sont calculés selon la règle OHADA : dies a quo compte, dies ad quem ne compte pas",
        "• Les taux légaux appliqués sont ceux fixés par la BCEAO pour la zone UEMOA",
        "• Les émoluments sont calculés selon le Décret 2017-066 du Bénin",
    ]

    if decompte_data.get('majoration'):
        mentions.append("• La majoration de 50% est appliquée conformément à la Loi 2024-10, Article 3")

    for m in mentions:
        elements.append(Paragraph(m, style_note))

    # ═══════════════════════════════════════════════════════════
    # SIGNATURE
    # ═══════════════════════════════════════════════════════════

    elements.append(Spacer(1, 30))
    ville = config.adresse_ville if config and config.adresse_ville else 'Cotonou'
    elements.append(Paragraph(f"Fait à {ville}, le {datetime.now().strftime('%d/%m/%Y')}", style_droite))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"<b>{nom_huissier}</b>", style_droite))
    elements.append(Paragraph("Huissier de Justice", style_droite))
    elements.append(Paragraph("═" * 70, style_centre))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

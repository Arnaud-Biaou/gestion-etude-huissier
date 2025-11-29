"""
Service de génération PDF pour le Point Global Créancier
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
    return f"{int(montant):,}".replace(',', ' ')


def generer_pdf_point_global(point_global):
    """
    Génère le PDF du point global créancier conforme au modèle

    Args:
        point_global: Instance de PointGlobalCreancier

    Returns:
        BytesIO: Buffer contenant le PDF
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
        fontSize=14,
        fontName='Helvetica-Bold'
    )
    style_section = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=10
    )
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10
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

    elements.append(Paragraph("═" * 70, style_centre))

    nom_huissier = config.nom_etude if config else "ÉTUDE DE MAÎTRE"
    juridiction = config.juridiction if config else "Tribunal de Première Instance"

    elements.append(Paragraph(f"<b>{nom_huissier.upper()}</b>", style_centre))
    elements.append(Paragraph(f"Huissier de Justice {juridiction}", style_centre))
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>ÉTAT RÉCAPITULATIF DES DOSSIERS DE RECOUVREMENT</b>", style_titre))
    elements.append(Paragraph(f"Établi le {datetime.now().strftime('%d/%m/%Y')}", style_centre))
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Spacer(1, 15))

    # Infos créancier
    creancier = point_global.creancier
    elements.append(Paragraph(f"<b>CRÉANCIER :</b> {creancier.nom}", style_normal))
    if creancier.adresse:
        elements.append(Paragraph(creancier.adresse, style_normal))
    if creancier.telephone:
        elements.append(Paragraph(f"Tél : {creancier.telephone}", style_normal))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(
        f"<b>Période couverte :</b> Du {point_global.periode_debut.strftime('%d/%m/%Y')} "
        f"au {point_global.periode_fin.strftime('%d/%m/%Y')}",
        style_normal
    ))
    elements.append(Paragraph(f"<b>Nombre de dossiers :</b> {point_global.nombre_dossiers}", style_normal))
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Spacer(1, 15))

    # ═══════════════════════════════════════════════════════════
    # I. SYNTHÈSE GLOBALE
    # ═══════════════════════════════════════════════════════════

    elements.append(Paragraph("<b>I. SYNTHÈSE GLOBALE</b>", style_section))
    elements.append(Paragraph("─" * 70, style_normal))

    synthese_data = [
        [f"Nombre total de dossiers confiés", "", f"{point_global.nombre_dossiers}"],
        ["", "", ""],
        [f"Dossiers en phase amiable", "", f"{point_global.nombre_amiable}"],
        [f"Dossiers en phase forcée", "", f"{point_global.nombre_force}"],
        [f"Dossiers clôturés (recouvrés)", "", f"{point_global.nombre_clotures_succes}"],
        [f"Dossiers clôturés (irrécouvrables)", "", f"{point_global.nombre_clotures_echec}"],
        [f"Dossiers en cours", "", f"{point_global.nombre_en_cours}"],
        ["", "", ""],
        ["MONTANTS GLOBAUX :", "", ""],
        [f"Total des créances confiées", "", f"{format_montant(point_global.total_creances)} FCFA"],
        [f"Total encaissé", "", f"{format_montant(point_global.total_encaisse)} FCFA"],
        [f"Total reversé au créancier", "", f"{format_montant(point_global.total_reverse)} FCFA"],
        [f"Total reste dû", "", f"{format_montant(point_global.total_reste_du)} FCFA"],
        ["", "", ""],
        [f"Taux de recouvrement global", "", f"{point_global.taux_recouvrement:.2f} %"],
    ]

    table_synthese = Table(synthese_data, colWidths=[10 * cm, 2 * cm, 5 * cm])
    table_synthese.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 8), (0, 8), 'Helvetica-Bold'),
    ]))
    elements.append(table_synthese)
    elements.append(Paragraph("═" * 70, style_centre))
    elements.append(Spacer(1, 15))

    # ═══════════════════════════════════════════════════════════
    # II. DÉTAIL PAR DOSSIER
    # ═══════════════════════════════════════════════════════════

    elements.append(Paragraph("<b>II. DÉTAIL PAR DOSSIER</b>", style_section))
    elements.append(Paragraph("─" * 70, style_normal))

    # En-tête du tableau
    header = ['Réf Dossier', 'Débiteur', 'Type', 'Créance', 'Encaissé', 'Reversé', 'Reste dû']
    data_detail = [header]

    dossiers = point_global.get_dossiers_filtres()
    for dossier in dossiers:
        type_rec = 'A' if dossier.type_recouvrement == 'amiable' else 'F'
        debiteur_nom = dossier.debiteur.get_nom_complet()[:20] if dossier.debiteur else '-'
        data_detail.append([
            dossier.reference[:12],
            debiteur_nom,
            type_rec,
            format_montant(dossier.montant_principal),
            format_montant(dossier.montant_encaisse or 0),
            format_montant(dossier.montant_reverse or 0),
            format_montant(dossier.montant_principal - (dossier.montant_encaisse or 0)),
        ])

    # Ligne totaux
    data_detail.append([
        'TOTAUX',
        f'{point_global.nombre_dossiers} dossiers',
        '',
        format_montant(point_global.total_creances),
        format_montant(point_global.total_encaisse),
        format_montant(point_global.total_reverse),
        format_montant(point_global.total_reste_du),
    ])

    table_detail = Table(data_detail, colWidths=[2 * cm, 3.5 * cm, 1 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    table_detail.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))
    elements.append(table_detail)
    elements.append(Paragraph("═" * 70, style_centre))

    # ═══════════════════════════════════════════════════════════
    # III. DOSSIERS RECOUVRÉS
    # ═══════════════════════════════════════════════════════════

    dossiers_recouvres = dossiers.filter(statut='cloture', motif_cloture='recouvre')
    if dossiers_recouvres.exists():
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>III. DOSSIERS RECOUVRÉS (CLÔTURÉS AVEC SUCCÈS)</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        for d in dossiers_recouvres:
            debiteur_nom = d.debiteur.get_nom_complet() if d.debiteur else '-'
            date_cloture = d.date_cloture.strftime('%d/%m/%Y') if d.date_cloture else '-'
            elements.append(Paragraph(
                f"• {d.reference} - {debiteur_nom} : {format_montant(d.montant_principal)} FCFA "
                f"(clôturé le {date_cloture})",
                style_normal
            ))

        total_recouvre = sum(d.montant_principal for d in dossiers_recouvres)
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"<b>Nombre : {dossiers_recouvres.count()}</b>", style_normal))
        elements.append(Paragraph(f"<b>Montant total recouvré : {format_montant(total_recouvre)} FCFA</b>", style_normal))

    # ═══════════════════════════════════════════════════════════
    # IV. DOSSIERS EN COURS
    # ═══════════════════════════════════════════════════════════

    dossiers_en_cours = dossiers.filter(statut='en_cours')
    if dossiers_en_cours.exists():
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>IV. DOSSIERS EN COURS</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        header_ec = ['Réf', 'Débiteur', 'Reste dû', 'Dernière action', 'Prochaine étape']
        data_ec = [header_ec]

        for d in dossiers_en_cours[:20]:  # Limiter à 20 pour lisibilité
            reste = d.montant_principal - (d.montant_encaisse or 0)
            debiteur_nom = d.debiteur.get_nom_complet()[:15] if d.debiteur else '-'
            data_ec.append([
                d.reference[:12],
                debiteur_nom,
                format_montant(reste),
                (d.derniere_action[:20] if d.derniere_action else '-'),
                (d.prochaine_etape[:20] if d.prochaine_etape else '-'),
            ])

        table_ec = Table(data_ec, colWidths=[2 * cm, 3.5 * cm, 2.5 * cm, 4 * cm, 4 * cm])
        table_ec.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ]))
        elements.append(table_ec)

    # ═══════════════════════════════════════════════════════════
    # V. DOSSIERS IRRÉCOUVRABLES
    # ═══════════════════════════════════════════════════════════

    dossiers_irrecouvrables = dossiers.filter(statut='cloture').exclude(motif_cloture='recouvre')
    if dossiers_irrecouvrables.exists():
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>V. DOSSIERS IRRÉCOUVRABLES</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))

        for d in dossiers_irrecouvrables:
            debiteur_nom = d.debiteur.get_nom_complet() if d.debiteur else '-'
            motif = d.get_motif_cloture_display() if hasattr(d, 'get_motif_cloture_display') else d.motif_cloture
            elements.append(Paragraph(
                f"• {d.reference} - {debiteur_nom} : {format_montant(d.montant_principal)} FCFA - "
                f"Motif : {motif}",
                style_normal
            ))

        total_irr = sum(d.montant_principal for d in dossiers_irrecouvrables)
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"<b>Nombre : {dossiers_irrecouvrables.count()}</b>", style_normal))
        elements.append(Paragraph(f"<b>Montant total non recouvré : {format_montant(total_irr)} FCFA</b>", style_normal))

    # ═══════════════════════════════════════════════════════════
    # VII. HONORAIRES ET FRAIS RETENUS
    # ═══════════════════════════════════════════════════════════

    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>VI. HONORAIRES ET FRAIS RETENUS PAR L'ÉTUDE</b>", style_section))
    elements.append(Paragraph("─" * 70, style_normal))

    honoraires_data = [
        [f"Frais de procédure totaux", f"{format_montant(point_global.total_frais_procedure)} FCFA"],
        [f"Émoluments proportionnels", f"{format_montant(point_global.total_emoluments)} FCFA"],
        [f"Honoraires (phase amiable)", f"{format_montant(point_global.total_honoraires_amiable)} FCFA"],
        ["─" * 40, "─" * 15],
        [f"TOTAL RETENU", f"{format_montant(point_global.total_retenu)} FCFA"],
    ]

    table_hon = Table(honoraires_data, colWidths=[10 * cm, 5 * cm])
    table_hon.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table_hon)
    elements.append(Paragraph("═" * 70, style_centre))

    # ═══════════════════════════════════════════════════════════
    # OBSERVATIONS
    # ═══════════════════════════════════════════════════════════

    if point_global.observations:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>VII. OBSERVATIONS GÉNÉRALES</b>", style_section))
        elements.append(Paragraph("─" * 70, style_normal))
        elements.append(Paragraph(point_global.observations, style_normal))
        elements.append(Paragraph("═" * 70, style_centre))

    # ═══════════════════════════════════════════════════════════
    # SIGNATURE
    # ═══════════════════════════════════════════════════════════

    elements.append(Spacer(1, 30))
    ville = config.adresse_ville if config and config.adresse_ville else 'Parakou'
    elements.append(Paragraph(f"Fait à {ville}, le {datetime.now().strftime('%d/%m/%Y')}", style_droite))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"<b>{nom_huissier}</b>", style_droite))
    elements.append(Paragraph("Huissier de Justice", style_droite))
    elements.append(Paragraph("═" * 70, style_centre))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

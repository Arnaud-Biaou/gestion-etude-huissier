"""
Génération PDF complète des mémoires de cédules
- Page 1 (portrait) : En-tête + Réquisition + Exécutoire
- Page 2+ (paysage) : Tableau des coûts
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
    - Page 1 (portrait) : En-tête + Réquisition + Exécutoire
    - Page 2+ (paysage) : Tableau des coûts
    """
    buffer = BytesIO()

    # Récupérer les infos
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
    else:
        autorite_req = juridiction.get_autorite_requisition()
        autorite_exec = juridiction.get_autorite_executoire()
        juridiction_nom = juridiction.nom
        juridiction_ville = juridiction.ville

    # Montant en lettres
    montant_lettres = nombre_en_lettres(memoire.montant_total)
    montant_chiffres = f"{int(memoire.montant_total):,}".replace(',', ' ')

    # Configuration étude
    try:
        from parametres.models import ConfigurationEtude
        config = ConfigurationEtude.get_instance()
        huissier_nom = config.nom_etude or "Maître [NOM]"
        juridiction_competence = config.juridiction or "Tribunal de Première Instance de Parakou et la Cour d'Appel de Parakou"
    except:
        huissier_nom = memoire.huissier.nom if memoire.huissier else "Maître [NOM]"
        juridiction_competence = "Tribunal de Première Instance de Parakou et la Cour d'Appel de Parakou"

    huissier_titre = f"{huissier_nom}, Huissier de Justice près le {juridiction_competence}"

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
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leading=14
    )

    style_signature = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )

    style_visa = ParagraphStyle(
        'Visa',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT
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

    # Document portrait pour page 1
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []

    # === PAGE 1 : EN-TÊTE + RÉQUISITION + EXÉCUTOIRE ===

    # En-tête
    elements.append(Paragraph(f"<b>MÉMOIRE N° {memoire.numero}</b>", style_titre))
    elements.append(Paragraph(f"du mois de {mois_nom} {memoire.annee}", style_sous_titre))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("<b>ÉTAT DES INDEMNITÉS DUES À</b>", style_sous_titre))
    elements.append(Paragraph(huissier_titre, style_normal))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"<b>Autorité requérante :</b> {juridiction_nom}", style_normal))
    elements.append(Spacer(1, 20))

    # Encadré références légales
    ref_legales = """
    <b>Références :</b><br/>
    - Décret N° 2012-143 du 07 juin 2012 portant réglementation des frais de justice criminelle,
      correctionnelle et de police (Articles 81 et suivants)<br/>
    - Décret N° 2012-435 du 19 novembre 2012 modifiant l'article 43<br/>
    - Décret N° 2007-155 du 03 avril 2007 relatif aux frais de mission
    """
    elements.append(Paragraph(ref_legales, style_normal))
    elements.append(Spacer(1, 25))

    # === RÉQUISITION ===
    elements.append(Paragraph("<b><u>RÉQUISITION</u></b>", style_section))
    elements.append(Spacer(1, 10))

    texte_requisition = f"""
    Nous ................................................................................., {autorite_req['titre']} près la {juridiction_nom} ;<br/><br/>
    Vu le présent mémoire, les pièces jointes ;<br/><br/>
    Vu le décret N° 2012-143 du 07 juin 2012 portant réglementation des frais de justice criminelle,
    correctionnelle et de police en ses articles 81 et suivants ;<br/><br/>
    Requérons qu'il soit délivré exécutoire par Monsieur le {autorite_exec['titre']} ;<br/><br/>
    Sur la caisse du Trésor public, chapitre des frais de justice, pour paiement de la somme de
    <b>FCFA {montant_lettres} ({montant_chiffres})</b>.
    """
    elements.append(Paragraph(texte_requisition, style_normal))
    elements.append(Spacer(1, 15))

    # Signatures réquisition
    date_lieu = f"{juridiction_ville}, le .......................... {memoire.annee}"
    elements.append(Paragraph(date_lieu, style_signature))
    elements.append(Spacer(1, 10))

    if autorite_req.get('avec_visa', False):
        # TPI : Visa à gauche, Signature à droite
        data_sig = [
            [
                Paragraph(f"<b>Vu :</b><br/>Le {autorite_req.get('visa_titre', 'Procureur Général')}", style_visa),
                Paragraph(f"<b>Le {autorite_req['titre']}</b>", style_signature)
            ],
            ["", ""],
            ["", ""],
        ]
        table_sig = Table(data_sig, colWidths=[8*cm, 8*cm])
        table_sig.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table_sig)
    else:
        # Cour d'Appel ou Spéciale : Signature seule à droite
        elements.append(Paragraph(f"<b>Le {autorite_req['titre']}</b>", style_signature))
        elements.append(Spacer(1, 30))

    elements.append(Spacer(1, 25))

    # === EXÉCUTOIRE ===
    elements.append(Paragraph("<b><u>EXÉCUTOIRE</u></b>", style_section))
    elements.append(Spacer(1, 10))

    texte_executoire = f"""
    Nous ................................................................................., {autorite_exec['titre']} ;<br/><br/>
    Vu la réquisition ci-dessus, les pièces jointes et le texte ci-dessus visé ;<br/><br/>
    Avons arrêté et rendu exécutoire le mémoire ci-contre pour la somme de
    <b>FCFA {montant_lettres} ({montant_chiffres})</b>.<br/><br/>
    Montant de la taxe que nous avons fait par application des articles susvisés ;<br/><br/>
    Et attendu qu'il n'y a pas de partie civile en cause, ordonnons que ladite somme soit payée à
    {huissier_titre}, par les soins de l'Administration.
    """
    elements.append(Paragraph(texte_executoire, style_normal))
    elements.append(Spacer(1, 15))

    # Signatures exécutoire
    elements.append(Paragraph(date_lieu, style_signature))
    elements.append(Spacer(1, 10))

    if autorite_exec.get('avec_visa', False):
        titre_exec_court = autorite_exec['titre'].split(' du ')[0] if ' du ' in autorite_exec['titre'] else autorite_exec['titre']
        data_sig = [
            [
                Paragraph(f"<b>Vu :</b><br/>Le {autorite_exec.get('visa_titre', 'Président de la Cour')}", style_visa),
                Paragraph(f"<b>Le {titre_exec_court}</b>", style_signature)
            ],
            ["", ""],
            ["", ""],
        ]
        table_sig = Table(data_sig, colWidths=[8*cm, 8*cm])
        table_sig.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(table_sig)
    else:
        elements.append(Paragraph("<b>Le Président</b>", style_signature))

    # Saut de page vers le tableau (sera en paysage dans une version future)
    elements.append(PageBreak())

    # === PAGE 2+ : TABLEAU DES COÛTS ===
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

    # Certification
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Certifié sincère et véritable", style_signature))
    elements.append(Spacer(1, 5))
    date_cert = memoire.date_certification.strftime('%d/%m/%Y') if memoire.date_certification else '.....................'
    elements.append(Paragraph(
        f"Fait à {memoire.lieu_certification}, le {date_cert}",
        style_signature
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(huissier_nom, style_signature))
    elements.append(Paragraph("Huissier de Justice", style_signature))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

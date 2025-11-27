"""
Commande pour initialiser les modèles de documents par défaut
"""
from django.core.management.base import BaseCommand
from documents.models import ModeleDocument, ConfigurationDocuments


class Command(BaseCommand):
    help = 'Initialise les modèles de documents par défaut'

    def handle(self, *args, **options):
        self.stdout.write('Initialisation des modèles de documents...')

        # Configuration par défaut
        config = ConfigurationDocuments.get_instance()
        if not config.nom_etude:
            config.nom_etude = "ÉTUDE D'HUISSIER DE JUSTICE"
            config.adresse_etude = "Cotonou, République du Bénin"
            config.telephone_etude = "+229 XX XX XX XX"
            config.email_etude = "contact@etude.bj"
            config.nom_huissier = "Maître [NOM]"
            config.qualite_huissier = "Huissier de Justice"
            config.save()
            self.stdout.write(self.style.SUCCESS('Configuration créée'))

        # Modèles d'actes
        modeles_actes = [
            {
                'nom': 'Commandement de payer',
                'code': 'commandement',
                'type_modele': 'acte',
                'description': 'Commandement de payer une somme d\'argent',
                'contenu_template': """
<h2 style="text-align: center;">COMMANDEMENT DE PAYER</h2>

<p>L'AN DEUX MILLE {{annee}},</p>
<p>Et le {{date_jour}}</p>

<p>À la requête de : <strong>{{creancier_nom}}</strong></p>
<p>Demeurant à : {{creancier_adresse}}</p>

<p>J'ai, <strong>{{huissier_nom}}</strong>, {{qualite_huissier}}, soussigné,</p>

<p><strong>FAIT COMMANDEMENT</strong></p>

<p>À : <strong>{{debiteur_nom}}</strong></p>
<p>Demeurant à : {{debiteur_adresse}}</p>

<p>D'avoir à payer à <strong>{{creancier_nom}}</strong> la somme de :</p>

<ul>
    <li>Principal : {{montant_principal}} FCFA</li>
    <li>Intérêts : {{montant_interets}} FCFA</li>
    <li>Frais : {{montant_frais}} FCFA</li>
    <li><strong>TOTAL : {{montant_total}} FCFA</strong></li>
</ul>

<p>En vertu de : {{titre_executoire}}</p>

<p>À défaut de paiement immédiat, il sera procédé à l'exécution forcée conformément aux dispositions de l'Acte Uniforme OHADA portant organisation des procédures simplifiées de recouvrement et des voies d'exécution.</p>

<p>Dont acte.</p>
                """,
                'variables': [
                    {'nom': 'creancier_nom', 'description': 'Nom du créancier'},
                    {'nom': 'creancier_adresse', 'description': 'Adresse du créancier'},
                    {'nom': 'debiteur_nom', 'description': 'Nom du débiteur'},
                    {'nom': 'debiteur_adresse', 'description': 'Adresse du débiteur'},
                    {'nom': 'montant_principal', 'description': 'Montant principal'},
                    {'nom': 'montant_interets', 'description': 'Montant des intérêts'},
                    {'nom': 'montant_frais', 'description': 'Montant des frais'},
                    {'nom': 'montant_total', 'description': 'Montant total'},
                    {'nom': 'titre_executoire', 'description': 'Titre exécutoire'},
                ],
                'ordre_affichage': 1,
            },
            {
                'nom': 'Signification de décision',
                'code': 'signification',
                'type_modele': 'acte',
                'description': 'Signification d\'une décision de justice',
                'contenu_template': """
<h2 style="text-align: center;">SIGNIFICATION DE DÉCISION</h2>

<p>L'AN DEUX MILLE {{annee}},</p>
<p>Et le {{date_jour}}</p>

<p>À la requête de : <strong>{{requerant_nom}}</strong></p>
<p>Demeurant à : {{requerant_adresse}}</p>

<p>J'ai, <strong>{{huissier_nom}}</strong>, {{qualite_huissier}}, soussigné,</p>

<p><strong>SIGNIFIÉ</strong></p>

<p>À : <strong>{{destinataire_nom}}</strong></p>
<p>Demeurant à : {{destinataire_adresse}}</p>

<p>Copie d'une décision de justice rendue par :</p>
<p><strong>{{juridiction}}</strong></p>
<p>En date du : {{date_decision}}</p>
<p>Référence : {{reference_decision}}</p>

<p><strong>Dispositif de la décision :</strong></p>
<p>{{dispositif}}</p>

<p>Afin que le destinataire n'en ignore.</p>

<p>Dont acte.</p>
                """,
                'variables': [
                    {'nom': 'requerant_nom', 'description': 'Nom du requérant'},
                    {'nom': 'requerant_adresse', 'description': 'Adresse du requérant'},
                    {'nom': 'destinataire_nom', 'description': 'Nom du destinataire'},
                    {'nom': 'destinataire_adresse', 'description': 'Adresse du destinataire'},
                    {'nom': 'juridiction', 'description': 'Juridiction ayant rendu la décision'},
                    {'nom': 'date_decision', 'description': 'Date de la décision'},
                    {'nom': 'reference_decision', 'description': 'Référence de la décision'},
                    {'nom': 'dispositif', 'description': 'Dispositif de la décision'},
                ],
                'ordre_affichage': 2,
            },
            {
                'nom': 'Procès-verbal de saisie-attribution',
                'code': 'pv_saisie_attribution',
                'type_modele': 'acte',
                'description': 'Procès-verbal de saisie-attribution de créances',
                'contenu_template': """
<h2 style="text-align: center;">PROCÈS-VERBAL DE SAISIE-ATTRIBUTION DE CRÉANCES</h2>

<p>L'AN DEUX MILLE {{annee}},</p>
<p>Et le {{date_jour}}</p>

<p>À la requête de : <strong>{{creancier_nom}}</strong></p>
<p>Demeurant à : {{creancier_adresse}}</p>

<p>Créancier saisissant, agissant en vertu de : {{titre_executoire}}</p>

<p>J'ai, <strong>{{huissier_nom}}</strong>, {{qualite_huissier}}, soussigné,</p>

<p><strong>PROCÉDÉ À UNE SAISIE-ATTRIBUTION</strong></p>

<p>Entre les mains de : <strong>{{tiers_saisi_nom}}</strong></p>
<p>Adresse : {{tiers_saisi_adresse}}</p>

<p>Sur les sommes dues à : <strong>{{debiteur_nom}}</strong></p>
<p>Demeurant à : {{debiteur_adresse}}</p>

<p>Pour avoir paiement de la somme de <strong>{{montant_saisie}} FCFA</strong></p>

<p>Le tiers saisi déclare :</p>
<p>{{declaration_tiers}}</p>

<p>Le tiers saisi est informé qu'il lui est fait défense de se libérer des sommes saisies entre les mains du débiteur.</p>

<p>Dont acte.</p>
                """,
                'variables': [
                    {'nom': 'creancier_nom', 'description': 'Nom du créancier'},
                    {'nom': 'creancier_adresse', 'description': 'Adresse du créancier'},
                    {'nom': 'debiteur_nom', 'description': 'Nom du débiteur'},
                    {'nom': 'debiteur_adresse', 'description': 'Adresse du débiteur'},
                    {'nom': 'tiers_saisi_nom', 'description': 'Nom du tiers saisi'},
                    {'nom': 'tiers_saisi_adresse', 'description': 'Adresse du tiers saisi'},
                    {'nom': 'titre_executoire', 'description': 'Titre exécutoire'},
                    {'nom': 'montant_saisie', 'description': 'Montant de la saisie'},
                    {'nom': 'declaration_tiers', 'description': 'Déclaration du tiers saisi'},
                ],
                'ordre_affichage': 3,
            },
            {
                'nom': 'Procès-verbal de constat',
                'code': 'pv_constat',
                'type_modele': 'acte',
                'description': 'Procès-verbal de constat',
                'contenu_template': """
<h2 style="text-align: center;">PROCÈS-VERBAL DE CONSTAT</h2>

<p>L'AN DEUX MILLE {{annee}},</p>
<p>Et le {{date_jour}}, à {{heure}}</p>

<p>À la requête de : <strong>{{requerant_nom}}</strong></p>
<p>Demeurant à : {{requerant_adresse}}</p>

<p>J'ai, <strong>{{huissier_nom}}</strong>, {{qualite_huissier}}, soussigné,</p>

<p>Me suis transporté à l'adresse suivante :</p>
<p><strong>{{lieu_constat}}</strong></p>

<p>Aux fins de dresser constat de : {{objet_constat}}</p>

<p><strong>CONSTATATIONS :</strong></p>

<p>{{description_constat}}</p>

<p><strong>PHOTOGRAPHIES :</strong></p>
<p>{{nombre_photos}} photographies ont été prises et annexées au présent procès-verbal.</p>

<p>De tout quoi j'ai dressé le présent procès-verbal pour servir et valoir ce que de droit.</p>

<p>Dont acte.</p>
                """,
                'variables': [
                    {'nom': 'requerant_nom', 'description': 'Nom du requérant'},
                    {'nom': 'requerant_adresse', 'description': 'Adresse du requérant'},
                    {'nom': 'lieu_constat', 'description': 'Lieu du constat'},
                    {'nom': 'objet_constat', 'description': 'Objet du constat'},
                    {'nom': 'description_constat', 'description': 'Description des constatations'},
                    {'nom': 'nombre_photos', 'description': 'Nombre de photographies'},
                ],
                'ordre_affichage': 4,
            },
            {
                'nom': 'Dénonciation de saisie',
                'code': 'denonciation',
                'type_modele': 'acte',
                'description': 'Acte de dénonciation de saisie au débiteur',
                'contenu_template': """
<h2 style="text-align: center;">DÉNONCIATION DE SAISIE-ATTRIBUTION</h2>

<p>L'AN DEUX MILLE {{annee}},</p>
<p>Et le {{date_jour}}</p>

<p>À la requête de : <strong>{{creancier_nom}}</strong></p>
<p>Demeurant à : {{creancier_adresse}}</p>

<p>J'ai, <strong>{{huissier_nom}}</strong>, {{qualite_huissier}}, soussigné,</p>

<p><strong>DÉNONCÉ</strong></p>

<p>À : <strong>{{debiteur_nom}}</strong></p>
<p>Demeurant à : {{debiteur_adresse}}</p>

<p>Le procès-verbal de saisie-attribution pratiquée le {{date_saisie}} entre les mains de {{tiers_saisi_nom}}.</p>

<p>Cette saisie a été pratiquée pour avoir paiement de la somme de <strong>{{montant_saisie}} FCFA</strong></p>

<p>En vertu de : {{titre_executoire}}</p>

<p>Le débiteur est informé qu'il dispose d'un délai d'UN MOIS pour contester cette saisie devant le juge compétent.</p>

<p>Dont acte.</p>
                """,
                'variables': [
                    {'nom': 'creancier_nom', 'description': 'Nom du créancier'},
                    {'nom': 'creancier_adresse', 'description': 'Adresse du créancier'},
                    {'nom': 'debiteur_nom', 'description': 'Nom du débiteur'},
                    {'nom': 'debiteur_adresse', 'description': 'Adresse du débiteur'},
                    {'nom': 'date_saisie', 'description': 'Date de la saisie'},
                    {'nom': 'tiers_saisi_nom', 'description': 'Nom du tiers saisi'},
                    {'nom': 'montant_saisie', 'description': 'Montant de la saisie'},
                    {'nom': 'titre_executoire', 'description': 'Titre exécutoire'},
                ],
                'ordre_affichage': 5,
            },
        ]

        # Modèles de courriers
        modeles_courriers = [
            {
                'nom': 'Lettre de mise en demeure',
                'code': 'mise_demeure',
                'type_modele': 'courrier',
                'description': 'Lettre de mise en demeure avant poursuites',
                'contenu_template': """
<p>Madame, Monsieur,</p>

<p>Par la présente, nous vous mettons en demeure de régler la somme de <strong>{{montant}} FCFA</strong> due à {{creancier_nom}} au titre de {{objet_creance}}.</p>

<p>Cette somme était exigible depuis le {{date_echeance}}.</p>

<p>Nous vous accordons un délai de <strong>{{delai}} jours</strong> à compter de la réception de la présente pour procéder au règlement intégral de cette somme.</p>

<p>À défaut de règlement dans le délai imparti, nous serons contraints d'engager des poursuites judiciaires à votre encontre, ce qui entraînerait des frais supplémentaires à votre charge (intérêts de retard, frais d'huissier, frais de justice).</p>

<p>Pour tout règlement ou accord amiable, vous pouvez nous contacter aux coordonnées ci-dessous.</p>
                """,
                'variables': [
                    {'nom': 'montant', 'description': 'Montant dû'},
                    {'nom': 'creancier_nom', 'description': 'Nom du créancier'},
                    {'nom': 'objet_creance', 'description': 'Objet de la créance'},
                    {'nom': 'date_echeance', 'description': 'Date d\'échéance'},
                    {'nom': 'delai', 'description': 'Délai accordé en jours'},
                ],
                'ordre_affichage': 10,
            },
            {
                'nom': 'Lettre de relance',
                'code': 'relance',
                'type_modele': 'courrier',
                'description': 'Lettre de relance pour paiement',
                'contenu_template': """
<p>Madame, Monsieur,</p>

<p>Sauf erreur de notre part, nous constatons que notre précédent courrier du {{date_precedent_courrier}} relatif au règlement de la somme de <strong>{{montant}} FCFA</strong> est resté sans suite.</p>

<p>Nous vous prions de bien vouloir procéder au règlement de cette somme dans les meilleurs délais.</p>

<p>Si vous avez déjà effectué ce règlement, nous vous prions de ne pas tenir compte de ce rappel et vous en remercions.</p>

<p>Dans le cas contraire, nous vous serions reconnaissants de régulariser votre situation dans un délai de <strong>{{delai}} jours</strong>.</p>

<p>Nous restons à votre disposition pour tout arrangement ou toute question concernant ce dossier.</p>
                """,
                'variables': [
                    {'nom': 'date_precedent_courrier', 'description': 'Date du précédent courrier'},
                    {'nom': 'montant', 'description': 'Montant dû'},
                    {'nom': 'delai', 'description': 'Délai accordé en jours'},
                ],
                'ordre_affichage': 11,
            },
            {
                'nom': 'Accusé de réception de paiement',
                'code': 'accuse_paiement',
                'type_modele': 'courrier',
                'description': 'Accusé de réception de paiement',
                'contenu_template': """
<p>Madame, Monsieur,</p>

<p>Nous accusons réception de votre paiement d'un montant de <strong>{{montant_recu}} FCFA</strong> en date du {{date_paiement}}.</p>

<p>Mode de paiement : {{mode_paiement}}</p>

<p>Ce paiement a été affecté au règlement de : {{affectation}}</p>

{% if solde_restant > 0 %}
<p>Il reste un solde de <strong>{{solde_restant}} FCFA</strong> à régler.</p>
{% else %}
<p>Votre compte est désormais soldé. Nous vous remercions de votre paiement.</p>
{% endif %}

<p>Nous vous prions d'agréer l'expression de nos salutations distinguées.</p>
                """,
                'variables': [
                    {'nom': 'montant_recu', 'description': 'Montant reçu'},
                    {'nom': 'date_paiement', 'description': 'Date du paiement'},
                    {'nom': 'mode_paiement', 'description': 'Mode de paiement'},
                    {'nom': 'affectation', 'description': 'Affectation du paiement'},
                    {'nom': 'solde_restant', 'description': 'Solde restant'},
                ],
                'ordre_affichage': 12,
            },
        ]

        # Créer les modèles
        all_modeles = modeles_actes + modeles_courriers

        for modele_data in all_modeles:
            modele, created = ModeleDocument.objects.get_or_create(
                code=modele_data['code'],
                defaults={
                    'nom': modele_data['nom'],
                    'type_modele': modele_data['type_modele'],
                    'description': modele_data['description'],
                    'contenu_template': modele_data['contenu_template'],
                    'variables': modele_data['variables'],
                    'ordre_affichage': modele_data['ordre_affichage'],
                    'est_systeme': True,
                    'actif': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Modèle "{modele.nom}" créé'))
            else:
                self.stdout.write(f'  Modèle "{modele.nom}" existe déjà')

        self.stdout.write(self.style.SUCCESS('Initialisation des documents terminée!'))

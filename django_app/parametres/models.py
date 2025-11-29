"""
Modèles de données pour le module Paramètres
Gestion de la configuration globale de l'application
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json
import uuid


class ConfigurationEtude(models.Model):
    """Configuration globale de l'étude - Singleton"""

    # ===== SECTION 1: IDENTITÉ DE L'ÉTUDE =====
    nom_etude = models.CharField(
        max_length=200,
        default="Étude Me BIAOU",
        verbose_name="Nom de l'étude"
    )
    titre = models.CharField(
        max_length=100,
        default="Huissier de Justice",
        verbose_name="Titre"
    )
    juridiction = models.CharField(
        max_length=300,
        default="près le Tribunal de Première Instance de Parakou et la Cour d'Appel de Parakou",
        verbose_name="Juridiction"
    )
    adresse_rue = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Adresse (rue)"
    )
    adresse_quartier = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Quartier"
    )
    adresse_ville = models.CharField(
        max_length=100,
        default="Parakou",
        verbose_name="Ville"
    )
    adresse_bp = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Boîte postale"
    )
    telephone_fixe = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone fixe"
    )
    telephone_mobile1 = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Mobile 1"
    )
    telephone_mobile2 = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Mobile 2"
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Email professionnel"
    )
    site_web = models.URLField(
        blank=True,
        verbose_name="Site web"
    )
    numero_ifu = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Numéro IFU"
    )
    numero_rccm = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Numéro RCCM",
        help_text="Numéro du Registre du Commerce et du Crédit Mobilier"
    )
    numero_agrement = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro d'agrément / Inscription au tableau"
    )
    date_installation = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'installation"
    )

    # Logo, signature et couleurs
    logo = models.ImageField(
        upload_to='etude/logos/',
        null=True,
        blank=True,
        verbose_name="Logo de l'étude"
    )
    signature_huissier = models.ImageField(
        upload_to='etude/signatures/',
        null=True,
        blank=True,
        verbose_name="Signature de l'huissier",
        help_text="Image de la signature numérisée (PNG transparent recommandé)"
    )
    couleur_principale = models.CharField(
        max_length=7,
        default="#1a365d",
        verbose_name="Couleur principale"
    )
    couleur_secondaire = models.CharField(
        max_length=7,
        default="#c6a962",
        verbose_name="Couleur secondaire"
    )

    # Coordonnées bancaires
    banque_nom = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Banque principale"
    )
    banque_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code banque"
    )
    banque_guichet = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code guichet"
    )
    banque_compte = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Numéro de compte"
    )
    banque_cle = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Clé RIB"
    )
    banque_iban = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="IBAN"
    )
    banque_titulaire = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Titulaire du compte"
    )
    mobile_money_operateur = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Opérateur Mobile Money"
    )
    mobile_money_numero = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Numéro Mobile Money"
    )

    # ===== SECTION 2.1: PARAMÈTRES DOSSIERS =====
    dossier_prefixe = models.CharField(
        max_length=10,
        default="DOS-",
        verbose_name="Préfixe numéros de dossier"
    )
    dossier_numero_depart = models.PositiveIntegerField(
        default=1,
        verbose_name="Numéro de départ nouvelle année"
    )
    dossier_numero_cabinet = models.PositiveIntegerField(
        default=175,
        verbose_name="Numéro de cabinet",
        help_text="Préfixe numérique pour les références de dossiers (ex: 175)"
    )
    dossier_initiales_huissier = models.CharField(
        max_length=10,
        default="MAB",
        verbose_name="Initiales de l'huissier",
        help_text="Suffixe pour les références de dossiers (ex: MAB)"
    )

    # ===== SECTION 2.2: PARAMÈTRES FACTURATION =====
    facture_prefixe = models.CharField(
        max_length=10,
        default="FAC-",
        verbose_name="Préfixe factures"
    )
    tva_applicable = models.BooleanField(
        default=True,
        verbose_name="TVA applicable"
    )
    tva_taux = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('18.00'),
        verbose_name="Taux TVA (%)"
    )
    mecef_nim = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro NIM (MECeF)"
    )
    mecef_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Token API MECeF"
    )
    mecef_mode = models.CharField(
        max_length=20,
        choices=[('test', 'Test'), ('production', 'Production')],
        default='test',
        verbose_name="Mode MECeF"
    )
    facture_mentions_legales = models.TextField(
        blank=True,
        verbose_name="Mentions légales sur factures"
    )
    facture_conditions_paiement = models.CharField(
        max_length=200,
        default="Payable à réception",
        verbose_name="Conditions de paiement"
    )
    facture_delai_paiement = models.PositiveIntegerField(
        default=30,
        verbose_name="Délai de paiement (jours)"
    )
    facture_penalites_retard = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        verbose_name="Pénalités de retard (% par mois)"
    )

    # ===== SECTION 2.3: PARAMÈTRES TRÉSORERIE =====
    devise = models.CharField(
        max_length=10,
        default="FCFA",
        verbose_name="Devise"
    )
    tresorerie_seuil_alerte = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('100000'),
        verbose_name="Seuil alerte solde faible (F)"
    )
    tresorerie_validation_seuil = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('500000'),
        verbose_name="Validation obligatoire décaissements > (F)"
    )
    tresorerie_delai_reversement = models.PositiveIntegerField(
        default=30,
        verbose_name="Délai max reversement consignations (jours)"
    )
    tresorerie_compte_sequestre = models.BooleanField(
        default=True,
        verbose_name="Compte séquestre obligatoire"
    )

    # ===== SECTION 2.4: PARAMÈTRES COMPTABILITÉ =====
    exercice_debut = models.DateField(
        null=True,
        blank=True,
        verbose_name="Début exercice comptable"
    )
    exercice_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fin exercice comptable"
    )
    comptabilite_mode = models.CharField(
        max_length=20,
        choices=[('facile', 'Facile'), ('guide', 'Guidé'), ('expert', 'Expert')],
        default='guide',
        verbose_name="Mode de saisie"
    )
    regime_fiscal = models.CharField(
        max_length=30,
        choices=[
            ('reel_normal', 'Réel normal'),
            ('reel_simplifie', 'Réel simplifié'),
            ('micro', 'Micro')
        ],
        default='reel_normal',
        verbose_name="Régime fiscal"
    )
    tva_declaration = models.CharField(
        max_length=20,
        choices=[('mensuelle', 'Mensuelle'), ('trimestrielle', 'Trimestrielle')],
        default='mensuelle',
        verbose_name="Déclarations TVA"
    )
    echeances_rappel_jours = models.PositiveIntegerField(
        default=7,
        verbose_name="Rappels échéances fiscales (jours avant)"
    )

    # ===== SECTION 2.5: PARAMÈTRES RECOUVREMENT =====
    recouvrement_majoration_50 = models.BooleanField(
        default=True,
        verbose_name="Application majoration 50% (Loi 2024)"
    )
    recouvrement_delai_majoration = models.PositiveIntegerField(
        default=2,
        verbose_name="Délai avant majoration (mois)"
    )
    recouvrement_ordre_imputation = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Ordre imputation paiements"
    )

    # ===== SECTION 2.6: PARAMÈTRES GÉRANCE IMMOBILIÈRE =====
    gerance_taux_honoraires = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        verbose_name="Taux honoraires gestion (% loyer)"
    )
    gerance_date_reversement = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Date reversement propriétaires"
    )
    gerance_relance_niveau1 = models.PositiveIntegerField(
        default=5,
        verbose_name="Relance niveau 1 - Rappel (J+)"
    )
    gerance_relance_niveau2 = models.PositiveIntegerField(
        default=15,
        verbose_name="Relance niveau 2 - Relance (J+)"
    )
    gerance_relance_niveau3 = models.PositiveIntegerField(
        default=30,
        verbose_name="Relance niveau 3 - Mise en demeure (J+)"
    )
    gerance_relance_niveau4 = models.PositiveIntegerField(
        default=45,
        verbose_name="Relance niveau 4 - Commandement (J+)"
    )

    # ===== SECTION 2.7: PARAMÈTRES RH =====
    rh_smig = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('52000'),
        verbose_name="SMIG en vigueur (FCFA)"
    )
    rh_cnss_salarial_vieillesse = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('3.6'),
        verbose_name="CNSS Salarial Vieillesse (%)"
    )
    rh_cnss_patronal_pf = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('6.4'),
        verbose_name="CNSS Patronal PF (%)"
    )
    rh_cnss_patronal_vieillesse = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('6.4'),
        verbose_name="CNSS Patronal Vieillesse (%)"
    )
    rh_cnss_patronal_at = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.0'),
        verbose_name="CNSS Patronal AT (%)"
    )
    rh_plafond_cnss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('600000'),
        verbose_name="Plafond CNSS mensuel (FCFA)"
    )
    rh_conges_annuels = models.PositiveIntegerField(
        default=2,
        verbose_name="Congés annuels (jours/mois)"
    )
    rh_heures_hebdo = models.PositiveIntegerField(
        default=40,
        verbose_name="Heures travail hebdomadaires"
    )
    rh_jour_paie = models.PositiveIntegerField(
        default=28,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Jour de paie"
    )
    rh_taux_vps = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('4.0'),
        verbose_name="Taux VPS (%)",
        help_text="Versement Patronal sur Salaires"
    )
    rh_taux_risques_professionnels = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.0'),
        verbose_name="Taux AT/Risques professionnels (%)",
        help_text="Taux accidents du travail (variable selon activité: 1% à 4%)"
    )

    # ===== SECTION 2.8: PARAMÈTRES MÉMOIRES DE CÉDULES =====
    cedules_residence = models.CharField(
        max_length=200,
        default="Parakou",
        verbose_name="Résidence de l'huissier"
    )
    cedules_premier_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('980'),
        verbose_name="Premier original (F)"
    )
    cedules_deuxieme_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('980'),
        verbose_name="Deuxième original (F)"
    )
    cedules_copie = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('900'),
        verbose_name="Copie (F)"
    )
    cedules_mention_repertoire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('25'),
        verbose_name="Mention répertoire (F)"
    )
    cedules_vacation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('3000'),
        verbose_name="Vacation (F)"
    )
    cedules_frais_copie_role = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000'),
        verbose_name="Frais copie par rôle (F)"
    )
    cedules_tarif_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('140'),
        verbose_name="Tarif kilométrique (F/km)"
    )
    cedules_seuil_transport = models.PositiveIntegerField(
        default=20,
        verbose_name="Seuil transport (km)"
    )
    cedules_seuil_mission = models.PositiveIntegerField(
        default=100,
        verbose_name="Seuil frais mission (km)"
    )
    cedules_mission_1_repas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('15000'),
        verbose_name="Frais mission 1 repas (100-149 km)"
    )
    cedules_mission_2_repas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('30000'),
        verbose_name="Frais mission 2 repas (150-199 km)"
    )
    cedules_mission_journee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('45000'),
        verbose_name="Frais mission journée entière (≥200 km)"
    )

    # ===== SECTION 2.9: PARAMÈTRES AGENDA =====
    agenda_heure_debut = models.TimeField(
        default='08:00',
        verbose_name="Heure début journée"
    )
    agenda_heure_fin = models.TimeField(
        default='18:00',
        verbose_name="Heure fin journée"
    )
    agenda_duree_rdv = models.PositiveIntegerField(
        default=30,
        verbose_name="Durée RDV par défaut (minutes)"
    )
    agenda_rappel_jours = models.PositiveIntegerField(
        default=1,
        verbose_name="Rappel par défaut (jours avant)"
    )
    agenda_rappel_heures = models.PositiveIntegerField(
        default=1,
        verbose_name="Rappel par défaut (heures avant)"
    )
    agenda_jours_ouvres = models.JSONField(
        default=list,
        verbose_name="Jours ouvrés"
    )

    # ===== SECTION 4: NOTIFICATIONS =====
    notif_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuration notifications"
    )
    smtp_serveur = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Serveur SMTP"
    )
    smtp_port = models.PositiveIntegerField(
        default=587,
        verbose_name="Port SMTP"
    )
    smtp_utilisateur = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Utilisateur SMTP"
    )
    smtp_mot_de_passe = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Mot de passe SMTP"
    )
    smtp_expediteur = models.EmailField(
        blank=True,
        verbose_name="Email expéditeur"
    )
    sms_fournisseur = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Fournisseur SMS"
    )
    sms_api_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="API Key SMS"
    )
    sms_expediteur = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Numéro expéditeur SMS"
    )

    # ===== SECTION 5: SAUVEGARDES =====
    backup_auto = models.BooleanField(
        default=True,
        verbose_name="Sauvegardes automatiques"
    )
    backup_frequence = models.CharField(
        max_length=20,
        choices=[
            ('quotidienne', 'Quotidienne'),
            ('hebdomadaire', 'Hebdomadaire'),
            ('mensuelle', 'Mensuelle')
        ],
        default='quotidienne',
        verbose_name="Fréquence sauvegarde"
    )
    backup_heure = models.TimeField(
        default='02:00',
        verbose_name="Heure de sauvegarde"
    )
    backup_retention = models.PositiveIntegerField(
        default=30,
        verbose_name="Conservation sauvegardes (jours)"
    )
    backup_emplacement = models.CharField(
        max_length=20,
        choices=[
            ('local', 'Local'),
            ('google_drive', 'Google Drive'),
            ('dropbox', 'Dropbox')
        ],
        default='local',
        verbose_name="Emplacement sauvegarde"
    )

    # ===== SECTION 6: PERSONNALISATION =====
    theme_mode = models.CharField(
        max_length=20,
        choices=[('clair', 'Clair'), ('sombre', 'Sombre'), ('auto', 'Auto')],
        default='clair',
        verbose_name="Mode thème"
    )
    format_date = models.CharField(
        max_length=20,
        choices=[
            ('DD/MM/YYYY', 'JJ/MM/AAAA'),
            ('YYYY-MM-DD', 'AAAA-MM-JJ'),
            ('DD MMMM YYYY', 'JJ Mois AAAA')
        ],
        default='DD/MM/YYYY',
        verbose_name="Format des dates"
    )
    separateur_milliers = models.CharField(
        max_length=5,
        default=' ',
        verbose_name="Séparateur milliers"
    )
    separateur_decimales = models.CharField(
        max_length=5,
        default=',',
        verbose_name="Séparateur décimales"
    )
    dashboard_widgets = models.JSONField(
        default=list,
        verbose_name="Widgets tableau de bord"
    )
    dashboard_periode = models.CharField(
        max_length=20,
        choices=[('jour', 'Jour'), ('semaine', 'Semaine'), ('mois', 'Mois')],
        default='mois',
        verbose_name="Période par défaut tableau de bord"
    )

    # ===== SECTION 8: À PROPOS =====
    version_app = models.CharField(
        max_length=20,
        default="1.0.0",
        verbose_name="Version application"
    )
    date_mise_a_jour = models.DateField(
        null=True,
        blank=True,
        verbose_name="Dernière mise à jour"
    )

    # Métadonnées
    est_configure = models.BooleanField(
        default=False,
        verbose_name="Configuration effectuée"
    )
    date_configuration = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de configuration"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )
    modifie_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modifié par"
    )

    class Meta:
        verbose_name = "Configuration de l'étude"
        verbose_name_plural = "Configuration de l'étude"

    def __str__(self):
        return self.nom_etude

    @classmethod
    def get_instance(cls):
        """Singleton pattern - récupère ou crée l'instance unique"""
        instance, created = cls.objects.get_or_create(pk=1)
        if created:
            # Initialiser les valeurs par défaut
            instance.agenda_jours_ouvres = [1, 2, 3, 4, 5]  # Lundi à Vendredi
            instance.recouvrement_ordre_imputation = [
                'frais_procedure',
                'emoluments',
                'interets',
                'principal'
            ]
            instance.notif_config = cls.get_default_notif_config()
            instance.dashboard_widgets = cls.get_default_widgets()
            instance.save()
        return instance

    @staticmethod
    def get_default_notif_config():
        """Configuration par défaut des notifications"""
        return {
            'rdv_a_venir': {'app': True, 'email': True, 'sms': False, 'delai': '1 jour'},
            'tache_retard': {'app': True, 'email': True, 'sms': False, 'delai': 'Immédiat'},
            'facture_impayee': {'app': True, 'email': True, 'sms': False, 'delai': 'Quotidien'},
            'solde_caisse_faible': {'app': True, 'email': True, 'sms': True, 'delai': 'Immédiat'},
            'decaissement_attente': {'app': True, 'email': False, 'sms': False, 'delai': 'Immédiat'},
            'fin_contrat': {'app': True, 'email': True, 'sms': False, 'delai': '30 jours'},
            'loyer_impaye': {'app': True, 'email': True, 'sms': False, 'delai': 'J+5'},
            'reversement': {'app': True, 'email': True, 'sms': False, 'delai': 'Quotidien'},
            'echeance_fiscale': {'app': True, 'email': True, 'sms': False, 'delai': '7 jours'},
            'audience': {'app': True, 'email': True, 'sms': True, 'delai': '2 jours'},
            'dossier_inactif': {'app': True, 'email': False, 'sms': False, 'delai': '30 jours'},
        }

    @staticmethod
    def get_default_widgets():
        """Widgets par défaut du tableau de bord"""
        return [
            {'id': 'stats_dossiers', 'actif': True, 'ordre': 1},
            {'id': 'stats_facturation', 'actif': True, 'ordre': 2},
            {'id': 'stats_tresorerie', 'actif': True, 'ordre': 3},
            {'id': 'rdv_jour', 'actif': True, 'ordre': 4},
            {'id': 'taches_urgentes', 'actif': True, 'ordre': 5},
            {'id': 'factures_impayees', 'actif': True, 'ordre': 6},
        ]

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            # Identité étude
            'nom_etude': self.nom_etude,
            'titre': self.titre,
            'juridiction': self.juridiction,
            'adresse_rue': self.adresse_rue,
            'adresse_quartier': self.adresse_quartier,
            'adresse_ville': self.adresse_ville,
            'adresse_bp': self.adresse_bp,
            'telephone_fixe': self.telephone_fixe,
            'telephone_mobile1': self.telephone_mobile1,
            'telephone_mobile2': self.telephone_mobile2,
            'email': self.email,
            'site_web': self.site_web,
            'numero_ifu': self.numero_ifu,
            'numero_agrement': self.numero_agrement,
            'date_installation': self.date_installation.isoformat() if self.date_installation else None,
            'couleur_principale': self.couleur_principale,
            'couleur_secondaire': self.couleur_secondaire,
            'logo_url': self.logo.url if self.logo else None,
            # Banque
            'banque_nom': self.banque_nom,
            'banque_code': self.banque_code,
            'banque_guichet': self.banque_guichet,
            'banque_compte': self.banque_compte,
            'banque_cle': self.banque_cle,
            'banque_iban': self.banque_iban,
            'banque_titulaire': self.banque_titulaire,
            'mobile_money_operateur': self.mobile_money_operateur,
            'mobile_money_numero': self.mobile_money_numero,
            # Dossiers
            'dossier_prefixe': self.dossier_prefixe,
            'dossier_numero_depart': self.dossier_numero_depart,
            # Facturation
            'facture_prefixe': self.facture_prefixe,
            'tva_applicable': self.tva_applicable,
            'tva_taux': str(self.tva_taux),
            'mecef_nim': self.mecef_nim,
            'mecef_token': self.mecef_token,
            'mecef_mode': self.mecef_mode,
            'facture_mentions_legales': self.facture_mentions_legales,
            'facture_conditions_paiement': self.facture_conditions_paiement,
            'facture_delai_paiement': self.facture_delai_paiement,
            'facture_penalites_retard': str(self.facture_penalites_retard),
            # Trésorerie
            'devise': self.devise,
            'tresorerie_seuil_alerte': str(self.tresorerie_seuil_alerte),
            'tresorerie_validation_seuil': str(self.tresorerie_validation_seuil),
            'tresorerie_delai_reversement': self.tresorerie_delai_reversement,
            'tresorerie_compte_sequestre': self.tresorerie_compte_sequestre,
            # Comptabilité
            'exercice_debut': self.exercice_debut.isoformat() if self.exercice_debut else None,
            'exercice_fin': self.exercice_fin.isoformat() if self.exercice_fin else None,
            'comptabilite_mode': self.comptabilite_mode,
            'regime_fiscal': self.regime_fiscal,
            'tva_declaration': self.tva_declaration,
            'echeances_rappel_jours': self.echeances_rappel_jours,
            # Recouvrement
            'recouvrement_majoration_50': self.recouvrement_majoration_50,
            'recouvrement_delai_majoration': self.recouvrement_delai_majoration,
            'recouvrement_ordre_imputation': self.recouvrement_ordre_imputation,
            # Gérance
            'gerance_taux_honoraires': str(self.gerance_taux_honoraires),
            'gerance_date_reversement': self.gerance_date_reversement,
            'gerance_relance_niveau1': self.gerance_relance_niveau1,
            'gerance_relance_niveau2': self.gerance_relance_niveau2,
            'gerance_relance_niveau3': self.gerance_relance_niveau3,
            'gerance_relance_niveau4': self.gerance_relance_niveau4,
            # RH
            'rh_smig': str(self.rh_smig),
            'rh_cnss_salarial_vieillesse': str(self.rh_cnss_salarial_vieillesse),
            'rh_cnss_patronal_pf': str(self.rh_cnss_patronal_pf),
            'rh_cnss_patronal_vieillesse': str(self.rh_cnss_patronal_vieillesse),
            'rh_cnss_patronal_at': str(self.rh_cnss_patronal_at),
            'rh_plafond_cnss': str(self.rh_plafond_cnss),
            'rh_conges_annuels': self.rh_conges_annuels,
            'rh_heures_hebdo': self.rh_heures_hebdo,
            'rh_jour_paie': self.rh_jour_paie,
            'rh_taux_vps': str(self.rh_taux_vps),
            'rh_taux_risques_professionnels': str(self.rh_taux_risques_professionnels),
            # Cédules
            'cedules_residence': self.cedules_residence,
            'cedules_premier_original': str(self.cedules_premier_original),
            'cedules_deuxieme_original': str(self.cedules_deuxieme_original),
            'cedules_copie': str(self.cedules_copie),
            'cedules_mention_repertoire': str(self.cedules_mention_repertoire),
            'cedules_vacation': str(self.cedules_vacation),
            'cedules_frais_copie_role': str(self.cedules_frais_copie_role),
            'cedules_tarif_km': str(self.cedules_tarif_km),
            'cedules_seuil_transport': self.cedules_seuil_transport,
            'cedules_seuil_mission': self.cedules_seuil_mission,
            'cedules_mission_1_repas': str(self.cedules_mission_1_repas),
            'cedules_mission_2_repas': str(self.cedules_mission_2_repas),
            'cedules_mission_journee': str(self.cedules_mission_journee),
            # Agenda
            'agenda_heure_debut': self.agenda_heure_debut.strftime('%H:%M') if self.agenda_heure_debut else '08:00',
            'agenda_heure_fin': self.agenda_heure_fin.strftime('%H:%M') if self.agenda_heure_fin else '18:00',
            'agenda_duree_rdv': self.agenda_duree_rdv,
            'agenda_rappel_jours': self.agenda_rappel_jours,
            'agenda_rappel_heures': self.agenda_rappel_heures,
            'agenda_jours_ouvres': self.agenda_jours_ouvres,
            # Notifications
            'notif_config': self.notif_config,
            'smtp_serveur': self.smtp_serveur,
            'smtp_port': self.smtp_port,
            'smtp_utilisateur': self.smtp_utilisateur,
            'smtp_expediteur': self.smtp_expediteur,
            'sms_fournisseur': self.sms_fournisseur,
            'sms_expediteur': self.sms_expediteur,
            # Sauvegarde
            'backup_auto': self.backup_auto,
            'backup_frequence': self.backup_frequence,
            'backup_heure': self.backup_heure.strftime('%H:%M') if self.backup_heure else '02:00',
            'backup_retention': self.backup_retention,
            'backup_emplacement': self.backup_emplacement,
            # Personnalisation
            'theme_mode': self.theme_mode,
            'format_date': self.format_date,
            'separateur_milliers': self.separateur_milliers,
            'separateur_decimales': self.separateur_decimales,
            'dashboard_widgets': self.dashboard_widgets,
            'dashboard_periode': self.dashboard_periode,
            # À propos
            'version_app': self.version_app,
            'date_mise_a_jour': self.date_mise_a_jour.isoformat() if self.date_mise_a_jour else None,
            'est_configure': self.est_configure,
        }


class SiteAgence(models.Model):
    """Sites/Agences de l'étude"""
    nom = models.CharField(max_length=200, verbose_name="Nom du site")
    adresse = models.TextField(verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    responsable = models.CharField(max_length=200, blank=True, verbose_name="Responsable")
    est_principal = models.BooleanField(default=False, verbose_name="Site principal")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Site/Agence"
        verbose_name_plural = "Sites/Agences"
        ordering = ['-est_principal', 'nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul site principal
        if self.est_principal:
            SiteAgence.objects.filter(est_principal=True).exclude(pk=self.pk).update(est_principal=False)
        super().save(*args, **kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'adresse': self.adresse,
            'telephone': self.telephone,
            'responsable': self.responsable,
            'est_principal': self.est_principal,
            'actif': self.actif,
        }


class TypeDossier(models.Model):
    """Types de dossiers personnalisables"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    description = models.TextField(blank=True, verbose_name="Description")
    couleur = models.CharField(max_length=7, default="#1a365d", verbose_name="Couleur")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        verbose_name = "Type de dossier"
        verbose_name_plural = "Types de dossiers"
        ordering = ['ordre', 'libelle']

    def __str__(self):
        return self.libelle

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'description': self.description,
            'couleur': self.couleur,
            'actif': self.actif,
            'ordre': self.ordre,
        }


class StatutDossier(models.Model):
    """Statuts de dossiers personnalisables"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    couleur = models.CharField(max_length=7, default="#1a365d", verbose_name="Couleur")
    est_cloture = models.BooleanField(default=False, verbose_name="Est un statut de clôture")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        verbose_name = "Statut de dossier"
        verbose_name_plural = "Statuts de dossiers"
        ordering = ['ordre', 'libelle']

    def __str__(self):
        return self.libelle

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'couleur': self.couleur,
            'est_cloture': self.est_cloture,
            'actif': self.actif,
            'ordre': self.ordre,
        }


class ModeleDocument(models.Model):
    """Modèles de documents"""
    CATEGORIES = [
        ('actes', 'Actes de procédure'),
        ('factures', 'Factures et devis'),
        ('courriers', 'Courriers'),
        ('baux', 'Contrats de bail'),
        ('etats_lieux', 'États des lieux'),
        ('paie', 'Bulletins de paie'),
        ('memoires', 'Mémoires de frais'),
        ('rapports', 'Rapports'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom du modèle")
    categorie = models.CharField(
        max_length=50,
        choices=CATEGORIES,
        verbose_name="Catégorie"
    )
    contenu_html = models.TextField(verbose_name="Contenu HTML")
    variables_utilisees = models.JSONField(
        default=list,
        verbose_name="Variables utilisées"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parametres_modeles_crees',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"
        ordering = ['categorie', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'categorie': self.categorie,
            'categorie_display': self.get_categorie_display(),
            'contenu_html': self.contenu_html,
            'variables_utilisees': self.variables_utilisees,
            'actif': self.actif,
            'date_creation': self.date_creation.isoformat(),
            'date_modification': self.date_modification.isoformat(),
        }


class Localite(models.Model):
    """Table des localités pour calcul des distances"""
    nom = models.CharField(max_length=200, verbose_name="Nom de la localité")
    departement = models.CharField(max_length=100, blank=True, verbose_name="Département")
    commune = models.CharField(max_length=100, blank=True, verbose_name="Commune")
    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Distance (km)"
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Longitude"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Localité"
        verbose_name_plural = "Localités"
        ordering = ['departement', 'nom']
        unique_together = ['nom', 'commune']

    def __str__(self):
        if self.commune:
            return f"{self.nom} ({self.commune})"
        return self.nom

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'departement': self.departement,
            'commune': self.commune,
            'distance_km': str(self.distance_km),
            'latitude': str(self.latitude) if self.latitude else None,
            'longitude': str(self.longitude) if self.longitude else None,
            'actif': self.actif,
        }


class TauxLegal(models.Model):
    """Taux d'intérêt légal UEMOA par année"""
    annee = models.PositiveIntegerField(unique=True, verbose_name="Année")
    taux = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        verbose_name="Taux annuel (%)"
    )
    date_publication = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date publication JO"
    )
    reference_arrete = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Référence arrêté"
    )

    class Meta:
        ordering = ['-annee']
        verbose_name = "Taux d'intérêt légal"
        verbose_name_plural = "Taux d'intérêt légaux"

    def __str__(self):
        return f"{self.annee} : {self.taux}%"

    @classmethod
    def get_taux_annee(cls, annee):
        """Retourne le taux pour une année donnée"""
        try:
            return cls.objects.get(annee=annee).taux
        except cls.DoesNotExist:
            # Retourner le dernier taux connu
            dernier = cls.objects.order_by('-annee').first()
            return dernier.taux if dernier else Decimal('5.5')

    @classmethod
    def get_taux_actuel(cls):
        """Récupère le taux légal de l'année en cours"""
        from django.utils import timezone
        annee_actuelle = timezone.now().year
        try:
            return cls.objects.get(annee=annee_actuelle)
        except cls.DoesNotExist:
            return cls.objects.order_by('-annee').first()

    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'taux': str(self.taux),
            'date_publication': self.date_publication.isoformat() if self.date_publication else None,
            'reference_arrete': self.reference_arrete,
        }


class JourFerie(models.Model):
    """Table des jours fériés"""
    nom = models.CharField(max_length=200, verbose_name="Nom du jour férié")
    date_fixe = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date (jours fixes)"
    )
    jour_mois = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Jour du mois (récurrent)"
    )
    mois = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Mois (récurrent)"
    )
    est_mobile = models.BooleanField(
        default=False,
        verbose_name="Date mobile (Pâques, etc.)"
    )
    formule = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Formule de calcul (dates mobiles)"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Jour férié"
        verbose_name_plural = "Jours fériés"
        ordering = ['mois', 'jour_mois', 'nom']

    def __str__(self):
        if self.jour_mois and self.mois:
            return f"{self.nom} ({self.jour_mois}/{self.mois})"
        elif self.date_fixe:
            return f"{self.nom} ({self.date_fixe})"
        return self.nom

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'date_fixe': self.date_fixe.isoformat() if self.date_fixe else None,
            'jour_mois': self.jour_mois,
            'mois': self.mois,
            'est_mobile': self.est_mobile,
            'formule': self.formule,
            'actif': self.actif,
        }


class TypeActe(models.Model):
    """Types d'actes"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    categorie = models.CharField(max_length=100, blank=True, verbose_name="Catégorie")
    montant_defaut = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Montant par défaut"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Type d'acte"
        verbose_name_plural = "Types d'actes"
        ordering = ['categorie', 'libelle']

    def __str__(self):
        return self.libelle

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'categorie': self.categorie,
            'montant_defaut': str(self.montant_defaut),
            'actif': self.actif,
        }


class Juridiction(models.Model):
    """
    Juridictions du Bénin avec hiérarchie pour les mémoires de cédules
    """
    TYPE_CHOICES = [
        ('tpi', 'Tribunal de Première Instance'),
        ('cour_appel', "Cour d'Appel"),
        ('cour_speciale', 'Cour Spéciale'),
    ]

    CLASSE_TPI_CHOICES = [
        ('premiere', 'Première Classe'),
        ('deuxieme', 'Deuxième Classe'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200, verbose_name="Nom complet")
    nom_court = models.CharField(max_length=100, verbose_name="Nom abrégé")
    type_juridiction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    classe_tpi = models.CharField(
        max_length=20, choices=CLASSE_TPI_CHOICES, blank=True, null=True,
        verbose_name="Classe TPI"
    )

    # Hiérarchie
    cour_appel_rattachement = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='juridictions_rattachees',
        limit_choices_to={'type_juridiction': 'cour_appel'},
        verbose_name="Cour d'Appel de rattachement"
    )

    # Autorités
    titre_procureur = models.CharField(
        max_length=100, default="Procureur de la République",
        verbose_name="Titre du Procureur"
    )
    titre_president = models.CharField(
        max_length=100, default="Président",
        verbose_name="Titre du Président"
    )
    nom_procureur = models.CharField(
        max_length=200, blank=True, verbose_name="Nom du Procureur actuel"
    )
    nom_president = models.CharField(
        max_length=200, blank=True, verbose_name="Nom du Président actuel"
    )

    # Pour Cour d'Appel
    titre_procureur_general = models.CharField(
        max_length=100, default="Procureur Général", blank=True,
        verbose_name="Titre du Procureur Général"
    )
    nom_procureur_general = models.CharField(
        max_length=200, blank=True, verbose_name="Nom du Procureur Général"
    )
    nom_president_cour = models.CharField(
        max_length=200, blank=True, verbose_name="Nom du Président de la Cour"
    )

    # Localisation
    ville = models.CharField(max_length=100)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")

    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Juridiction"
        verbose_name_plural = "Juridictions"

    def __str__(self):
        return self.nom

    def get_autorite_requisition(self):
        """Retourne les infos pour la signature de la réquisition"""
        if self.type_juridiction == 'cour_appel':
            return {
                'titre': self.titre_procureur_general,
                'nom': self.nom_procureur_general,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': False
            }
        elif self.type_juridiction == 'cour_speciale':
            return {
                'titre': self.titre_procureur,  # "Procureur Spécial"
                'nom': self.nom_procureur,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': False
            }
        else:  # TPI
            return {
                'titre': self.titre_procureur,
                'nom': self.nom_procureur,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': True,
                'visa_titre': self.cour_appel_rattachement.titre_procureur_general if self.cour_appel_rattachement else "Procureur Général",
                'visa_nom': self.cour_appel_rattachement.nom_procureur_general if self.cour_appel_rattachement else ""
            }

    def get_autorite_executoire(self):
        """Retourne les infos pour la signature de l'exécutoire"""
        if self.type_juridiction == 'cour_appel':
            return {
                'titre': f"Président de la {self.nom}",
                'nom': self.nom_president_cour,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': False
            }
        elif self.type_juridiction == 'cour_speciale':
            return {
                'titre': f"Président de la {self.nom_court}",
                'nom': self.nom_president,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': False
            }
        else:  # TPI
            return {
                'titre': f"Président du {self.nom}",
                'nom': self.nom_president,
                'juridiction': self.nom,
                'ville': self.ville,
                'avec_visa': True,
                'visa_titre': f"Président de la {self.cour_appel_rattachement.nom}" if self.cour_appel_rattachement else "Président de la Cour d'Appel",
                'visa_nom': self.cour_appel_rattachement.nom_president_cour if self.cour_appel_rattachement else ""
            }

    def to_dict(self):
        return {
            'id': str(self.id),
            'nom': self.nom,
            'nom_court': self.nom_court,
            'type_juridiction': self.type_juridiction,
            'type_juridiction_display': self.get_type_juridiction_display(),
            'classe_tpi': self.classe_tpi,
            'cour_appel_rattachement_id': str(self.cour_appel_rattachement_id) if self.cour_appel_rattachement_id else None,
            'titre_procureur': self.titre_procureur,
            'nom_procureur': self.nom_procureur,
            'titre_president': self.titre_president,
            'nom_president': self.nom_president,
            'titre_procureur_general': self.titre_procureur_general,
            'nom_procureur_general': self.nom_procureur_general,
            'nom_president_cour': self.nom_president_cour,
            'ville': self.ville,
            'adresse': self.adresse,
            'telephone': self.telephone,
            'actif': self.actif,
            'ordre': self.ordre,
        }


class HistoriqueSauvegarde(models.Model):
    """Historique des sauvegardes"""
    STATUTS = [
        ('en_cours', 'En cours'),
        ('reussi', 'Réussi'),
        ('echec', 'Échec'),
    ]

    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    taille = models.BigIntegerField(default=0, verbose_name="Taille (octets)")
    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default='en_cours',
        verbose_name="Statut"
    )
    emplacement = models.CharField(max_length=500, blank=True, verbose_name="Emplacement")
    message = models.TextField(blank=True, verbose_name="Message")

    class Meta:
        verbose_name = "Sauvegarde"
        verbose_name_plural = "Historique des sauvegardes"
        ordering = ['-date']

    def __str__(self):
        return f"Sauvegarde du {self.date.strftime('%d/%m/%Y %H:%M')}"

    @property
    def taille_formatee(self):
        """Retourne la taille formatée (Ko, Mo, Go)"""
        if self.taille < 1024:
            return f"{self.taille} o"
        elif self.taille < 1024 * 1024:
            return f"{self.taille / 1024:.1f} Ko"
        elif self.taille < 1024 * 1024 * 1024:
            return f"{self.taille / (1024 * 1024):.1f} Mo"
        return f"{self.taille / (1024 * 1024 * 1024):.1f} Go"

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'taille': self.taille,
            'taille_formatee': self.taille_formatee,
            'statut': self.statut,
            'statut_display': self.get_statut_display(),
            'emplacement': self.emplacement,
            'message': self.message,
        }


class JournalModification(models.Model):
    """Journal des modifications des paramètres"""
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Utilisateur"
    )
    section = models.CharField(max_length=100, verbose_name="Section")
    champ = models.CharField(max_length=100, verbose_name="Champ modifié")
    ancienne_valeur = models.TextField(blank=True, verbose_name="Ancienne valeur")
    nouvelle_valeur = models.TextField(blank=True, verbose_name="Nouvelle valeur")

    class Meta:
        verbose_name = "Modification"
        verbose_name_plural = "Journal des modifications"
        ordering = ['-date']

    def __str__(self):
        return f"{self.section}.{self.champ} - {self.date.strftime('%d/%m/%Y %H:%M')}"

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'utilisateur': self.utilisateur.get_full_name() if self.utilisateur else 'Système',
            'section': self.section,
            'champ': self.champ,
            'ancienne_valeur': self.ancienne_valeur,
            'nouvelle_valeur': self.nouvelle_valeur,
        }


class ModeleTypeBail(models.Model):
    """Types de baux disponibles pour la gérance immobilière"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    description = models.TextField(blank=True, verbose_name="Description")
    modele_document = models.ForeignKey(
        ModeleDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Modèle de document associé"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Type de bail"
        verbose_name_plural = "Types de baux"
        ordering = ['libelle']

    def __str__(self):
        return self.libelle

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'description': self.description,
            'modele_document_id': self.modele_document_id,
            'actif': self.actif,
        }


class TrancheIPTS(models.Model):
    """
    Tranches du barème IPTS (Impôt Progressif sur Traitements et Salaires)
    Barème fiscal béninois pour le calcul de l'impôt sur les salaires
    """

    ordre = models.PositiveIntegerField(
        unique=True,
        verbose_name="Ordre de la tranche"
    )
    montant_min = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Montant minimum (FCFA)"
    )
    montant_max = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Montant maximum (FCFA)",
        help_text="Laisser vide pour la dernière tranche (illimité)"
    )
    taux = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux (%)"
    )

    # Période d'application
    date_debut = models.DateField(
        default='2024-01-01',
        verbose_name="Date d'effet"
    )
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    class Meta:
        verbose_name = "Tranche IPTS"
        verbose_name_plural = "Tranches IPTS"
        ordering = ['ordre']

    def __str__(self):
        if self.montant_max:
            return f"Tranche {self.ordre}: {self.montant_min:,.0f} - {self.montant_max:,.0f} FCFA → {self.taux}%"
        else:
            return f"Tranche {self.ordre}: > {self.montant_min:,.0f} FCFA → {self.taux}%"

    @classmethod
    def get_bareme_actif(cls):
        """Retourne le barème IPTS actif sous forme de liste de tuples"""
        from datetime import date
        tranches = cls.objects.filter(
            est_actif=True,
            date_debut__lte=date.today()
        ).filter(
            models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=date.today())
        ).order_by('ordre')

        bareme = []
        for t in tranches:
            bareme.append((t.montant_min, t.montant_max, t.taux))
        return bareme

    @classmethod
    def calculer_ipts(cls, salaire_imposable):
        """
        Calcule l'IPTS selon le barème actif

        Args:
            salaire_imposable: Montant du salaire imposable (après déduction CNSS)

        Returns:
            Montant de l'IPTS arrondi à l'entier
        """
        bareme = cls.get_bareme_actif()

        if not bareme:
            # Barème par défaut si aucun configuré (barème 2024 Bénin)
            bareme = [
                (Decimal('0'), Decimal('50000'), Decimal('0')),
                (Decimal('50001'), Decimal('130000'), Decimal('10')),
                (Decimal('130001'), Decimal('280000'), Decimal('15')),
                (Decimal('280001'), Decimal('480000'), Decimal('19')),
                (Decimal('480001'), Decimal('730000'), Decimal('24')),
                (Decimal('730001'), Decimal('1030000'), Decimal('28')),
                (Decimal('1030001'), Decimal('1380000'), Decimal('32')),
                (Decimal('1380001'), Decimal('1880000'), Decimal('35')),
                (Decimal('1880001'), Decimal('3780000'), Decimal('37')),
                (Decimal('3780001'), None, Decimal('40')),
            ]

        ipts = Decimal('0')
        reste = Decimal(str(salaire_imposable))

        for seuil_min, seuil_max, taux in bareme:
            seuil_min = Decimal(str(seuil_min))
            taux = Decimal(str(taux))

            if seuil_max:
                seuil_max = Decimal(str(seuil_max))
                largeur_tranche = seuil_max - seuil_min + 1
            else:
                # Dernière tranche illimitée
                if reste > 0:
                    ipts += reste * taux / 100
                break

            if reste <= 0:
                break

            montant_dans_tranche = min(reste, largeur_tranche)
            ipts += montant_dans_tranche * taux / 100
            reste -= montant_dans_tranche

        return ipts.quantize(Decimal('1'))

    def to_dict(self):
        return {
            'id': self.id,
            'ordre': self.ordre,
            'montant_min': str(self.montant_min),
            'montant_max': str(self.montant_max) if self.montant_max else None,
            'taux': str(self.taux),
            'date_debut': self.date_debut.isoformat() if self.date_debut else None,
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'est_actif': self.est_actif,
        }


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION EN-TÊTES ET PIEDS DE PAGE
# ═══════════════════════════════════════════════════════════════

class ConfigurationEnteteDocument(models.Model):
    """Configuration des en-têtes et pieds de page pour les documents"""

    TYPE_DOCUMENT_CHOICES = [
        ('etude', 'Documents de l\'étude (factures, rapports, courriers)'),
        ('memoire', 'Mémoires et cédules (en-tête juridiction)'),
        ('acte', 'Actes d\'huissier'),
        ('autre', 'Autres documents'),
    ]

    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        unique=True,
        verbose_name="Type de document"
    )

    # ═══════════════════════════════════════════════════════════════
    # EN-TÊTE
    # ═══════════════════════════════════════════════════════════════
    utiliser_entete_image = models.BooleanField(
        default=False,
        verbose_name="Utiliser une image d'en-tête"
    )
    entete_image = models.ImageField(
        upload_to='entetes/',
        null=True,
        blank=True,
        verbose_name="Image d'en-tête",
        help_text="Uploadez votre en-tête habituel (format recommandé : PNG ou JPG, largeur 2480px pour A4)"
    )
    entete_hauteur = models.PositiveIntegerField(
        default=150,
        verbose_name="Hauteur de l'en-tête (pixels)",
        help_text="Hauteur de la zone d'en-tête sur le document"
    )
    entete_marge_haut = models.PositiveIntegerField(
        default=20,
        verbose_name="Marge supérieure (pixels)"
    )
    entete_marge_gauche = models.PositiveIntegerField(
        default=50,
        verbose_name="Marge gauche (pixels)"
    )
    entete_marge_droite = models.PositiveIntegerField(
        default=50,
        verbose_name="Marge droite (pixels)"
    )
    entete_centrer = models.BooleanField(
        default=True,
        verbose_name="Centrer l'en-tête"
    )

    # ═══════════════════════════════════════════════════════════════
    # PIED DE PAGE
    # ═══════════════════════════════════════════════════════════════
    utiliser_pied_image = models.BooleanField(
        default=False,
        verbose_name="Utiliser une image de pied de page"
    )
    pied_image = models.ImageField(
        upload_to='pieds_page/',
        null=True,
        blank=True,
        verbose_name="Image de pied de page"
    )
    pied_hauteur = models.PositiveIntegerField(
        default=80,
        verbose_name="Hauteur du pied de page (pixels)"
    )
    pied_marge_bas = models.PositiveIntegerField(
        default=20,
        verbose_name="Marge inférieure (pixels)"
    )
    pied_centrer = models.BooleanField(
        default=True,
        verbose_name="Centrer le pied de page"
    )

    # Texte alternatif si pas d'image
    pied_texte = models.TextField(
        blank=True,
        verbose_name="Texte de pied de page (si pas d'image)",
        help_text="Ex: Adresse, téléphone, email, RCCM, IFU..."
    )

    # ═══════════════════════════════════════════════════════════════
    # MARGES DU CORPS
    # ═══════════════════════════════════════════════════════════════
    corps_marge_haut = models.PositiveIntegerField(
        default=180,
        verbose_name="Début du contenu (pixels depuis le haut)",
        help_text="Espace entre le haut de la page et le début du contenu"
    )
    corps_marge_bas = models.PositiveIntegerField(
        default=100,
        verbose_name="Fin du contenu (pixels depuis le bas)"
    )

    # Métadonnées
    est_actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration en-tête document"
        verbose_name_plural = "Configurations en-têtes documents"

    def __str__(self):
        return f"En-tête: {self.get_type_document_display()}"

    @classmethod
    def get_config(cls, type_document):
        """Récupère la configuration pour un type de document"""
        config, created = cls.objects.get_or_create(type_document=type_document)
        return config


class EnteteJuridiction(models.Model):
    """
    Configuration de l'en-tête hiérarchique des juridictions.
    Pour les mémoires : RÉPUBLIQUE DU BÉNIN → Cour d'Appel → TPI
    """

    NIVEAU_CHOICES = [
        (1, 'République (niveau national)'),
        (2, 'Cour Suprême / CRIET'),
        (3, 'Cour d\'Appel'),
        (4, 'Tribunal de Première Instance'),
        (5, 'Tribunal de Commerce'),
        (6, 'Autre juridiction'),
    ]

    # Identification
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    nom = models.CharField(max_length=200, verbose_name="Nom de la juridiction")
    nom_complet = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Nom complet",
        help_text="Ex: COUR D'APPEL DE PARAKOU"
    )

    # Hiérarchie
    niveau = models.PositiveIntegerField(choices=NIVEAU_CHOICES, verbose_name="Niveau hiérarchique")
    juridiction_superieure = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='juridictions_inferieures',
        verbose_name="Juridiction supérieure"
    )

    # Affichage en-tête
    afficher_embleme = models.BooleanField(default=True, verbose_name="Afficher l'emblème national")
    devise = models.CharField(
        max_length=100,
        default="Fraternité - Justice - Travail",
        verbose_name="Devise"
    )

    # Image/logo spécifique (optionnel)
    logo = models.ImageField(
        upload_to='logos_juridictions/',
        null=True,
        blank=True,
        verbose_name="Logo spécifique"
    )

    # Ordre d'affichage
    ordre_affichage = models.PositiveIntegerField(default=0)
    est_actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "En-tête juridiction"
        verbose_name_plural = "En-têtes juridictions"
        ordering = ['niveau', 'ordre_affichage']

    def __str__(self):
        return self.nom_complet or self.nom

    def get_hierarchie(self):
        """Retourne la hiérarchie complète (de la juridiction sup à celle-ci)"""
        hierarchie = [self]
        parent = self.juridiction_superieure
        while parent:
            hierarchie.insert(0, parent)
            parent = parent.juridiction_superieure
        return hierarchie

    def get_entete_complet(self):
        """Retourne l'en-tête formaté pour les mémoires"""
        lignes = []
        for j in self.get_hierarchie():
            lignes.append(j.nom_complet or j.nom.upper())
        return lignes

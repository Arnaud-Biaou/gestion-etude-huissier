from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
import json


class Utilisateur(AbstractUser):
    """Modele utilisateur personnalise"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secretaire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='clerc')
    telephone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class Collaborateur(models.Model):
    """Collaborateurs de l'etude"""
    ROLE_CHOICES = [
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secretaire'),
    ]
    nom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    actif = models.BooleanField(default=True)
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='collaborateur'
    )

    class Meta:
        verbose_name = 'Collaborateur'
        verbose_name_plural = 'Collaborateurs'

    def __str__(self):
        return self.nom


class Partie(models.Model):
    """Parties (demandeur ou defendeur) d'un dossier"""
    TYPE_PERSONNE_CHOICES = [
        ('physique', 'Personne physique'),
        ('morale', 'Personne morale'),
    ]
    FORME_JURIDIQUE_CHOICES = [
        ('SARL', 'SARL - Société à Responsabilité Limitée'),
        ('SARLU', 'SARLU - SARL Unipersonnelle'),
        ('SA', 'SA - Société Anonyme'),
        ('SAS', 'SAS - Société par Actions Simplifiée'),
        ('SASU', 'SASU - SAS Unipersonnelle'),
        ('SNC', 'SNC - Société en Nom Collectif'),
        ('SCS', 'SCS - Société en Commandite Simple'),
        ('GIE', 'GIE - Groupement d\'Intérêt Économique'),
        ('ASSOCIATION', 'Association'),
        ('ONG', 'ONG'),
        ('ETABLISSEMENT_PUBLIC', 'Établissement public'),
        ('AUTRE', 'Autre'),
    ]

    type_personne = models.CharField(max_length=10, choices=TYPE_PERSONNE_CHOICES, default='physique')

    # Personne physique
    nom = models.CharField(max_length=100, blank=True)
    prenoms = models.CharField(max_length=150, blank=True)
    nationalite = models.CharField(max_length=50, blank=True, default='Beninoise')
    profession = models.CharField(max_length=100, blank=True)
    domicile = models.TextField(blank=True)

    # ═══════════════════════════════════════════════════════════════
    # PERSONNE PHYSIQUE - Activité commerciale (si applicable)
    # ═══════════════════════════════════════════════════════════════
    est_commercant = models.BooleanField(
        default=False,
        verbose_name="Est commerçant/entrepreneur individuel"
    )
    nom_commercial = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom commercial",
        help_text="Ex: KOFFI DISTRIBUTION"
    )
    enseigne = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Enseigne",
        help_text="Ex: SUPERMARCHÉ DU CENTRE"
    )
    activite_commerciale = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Activité commerciale",
        help_text="Ex: Commerce général, Import-Export"
    )
    # Note: rccm et ifu peuvent aussi servir pour les personnes physiques commerçantes

    # Personne morale
    denomination = models.CharField(max_length=200, blank=True, verbose_name='Dénomination sociale')
    capital_social = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name='Capital social (FCFA)'
    )
    forme_juridique = models.CharField(
        max_length=20, choices=FORME_JURIDIQUE_CHOICES, blank=True,
        verbose_name='Forme juridique'
    )
    rccm = models.CharField(
        max_length=100, blank=True,
        verbose_name='N° RCCM',
        help_text='Ex: RB/COT/21 B 12345'
    )
    siege_social = models.TextField(
        blank=True,
        verbose_name='Siège social',
        help_text='Adresse complète du siège'
    )
    representant = models.CharField(
        max_length=150, blank=True,
        verbose_name='Représentant légal',
        help_text='Nom complet du gérant/directeur'
    )
    qualite_representant = models.CharField(
        max_length=100, blank=True,
        verbose_name='Qualité du représentant',
        help_text='Ex: Gérant, Directeur Général, PDG'
    )

    # Commun
    telephone = models.CharField(max_length=20, blank=True)
    ifu = models.CharField(
        max_length=50, blank=True,
        verbose_name='N° IFU',
        help_text='Identifiant Fiscal Unique'
    )

    class Meta:
        verbose_name = 'Partie'
        verbose_name_plural = 'Parties'

    def __str__(self):
        if self.type_personne == 'morale':
            return self.denomination or 'Personne morale sans nom'
        return f"{self.nom} {self.prenoms}".strip() or 'Personne physique sans nom'

    def get_nom_complet(self):
        if self.type_personne == 'morale':
            return self.denomination
        return f"{self.nom} {self.prenoms}".strip()

    def get_identification_complete(self):
        """Retourne l'identification complète pour les actes juridiques"""
        if self.type_personne == 'morale':
            lignes = [f"{self.denomination}"]
            if self.forme_juridique:
                lignes[0] = f"{self.denomination}, {self.get_forme_juridique_display()}"
            if self.capital_social:
                lignes.append(f"au capital de {self.capital_social:,.0f} FCFA".replace(',', ' '))
            if self.rccm:
                lignes.append(f"immatriculée au RCCM sous le n° {self.rccm}")
            if self.ifu:
                lignes.append(f"IFU: {self.ifu}")
            if self.siege_social:
                lignes.append(f"dont le siège social est sis à {self.siege_social}")
            if self.representant:
                qualite = f", {self.qualite_representant}" if self.qualite_representant else ""
                lignes.append(f"représentée par {self.representant}{qualite}")
            return ', '.join(lignes)
        else:
            # Personne physique
            lignes = [f"{self.nom} {self.prenoms}".strip()]

            # Si commerçant avec nom commercial ou enseigne
            if self.est_commercant or self.nom_commercial or self.enseigne:
                if self.nom_commercial:
                    lignes.append(f"exerçant sous le nom commercial \"{self.nom_commercial}\"")
                if self.enseigne:
                    lignes.append(f"exploitant l'enseigne \"{self.enseigne}\"")
                if self.activite_commerciale:
                    lignes.append(self.activite_commerciale)
                if self.rccm:
                    lignes.append(f"immatriculé(e) au RCCM sous le n° {self.rccm}")
                if self.ifu:
                    lignes.append(f"IFU: {self.ifu}")
            elif self.profession:
                lignes.append(self.profession)

            if self.nationalite:
                lignes.append(f"de nationalité {self.nationalite}")
            if self.domicile:
                lignes.append(f"demeurant à {self.domicile}")

            return ', '.join(lignes)


class Dossier(models.Model):
    """Dossier de l'etude"""
    TYPE_DOSSIER_CHOICES = [
        ('recouvrement', 'Recouvrement'),
        ('expulsion', 'Expulsion'),
        ('constat', 'Constat'),
        ('signification', 'Signification'),
        ('saisie', 'Saisie'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('urgent', 'Urgent'),
        ('archive', 'Archive'),
        ('cloture', 'Cloture'),
    ]
    PHASE_CHOICES = [
        ('amiable', 'Phase amiable'),
        ('force', 'Phase forcée (exécution)'),
    ]

    reference = models.CharField(max_length=20, unique=True)
    is_contentieux = models.BooleanField(default=False, verbose_name='Contentieux')
    type_dossier = models.CharField(max_length=20, choices=TYPE_DOSSIER_CHOICES, blank=True)
    description = models.TextField(blank=True)
    montant_creance = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    date_creance = models.DateField(null=True, blank=True)
    date_ouverture = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    # Lien avec le créancier
    creancier = models.ForeignKey(
        'Creancier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dossiers', verbose_name='Créancier'
    )

    # Phase du recouvrement (amiable ou forcé)
    phase = models.CharField(
        max_length=10, choices=PHASE_CHOICES, default='amiable',
        verbose_name='Phase de recouvrement'
    )
    date_passage_force = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date passage en phase forcée'
    )

    # Montants détaillés pour le suivi
    montant_principal = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name='Montant principal'
    )
    montant_interets = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Intérêts'
    )
    montant_frais = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de procédure'
    )
    montant_emoluments = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Émoluments'
    )
    montant_depens = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Dépens'
    )
    montant_accessoires = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Accessoires'
    )

    # Titre exécutoire (pour phase forcée)
    titre_executoire_type = models.CharField(
        max_length=100, blank=True,
        verbose_name='Type de titre exécutoire'
    )
    titre_executoire_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name='Référence du titre'
    )
    titre_executoire_date = models.DateField(
        null=True, blank=True,
        verbose_name='Date du titre'
    )
    titre_executoire_juridiction = models.CharField(
        max_length=200, blank=True,
        verbose_name='Juridiction'
    )

    affecte_a = models.ForeignKey(
        Collaborateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossiers'
    )
    demandeurs = models.ManyToManyField(Partie, related_name='dossiers_demandeur', blank=True)
    defendeurs = models.ManyToManyField(Partie, related_name='dossiers_defendeur', blank=True)

    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='dossiers_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dossier'
        verbose_name_plural = 'Dossiers'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut'], name='gestion_dos_statut_idx'),
            models.Index(fields=['type_dossier'], name='gestion_dos_type_idx'),
            models.Index(fields=['phase'], name='gestion_dos_phase_idx'),
            models.Index(fields=['date_ouverture'], name='gestion_dos_date_ouv_idx'),
            models.Index(fields=['date_creation'], name='gestion_dos_date_cre_idx'),
        ]

    def __str__(self):
        return f"{self.reference} - {self.get_intitule()}"

    def get_intitule(self):
        demandeur = self.demandeurs.first()
        defendeur = self.defendeurs.first()
        if self.is_contentieux and demandeur and defendeur:
            return f"{demandeur.get_nom_complet()} C/ {defendeur.get_nom_complet()}"
        elif demandeur:
            return demandeur.get_nom_complet()
        return "Sans parties"

    def get_montant_total_du(self):
        """Calcule le montant total dû sur le dossier"""
        total = (
            (self.montant_principal or self.montant_creance or 0) +
            (self.montant_interets or 0) +
            (self.montant_frais or 0) +
            (self.montant_emoluments or 0) +
            (self.montant_depens or 0) +
            (self.montant_accessoires or 0)
        )
        return total

    def get_total_encaisse(self):
        """Retourne le total encaissé sur ce dossier"""
        from django.db.models import Sum
        return self.encaissements.filter(statut='valide').aggregate(
            total=Sum('montant')
        )['total'] or 0

    def get_solde_restant(self):
        """Retourne le solde restant dû"""
        return self.get_montant_total_du() - self.get_total_encaisse()

    def get_taux_recouvrement(self):
        """Retourne le taux de recouvrement"""
        total_du = self.get_montant_total_du()
        if total_du > 0:
            return (self.get_total_encaisse() / total_du) * 100
        return 0

    def basculer_vers_force(self, utilisateur, motif, titre_info=None, frais_supplementaires=None):
        """Bascule le dossier de la phase amiable vers la phase forcée"""
        from django.db.models import Sum

        if self.phase == 'force':
            raise ValueError("Ce dossier est déjà en phase forcée")

        # Calculer l'état actuel de la créance
        total_encaisse = self.get_total_encaisse()
        principal_restant = (self.montant_principal or self.montant_creance or 0)
        interets_restant = self.montant_interets or 0
        frais_restant = self.montant_frais or 0

        # Imputer les encaissements déjà effectués
        reste_a_imputer = total_encaisse
        if reste_a_imputer > 0:
            # Imputer d'abord sur les frais
            if frais_restant > 0:
                imputation_frais = min(reste_a_imputer, frais_restant)
                frais_restant -= imputation_frais
                reste_a_imputer -= imputation_frais
            # Puis sur les intérêts
            if reste_a_imputer > 0 and interets_restant > 0:
                imputation_interets = min(reste_a_imputer, interets_restant)
                interets_restant -= imputation_interets
                reste_a_imputer -= imputation_interets
            # Enfin sur le principal
            if reste_a_imputer > 0:
                principal_restant -= reste_a_imputer

        total_reste_du = principal_restant + interets_restant + frais_restant

        # Créer l'enregistrement de basculement
        basculement = BasculementAmiableForce(
            dossier=self,
            motif=motif,
            effectue_par=utilisateur,
            montant_principal_restant=principal_restant,
            montant_interets_restant=interets_restant,
            montant_frais_restant=frais_restant,
            total_reste_du=total_reste_du,
            donnees_phase_amiable={
                'montant_principal_initial': float(self.montant_principal or self.montant_creance or 0),
                'montant_interets_initial': float(self.montant_interets or 0),
                'montant_frais_initial': float(self.montant_frais or 0),
                'total_encaisse': float(total_encaisse),
                'nb_encaissements': self.encaissements.filter(statut='valide').count(),
                'date_basculement': timezone.now().isoformat()
            }
        )

        # Titre exécutoire
        if titre_info:
            basculement.type_titre = titre_info.get('type', '')
            basculement.reference_titre = titre_info.get('reference', '')
            basculement.juridiction = titre_info.get('juridiction', '')
            basculement.date_titre = titre_info.get('date')

            self.titre_executoire_type = titre_info.get('type', '')
            self.titre_executoire_reference = titre_info.get('reference', '')
            self.titre_executoire_juridiction = titre_info.get('juridiction', '')
            self.titre_executoire_date = titre_info.get('date')

        # Frais supplémentaires
        if frais_supplementaires:
            basculement.depens = frais_supplementaires.get('depens', 0)
            basculement.frais_justice = frais_supplementaires.get('frais_justice', 0)

            # Calculer les émoluments OHADA
            emoluments = basculement.calculer_emoluments_ohada(total_reste_du)
            basculement.emoluments_ohada = emoluments

            # Nouveau total
            basculement.nouveau_total = (
                total_reste_du +
                basculement.depens +
                basculement.frais_justice +
                basculement.emoluments_ohada
            )

            # Mettre à jour le dossier
            self.montant_principal = principal_restant
            self.montant_interets = interets_restant
            self.montant_frais = frais_restant
            self.montant_depens = basculement.depens + basculement.frais_justice
            self.montant_emoluments = basculement.emoluments_ohada
        else:
            basculement.nouveau_total = total_reste_du
            self.montant_principal = principal_restant
            self.montant_interets = interets_restant
            self.montant_frais = frais_restant

        basculement.save()

        # Mettre à jour le dossier
        self.phase = 'force'
        self.date_passage_force = timezone.now()
        self.save()

        return basculement

    @classmethod
    def generer_reference(cls):
        now = timezone.now()
        prefix = 175  # Numero de la loi
        mois = str(now.month).zfill(2)
        annee = str(now.year)[-2:]
        suffix = "MAB"  # Initiales de l'huissier

        # Trouver le prochain numero
        derniers = cls.objects.filter(
            reference__startswith=f"{prefix}_{mois}{annee}"
        ).count()

        return f"{prefix + derniers}_{mois}{annee}_{suffix}"


class Facture(models.Model):
    """Factures de l'etude"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('attente', 'En attente'),
        ('payee', 'Payee'),
        ('annulee', 'Annulee'),
    ]

    # ═══════════════════════════════════════════════════════════════
    # TYPE DE FACTURE (Standard, Avoir, Corrective)
    # ═══════════════════════════════════════════════════════════════

    TYPE_FACTURE_CHOICES = [
        ('standard', 'Facture standard'),
        ('avoir', 'Facture d\'avoir (annulation)'),
        ('corrective', 'Facture corrective'),
    ]

    # ═══════════════════════════════════════════════════════════════
    # STATUT MECeF ÉTENDU
    # ═══════════════════════════════════════════════════════════════

    STATUT_MECEF_CHOICES = [
        ('non_normalise', 'Non normalisé'),
        ('en_attente', 'En attente de normalisation'),
        ('normalise', 'Normalisé'),
        ('erreur', 'Erreur de normalisation'),
        ('annule', 'Annulé par avoir'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    dossier = models.ForeignKey(
        Dossier, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures'
    )
    client = models.CharField(max_length=200)
    ifu = models.CharField(max_length=20, blank=True, verbose_name='IFU Client')
    montant_ht = models.DecimalField(max_digits=15, decimal_places=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    montant_tva = models.DecimalField(max_digits=15, decimal_places=0)
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=0)
    date_emission = models.DateField(default=timezone.now)
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='attente')
    observations = models.TextField(blank=True)

    # MECeF
    mecef_qr = models.TextField(blank=True, verbose_name='QR Code MECeF')
    mecef_numero = models.CharField(max_length=50, blank=True, verbose_name='Numero MECeF')
    nim = models.CharField(max_length=20, blank=True, verbose_name='NIM')
    date_mecef = models.DateTimeField(null=True, blank=True, verbose_name='Date normalisation MECeF')

    # ═══════════════════════════════════════════════════════════════
    # CHAMPS AVOIR ET FACTURES CORRECTIVES
    # ═══════════════════════════════════════════════════════════════

    type_facture = models.CharField(
        max_length=20,
        choices=TYPE_FACTURE_CHOICES,
        default='standard',
        verbose_name="Type de facture"
    )

    # Lien avec facture originale (pour avoir et corrective)
    facture_origine = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='factures_liees',
        verbose_name="Facture d'origine",
        help_text="Facture originale annulée (pour avoir) ou corrigée (pour corrective)"
    )

    # Motif de l'avoir ou de la correction
    motif_avoir_correction = models.TextField(
        blank=True,
        verbose_name="Motif de l'avoir/correction",
        help_text="Raison de l'annulation ou de la correction"
    )

    # Statut MECeF étendu
    statut_mecef = models.CharField(
        max_length=20,
        choices=STATUT_MECEF_CHOICES,
        default='non_normalise',
        verbose_name="Statut MECeF"
    )

    # Avoir lié (pour une facture standard annulée)
    avoir_lie = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facture_annulee',
        verbose_name="Avoir d'annulation"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date_emission']

    def __str__(self):
        return f"{self.numero} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.montant_tva:
            self.montant_tva = self.montant_ht * self.taux_tva / 100
        if not self.montant_ttc:
            self.montant_ttc = self.montant_ht + self.montant_tva
        super().save(*args, **kwargs)

    @classmethod
    def generer_numero(cls, type_facture='standard'):
        """Génère un numéro de facture unique selon le type"""
        from django.utils import timezone
        now = timezone.now()
        annee = now.year

        # Préfixe selon le type de facture
        if type_facture == 'avoir':
            prefix = f"AVO-{annee}-"
        elif type_facture == 'corrective':
            prefix = f"COR-{annee}-"
        else:
            prefix = f"FAC-{annee}-"

        # Trouver le dernier numéro avec ce préfixe
        derniere = cls.objects.filter(numero__startswith=prefix).order_by('-numero').first()

        if derniere:
            try:
                dernier_num = int(derniere.numero.split('-')[-1])
                nouveau_num = dernier_num + 1
            except (ValueError, IndexError):
                nouveau_num = 1
        else:
            nouveau_num = 1

        # Vérifier l'unicité et incrémenter si nécessaire
        for _ in range(100):
            numero = f"{prefix}{nouveau_num:04d}"
            if not cls.objects.filter(numero=numero).exists():
                return numero
            nouveau_num += 1

        # Fallback avec timestamp
        import time
        return f"{prefix}{int(time.time())}"

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES AVOIR ET FACTURES CORRECTIVES
    # ═══════════════════════════════════════════════════════════════

    def peut_creer_avoir(self):
        """Vérifie si on peut créer un avoir pour cette facture"""
        return (
            self.type_facture == 'standard' and
            self.statut_mecef == 'normalise' and
            not self.avoir_lie
        )

    def creer_avoir(self, motif, user=None, lignes_ids=None):
        """Crée une facture d'avoir pour annuler cette facture (totalement ou partiellement)"""
        if not self.peut_creer_avoir():
            raise ValueError("Impossible de créer un avoir pour cette facture")

        # Sélectionner les lignes à annuler
        if lignes_ids:
            lignes_a_annuler = self.lignes.filter(id__in=lignes_ids)
            annulation_partielle = True
        else:
            lignes_a_annuler = self.lignes.all()
            annulation_partielle = False

        # Calculer les montants de l'avoir
        total_honoraires = 0
        total_debours = 0

        for ligne in lignes_a_annuler:
            if ligne.type_ligne == 'debours':
                total_debours += abs(ligne.montant_ht or ligne.prix_unitaire)
            else:
                total_honoraires += abs(ligne.honoraires or ligne.prix_unitaire)
                total_debours += abs(ligne.timbre or 0) + abs(ligne.enregistrement or 0)

        montant_ht = total_honoraires + total_debours
        montant_tva = total_honoraires * self.taux_tva / 100
        montant_ttc = montant_ht + montant_tva

        avoir = Facture.objects.create(
            numero=Facture.generer_numero('avoir'),
            type_facture='avoir',
            facture_origine=self,
            client=self.client,
            ifu=self.ifu,
            dossier=self.dossier,
            montant_ht=-montant_ht,  # Montant négatif
            taux_tva=self.taux_tva,
            montant_tva=-montant_tva,
            montant_ttc=-montant_ttc,
            motif_avoir_correction=motif,
            observations=f"AVOIR {'partiel ' if annulation_partielle else ''}sur facture {self.numero}",
            date_emission=timezone.now().date(),
        )

        # Copier les lignes avec montants négatifs
        for ligne in lignes_a_annuler:
            LigneFacture.objects.create(
                facture=avoir,
                description=f"Annulation: {ligne.description}",
                quantite=ligne.quantite,
                prix_unitaire=-abs(ligne.prix_unitaire),
                type_ligne=ligne.type_ligne,
                honoraires=-abs(ligne.honoraires) if ligne.honoraires else None,
                timbre=-abs(ligne.timbre) if ligne.timbre else None,
                enregistrement=-abs(ligne.enregistrement) if ligne.enregistrement else None,
                montant_ht=-abs(ligne.montant_ht) if ligne.montant_ht else -abs(ligne.prix_unitaire)
            )

        # Pour une annulation totale, lier l'avoir à la facture originale
        if not annulation_partielle:
            self.avoir_lie = avoir
            self.statut_mecef = 'annule'
            self.save()

        return avoir

    def creer_facture_corrective(self, nouvelles_donnees, motif, user=None):
        """Crée une facture corrective après avoir créé un avoir"""
        if not self.avoir_lie:
            raise ValueError("Créez d'abord un avoir avant la facture corrective")

        # Générer un nouveau numéro pour la facture corrective
        numero_corrective = f"COR-{self.numero}"

        corrective = Facture.objects.create(
            numero=numero_corrective,
            type_facture='corrective',
            facture_origine=self,
            client=self.client,
            ifu=self.ifu,
            dossier=self.dossier,
            motif_avoir_correction=motif,
            observations=f"CORRECTIVE de facture {self.numero}",
            date_emission=timezone.now().date(),
            taux_tva=self.taux_tva,
            **nouvelles_donnees
        )

        return corrective

    def est_avoir(self):
        """Vérifie si cette facture est un avoir"""
        return self.type_facture == 'avoir'

    def est_corrective(self):
        """Vérifie si cette facture est une corrective"""
        return self.type_facture == 'corrective'

    def est_annulee(self):
        """Vérifie si cette facture a été annulée par un avoir"""
        return self.statut_mecef == 'annule' or self.avoir_lie is not None


class LigneFacture(models.Model):
    """Lignes de facture"""
    TYPE_LIGNE_CHOICES = [
        ('acte', 'Acte'),
        ('debours', 'Débours'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    description = models.CharField(max_length=500)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=0)

    # Type de ligne : acte ou débours
    type_ligne = models.CharField(
        max_length=20,
        choices=TYPE_LIGNE_CHOICES,
        default='acte',
        verbose_name='Type de ligne'
    )

    # Champs spécifiques aux actes (décomposition)
    honoraires = models.DecimalField(
        max_digits=15, decimal_places=0,
        null=True, blank=True,
        verbose_name='Honoraires'
    )
    timbre = models.DecimalField(
        max_digits=15, decimal_places=0,
        null=True, blank=True,
        verbose_name='Timbre'
    )
    enregistrement = models.DecimalField(
        max_digits=15, decimal_places=0,
        null=True, blank=True,
        verbose_name='Enregistrement'
    )
    montant_ht = models.DecimalField(
        max_digits=15, decimal_places=0,
        null=True, blank=True,
        verbose_name='Montant HT'
    )

    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'

    def __str__(self):
        return f"{self.description} x {self.quantite}"

    @property
    def total(self):
        # Pour les débours, retourne juste le prix_unitaire (montant fixe)
        if self.type_ligne == 'debours':
            return self.prix_unitaire
        # Pour les actes, utilise montant_ht si disponible, sinon calcul classique
        if self.montant_ht:
            return self.montant_ht
        return self.quantite * self.prix_unitaire

    def save(self, *args, **kwargs):
        # Pour les débours, le montant_ht = prix_unitaire (pas de décomposition)
        if self.type_ligne == 'debours':
            self.montant_ht = self.prix_unitaire
            self.honoraires = None
            self.timbre = None
            self.enregistrement = None
        # Pour les actes, calculer montant_ht si honoraires/timbre/enreg sont fournis
        elif self.honoraires is not None:
            h = self.honoraires or 0
            t = self.timbre or 0
            e = self.enregistrement or 0
            self.montant_ht = h + t + e
            self.prix_unitaire = h  # Prix unitaire = honoraires pour compatibilité
        super().save(*args, **kwargs)


class ActeProcedure(models.Model):
    """Actes de procedure du catalogue"""
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=200)
    tarif = models.DecimalField(max_digits=10, decimal_places=0)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Acte de procedure'
        verbose_name_plural = 'Actes de procedure'
        ordering = ['libelle']

    def __str__(self):
        return f"{self.libelle} ({self.tarif:,.0f} FCFA)"


class HistoriqueCalcul(models.Model):
    """Historique des calculs de recouvrement"""
    MODE_CHOICES = [
        ('complet', 'Calcul complet'),
        ('emoluments', 'Emoluments seuls'),
    ]

    nom = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    donnees = models.JSONField()  # Stocke toutes les donnees du calcul
    resultats = models.JSONField()  # Stocke les resultats
    total = models.DecimalField(max_digits=15, decimal_places=0)

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='calculs'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique de calcul'
        verbose_name_plural = 'Historiques de calculs'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} - {self.total:,.0f} FCFA"


class TauxLegal(models.Model):
    """Taux legaux UEMOA par annee"""
    annee = models.IntegerField(unique=True)
    taux = models.DecimalField(max_digits=6, decimal_places=4)
    source = models.CharField(max_length=100, default='BCEAO')

    class Meta:
        verbose_name = 'Taux legal'
        verbose_name_plural = 'Taux legaux'
        ordering = ['-annee']

    def __str__(self):
        return f"{self.annee}: {self.taux}%"


class MessageChatbot(models.Model):
    """Messages du chatbot pour l'historique"""
    TYPE_CHOICES = [
        ('bot', 'Bot'),
        ('user', 'Utilisateur'),
    ]

    session_id = models.CharField(max_length=100)
    type_message = models.CharField(max_length=10, choices=TYPE_CHOICES)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message chatbot'
        verbose_name_plural = 'Messages chatbot'
        ordering = ['date_creation']

    def __str__(self):
        return f"{self.type_message} - {self.session_id[:8]} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"


# =============================================================================
# MODELES POUR LA GESTION DES CREANCIERS
# =============================================================================

class Creancier(models.Model):
    """Créanciers (banques, microfinances, entreprises, particuliers)"""
    TYPE_CREANCIER_CHOICES = [
        ('banque', 'Banque'),
        ('microfinance', 'Institution de Microfinance'),
        ('entreprise', 'Entreprise'),
        ('particulier', 'Particulier'),
        ('etat', 'État/Administration'),
        ('autre', 'Autre'),
    ]

    # Informations générales
    code = models.CharField(max_length=20, unique=True, verbose_name='Code créancier')
    nom = models.CharField(max_length=200, verbose_name='Nom/Dénomination')
    type_creancier = models.CharField(max_length=20, choices=TYPE_CREANCIER_CHOICES, default='entreprise')

    # Coordonnées
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)

    # Informations fiscales et légales
    ifu = models.CharField(
        max_length=50, blank=True,
        verbose_name='N° IFU',
        help_text='Identifiant Fiscal Unique'
    )
    rccm = models.CharField(
        max_length=100, blank=True,
        verbose_name='N° RCCM',
        help_text='Ex: RB/COT/21 B 12345'
    )

    # Informations personnes morales
    FORME_JURIDIQUE_CHOICES = [
        ('SARL', 'SARL - Société à Responsabilité Limitée'),
        ('SARLU', 'SARLU - SARL Unipersonnelle'),
        ('SA', 'SA - Société Anonyme'),
        ('SAS', 'SAS - Société par Actions Simplifiée'),
        ('SASU', 'SASU - SAS Unipersonnelle'),
        ('SNC', 'SNC - Société en Nom Collectif'),
        ('SCS', 'SCS - Société en Commandite Simple'),
        ('GIE', 'GIE - Groupement d\'Intérêt Économique'),
        ('ASSOCIATION', 'Association'),
        ('ONG', 'ONG'),
        ('ETABLISSEMENT_PUBLIC', 'Établissement public'),
        ('AUTRE', 'Autre'),
    ]
    forme_juridique = models.CharField(
        max_length=20, choices=FORME_JURIDIQUE_CHOICES, blank=True,
        verbose_name='Forme juridique'
    )
    capital_social = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name='Capital social (FCFA)'
    )
    siege_social = models.TextField(
        blank=True,
        verbose_name='Siège social',
        help_text='Adresse complète du siège social'
    )
    representant_legal = models.CharField(
        max_length=200, blank=True,
        verbose_name='Représentant légal',
        help_text='Nom complet du gérant/directeur'
    )
    qualite_representant = models.CharField(
        max_length=100, blank=True,
        verbose_name='Qualité du représentant',
        help_text='Ex: Gérant, Directeur Général, PDG'
    )

    # Contact référent
    contact_nom = models.CharField(max_length=100, blank=True, verbose_name='Nom du contact')
    contact_fonction = models.CharField(max_length=100, blank=True, verbose_name='Fonction')
    contact_telephone = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)

    # Coordonnées bancaires pour les reversements
    banque_nom = models.CharField(max_length=100, blank=True, verbose_name='Banque')
    banque_iban = models.CharField(max_length=50, blank=True, verbose_name='IBAN')
    banque_rib = models.CharField(max_length=50, blank=True, verbose_name='RIB')

    # Paramètres
    taux_commission = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        verbose_name='Taux de commission (%)'
    )
    delai_reversement = models.IntegerField(
        default=15, verbose_name='Délai de reversement (jours)'
    )

    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Créancier'
        verbose_name_plural = 'Créanciers'
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @classmethod
    def generer_code(cls):
        """Génère un code créancier unique"""
        count = cls.objects.count() + 1
        return f"CR-{str(count).zfill(4)}"

    def get_total_creances(self):
        """Retourne le total des créances confiées"""
        from django.db.models import Sum
        return self.dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

    def get_total_encaisse(self):
        """Retourne le total encaissé"""
        from django.db.models import Sum
        return Encaissement.objects.filter(
            dossier__creancier=self,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0

    def get_total_reverse(self):
        """Retourne le total reversé"""
        from django.db.models import Sum
        return Reversement.objects.filter(
            creancier=self,
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or 0


class PortefeuilleCreancier(models.Model):
    """Gestion du portefeuille de dossiers d'un créancier"""
    creancier = models.OneToOneField(
        Creancier, on_delete=models.CASCADE, related_name='portefeuille'
    )
    date_debut_relation = models.DateField(verbose_name='Date début de relation')

    # Contact référent au sein de l'étude
    gestionnaire = models.ForeignKey(
        Collaborateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='portefeuilles_geres', verbose_name='Gestionnaire référent'
    )

    # Paramètres spécifiques
    parametres = models.JSONField(default=dict, blank=True, verbose_name='Paramètres personnalisés')

    # Statistiques (mises à jour périodiquement)
    nb_dossiers_actifs = models.IntegerField(default=0)
    montant_total_creances = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_encaisse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_reverse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    taux_recouvrement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    derniere_maj_stats = models.DateTimeField(null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Portefeuille créancier'
        verbose_name_plural = 'Portefeuilles créanciers'

    def __str__(self):
        return f"Portefeuille {self.creancier.nom}"

    def actualiser_statistiques(self):
        """Met à jour les statistiques du portefeuille"""
        from django.db.models import Sum, Count

        # Dossiers actifs
        dossiers_actifs = self.creancier.dossiers.exclude(statut='cloture')
        self.nb_dossiers_actifs = dossiers_actifs.count()

        # Montants
        self.montant_total_creances = self.creancier.dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

        self.montant_total_encaisse = Encaissement.objects.filter(
            dossier__creancier=self.creancier,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0

        self.montant_total_reverse = Reversement.objects.filter(
            creancier=self.creancier,
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or 0

        # Taux de recouvrement
        if self.montant_total_creances > 0:
            self.taux_recouvrement = (self.montant_total_encaisse / self.montant_total_creances) * 100

        self.derniere_maj_stats = timezone.now()
        self.save()


# =============================================================================
# MODELES POUR L'HISTORIQUE DES ENCAISSEMENTS
# =============================================================================

class Encaissement(models.Model):
    """Encaissements reçus sur les dossiers"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('rembourse', 'Remboursé'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
        ('compensation', 'Compensation'),
        ('autre', 'Autre'),
    ]

    # Référence unique
    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')

    # Lien avec le dossier
    dossier = models.ForeignKey(
        'Dossier', on_delete=models.PROTECT, related_name='encaissements'
    )

    # Informations de l'encaissement
    montant = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='Montant')
    date_encaissement = models.DateField(default=timezone.now, verbose_name='Date d\'encaissement')
    date_valeur = models.DateField(null=True, blank=True, verbose_name='Date de valeur')

    mode_paiement = models.CharField(
        max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes'
    )

    # Informations sur le payeur
    payeur_nom = models.CharField(max_length=200, verbose_name='Nom du payeur')
    payeur_telephone = models.CharField(max_length=50, blank=True)
    payeur_qualite = models.CharField(
        max_length=100, blank=True,
        verbose_name='Qualité du payeur',
        help_text='Ex: Débiteur, Mandataire, Caution, etc.'
    )

    # Informations complémentaires selon le mode de paiement
    reference_paiement = models.CharField(
        max_length=100, blank=True,
        verbose_name='Référence du paiement',
        help_text='N° de chèque, référence virement, etc.'
    )
    banque_emettrice = models.CharField(max_length=100, blank=True)

    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='encaissements_valides'
    )

    # Cumuls (calculés automatiquement)
    cumul_encaisse_avant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Cumul encaissé avant cet encaissement'
    )
    cumul_encaisse_apres = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Cumul encaissé après cet encaissement'
    )
    solde_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Solde restant dû'
    )

    # Reversement
    montant_a_reverser = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Montant à reverser au créancier'
    )
    reversement_statut = models.CharField(
        max_length=20, default='en_attente',
        choices=[('en_attente', 'En attente'), ('reverse', 'Reversé')],
        verbose_name='Statut reversement'
    )

    # Traçabilité
    observations = models.TextField(blank=True)
    piece_justificative = models.FileField(
        upload_to='encaissements/', blank=True, null=True,
        verbose_name='Pièce justificative'
    )

    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='encaissements_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # TRAÇABILITÉ COMPTABLE
    compte_tresorerie = models.ForeignKey(
        'tresorerie.CompteBancaire',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='encaissements',
        verbose_name="Compte de trésorerie"
    )

    mouvement_tresorerie = models.OneToOneField(
        'tresorerie.MouvementTresorerie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encaissement_source',
        verbose_name="Mouvement de trésorerie"
    )

    class Meta:
        verbose_name = 'Encaissement'
        verbose_name_plural = 'Encaissements'
        ordering = ['-date_encaissement', '-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.montant:,.0f} FCFA"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour l'encaissement"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"ENC-{now.year}-{str(count).zfill(5)}"

    def save(self, *args, **kwargs):
        # Générer la référence si nouvelle
        if not self.reference:
            self.reference = self.generer_reference()

        # Calculer les cumuls si validé
        if self.statut == 'valide':
            self.calculer_cumuls()
            self.calculer_montant_a_reverser()

        super().save(*args, **kwargs)

    def calculer_cumuls(self):
        """Calcule les cumuls progressifs"""
        from django.db.models import Sum

        # Cumul avant cet encaissement
        encaissements_anterieurs = Encaissement.objects.filter(
            dossier=self.dossier,
            statut='valide',
            date_encaissement__lt=self.date_encaissement
        ).exclude(pk=self.pk)

        self.cumul_encaisse_avant = encaissements_anterieurs.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Cumul après
        self.cumul_encaisse_apres = self.cumul_encaisse_avant + self.montant

        # Solde restant (basé sur le montant total dû du dossier)
        montant_total_du = self.dossier.get_montant_total_du()
        self.solde_restant = montant_total_du - self.cumul_encaisse_apres

    def calculer_montant_a_reverser(self):
        """Calcule le montant à reverser au créancier"""
        if hasattr(self.dossier, 'creancier') and self.dossier.creancier:
            # Appliquer le taux de commission du créancier
            taux_commission = self.dossier.creancier.taux_commission / 100
            commission = self.montant * taux_commission
            self.montant_a_reverser = self.montant - commission
        else:
            self.montant_a_reverser = self.montant

    def valider(self, utilisateur):
        """Valide l'encaissement"""
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.valide_par = utilisateur
        self.save()

    def annuler(self, motif=''):
        """Annule l'encaissement"""
        self.statut = 'annule'
        if motif:
            self.observations = f"{self.observations}\nAnnulation: {motif}"
        self.save()


class ImputationEncaissement(models.Model):
    """Détail de l'imputation d'un encaissement sur les différentes composantes de la créance"""
    TYPE_IMPUTATION_CHOICES = [
        ('principal', 'Principal'),
        ('interets', 'Intérêts'),
        ('interets_retard', 'Intérêts de retard'),
        ('frais', 'Frais de procédure'),
        ('emoluments', 'Émoluments'),
        ('debours', 'Débours'),
        ('depens', 'Dépens'),
        ('accessoires', 'Accessoires'),
        ('autres', 'Autres'),
    ]

    encaissement = models.ForeignKey(
        Encaissement, on_delete=models.CASCADE, related_name='imputations'
    )

    type_imputation = models.CharField(
        max_length=20, choices=TYPE_IMPUTATION_CHOICES
    )
    montant = models.DecimalField(max_digits=15, decimal_places=0)

    # Soldes avant/après pour ce type
    solde_avant = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    solde_apres = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    observations = models.CharField(max_length=500, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imputation d\'encaissement'
        verbose_name_plural = 'Imputations d\'encaissements'
        ordering = ['encaissement', 'type_imputation']

    def __str__(self):
        return f"{self.encaissement.reference} - {self.get_type_imputation_display()}: {self.montant:,.0f} FCFA"


# =============================================================================
# MODELES POUR LE SUIVI DES REVERSEMENTS
# =============================================================================

class Reversement(models.Model):
    """Reversements effectués aux créanciers"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente de reversement'),
        ('en_cours', 'En cours'),
        ('effectue', 'Effectué'),
        ('annule', 'Annulé'),
    ]
    MODE_REVERSEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('autre', 'Autre'),
    ]

    # Référence unique
    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')

    # Créancier bénéficiaire
    creancier = models.ForeignKey(
        Creancier, on_delete=models.PROTECT, related_name='reversements'
    )

    # Montant et dates
    montant = models.DecimalField(max_digits=15, decimal_places=0)
    date_reversement = models.DateField(null=True, blank=True, verbose_name='Date de reversement')

    # Mode de reversement
    mode_reversement = models.CharField(
        max_length=20, choices=MODE_REVERSEMENT_CHOICES, default='virement'
    )

    # Références du paiement
    reference_virement = models.CharField(max_length=100, blank=True, verbose_name='Référence virement')
    numero_cheque = models.CharField(max_length=50, blank=True, verbose_name='Numéro de chèque')
    banque = models.CharField(max_length=100, blank=True, verbose_name='Banque émettrice')

    # Encaissements concernés
    encaissements = models.ManyToManyField(
        Encaissement, related_name='reversements', blank=True
    )

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Preuve de reversement
    preuve_reversement = models.FileField(
        upload_to='reversements/', blank=True, null=True,
        verbose_name='Preuve de reversement'
    )

    # Détails
    observations = models.TextField(blank=True)

    # Traçabilité
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='reversements_crees'
    )
    effectue_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reversements_effectues'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # TRAÇABILITÉ COMPTABLE
    compte_tresorerie = models.ForeignKey(
        'tresorerie.CompteBancaire',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reversements',
        verbose_name="Compte de trésorerie"
    )

    mouvement_tresorerie = models.OneToOneField(
        'tresorerie.MouvementTresorerie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversement_source',
        verbose_name="Mouvement de trésorerie"
    )

    class Meta:
        verbose_name = 'Reversement'
        verbose_name_plural = 'Reversements'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.montant:,.0f} FCFA → {self.creancier.nom}"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour le reversement"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"REV-{now.year}-{str(count).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def effectuer(self, utilisateur):
        """Marque le reversement comme effectué"""
        self.statut = 'effectue'
        self.date_reversement = timezone.now().date()
        self.effectue_par = utilisateur
        self.save()

        # Mettre à jour le statut des encaissements liés
        for encaissement in self.encaissements.all():
            encaissement.reversement_statut = 'reverse'
            encaissement.save()

    def annuler(self, motif=''):
        """Annule le reversement"""
        self.statut = 'annule'
        if motif:
            self.observations = f"{self.observations}\nAnnulation: {motif}"
        self.save()

        # Remettre les encaissements en attente
        for encaissement in self.encaissements.all():
            encaissement.reversement_statut = 'en_attente'
            encaissement.save()


# =============================================================================
# MODELES POUR LE PASSAGE AMIABLE → FORCÉ
# =============================================================================

class BasculementAmiableForce(models.Model):
    """Historique des basculements de la phase amiable vers la phase forcée"""
    MOTIF_CHOICES = [
        ('titre_executoire', 'Obtention d\'un titre exécutoire'),
        ('echec_amiable', 'Échec de la phase amiable'),
        ('decision_creancier', 'Décision du créancier'),
        ('autre', 'Autre'),
    ]

    dossier = models.ForeignKey(
        'Dossier', on_delete=models.CASCADE, related_name='basculements'
    )

    # Date et motif du basculement
    date_basculement = models.DateTimeField(default=timezone.now)
    motif = models.CharField(max_length=30, choices=MOTIF_CHOICES)
    motif_detail = models.TextField(blank=True, verbose_name='Détail du motif')

    # Titre exécutoire (si applicable)
    type_titre = models.CharField(max_length=100, blank=True, verbose_name='Type de titre')
    reference_titre = models.CharField(max_length=100, blank=True, verbose_name='Référence du titre')
    juridiction = models.CharField(max_length=200, blank=True, verbose_name='Juridiction')
    date_titre = models.DateField(null=True, blank=True, verbose_name='Date du titre')

    # État de la créance au moment du basculement
    montant_principal_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Principal restant'
    )
    montant_interets_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Intérêts restants'
    )
    montant_frais_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais restants'
    )
    total_reste_du = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total restant dû'
    )

    # Nouveaux frais ajoutés lors du basculement
    depens = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Dépens'
    )
    frais_justice = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de justice'
    )
    emoluments_ohada = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Émoluments OHADA'
    )
    nouveau_total = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Nouveau total après basculement'
    )

    # Données complètes sauvegardées (JSON)
    donnees_phase_amiable = models.JSONField(
        default=dict, blank=True,
        verbose_name='Données de la phase amiable'
    )

    # Traçabilité
    effectue_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='basculements_effectues'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Basculement amiable → forcé'
        verbose_name_plural = 'Basculements amiable → forcé'
        ordering = ['-date_basculement']

    def __str__(self):
        return f"Basculement {self.dossier.reference} - {self.date_basculement.strftime('%d/%m/%Y')}"

    def calculer_emoluments_ohada(self, montant):
        """Calcule les émoluments selon le barème OHADA"""
        # Barème des émoluments OHADA (simplifié)
        if montant <= 500000:
            return montant * 0.10
        elif montant <= 1000000:
            return 50000 + (montant - 500000) * 0.08
        elif montant <= 5000000:
            return 90000 + (montant - 1000000) * 0.05
        elif montant <= 10000000:
            return 290000 + (montant - 5000000) * 0.03
        else:
            return 440000 + (montant - 10000000) * 0.01


# =============================================================================
# MODELES POUR LE POINT CLIENT
# =============================================================================

class PointGlobalCreancier(models.Model):
    """Points globaux générés pour les créanciers"""

    creancier = models.ForeignKey(
        Creancier, on_delete=models.CASCADE, related_name='points_globaux'
    )

    # Période couverte
    date_generation = models.DateTimeField(default=timezone.now)
    periode_debut = models.DateField(verbose_name='Début de période')
    periode_fin = models.DateField(verbose_name='Fin de période')

    # Filtres appliqués
    filtres = models.JSONField(default=dict, blank=True, verbose_name='Filtres appliqués')

    # Statistiques du point
    nb_dossiers_total = models.IntegerField(default=0)
    nb_dossiers_actifs = models.IntegerField(default=0)
    nb_dossiers_clotures = models.IntegerField(default=0)

    montant_total_creances = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_encaisse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_reverse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_reste_a_encaisser = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_reste_a_reverser = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    taux_recouvrement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Données détaillées (JSON)
    donnees_detaillees = models.JSONField(
        default=dict, blank=True,
        verbose_name='Données détaillées du point'
    )

    # Document PDF généré
    document_pdf = models.FileField(
        upload_to='points_creanciers/', blank=True, null=True,
        verbose_name='Document PDF'
    )

    # Traçabilité
    genere_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='points_generes'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Point global créancier'
        verbose_name_plural = 'Points globaux créanciers'
        ordering = ['-date_generation']

    def __str__(self):
        return f"Point {self.creancier.nom} - {self.date_generation.strftime('%d/%m/%Y')}"

    def generer_donnees(self):
        """Génère les données détaillées du point"""
        from django.db.models import Sum, Count, Q

        # Filtrer les dossiers du créancier
        dossiers = self.creancier.dossiers.all()

        # Appliquer les filtres si présents
        if self.filtres:
            if 'statut' in self.filtres:
                dossiers = dossiers.filter(statut=self.filtres['statut'])
            if 'montant_min' in self.filtres:
                dossiers = dossiers.filter(montant_creance__gte=self.filtres['montant_min'])
            if 'montant_max' in self.filtres:
                dossiers = dossiers.filter(montant_creance__lte=self.filtres['montant_max'])
            if 'gestionnaire' in self.filtres:
                dossiers = dossiers.filter(affecte_a_id=self.filtres['gestionnaire'])

        # Statistiques
        self.nb_dossiers_total = dossiers.count()
        self.nb_dossiers_actifs = dossiers.filter(statut__in=['actif', 'urgent']).count()
        self.nb_dossiers_clotures = dossiers.filter(statut='cloture').count()

        self.montant_total_creances = dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

        # Encaissements
        encaissements = Encaissement.objects.filter(
            dossier__in=dossiers,
            statut='valide',
            date_encaissement__gte=self.periode_debut,
            date_encaissement__lte=self.periode_fin
        )

        self.montant_total_encaisse = encaissements.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Reversements
        reversements = Reversement.objects.filter(
            creancier=self.creancier,
            statut='effectue',
            date_reversement__gte=self.periode_debut,
            date_reversement__lte=self.periode_fin
        )

        self.montant_total_reverse = reversements.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Calculs
        self.montant_reste_a_encaisser = self.montant_total_creances - self.montant_total_encaisse

        encaisse_non_reverse = Encaissement.objects.filter(
            dossier__in=dossiers,
            statut='valide',
            reversement_statut='en_attente'
        ).aggregate(total=Sum('montant_a_reverser'))['total'] or 0
        self.montant_reste_a_reverser = encaisse_non_reverse

        # Taux de recouvrement
        if self.montant_total_creances > 0:
            self.taux_recouvrement = (self.montant_total_encaisse / self.montant_total_creances) * 100

        # Données détaillées par dossier
        details = []
        for dossier in dossiers:
            enc = dossier.encaissements.filter(statut='valide')
            total_enc = enc.aggregate(total=Sum('montant'))['total'] or 0

            details.append({
                'reference': dossier.reference,
                'intitule': dossier.get_intitule(),
                'statut': dossier.statut,
                'montant_creance': float(dossier.montant_creance or 0),
                'total_encaisse': float(total_enc),
                'solde_restant': float((dossier.montant_creance or 0) - total_enc),
                'nb_encaissements': enc.count(),
                'dernier_encaissement': enc.order_by('-date_encaissement').first().date_encaissement.isoformat() if enc.exists() else None
            })

        self.donnees_detaillees = {
            'dossiers': details,
            'periode': {
                'debut': self.periode_debut.isoformat(),
                'fin': self.periode_fin.isoformat()
            },
            'resume': {
                'nb_dossiers_total': self.nb_dossiers_total,
                'nb_dossiers_actifs': self.nb_dossiers_actifs,
                'montant_creances': float(self.montant_total_creances),
                'montant_encaisse': float(self.montant_total_encaisse),
                'montant_reverse': float(self.montant_total_reverse),
                'taux_recouvrement': float(self.taux_recouvrement)
            }
        }

        self.save()


class EnvoiAutomatiquePoint(models.Model):
    """Configuration d'envoi automatique des points aux créanciers"""
    FREQUENCE_CHOICES = [
        ('quotidien', 'Quotidien'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('bimensuel', 'Bimensuel'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
    ]

    creancier = models.ForeignKey(
        Creancier, on_delete=models.CASCADE, related_name='envois_automatiques'
    )

    # Configuration
    frequence = models.CharField(max_length=20, choices=FREQUENCE_CHOICES, default='mensuel')
    jour_envoi = models.IntegerField(
        default=1, verbose_name='Jour d\'envoi',
        help_text='Jour du mois (1-28) ou jour de la semaine (1-7 pour hebdomadaire)'
    )
    heure_envoi = models.TimeField(default='08:00', verbose_name='Heure d\'envoi')

    # Destinataires
    destinataires = models.JSONField(
        default=list, verbose_name='Adresses email destinataires'
    )
    copie_gestionnaire = models.BooleanField(
        default=True, verbose_name='Envoyer copie au gestionnaire'
    )

    # Filtres à appliquer
    filtres_point = models.JSONField(default=dict, blank=True, verbose_name='Filtres')

    # Suivi
    actif = models.BooleanField(default=True)
    dernier_envoi = models.DateTimeField(null=True, blank=True)
    prochain_envoi = models.DateTimeField(null=True, blank=True)
    nb_envois_total = models.IntegerField(default=0)

    # Traçabilité
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='envois_auto_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Envoi automatique de point'
        verbose_name_plural = 'Envois automatiques de points'
        ordering = ['creancier', 'frequence']

    def __str__(self):
        return f"Envoi {self.get_frequence_display()} - {self.creancier.nom}"

    def calculer_prochain_envoi(self):
        """Calcule la date du prochain envoi"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta

        now = timezone.now()

        if self.frequence == 'quotidien':
            prochain = now + timedelta(days=1)
        elif self.frequence == 'hebdomadaire':
            jours_jusqu_au = (self.jour_envoi - now.weekday()) % 7
            if jours_jusqu_au == 0:
                jours_jusqu_au = 7
            prochain = now + timedelta(days=jours_jusqu_au)
        elif self.frequence == 'bimensuel':
            if now.day < 15:
                prochain = now.replace(day=15)
            else:
                prochain = (now + relativedelta(months=1)).replace(day=1)
        elif self.frequence == 'mensuel':
            jour = min(self.jour_envoi, 28)
            if now.day < jour:
                prochain = now.replace(day=jour)
            else:
                prochain = (now + relativedelta(months=1)).replace(day=jour)
        elif self.frequence == 'trimestriel':
            mois_prochain = ((now.month - 1) // 3 + 1) * 3 + 1
            if mois_prochain > 12:
                prochain = now.replace(year=now.year + 1, month=mois_prochain - 12, day=min(self.jour_envoi, 28))
            else:
                prochain = now.replace(month=mois_prochain, day=min(self.jour_envoi, 28))
        else:
            prochain = now + timedelta(days=30)

        self.prochain_envoi = prochain.replace(
            hour=self.heure_envoi.hour,
            minute=self.heure_envoi.minute,
            second=0,
            microsecond=0
        )
        self.save()


class HistoriqueEnvoiPoint(models.Model):
    """Historique des envois de points automatiques"""
    STATUT_CHOICES = [
        ('succes', 'Succès'),
        ('echec', 'Échec'),
        ('partiel', 'Partiel'),
    ]

    envoi_config = models.ForeignKey(
        EnvoiAutomatiquePoint, on_delete=models.CASCADE, related_name='historique'
    )
    point_global = models.ForeignKey(
        PointGlobalCreancier, on_delete=models.SET_NULL, null=True,
        related_name='envois'
    )

    date_envoi = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)

    destinataires_envoyes = models.JSONField(default=list)
    destinataires_echec = models.JSONField(default=list)

    message_erreur = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Historique d\'envoi de point'
        verbose_name_plural = 'Historiques d\'envois de points'
        ordering = ['-date_envoi']

    def __str__(self):
        return f"Envoi {self.date_envoi.strftime('%d/%m/%Y %H:%M')} - {self.statut}"


# =============================================================================
# MODELES POUR LES MÉMOIRES DE CÉDULES - STRUCTURE HIÉRARCHIQUE À 4 NIVEAUX
# =============================================================================

class AutoriteRequerante(models.Model):
    """Autorités requérantes (juridictions) pour les mémoires de cédules"""
    code = models.CharField(max_length=50, unique=True, verbose_name='Code')
    nom = models.CharField(max_length=300, verbose_name='Nom de l\'autorité')
    type_juridiction = models.CharField(
        max_length=100, blank=True,
        verbose_name='Type de juridiction',
        help_text='Ex: CRIET, TPI, Cour d\'Appel, Cour Suprême, etc.'
    )
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    ville = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Autorité requérante'
        verbose_name_plural = 'Autorités requérantes'
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"


class Memoire(models.Model):
    """
    NIVEAU 1 - MÉMOIRE DE CÉDULES

    Document regroupant les frais de signification d'actes judiciaires
    pour une période donnée et une autorité requérante.
    """
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_cours', 'En cours de rédaction'),
        ('a_verifier', 'À vérifier'),
        ('certifie', 'Certifié par l\'huissier'),
        ('soumis', 'Soumis au Parquet'),
        ('vise', 'Visé par le Procureur'),
        ('taxe', 'Taxé par le Président'),
        ('en_paiement', 'Transmis au Trésor'),
        ('paye', 'Payé'),
        ('rejete', 'Rejeté'),
    ]

    # Identification
    numero = models.CharField(
        max_length=50, unique=True, verbose_name='Numéro du mémoire'
    )

    # Période
    mois = models.PositiveSmallIntegerField(
        verbose_name='Mois',
        help_text='Mois de la période (1-12)'
    )
    annee = models.PositiveIntegerField(verbose_name='Année')

    # Relations
    huissier = models.ForeignKey(
        Collaborateur, on_delete=models.PROTECT,
        related_name='memoires_cedules',
        verbose_name='Huissier',
        limit_choices_to={'role': 'huissier'}
    )
    autorite_requerante = models.ForeignKey(
        AutoriteRequerante, on_delete=models.PROTECT,
        related_name='memoires',
        verbose_name='Autorité requérante'
    )

    # Juridiction requérante (nouveau modèle avec hiérarchie)
    juridiction = models.ForeignKey(
        'parametres.Juridiction',
        on_delete=models.PROTECT,
        related_name='memoires',
        verbose_name='Juridiction requérante',
        null=True, blank=True,
        help_text="Juridiction pour génération des signatures Réquisition/Exécutoire"
    )

    # Résidence de l'huissier (pour calcul des distances)
    residence_huissier = models.CharField(
        max_length=200, verbose_name='Résidence de l\'huissier',
        help_text='Ville de résidence pour le calcul des distances'
    )

    # Totaux (calculés automatiquement)
    montant_total_actes = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total des actes'
    )
    montant_total_transport = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total transport'
    )
    montant_total_mission = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total mission'
    )
    montant_total = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total général'
    )
    montant_total_lettres = models.CharField(
        max_length=500, blank=True,
        verbose_name='Montant en lettres'
    )

    # Statut et certification
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='brouillon'
    )
    date_certification = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de certification'
    )
    certifie_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='memoires_certifies',
        verbose_name='Certifié par'
    )
    lieu_certification = models.CharField(
        max_length=100, blank=True, default='Parakou',
        verbose_name='Lieu de certification'
    )

    # Dates du workflow de validation
    date_visa = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date visa Procureur'
    )
    date_taxation = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date taxation Président'
    )
    date_transmission_tresor = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date transmission Trésor'
    )
    date_paiement = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de paiement'
    )

    # Observations
    observations = models.TextField(blank=True)

    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW DE VALIDATION PAR L'AUTORITÉ
    # ═══════════════════════════════════════════════════════════════

    STATUT_VALIDATION_CHOICES = [
        ('soumis', 'Soumis'),
        ('en_attente', 'En attente de contrôle'),
        ('valide', 'Validé'),
        ('rejete_correction', 'Rejeté - Correction demandée'),
        ('rejete_definitif', 'Rejeté définitivement'),
        ('paye', 'Payé'),
    ]

    statut_validation = models.CharField(
        max_length=30,
        choices=STATUT_VALIDATION_CHOICES,
        default='soumis',
        verbose_name="Statut de validation"
    )

    # Contrôle par l'autorité
    date_soumission = models.DateField(null=True, blank=True, verbose_name="Date de soumission")
    autorite_controle = models.CharField(max_length=200, blank=True, verbose_name="Autorité de contrôle")
    date_controle = models.DateField(null=True, blank=True, verbose_name="Date du contrôle")

    # Rejet
    motif_rejet = models.TextField(blank=True, verbose_name="Motif du rejet")
    montant_corrige = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Montant corrigé demandé",
        help_text="Montant demandé par l'autorité si correction requise"
    )
    date_rejet = models.DateField(null=True, blank=True, verbose_name="Date du rejet")

    # Mémoire correctif (si ce mémoire est une correction d'un autre)
    memoire_original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memoires_correctifs',
        verbose_name="Mémoire original (si correctif)"
    )
    est_correctif = models.BooleanField(default=False, verbose_name="Est un mémoire correctif")

    # Traçabilité
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name='memoires_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mémoire de cédules'
        verbose_name_plural = 'Mémoires de cédules'
        ordering = ['-annee', '-mois', '-numero']
        unique_together = ['mois', 'annee', 'autorite_requerante', 'huissier']

    def __str__(self):
        mois_noms = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"Mémoire N° {self.numero} - {mois_noms[self.mois]} {self.annee}"

    @classmethod
    def generer_numero(cls):
        """Génère un numéro de mémoire unique"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"{count}"

    def calculer_totaux(self):
        """Recalcule tous les totaux du mémoire"""
        from django.db.models import Sum

        totaux = self.affaires.aggregate(
            actes=Sum('montant_total_actes'),
            transport=Sum('montant_total_transport'),
            mission=Sum('montant_total_mission'),
            total=Sum('montant_total_affaire')
        )

        self.montant_total_actes = totaux['actes'] or 0
        self.montant_total_transport = totaux['transport'] or 0
        self.montant_total_mission = totaux['mission'] or 0
        self.montant_total = totaux['total'] or 0
        self.montant_total_lettres = self.nombre_en_lettres(self.montant_total)
        self.save()

    @staticmethod
    def nombre_en_lettres(nombre):
        """Convertit un nombre en lettres (FCFA)"""
        unites = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf']
        dizaines = ['', 'dix', 'vingt', 'trente', 'quarante', 'cinquante',
                    'soixante', 'soixante', 'quatre-vingt', 'quatre-vingt']

        def convertir_moins_de_100(n):
            if n == 0:
                return ''
            if n < 10:
                return unites[n]
            if n == 10:
                return 'dix'
            if n == 11:
                return 'onze'
            if n == 12:
                return 'douze'
            if n == 13:
                return 'treize'
            if n == 14:
                return 'quatorze'
            if n == 15:
                return 'quinze'
            if n == 16:
                return 'seize'
            if n < 20:
                return 'dix-' + unites[n - 10]
            if n < 70:
                d, u = divmod(n, 10)
                if u == 0:
                    return dizaines[d]
                if u == 1 and d in [2, 3, 4, 5, 6]:
                    return dizaines[d] + '-et-un'
                return dizaines[d] + '-' + unites[u]
            if n < 80:
                return 'soixante-' + convertir_moins_de_100(n - 60)
            if n == 80:
                return 'quatre-vingts'
            if n < 100:
                return 'quatre-vingt-' + convertir_moins_de_100(n - 80)
            return ''

        def convertir_moins_de_1000(n):
            if n < 100:
                return convertir_moins_de_100(n)
            c, r = divmod(n, 100)
            if c == 1:
                if r == 0:
                    return 'cent'
                return 'cent ' + convertir_moins_de_100(r)
            else:
                if r == 0:
                    return unites[c] + ' cents'
                return unites[c] + ' cent ' + convertir_moins_de_100(r)

        def convertir(n):
            if n == 0:
                return 'zéro'

            milliards, reste = divmod(n, 1000000000)
            millions, reste = divmod(reste, 1000000)
            milliers, reste = divmod(reste, 1000)

            resultat = ''

            if milliards > 0:
                if milliards == 1:
                    resultat += 'un milliard '
                else:
                    resultat += convertir_moins_de_1000(milliards) + ' milliards '

            if millions > 0:
                if millions == 1:
                    resultat += 'un million '
                else:
                    resultat += convertir_moins_de_1000(millions) + ' millions '

            if milliers > 0:
                if milliers == 1:
                    resultat += 'mille '
                else:
                    resultat += convertir_moins_de_1000(milliers) + ' mille '

            if reste > 0:
                resultat += convertir_moins_de_1000(reste)

            return resultat.strip().upper() + ' FRANCS CFA'

        return convertir(int(nombre))

    def get_nb_affaires(self):
        """Retourne le nombre d'affaires"""
        return self.affaires.count()

    def get_nb_destinataires(self):
        """Retourne le nombre total de destinataires"""
        return sum(a.destinataires.count() for a in self.affaires.all())

    def get_nb_actes(self):
        """Retourne le nombre total d'actes"""
        count = 0
        for affaire in self.affaires.all():
            for dest in affaire.destinataires.all():
                count += dest.actes.count()
        return count

    def verifier_coherence(self):
        """
        Vérifie la cohérence des données du mémoire
        Retourne une liste d'alertes
        """
        alertes = []

        for affaire in self.affaires.all():
            # Vérifier les doublons de numéro de parquet
            autres_affaires = self.affaires.exclude(pk=affaire.pk).filter(
                numero_parquet=affaire.numero_parquet
            )
            if autres_affaires.exists():
                alertes.append({
                    'type': 'doublon_affaire',
                    'message': f"L'affaire {affaire.numero_parquet} existe en double dans ce mémoire",
                    'affaire': affaire.numero_parquet
                })

            for dest in affaire.destinataires.all():
                # Vérifier les distances non renseignées
                if dest.distance_km is None or dest.distance_km == 0:
                    if dest.localite and dest.localite.lower() != self.residence_huissier.lower():
                        alertes.append({
                            'type': 'distance_manquante',
                            'message': f"Distance non renseignée pour {dest.get_nom_complet()} à {dest.localite}",
                            'destinataire': dest.get_nom_complet(),
                            'affaire': affaire.numero_parquet
                        })

                for acte in dest.actes.all():
                    # Vérifier les dates
                    if acte.date_acte:
                        if acte.date_acte.month != self.mois or acte.date_acte.year != self.annee:
                            alertes.append({
                                'type': 'date_hors_periode',
                                'message': f"L'acte du {acte.date_acte.strftime('%d/%m/%Y')} est hors de la période du mémoire",
                                'acte': str(acte),
                                'affaire': affaire.numero_parquet
                            })

        return alertes

    def certifier(self, utilisateur):
        """Certifie le mémoire"""
        self.statut = 'certifie'
        self.date_certification = timezone.now()
        self.certifie_par = utilisateur
        self.calculer_totaux()
        self.save()


class AffaireMemoire(models.Model):
    """
    NIVEAU 2 - AFFAIRE

    Regroupement par numéro de parquet au sein d'un mémoire.
    Une affaire peut concerner plusieurs destinataires.
    """

    memoire = models.ForeignKey(
        Memoire, on_delete=models.CASCADE,
        related_name='affaires',
        verbose_name='Mémoire'
    )

    # Identification de l'affaire
    numero_parquet = models.CharField(
        max_length=100, verbose_name='Numéro de parquet',
        help_text='Ex: CRIET/2021/RP/0928'
    )
    intitule_affaire = models.CharField(
        max_length=300, verbose_name='Intitulé de l\'affaire',
        help_text='Ex: MP c/ DUPONT Jean et autres'
    )
    nature_infraction = models.CharField(
        max_length=300, blank=True,
        verbose_name='Nature de l\'infraction'
    )
    date_audience = models.DateField(
        null=True, blank=True,
        verbose_name='Date d\'audience'
    )

    # Totaux (calculés automatiquement)
    montant_total_actes = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total des actes'
    )
    montant_total_transport = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total transport'
    )
    montant_total_mission = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total mission'
    )
    montant_total_affaire = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total affaire'
    )

    # Ordre d'affichage
    ordre_affichage = models.PositiveIntegerField(default=0)

    # Traçabilité
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Affaire du mémoire'
        verbose_name_plural = 'Affaires du mémoire'
        ordering = ['ordre_affichage', 'numero_parquet']
        unique_together = ['memoire', 'numero_parquet']

    def __str__(self):
        return f"{self.numero_parquet} - {self.intitule_affaire}"

    def calculer_totaux(self):
        """Recalcule tous les totaux de l'affaire"""
        from django.db.models import Sum

        totaux = self.destinataires.aggregate(
            actes=Sum('montant_total_actes'),
            transport=Sum('frais_transport'),
            mission=Sum('frais_mission'),
            total=Sum('montant_total_destinataire')
        )

        self.montant_total_actes = totaux['actes'] or 0
        self.montant_total_transport = totaux['transport'] or 0
        self.montant_total_mission = totaux['mission'] or 0
        self.montant_total_affaire = totaux['total'] or 0
        self.save()

        # Mettre à jour le mémoire parent
        self.memoire.calculer_totaux()

    def get_nb_destinataires(self):
        return self.destinataires.count()

    def get_nb_actes(self):
        return sum(d.actes.count() for d in self.destinataires.all())


class DestinataireAffaire(models.Model):
    """
    NIVEAU 3 - DESTINATAIRE

    Personne à qui les actes sont signifiés.
    Les frais de transport et mission sont calculés UNE SEULE FOIS par destinataire,
    même si plusieurs actes lui sont signifiés lors du même déplacement.
    """
    QUALITE_CHOICES = [
        ('prevenu', 'Prévenu'),
        ('temoin', 'Témoin'),
        ('partie_civile', 'Partie civile'),
        ('civilement_responsable', 'Civilement responsable'),
        ('avocat', 'Avocat'),
        ('autre', 'Autre'),
    ]

    TYPE_MISSION_CHOICES = [
        ('aucune', 'Aucune mission'),
        ('1_repas', '1 repas (distance 100-149 km)'),
        ('2_repas', '2 repas (distance 150-199 km)'),
        ('journee_complete', 'Journée entière (distance ≥ 200 km)'),
    ]

    # Constantes de tarification
    TARIF_KM = 140  # F par km
    SEUIL_TRANSPORT_KM = 20  # Transport facturé si distance > 20 km
    SEUIL_MISSION_KM = 100  # Mission applicable si distance >= 100 km

    TARIFS_MISSION = {
        'aucune': 0,
        '1_repas': 15000,         # 15 000 FCFA (100-149 km)
        '2_repas': 30000,         # 30 000 FCFA (150-199 km)
        'journee_complete': 45000, # 45 000 FCFA (≥ 200 km)
    }

    affaire = models.ForeignKey(
        AffaireMemoire, on_delete=models.CASCADE,
        related_name='destinataires',
        verbose_name='Affaire'
    )

    # Identité
    nom = models.CharField(max_length=100, verbose_name='Nom')
    prenoms = models.CharField(max_length=200, blank=True, verbose_name='Prénoms')
    raison_sociale = models.CharField(
        max_length=300, blank=True,
        verbose_name='Raison sociale',
        help_text='Pour les personnes morales'
    )
    qualite = models.CharField(
        max_length=30, choices=QUALITE_CHOICES,
        verbose_name='Qualité'
    )
    titre = models.CharField(
        max_length=50, blank=True,
        verbose_name='Titre',
        help_text='Ex: Me, Dr, etc.'
    )

    # Adresse de signification
    adresse = models.TextField(verbose_name='Adresse de signification')
    localite = models.CharField(max_length=100, verbose_name='Localité/Ville')

    # Distance et frais de déplacement
    distance_km = models.PositiveIntegerField(
        default=0,
        verbose_name='Distance (km)',
        help_text='Distance depuis la résidence de l\'huissier'
    )

    # Type de mission (déterminé automatiquement ou manuellement)
    type_mission = models.CharField(
        max_length=30, choices=TYPE_MISSION_CHOICES,
        default='aucune', verbose_name='Type de mission'
    )

    # Frais calculés automatiquement
    frais_transport = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de transport',
        help_text='Distance × 140 F × 2 (aller-retour) - UNE SEULE FOIS'
    )
    frais_mission = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de mission',
        help_text='15 000 (1 repas) / 30 000 (2 repas) / 45 000 F (journée) - UNE SEULE FOIS'
    )

    # Totaux
    montant_total_actes = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total des actes'
    )
    montant_total_destinataire = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total destinataire'
    )

    # Ordre d'affichage
    ordre_affichage = models.PositiveIntegerField(default=0)

    # Observations
    observations = models.TextField(blank=True)

    # Traçabilité
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destinataire'
        verbose_name_plural = 'Destinataires'
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.get_nom_complet()} ({self.get_qualite_display()})"

    def get_nom_complet(self):
        """Retourne le nom complet du destinataire"""
        if self.raison_sociale:
            return self.raison_sociale
        titre = f"{self.titre} " if self.titre else ""
        return f"{titre}{self.nom} {self.prenoms}".strip()

    def determiner_type_mission(self):
        """Détermine automatiquement le type de mission selon la distance"""
        if self.distance_km < self.SEUIL_MISSION_KM:
            return 'aucune'
        elif self.distance_km < 150:
            return '1_repas'
        elif self.distance_km < 200:
            return '2_repas'
        else:
            return 'journee_complete'

    def calculer_frais_transport(self):
        """
        Calcule les frais de transport.
        RÈGLE CRITIQUE: Les frais sont comptés UNE SEULE FOIS par destinataire,
        peu importe le nombre d'actes signifiés.
        """
        if self.distance_km > self.SEUIL_TRANSPORT_KM:
            # Distance × 140 F × 2 (aller-retour)
            return self.distance_km * self.TARIF_KM * 2
        return 0

    def calculer_frais_mission(self):
        """
        Calcule les frais de mission.
        RÈGLE CRITIQUE: Les frais sont comptés UNE SEULE FOIS par destinataire,
        peu importe le nombre d'actes signifiés.
        """
        return self.TARIFS_MISSION.get(self.type_mission, 0)

    def calculer_totaux(self):
        """Recalcule tous les totaux du destinataire"""
        from django.db.models import Sum

        # Déterminer le type de mission si non défini
        if not self.type_mission or self.type_mission == 'aucune':
            self.type_mission = self.determiner_type_mission()

        # Calculer les frais de déplacement (UNE SEULE FOIS)
        self.frais_transport = self.calculer_frais_transport()
        self.frais_mission = self.calculer_frais_mission()

        # Calculer le total des actes
        total_actes = self.actes.aggregate(
            total=Sum('montant_total_acte')
        )['total'] or 0

        self.montant_total_actes = total_actes

        # Total destinataire = actes + transport + mission
        self.montant_total_destinataire = (
            self.montant_total_actes +
            self.frais_transport +
            self.frais_mission
        )

        self.save()

        # Mettre à jour l'affaire parente
        self.affaire.calculer_totaux()

    def save(self, *args, **kwargs):
        # Auto-calcul si la distance change
        if self.pk:
            old = DestinataireAffaire.objects.filter(pk=self.pk).first()
            if old and old.distance_km != self.distance_km:
                self.type_mission = self.determiner_type_mission()
                self.frais_transport = self.calculer_frais_transport()
                self.frais_mission = self.calculer_frais_mission()
        super().save(*args, **kwargs)


class ActeDestinataire(models.Model):
    """
    NIVEAU 4 - ACTE

    Acte de signification individuel.
    Chaque acte a un montant fixe de 4 985 F (Art. 81).
    """
    TYPE_ACTE_CHOICES = [
        ('invitation', 'Signification invitation à comparaître'),
        ('citation', 'Signification citation à comparaître'),
        ('convocation', 'Signification convocation'),
        ('ordonnance', 'Signification ordonnance'),
        ('jugement', 'Signification jugement'),
        ('arret', 'Signification arrêt'),
        ('mandat', 'Signification mandat de comparution'),
        ('notification', 'Notification'),
        ('autre', 'Autre'),
    ]

    # Tarifs fixes (Article 81)
    MONTANT_BASE = 4985  # F par acte
    TARIF_COPIE_SUPPLEMENTAIRE = 900  # F par copie
    TARIF_ROLE_PIECES = 1000  # F par rôle de pièces jointes

    destinataire = models.ForeignKey(
        DestinataireAffaire, on_delete=models.CASCADE,
        related_name='actes',
        verbose_name='Destinataire'
    )

    # Informations de l'acte
    date_acte = models.DateField(verbose_name='Date de signification')
    type_acte = models.CharField(
        max_length=30, choices=TYPE_ACTE_CHOICES,
        verbose_name='Type d\'acte'
    )
    type_acte_autre = models.CharField(
        max_length=200, blank=True,
        verbose_name='Précision si autre',
        help_text='À renseigner si le type est "Autre"'
    )

    # Montants
    montant_base = models.DecimalField(
        max_digits=10, decimal_places=0, default=MONTANT_BASE,
        verbose_name='Montant de base (Art. 81)'
    )

    # Copies supplémentaires
    copies_supplementaires = models.PositiveSmallIntegerField(
        default=0, verbose_name='Copies supplémentaires'
    )
    montant_copies = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        verbose_name='Montant copies'
    )

    # Pièces jointes (rôles)
    roles_pieces_jointes = models.PositiveSmallIntegerField(
        default=0, verbose_name='Nombre de rôles de pièces jointes'
    )
    montant_pieces = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        verbose_name='Montant pièces jointes'
    )

    # Total de l'acte
    montant_total_acte = models.DecimalField(
        max_digits=15, decimal_places=0, default=MONTANT_BASE,
        verbose_name='Montant total de l\'acte'
    )

    # Observations
    observations = models.TextField(blank=True)

    # Traçabilité
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Acte signifié'
        verbose_name_plural = 'Actes signifiés'
        ordering = ['date_acte', 'type_acte']

    def __str__(self):
        return f"{self.get_type_acte_display()} du {self.date_acte.strftime('%d/%m/%Y')}"

    def get_type_display_complet(self):
        """Retourne le libellé complet du type d'acte"""
        if self.type_acte == 'autre' and self.type_acte_autre:
            return f"Autre ({self.type_acte_autre})"
        return self.get_type_acte_display()

    def calculer_totaux(self):
        """Recalcule les montants de l'acte"""
        self.montant_base = self.MONTANT_BASE
        self.montant_copies = self.copies_supplementaires * self.TARIF_COPIE_SUPPLEMENTAIRE
        self.montant_pieces = self.roles_pieces_jointes * self.TARIF_ROLE_PIECES

        self.montant_total_acte = (
            self.montant_base +
            self.montant_copies +
            self.montant_pieces
        )

    def save(self, *args, **kwargs):
        # Recalculer les montants
        self.calculer_totaux()
        super().save(*args, **kwargs)

        # Mettre à jour le destinataire parent
        self.destinataire.calculer_totaux()


class RegistreParquet(models.Model):
    """
    Registre obligatoire au Parquet (Article 75 - Décret n°2012-143)
    Trace toutes les diligences effectuées pour les mémoires de cédules
    """
    memoire = models.ForeignKey(
        Memoire, on_delete=models.CASCADE,
        related_name='registre_parquet',
        verbose_name='Mémoire'
    )
    acte = models.ForeignKey(
        ActeDestinataire, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='entrees_registre',
        verbose_name='Acte lié'
    )
    reference_affaire = models.CharField(
        max_length=100,
        verbose_name='Référence affaire'
    )
    nature_diligence = models.CharField(
        max_length=200,
        verbose_name='Nature de la diligence'
    )
    date_diligence = models.DateField(
        verbose_name='Date de la diligence'
    )
    montant_emoluments = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Montant des émoluments'
    )
    observations = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrée registre Parquet'
        verbose_name_plural = 'Registre Parquet'
        ordering = ['-date_diligence', '-date_creation']

    def __str__(self):
        return f"{self.reference_affaire} - {self.date_diligence}"


# =============================================================================
# MODELES POUR LE MODULE SÉCURITÉ
# =============================================================================

class Role(models.Model):
    """Rôles utilisateurs avec leurs permissions associées"""
    ROLES_SYSTEME = [
        ('admin', 'Administrateur (Huissier titulaire)'),
        ('clerc_principal', 'Clerc principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secrétaire'),
        ('agent_recouvrement', 'Agent de recouvrement'),
        ('comptable', 'Comptable'),
        ('stagiaire', 'Stagiaire'),
        ('consultant', 'Consultant (lecture seule)'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='Code du rôle')
    nom = models.CharField(max_length=100, verbose_name='Nom du rôle')
    description = models.TextField(blank=True, verbose_name='Description')
    est_systeme = models.BooleanField(
        default=False,
        verbose_name='Rôle système',
        help_text='Les rôles système ne peuvent pas être supprimés'
    )
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Permission(models.Model):
    """Permissions granulaires pour les différents modules"""
    MODULES = [
        ('dossiers', 'Dossiers'),
        ('facturation', 'Facturation'),
        ('tresorerie', 'Trésorerie'),
        ('comptabilite', 'Comptabilité'),
        ('recouvrement', 'Recouvrement'),
        ('gerance', 'Gérance Immobilière'),
        ('rh', 'Ressources Humaines'),
        ('agenda', 'Agenda'),
        ('memoires', 'Mémoires Cédules'),
        ('parametres', 'Paramètres'),
        ('securite', 'Sécurité'),
    ]

    code = models.CharField(
        max_length=100, unique=True, verbose_name='Code permission',
        help_text='Ex: dossiers.creer, tresorerie.voir'
    )
    nom = models.CharField(max_length=200, verbose_name='Nom de la permission')
    module = models.CharField(max_length=50, choices=MODULES, verbose_name='Module')
    description = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.module} - {self.nom}"


class RolePermission(models.Model):
    """Association rôle-permission"""
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='permissions_role'
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name='roles_permission'
    )

    class Meta:
        verbose_name = 'Permission du rôle'
        verbose_name_plural = 'Permissions des rôles'
        unique_together = ['role', 'permission']

    def __str__(self):
        return f"{self.role.nom} - {self.permission.code}"


class PermissionUtilisateur(models.Model):
    """Surcharge des permissions pour un utilisateur spécifique"""
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='permissions_personnalisees'
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name='utilisateurs_permission'
    )
    autorise = models.BooleanField(
        default=True,
        verbose_name='Autorisé',
        help_text='True pour accorder, False pour refuser (surcharge le rôle)'
    )

    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permissions_modifiees'
    )

    class Meta:
        verbose_name = 'Permission utilisateur'
        verbose_name_plural = 'Permissions utilisateurs'
        unique_together = ['utilisateur', 'permission']

    def __str__(self):
        status = "✓" if self.autorise else "✗"
        return f"{self.utilisateur} - {self.permission.code} [{status}]"


class SessionUtilisateur(models.Model):
    """Sessions utilisateurs pour le suivi des connexions"""
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='sessions_securite'
    )
    token = models.CharField(max_length=255, unique=True)
    adresse_ip = models.GenericIPAddressField(verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='Navigateur/Agent')

    # Informations sur le navigateur décomposées
    navigateur = models.CharField(max_length=100, blank=True)
    systeme_os = models.CharField(max_length=100, blank=True, verbose_name='Système d\'exploitation')

    # Timestamps
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de connexion')
    date_derniere_activite = models.DateTimeField(auto_now=True, verbose_name='Dernière activité')
    date_expiration = models.DateTimeField(verbose_name='Date d\'expiration')

    # État
    active = models.BooleanField(default=True)
    module_actuel = models.CharField(max_length=100, blank=True, verbose_name='Module actuel')

    class Meta:
        verbose_name = 'Session utilisateur'
        verbose_name_plural = 'Sessions utilisateurs'
        ordering = ['-date_derniere_activite']

    def __str__(self):
        return f"Session {self.utilisateur} - {self.adresse_ip}"

    def est_inactive(self, minutes_inactivite=30):
        """Vérifie si la session est inactive depuis X minutes"""
        from datetime import timedelta
        seuil = timezone.now() - timedelta(minutes=minutes_inactivite)
        return self.date_derniere_activite < seuil

    def forcer_deconnexion(self):
        """Force la déconnexion de cette session"""
        self.active = False
        self.save()


class JournalAudit(models.Model):
    """Journal d'audit pour tracer toutes les actions importantes"""
    ACTIONS = [
        ('connexion', 'Connexion'),
        ('deconnexion', 'Déconnexion'),
        ('echec_connexion', 'Échec de connexion'),
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('consultation', 'Consultation'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approbation', 'Approbation'),
        ('rejet', 'Rejet'),
        ('changement_mdp', 'Changement de mot de passe'),
        ('reset_mdp', 'Réinitialisation de mot de passe'),
        ('acces_refuse', 'Accès refusé'),
        ('parametrage', 'Modification paramètres'),
    ]

    MODULES = [
        ('connexion', 'Connexion'),
        ('dossiers', 'Dossiers'),
        ('facturation', 'Facturation'),
        ('tresorerie', 'Trésorerie'),
        ('comptabilite', 'Comptabilité'),
        ('recouvrement', 'Recouvrement'),
        ('gerance', 'Gérance'),
        ('rh', 'Ressources Humaines'),
        ('agenda', 'Agenda'),
        ('memoires', 'Mémoires'),
        ('parametres', 'Paramètres'),
        ('securite', 'Sécurité'),
        ('systeme', 'Système'),
    ]

    date_heure = models.DateTimeField(auto_now_add=True, verbose_name='Date/Heure')
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actions_audit'
    )
    utilisateur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nom utilisateur',
        help_text='Sauvegardé en cas de suppression de l\'utilisateur'
    )

    action = models.CharField(max_length=50, choices=ACTIONS, verbose_name='Action')
    module = models.CharField(max_length=50, choices=MODULES, verbose_name='Module')
    details = models.TextField(blank=True, verbose_name='Détails')

    # Données avant/après modification (JSON)
    donnees_avant = models.JSONField(null=True, blank=True, verbose_name='Données avant')
    donnees_apres = models.JSONField(null=True, blank=True, verbose_name='Données après')

    # Informations techniques
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='Navigateur')

    # Référence à l'objet concerné
    objet_type = models.CharField(max_length=100, blank=True, verbose_name='Type d\'objet')
    objet_id = models.CharField(max_length=100, blank=True, verbose_name='ID de l\'objet')
    objet_representation = models.CharField(max_length=500, blank=True, verbose_name='Représentation')

    class Meta:
        verbose_name = 'Entrée du journal d\'audit'
        verbose_name_plural = 'Journal d\'audit'
        ordering = ['-date_heure']
        indexes = [
            models.Index(fields=['date_heure']),
            models.Index(fields=['utilisateur']),
            models.Index(fields=['action']),
            models.Index(fields=['module']),
        ]

    def __str__(self):
        return f"{self.date_heure.strftime('%d/%m/%Y %H:%M')} - {self.utilisateur_nom} - {self.get_action_display()}"

    def save(self, *args, **kwargs):
        # Sauvegarder le nom de l'utilisateur
        if self.utilisateur and not self.utilisateur_nom:
            self.utilisateur_nom = str(self.utilisateur)
        super().save(*args, **kwargs)

    @classmethod
    def log_action(cls, utilisateur, action, module, details='', objet=None,
                   donnees_avant=None, donnees_apres=None, request=None):
        """Méthode utilitaire pour créer une entrée d'audit"""
        entry = cls(
            utilisateur=utilisateur,
            action=action,
            module=module,
            details=details,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
        )

        if objet:
            entry.objet_type = objet.__class__.__name__
            entry.objet_id = str(objet.pk) if hasattr(objet, 'pk') else ''
            entry.objet_representation = str(objet)[:500]

        if request:
            entry.adresse_ip = cls.get_client_ip(request)
            entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        entry.save()
        return entry

    @staticmethod
    def get_client_ip(request):
        """Récupère l'adresse IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AlerteSecurite(models.Model):
    """Alertes de sécurité générées par le système"""
    TYPES = [
        ('echec_connexion', 'Échec de connexion répété'),
        ('nouvelle_ip', 'Connexion depuis nouvelle IP'),
        ('hors_horaires', 'Connexion hors horaires'),
        ('acces_refuse', 'Tentative d\'accès non autorisé'),
        ('export_massif', 'Export massif de données'),
        ('modif_securite', 'Modification paramètres sécurité'),
        ('utilisateur_cree', 'Création utilisateur'),
        ('utilisateur_supprime', 'Suppression utilisateur'),
        ('mdp_admin_change', 'Changement mot de passe admin'),
        ('session_suspecte', 'Session suspecte'),
    ]

    GRAVITES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('critical', 'Critique'),
    ]

    date_heure = models.DateTimeField(auto_now_add=True, verbose_name='Date/Heure')
    type_alerte = models.CharField(max_length=50, choices=TYPES, verbose_name='Type')
    gravite = models.CharField(max_length=20, choices=GRAVITES, default='info', verbose_name='Gravité')
    description = models.TextField(verbose_name='Description')

    # Utilisateur concerné
    utilisateur_concerne = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_securite'
    )
    utilisateur_nom = models.CharField(max_length=200, blank=True)

    # Informations techniques
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    donnees_supplementaires = models.JSONField(null=True, blank=True, verbose_name='Données')

    # Traitement
    traitee = models.BooleanField(default=False, verbose_name='Traitée')
    date_traitement = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alertes_traitees'
    )
    commentaire_traitement = models.TextField(blank=True, verbose_name='Commentaire')

    class Meta:
        verbose_name = 'Alerte de sécurité'
        verbose_name_plural = 'Alertes de sécurité'
        ordering = ['-date_heure']

    def __str__(self):
        return f"{self.get_gravite_display()} - {self.get_type_alerte_display()} - {self.date_heure.strftime('%d/%m/%Y %H:%M')}"

    def marquer_traitee(self, utilisateur, commentaire=''):
        """Marque l'alerte comme traitée"""
        self.traitee = True
        self.date_traitement = timezone.now()
        self.traite_par = utilisateur
        self.commentaire_traitement = commentaire
        self.save()

    @classmethod
    def creer_alerte(cls, type_alerte, description, gravite='info',
                     utilisateur=None, adresse_ip=None, donnees=None):
        """Crée une nouvelle alerte de sécurité"""
        alerte = cls(
            type_alerte=type_alerte,
            description=description,
            gravite=gravite,
            utilisateur_concerne=utilisateur,
            adresse_ip=adresse_ip,
            donnees_supplementaires=donnees,
        )
        if utilisateur:
            alerte.utilisateur_nom = str(utilisateur)
        alerte.save()
        return alerte


class AdresseIPAutorisee(models.Model):
    """Liste blanche des adresses IP autorisées"""
    adresse_ip = models.GenericIPAddressField(verbose_name='Adresse IP')
    description = models.CharField(max_length=200, blank=True, verbose_name='Description')
    active = models.BooleanField(default=True)

    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ips_ajoutees'
    )

    class Meta:
        verbose_name = 'Adresse IP autorisée'
        verbose_name_plural = 'Adresses IP autorisées'
        ordering = ['adresse_ip']

    def __str__(self):
        return f"{self.adresse_ip} - {self.description}"


class AdresseIPBloquee(models.Model):
    """Liste noire des adresses IP bloquées"""
    adresse_ip = models.GenericIPAddressField(verbose_name='Adresse IP')
    raison = models.TextField(verbose_name='Raison du blocage')
    active = models.BooleanField(default=True)

    date_blocage = models.DateTimeField(auto_now_add=True)
    bloque_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ips_bloquees'
    )
    date_expiration = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date d\'expiration',
        help_text='Laisser vide pour un blocage permanent'
    )

    class Meta:
        verbose_name = 'Adresse IP bloquée'
        verbose_name_plural = 'Adresses IP bloquées'
        ordering = ['-date_blocage']

    def __str__(self):
        return f"🚫 {self.adresse_ip} - {self.raison[:50]}"


class PolitiqueSecurite(models.Model):
    """Configuration des politiques de sécurité"""
    # Mot de passe
    mdp_longueur_min = models.PositiveSmallIntegerField(default=8, verbose_name='Longueur minimale MDP')
    mdp_exiger_majuscule = models.BooleanField(default=True, verbose_name='Exiger majuscule')
    mdp_exiger_minuscule = models.BooleanField(default=True, verbose_name='Exiger minuscule')
    mdp_exiger_chiffre = models.BooleanField(default=True, verbose_name='Exiger chiffre')
    mdp_exiger_special = models.BooleanField(default=False, verbose_name='Exiger caractère spécial')
    mdp_expiration_jours = models.PositiveSmallIntegerField(
        default=90, verbose_name='Expiration MDP (jours)',
        help_text='0 = jamais'
    )
    mdp_historique = models.PositiveSmallIntegerField(
        default=5, verbose_name='Historique MDP',
        help_text='Empêche la réutilisation des X derniers mots de passe'
    )
    mdp_tentatives_blocage = models.PositiveSmallIntegerField(
        default=5, verbose_name='Tentatives avant blocage'
    )
    mdp_duree_blocage = models.PositiveSmallIntegerField(
        default=30, verbose_name='Durée de blocage (minutes)',
        help_text='0 = déblocage manuel'
    )

    # Sessions
    session_duree_heures = models.PositiveSmallIntegerField(
        default=8, verbose_name='Durée de session (heures)'
    )
    session_inactivite_minutes = models.PositiveSmallIntegerField(
        default=30, verbose_name='Déconnexion après inactivité (minutes)'
    )
    session_simultanees = models.PositiveSmallIntegerField(
        default=1, verbose_name='Sessions simultanées autorisées'
    )
    session_forcer_deconnexion = models.BooleanField(
        default=True, verbose_name='Forcer déconnexion si nouvelle session'
    )
    session_multi_appareils = models.BooleanField(
        default=False, verbose_name='Autoriser plusieurs appareils'
    )

    # 2FA
    CHOIX_2FA = [
        ('desactive', 'Désactivée'),
        ('optionnel', 'Optionnelle'),
        ('obligatoire_tous', 'Obligatoire pour tous'),
        ('obligatoire_admin', 'Obligatoire pour administrateurs'),
    ]
    mode_2fa = models.CharField(
        max_length=20, choices=CHOIX_2FA, default='optionnel',
        verbose_name='Authentification à deux facteurs'
    )

    # Restrictions d'accès
    restriction_ip_active = models.BooleanField(
        default=False, verbose_name='Restriction par IP activée'
    )
    restriction_horaires_active = models.BooleanField(
        default=False, verbose_name='Restriction horaires activée'
    )
    horaire_debut = models.TimeField(
        default='06:00', verbose_name='Heure début autorisée'
    )
    horaire_fin = models.TimeField(
        default='22:00', verbose_name='Heure fin autorisée'
    )
    jours_autorises = models.JSONField(
        default=list, verbose_name='Jours autorisés',
        help_text='Liste des jours (1=Lundi, 7=Dimanche)'
    )

    # Journal d'audit
    audit_conservation_jours = models.PositiveSmallIntegerField(
        default=365, verbose_name='Conservation des logs (jours)'
    )
    audit_archive_auto = models.BooleanField(
        default=True, verbose_name='Archivage automatique'
    )
    audit_export_periodique = models.CharField(
        max_length=20, default='mensuel',
        choices=[('mensuel', 'Mensuel'), ('trimestriel', 'Trimestriel'), ('annuel', 'Annuel')],
        verbose_name='Export périodique'
    )

    # Alertes
    alerte_email = models.EmailField(
        blank=True, verbose_name='Email de notification des alertes'
    )
    alerte_echec_connexion = models.BooleanField(default=True)
    alerte_nouvelle_ip = models.BooleanField(default=True)
    alerte_hors_horaires = models.BooleanField(default=True)
    alerte_acces_refuse = models.BooleanField(default=True)
    alerte_export_massif = models.BooleanField(default=True)
    alerte_modif_securite = models.BooleanField(default=True)
    alerte_utilisateur_cree = models.BooleanField(default=True)
    alerte_mdp_admin = models.BooleanField(default=True)

    # Maintenance
    maintenance_active = models.BooleanField(default=False, verbose_name='Mode maintenance')
    maintenance_message = models.TextField(
        blank=True, default='L\'application est temporairement indisponible pour maintenance.',
        verbose_name='Message de maintenance'
    )
    maintenance_admin_autorise = models.BooleanField(
        default=True, verbose_name='Autoriser admin pendant maintenance'
    )

    # Méta
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='politiques_modifiees'
    )

    class Meta:
        verbose_name = 'Politique de sécurité'
        verbose_name_plural = 'Politique de sécurité'

    def __str__(self):
        return f"Politique de sécurité (modifiée le {self.date_modification.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        # Assurer qu'il n'y a qu'une seule politique
        if not self.pk and PolitiqueSecurite.objects.exists():
            raise ValueError("Une seule politique de sécurité peut exister")
        super().save(*args, **kwargs)

    @classmethod
    def get_politique(cls):
        """Récupère ou crée la politique de sécurité unique"""
        politique, created = cls.objects.get_or_create(pk=1)
        if created:
            # Définir les jours autorisés par défaut (Lundi à Vendredi)
            politique.jours_autorises = [1, 2, 3, 4, 5]
            politique.save()
        return politique


class CleRecuperation(models.Model):
    """Clés de récupération pour l'accès administrateur"""
    cle_hash = models.CharField(max_length=255, verbose_name='Hash de la clé')
    active = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    creee_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cles_creees'
    )

    date_utilisation = models.DateTimeField(null=True, blank=True)
    utilisee_par_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Clé de récupération'
        verbose_name_plural = 'Clés de récupération'
        ordering = ['-date_creation']

    def __str__(self):
        status = "Active" if self.active else "Inactive"
        return f"Clé de récupération ({status}) - {self.date_creation.strftime('%d/%m/%Y')}"

    @classmethod
    def generer_nouvelle_cle(cls, utilisateur=None):
        """Génère une nouvelle clé de récupération"""
        import secrets
        import hashlib

        # Désactiver les anciennes clés
        cls.objects.filter(active=True).update(active=False)

        # Générer une nouvelle clé (format: XXXX-XXXX-XXXX-XXXX)
        parties = [secrets.token_hex(2).upper() for _ in range(4)]
        cle_claire = '-'.join(parties)

        # Hasher la clé
        cle_hash = hashlib.sha256(cle_claire.encode()).hexdigest()

        # Sauvegarder
        nouvelle_cle = cls.objects.create(
            cle_hash=cle_hash,
            creee_par=utilisateur,
        )

        # Retourner la clé en clair (à afficher une seule fois)
        return cle_claire, nouvelle_cle


class HistoriqueMdpUtilisateur(models.Model):
    """Historique des mots de passe pour éviter la réutilisation"""
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='historique_mdp'
    )
    mdp_hash = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique mot de passe'
        verbose_name_plural = 'Historiques mots de passe'
        ordering = ['-date_creation']

    def __str__(self):
        return f"MDP {self.utilisateur} - {self.date_creation.strftime('%d/%m/%Y')}"


# =============================================================================
# MODÈLE CALENDRIER SAISIE IMMOBILIÈRE
# =============================================================================

class CalendrierSaisieImmo(models.Model):
    """
    Calendrier de procédure de saisie immobilière
    Conforme aux Articles 246 à 335 de l'Acte uniforme OHADA
    """

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('abandonne', 'Abandonné'),
    ]

    # Identification
    reference = models.CharField(max_length=50, unique=True)
    dossier = models.ForeignKey(
        'Dossier',
        on_delete=models.CASCADE,
        related_name='calendriers_saisie_immo',
        null=True, blank=True
    )

    # Parties
    creancier = models.CharField(max_length=500, verbose_name="Créancier poursuivant")
    debiteurs = models.TextField(verbose_name="Débiteur(s) saisi(s)")

    # Juridiction
    juridiction = models.CharField(
        max_length=200,
        default="Tribunal de Première Instance de Première Classe de Parakou"
    )

    # Immeuble
    designation_immeuble = models.TextField(verbose_name="Désignation de l'immeuble")
    titre_foncier = models.CharField(max_length=100, blank=True, verbose_name="N° Titre foncier")

    # Dates clés (proposées/planifiées)
    date_commandement = models.DateField(verbose_name="Date signification commandement")
    date_publication = models.DateField(null=True, blank=True)
    date_depot_cahier = models.DateField(null=True, blank=True)
    date_sommation = models.DateField(null=True, blank=True)
    date_audience_eventuelle = models.DateField(null=True, blank=True)
    date_adjudication = models.DateField(null=True, blank=True)

    # Dates réelles (quand les actes sont faits)
    date_publication_reelle = models.DateField(null=True, blank=True)
    date_depot_cahier_reel = models.DateField(null=True, blank=True)
    date_sommation_reelle = models.DateField(null=True, blank=True)
    date_audience_reelle = models.DateField(null=True, blank=True)
    date_adjudication_reelle = models.DateField(null=True, blank=True)

    # Statut et suivi
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    observations = models.TextField(blank=True)

    # Document PDF
    document_pdf = models.FileField(upload_to='calendriers_saisie_immo/', null=True, blank=True)

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='calendriers_saisie_crees'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Calendrier saisie immobilière"
        verbose_name_plural = "Calendriers saisies immobilières"

    def __str__(self):
        return f"{self.reference} - {self.creancier} c/ {self.debiteurs[:50]}"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour le calendrier"""
        now = timezone.now()
        count = cls.objects.filter(created_at__year=now.year).count() + 1
        return f"SAI-{now.year}-{str(count).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def calculer_calendrier(self):
        """Calcule toutes les dates du calendrier"""
        from gestion.services.calcul_delais_ohada import CalendrierSaisieImmobiliere

        cal = CalendrierSaisieImmobiliere(self.date_commandement)
        etapes = cal.calculer_calendrier(
            date_publication=self.date_publication,
            date_depot_cahier=self.date_depot_cahier,
            date_sommation=self.date_sommation,
            date_audience=self.date_audience_eventuelle,
            date_adjudication=self.date_adjudication,
        )
        return etapes

    def get_prochaine_echeance(self):
        """Retourne la prochaine échéance à respecter"""
        from datetime import date as date_type
        etapes = self.calculer_calendrier()
        aujourd_hui = date_type.today()

        for etape in etapes:
            if etape.get('date_butoir'):
                butoir = etape['date_butoir']
                if isinstance(butoir, tuple):
                    butoir = butoir[1]  # Date max de la fenêtre
                if butoir >= aujourd_hui:
                    return etape
        return None

    def get_alertes(self):
        """Retourne les alertes sur les délais"""
        from datetime import date as date_type, timedelta
        alertes = []
        aujourd_hui = date_type.today()

        etapes = self.calculer_calendrier()
        for etape in etapes:
            butoir = etape.get('date_butoir')
            if butoir:
                if isinstance(butoir, tuple):
                    butoir = butoir[1]

                jours_restants = (butoir - aujourd_hui).days

                if jours_restants < 0:
                    alertes.append({
                        'type': 'danger',
                        'etape': etape['nature'],
                        'message': f"DÉLAI DÉPASSÉ de {-jours_restants} jours !",
                    })
                elif jours_restants <= 5:
                    alertes.append({
                        'type': 'warning',
                        'etape': etape['nature'],
                        'message': f"Échéance dans {jours_restants} jours",
                    })
                elif jours_restants <= 15:
                    alertes.append({
                        'type': 'info',
                        'etape': etape['nature'],
                        'message': f"Échéance dans {jours_restants} jours",
                    })

        return alertes

    def to_dict(self):
        """Convertit le calendrier en dictionnaire"""
        return {
            'id': self.id,
            'reference': self.reference,
            'creancier': self.creancier,
            'debiteurs': self.debiteurs,
            'juridiction': self.juridiction,
            'designation_immeuble': self.designation_immeuble,
            'titre_foncier': self.titre_foncier,
            'date_commandement': self.date_commandement.isoformat() if self.date_commandement else None,
            'date_publication': self.date_publication.isoformat() if self.date_publication else None,
            'date_depot_cahier': self.date_depot_cahier.isoformat() if self.date_depot_cahier else None,
            'date_sommation': self.date_sommation.isoformat() if self.date_sommation else None,
            'date_audience_eventuelle': self.date_audience_eventuelle.isoformat() if self.date_audience_eventuelle else None,
            'date_adjudication': self.date_adjudication.isoformat() if self.date_adjudication else None,
            'statut': self.statut,
            'observations': self.observations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pdf_url': self.document_pdf.url if self.document_pdf else None,
        }


class PaiementGlobalMemoires(models.Model):
    """
    Paiement global effectué par le Comptable Public.
    Non rattachable à un mémoire spécifique.

    Contexte métier :
    - Les mémoires de frais (cédules) ne sont PAS payés individuellement
    - Le Comptable Public (niveau Cour d'Appel ou Cour Spéciale) effectue un paiement GLOBAL
    - Ce montant n'est pas forcément égal à la somme des mémoires en attente
    - Impossible de rattacher le paiement à un mémoire spécifique
    - Le Comptable demande une FACTURE NORMALISÉE MECeF pour payer
    """

    JURIDICTION_CHOICES = [
        ('ca_parakou', 'Cour d\'Appel de Parakou'),
        ('ca_cotonou', 'Cour d\'Appel de Cotonou'),
        ('ca_abomey', 'Cour d\'Appel d\'Abomey'),
        ('criet', 'CRIET'),
        ('cour_supreme', 'Cour Suprême'),
        ('autre', 'Autre juridiction'),
    ]

    # Identification
    reference = models.CharField(
        max_length=50, unique=True, verbose_name="Référence paiement"
    )

    # Source du paiement
    juridiction = models.CharField(
        max_length=50, choices=JURIDICTION_CHOICES, verbose_name="Juridiction payeuse"
    )
    comptable_public = models.CharField(
        max_length=200, blank=True, verbose_name="Nom du Comptable Public"
    )

    # Montant
    montant = models.DecimalField(
        max_digits=12, decimal_places=0, verbose_name="Montant reçu"
    )
    date_paiement = models.DateField(verbose_name="Date du paiement")
    mode_paiement = models.CharField(
        max_length=50, blank=True, verbose_name="Mode de paiement"
    )
    reference_virement = models.CharField(
        max_length=100, blank=True, verbose_name="Référence virement/chèque"
    )

    # Facture normalisée MECeF (demandée par le comptable pour payer)
    facture_mecef = models.ForeignKey(
        'Facture',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_memoires',
        verbose_name="Facture MECeF associée"
    )

    # Période couverte (indicatif)
    periode_debut = models.DateField(
        null=True, blank=True, verbose_name="Période du"
    )
    periode_fin = models.DateField(
        null=True, blank=True, verbose_name="Période au"
    )

    # Affectation indicative (optionnel - pour suivi interne)
    memoires_concernes = models.ManyToManyField(
        'Memoire',
        blank=True,
        related_name='paiements_recus',
        verbose_name="Mémoires concernés (indicatif)",
        help_text="Association indicative, le paiement n'est pas rattaché à un mémoire spécifique"
    )

    # Trésorerie
    compte_tresorerie = models.ForeignKey(
        'tresorerie.CompteBancaire',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='paiements_memoires',
        verbose_name="Compte crédité"
    )
    mouvement_tresorerie = models.OneToOneField(
        'tresorerie.MouvementTresorerie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiement_memoires_source'
    )

    # Notes
    observations = models.TextField(blank=True)

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='paiements_memoires_crees'
    )

    class Meta:
        verbose_name = "Paiement global mémoires"
        verbose_name_plural = "Paiements globaux mémoires"
        ordering = ['-date_paiement']

    def __str__(self):
        return f"{self.reference} - {self.montant:,.0f} FCFA ({self.get_juridiction_display()})"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour le paiement global"""
        from datetime import datetime
        annee = datetime.now().year
        count = cls.objects.filter(created_at__year=annee).count() + 1
        return f"PGM-{annee}-{count:04d}"


class HistoriqueValidationMemoire(models.Model):
    """Historique des actions de validation/rejet sur un mémoire"""

    ACTION_CHOICES = [
        ('soumission', 'Soumission'),
        ('validation', 'Validation'),
        ('rejet_correction', 'Rejet avec demande de correction'),
        ('rejet_definitif', 'Rejet définitif'),
        ('correction', 'Correction effectuée'),
    ]

    memoire = models.ForeignKey(
        'Memoire',
        on_delete=models.CASCADE,
        related_name='historique_validations'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    date_action = models.DateTimeField(auto_now_add=True)
    effectue_par = models.CharField(max_length=200, blank=True, verbose_name="Effectué par")
    commentaire = models.TextField(blank=True)
    montant_avant = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    montant_apres = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    class Meta:
        verbose_name = "Historique validation mémoire"
        verbose_name_plural = "Historiques validation mémoires"
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.memoire.numero} - {self.get_action_display()} ({self.date_action.strftime('%d/%m/%Y')})"


class PermissionsGranulaires(models.Model):
    """
    Permissions granulaires par utilisateur.
    L'administrateur coche les actions autorisées pour chaque collaborateur.
    """

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='permissions_granulaires',
        verbose_name="Utilisateur"
    )

    # ═══════════════════════════════════════════════════════════════
    # MODULE DOSSIERS
    # ═══════════════════════════════════════════════════════════════
    dossiers_voir = models.BooleanField(default=True, verbose_name="Voir les dossiers")
    dossiers_creer = models.BooleanField(default=False, verbose_name="Créer des dossiers")
    dossiers_modifier = models.BooleanField(default=False, verbose_name="Modifier les dossiers")
    dossiers_supprimer = models.BooleanField(default=False, verbose_name="Supprimer des dossiers")
    dossiers_voir_tous = models.BooleanField(default=False, verbose_name="Voir TOUS les dossiers (sinon uniquement les siens)")

    # ═══════════════════════════════════════════════════════════════
    # MODULE RECOUVREMENT
    # ═══════════════════════════════════════════════════════════════
    recouvrement_voir = models.BooleanField(default=True, verbose_name="Voir les recouvrements")
    recouvrement_creer = models.BooleanField(default=False, verbose_name="Créer des recouvrements")
    recouvrement_modifier = models.BooleanField(default=False, verbose_name="Modifier les recouvrements")
    recouvrement_encaisser = models.BooleanField(default=False, verbose_name="Enregistrer des encaissements")
    recouvrement_reverser = models.BooleanField(default=False, verbose_name="Effectuer des reversements")
    recouvrement_point_global = models.BooleanField(default=False, verbose_name="Générer des points globaux")

    # ═══════════════════════════════════════════════════════════════
    # MODULE FACTURATION
    # ═══════════════════════════════════════════════════════════════
    factures_voir = models.BooleanField(default=True, verbose_name="Voir les factures")
    factures_creer = models.BooleanField(default=False, verbose_name="Créer des factures")
    factures_modifier = models.BooleanField(default=False, verbose_name="Modifier les factures")
    factures_supprimer = models.BooleanField(default=False, verbose_name="Supprimer des factures")
    factures_normaliser_mecef = models.BooleanField(default=False, verbose_name="Normaliser MECeF")
    factures_avoir = models.BooleanField(default=False, verbose_name="Créer des avoirs")

    # ═══════════════════════════════════════════════════════════════
    # MODULE MÉMOIRES / CÉDULES
    # ═══════════════════════════════════════════════════════════════
    memoires_voir = models.BooleanField(default=True, verbose_name="Voir les mémoires")
    memoires_creer = models.BooleanField(default=False, verbose_name="Créer des mémoires")
    memoires_modifier = models.BooleanField(default=False, verbose_name="Modifier les mémoires")
    memoires_soumettre = models.BooleanField(default=False, verbose_name="Soumettre les mémoires")
    memoires_paiement_global = models.BooleanField(default=False, verbose_name="Enregistrer paiements globaux")

    # ═══════════════════════════════════════════════════════════════
    # MODULE TRÉSORERIE
    # ═══════════════════════════════════════════════════════════════
    tresorerie_voir = models.BooleanField(default=False, verbose_name="Voir la trésorerie")
    tresorerie_mouvements = models.BooleanField(default=False, verbose_name="Créer des mouvements")
    tresorerie_rapprochement = models.BooleanField(default=False, verbose_name="Rapprochement bancaire")
    tresorerie_voir_soldes = models.BooleanField(default=False, verbose_name="Voir les soldes des comptes")

    # ═══════════════════════════════════════════════════════════════
    # MODULE COMPTABILITÉ
    # ═══════════════════════════════════════════════════════════════
    comptabilite_voir = models.BooleanField(default=False, verbose_name="Voir la comptabilité")
    comptabilite_ecritures = models.BooleanField(default=False, verbose_name="Saisir des écritures")
    comptabilite_cloture = models.BooleanField(default=False, verbose_name="Clôturer des périodes")
    comptabilite_etats = models.BooleanField(default=False, verbose_name="Générer les états financiers")

    # ═══════════════════════════════════════════════════════════════
    # MODULE GÉRANCE IMMOBILIÈRE
    # ═══════════════════════════════════════════════════════════════
    gerance_voir = models.BooleanField(default=False, verbose_name="Voir la gérance")
    gerance_biens = models.BooleanField(default=False, verbose_name="Gérer les biens")
    gerance_baux = models.BooleanField(default=False, verbose_name="Gérer les baux")
    gerance_quittances = models.BooleanField(default=False, verbose_name="Générer des quittances")
    gerance_reversements = models.BooleanField(default=False, verbose_name="Reversements propriétaires")

    # ═══════════════════════════════════════════════════════════════
    # MODULE AGENDA
    # ═══════════════════════════════════════════════════════════════
    agenda_voir = models.BooleanField(default=True, verbose_name="Voir l'agenda")
    agenda_creer = models.BooleanField(default=True, verbose_name="Créer des événements")
    agenda_modifier_tous = models.BooleanField(default=False, verbose_name="Modifier tous les événements")
    agenda_taches = models.BooleanField(default=True, verbose_name="Gérer les tâches")

    # ═══════════════════════════════════════════════════════════════
    # MODULE DOCUMENTS / DRIVE
    # ═══════════════════════════════════════════════════════════════
    documents_voir = models.BooleanField(default=True, verbose_name="Voir les documents")
    documents_uploader = models.BooleanField(default=True, verbose_name="Uploader des documents")
    documents_supprimer = models.BooleanField(default=False, verbose_name="Supprimer des documents")
    documents_tous_dossiers = models.BooleanField(default=False, verbose_name="Accéder à tous les dossiers")

    # ═══════════════════════════════════════════════════════════════
    # MODULE RH
    # ═══════════════════════════════════════════════════════════════
    rh_voir = models.BooleanField(default=False, verbose_name="Voir les RH")
    rh_employes = models.BooleanField(default=False, verbose_name="Gérer les employés")
    rh_conges = models.BooleanField(default=False, verbose_name="Gérer les congés")
    rh_paie = models.BooleanField(default=False, verbose_name="Gérer la paie")

    # ═══════════════════════════════════════════════════════════════
    # MODULE PARAMÈTRES
    # ═══════════════════════════════════════════════════════════════
    parametres_voir = models.BooleanField(default=False, verbose_name="Voir les paramètres")
    parametres_modifier = models.BooleanField(default=False, verbose_name="Modifier les paramètres")
    parametres_utilisateurs = models.BooleanField(default=False, verbose_name="Gérer les utilisateurs")
    parametres_permissions = models.BooleanField(default=False, verbose_name="Gérer les permissions")

    # ═══════════════════════════════════════════════════════════════
    # RAPPORTS ET EXPORTS
    # ═══════════════════════════════════════════════════════════════
    rapports_voir = models.BooleanField(default=False, verbose_name="Voir les rapports")
    rapports_generer = models.BooleanField(default=False, verbose_name="Générer des rapports")
    exports_excel = models.BooleanField(default=False, verbose_name="Exporter en Excel")
    exports_pdf = models.BooleanField(default=True, verbose_name="Exporter en PDF")

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permissions_granulaires_modifiees'
    )

    class Meta:
        verbose_name = "Permissions granulaires"
        verbose_name_plural = "Permissions granulaires"

    def __str__(self):
        return f"Permissions granulaires de {self.utilisateur.get_full_name() or self.utilisateur.username}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """Récupère ou crée les permissions pour un utilisateur"""
        permissions, created = cls.objects.get_or_create(utilisateur=user)
        return permissions

    def has_permission(self, permission_name):
        """Vérifie si l'utilisateur a une permission spécifique"""
        if hasattr(self, permission_name):
            return getattr(self, permission_name)
        return False

    def get_permissions_by_module(self):
        """Retourne les permissions groupées par module"""
        modules = {
            'dossiers': {
                'label': 'Dossiers',
                'permissions': [
                    ('dossiers_voir', self.dossiers_voir),
                    ('dossiers_creer', self.dossiers_creer),
                    ('dossiers_modifier', self.dossiers_modifier),
                    ('dossiers_supprimer', self.dossiers_supprimer),
                    ('dossiers_voir_tous', self.dossiers_voir_tous),
                ]
            },
            'recouvrement': {
                'label': 'Recouvrement',
                'permissions': [
                    ('recouvrement_voir', self.recouvrement_voir),
                    ('recouvrement_creer', self.recouvrement_creer),
                    ('recouvrement_modifier', self.recouvrement_modifier),
                    ('recouvrement_encaisser', self.recouvrement_encaisser),
                    ('recouvrement_reverser', self.recouvrement_reverser),
                    ('recouvrement_point_global', self.recouvrement_point_global),
                ]
            },
            'factures': {
                'label': 'Facturation',
                'permissions': [
                    ('factures_voir', self.factures_voir),
                    ('factures_creer', self.factures_creer),
                    ('factures_modifier', self.factures_modifier),
                    ('factures_supprimer', self.factures_supprimer),
                    ('factures_normaliser_mecef', self.factures_normaliser_mecef),
                    ('factures_avoir', self.factures_avoir),
                ]
            },
            'memoires': {
                'label': 'Mémoires / Cédules',
                'permissions': [
                    ('memoires_voir', self.memoires_voir),
                    ('memoires_creer', self.memoires_creer),
                    ('memoires_modifier', self.memoires_modifier),
                    ('memoires_soumettre', self.memoires_soumettre),
                    ('memoires_paiement_global', self.memoires_paiement_global),
                ]
            },
            'tresorerie': {
                'label': 'Trésorerie',
                'permissions': [
                    ('tresorerie_voir', self.tresorerie_voir),
                    ('tresorerie_mouvements', self.tresorerie_mouvements),
                    ('tresorerie_rapprochement', self.tresorerie_rapprochement),
                    ('tresorerie_voir_soldes', self.tresorerie_voir_soldes),
                ]
            },
            'comptabilite': {
                'label': 'Comptabilité',
                'permissions': [
                    ('comptabilite_voir', self.comptabilite_voir),
                    ('comptabilite_ecritures', self.comptabilite_ecritures),
                    ('comptabilite_cloture', self.comptabilite_cloture),
                    ('comptabilite_etats', self.comptabilite_etats),
                ]
            },
            'gerance': {
                'label': 'Gérance Immobilière',
                'permissions': [
                    ('gerance_voir', self.gerance_voir),
                    ('gerance_biens', self.gerance_biens),
                    ('gerance_baux', self.gerance_baux),
                    ('gerance_quittances', self.gerance_quittances),
                    ('gerance_reversements', self.gerance_reversements),
                ]
            },
            'agenda': {
                'label': 'Agenda',
                'permissions': [
                    ('agenda_voir', self.agenda_voir),
                    ('agenda_creer', self.agenda_creer),
                    ('agenda_modifier_tous', self.agenda_modifier_tous),
                    ('agenda_taches', self.agenda_taches),
                ]
            },
            'documents': {
                'label': 'Documents / Drive',
                'permissions': [
                    ('documents_voir', self.documents_voir),
                    ('documents_uploader', self.documents_uploader),
                    ('documents_supprimer', self.documents_supprimer),
                    ('documents_tous_dossiers', self.documents_tous_dossiers),
                ]
            },
            'rh': {
                'label': 'Ressources Humaines',
                'permissions': [
                    ('rh_voir', self.rh_voir),
                    ('rh_employes', self.rh_employes),
                    ('rh_conges', self.rh_conges),
                    ('rh_paie', self.rh_paie),
                ]
            },
            'parametres': {
                'label': 'Paramètres',
                'permissions': [
                    ('parametres_voir', self.parametres_voir),
                    ('parametres_modifier', self.parametres_modifier),
                    ('parametres_utilisateurs', self.parametres_utilisateurs),
                    ('parametres_permissions', self.parametres_permissions),
                ]
            },
            'rapports': {
                'label': 'Rapports et Exports',
                'permissions': [
                    ('rapports_voir', self.rapports_voir),
                    ('rapports_generer', self.rapports_generer),
                    ('exports_excel', self.exports_excel),
                    ('exports_pdf', self.exports_pdf),
                ]
            },
        }
        return modules


class ActeSecurise(models.Model):
    """
    Enregistrement de sécurisation pour chaque acte produit.
    Permet la vérification d'authenticité via QR code.
    """
    # Identifiant unique de vérification
    code_verification = models.CharField(
        max_length=25,
        unique=True,
        db_index=True,
        verbose_name="Code de vérification"
    )  # Format: ACT-2025-1130-7F3B2

    # Lien vers le dossier
    dossier = models.ForeignKey(
        'Dossier',
        on_delete=models.CASCADE,
        related_name='actes_securises',
        verbose_name="Dossier"
    )

    # Type d'acte
    TYPE_ACTE_CHOICES = [
        ('signification', 'Signification'),
        ('constat', 'Procès-verbal de constat'),
        ('sommation', 'Sommation'),
        ('commandement', 'Commandement de payer'),
        ('saisie', 'Procès-verbal de saisie'),
        ('inventaire', 'Inventaire'),
        ('citation', 'Citation à comparaître'),
        ('notification', 'Notification'),
        ('proces_verbal', 'Procès-verbal'),
        ('autre', 'Autre acte'),
    ]
    type_acte = models.CharField(
        max_length=50,
        choices=TYPE_ACTE_CHOICES,
        verbose_name="Type d'acte"
    )

    # Informations de l'acte
    titre_acte = models.CharField(
        max_length=255,
        verbose_name="Titre de l'acte"
    )
    date_acte = models.DateField(
        verbose_name="Date de l'acte"
    )

    # Parties concernées (résumé pour affichage vérification)
    parties_resume = models.TextField(
        verbose_name="Parties",
        help_text="Ex: BANQUE XYZ c/ M. DUPONT Jean"
    )

    # Sécurisation - Hash du contenu
    hash_contenu = models.CharField(
        max_length=64,
        verbose_name="Hash du document",
        help_text="SHA-256 du contenu PDF"
    )
    hash_algorithme = models.CharField(
        max_length=10,
        default='SHA256',
        verbose_name="Algorithme"
    )

    # Lien vers document (optionnel)
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actes_securises',
        verbose_name="Document associé"
    )

    # Métadonnées de création
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Créé par"
    )
    cree_le = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )

    # Statistiques de vérification
    nombre_verifications = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de vérifications"
    )
    derniere_verification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière vérification"
    )

    # Statut
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Décocher pour invalider un acte (erreur, annulation)"
    )

    class Meta:
        verbose_name = "Acte sécurisé"
        verbose_name_plural = "Actes sécurisés"
        ordering = ['-cree_le']
        indexes = [
            models.Index(fields=['code_verification']),
            models.Index(fields=['dossier', '-date_acte']),
        ]

    def __str__(self):
        return f"{self.code_verification} - {self.titre_acte}"

    @classmethod
    def generer_code_verification(cls):
        """
        Génère un code unique pour un acte.
        Format: ACT-AAAA-MMJJ-XXXXX
        """
        import secrets
        from django.utils import timezone

        now = timezone.now()

        while True:
            random_part = secrets.token_hex(3).upper()  # 6 caractères hex
            code = f"ACT-{now.year}-{now.month:02d}{now.day:02d}-{random_part}"

            # Vérifier unicité
            if not cls.objects.filter(code_verification=code).exists():
                return code

    @staticmethod
    def calculer_hash(contenu_bytes):
        """
        Calcule le hash SHA-256 d'un contenu.
        """
        import hashlib
        return hashlib.sha256(contenu_bytes).hexdigest()

    def get_verification_url(self):
        """URL relative de vérification"""
        return f"/verification/{self.code_verification}/"

    def get_qr_data(self):
        """Données à encoder dans le QR code"""
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'https://etude-biaou.bj')
        return f"{base_url}/v/{self.code_verification}"

    def incrementer_verification(self):
        """Incrémente le compteur lors d'une vérification"""
        from django.utils import timezone
        self.nombre_verifications += 1
        self.derniere_verification = timezone.now()
        self.save(update_fields=['nombre_verifications', 'derniere_verification'])


# Import des modèles d'import (pour les inclure dans les migrations)
from gestion.models_import import SessionImport, DossierImportTemp

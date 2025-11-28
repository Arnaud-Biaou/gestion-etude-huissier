from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Collaborateur, Partie, Dossier, Facture, LigneFacture,
    ActeProcedure, HistoriqueCalcul, TauxLegal, MessageChatbot,
    Creancier, PortefeuilleCreancier, Encaissement, ImputationEncaissement,
    Reversement, BasculementAmiableForce, PointGlobalCreancier,
    EnvoiAutomatiquePoint, HistoriqueEnvoiPoint,
    # Mémoires de Cédules
    AutoriteRequerante, Memoire, AffaireMemoire, DestinataireAffaire, ActeDestinataire,
    RegistreParquet,
    # Modèles de sécurité
    Role, Permission, RolePermission, PermissionUtilisateur,
    SessionUtilisateur, JournalAudit, AlerteSecurite,
    PolitiqueSecurite, AdresseIPAutorisee, AdresseIPBloquee
)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplementaires', {'fields': ('role', 'telephone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplementaires', {'fields': ('role', 'telephone')}),
    )


@admin.register(Collaborateur)
class CollaborateurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'role', 'email', 'telephone', 'actif')
    list_filter = ('role', 'actif')
    search_fields = ('nom', 'email')


@admin.register(Partie)
class PartieAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type_personne', 'telephone', 'ifu')
    list_filter = ('type_personne',)
    search_fields = ('nom', 'prenoms', 'denomination')


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ('reference', 'get_intitule', 'type_dossier', 'is_contentieux', 'phase', 'statut', 'creancier', 'affecte_a', 'date_ouverture')
    list_filter = ('type_dossier', 'is_contentieux', 'phase', 'statut', 'creancier', 'affecte_a')
    search_fields = ('reference', 'description')
    date_hierarchy = 'date_ouverture'
    filter_horizontal = ('demandeurs', 'defendeurs')

    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'is_contentieux', 'type_dossier', 'description', 'statut')
        }),
        ('Créancier et phase', {
            'fields': ('creancier', 'phase', 'date_passage_force')
        }),
        ('Créance', {
            'fields': ('montant_creance', 'date_creance', 'montant_principal', 'montant_interets',
                       'montant_frais', 'montant_emoluments', 'montant_depens', 'montant_accessoires')
        }),
        ('Titre exécutoire', {
            'fields': ('titre_executoire_type', 'titre_executoire_reference',
                       'titre_executoire_date', 'titre_executoire_juridiction'),
            'classes': ('collapse',)
        }),
        ('Parties', {
            'fields': ('demandeurs', 'defendeurs')
        }),
        ('Affectation', {
            'fields': ('affecte_a', 'date_ouverture', 'cree_par')
        }),
    )


class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'montant_ht', 'montant_tva', 'montant_ttc', 'date_emission', 'statut', 'mecef_numero')
    list_filter = ('statut', 'date_emission')
    search_fields = ('numero', 'client', 'ifu', 'mecef_numero')
    date_hierarchy = 'date_emission'
    inlines = [LigneFactureInline]
    readonly_fields = ('date_creation',)

    fieldsets = (
        ('Informations generales', {
            'fields': ('numero', 'dossier', 'client', 'ifu', 'statut')
        }),
        ('Montants', {
            'fields': ('montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc')
        }),
        ('Dates', {
            'fields': ('date_emission', 'date_echeance', 'date_creation')
        }),
        ('MECeF', {
            'fields': ('mecef_numero', 'nim', 'mecef_qr', 'date_mecef'),
            'classes': ('collapse',)
        }),
        ('Observations', {
            'fields': ('observations',),
            'classes': ('collapse',)
        }),
    )


@admin.register(LigneFacture)
class LigneFactureAdmin(admin.ModelAdmin):
    list_display = ('facture', 'description', 'quantite', 'prix_unitaire')
    list_filter = ('facture',)
    search_fields = ('description',)


@admin.register(ActeProcedure)
class ActeProcedureAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'tarif', 'actif')
    list_filter = ('actif',)
    search_fields = ('code', 'libelle')


@admin.register(HistoriqueCalcul)
class HistoriqueCalculAdmin(admin.ModelAdmin):
    list_display = ('nom', 'mode', 'total', 'utilisateur', 'date_creation')
    list_filter = ('mode', 'date_creation')
    search_fields = ('nom',)
    date_hierarchy = 'date_creation'


@admin.register(TauxLegal)
class TauxLegalAdmin(admin.ModelAdmin):
    list_display = ('annee', 'taux', 'source')
    ordering = ('-annee',)


@admin.register(MessageChatbot)
class MessageChatbotAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'type_message', 'contenu', 'date_creation')
    list_filter = ('type_message', 'date_creation')
    search_fields = ('contenu',)


# ============================================
# Administration des Créanciers
# ============================================

class PortefeuilleCreancierInline(admin.StackedInline):
    model = PortefeuilleCreancier
    extra = 0
    readonly_fields = ('nb_dossiers_actifs', 'montant_total_creances', 'montant_total_encaisse',
                       'montant_total_reverse', 'taux_recouvrement', 'derniere_maj_stats')


@admin.register(Creancier)
class CreancierAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type_creancier', 'telephone', 'email', 'taux_commission', 'actif')
    list_filter = ('type_creancier', 'actif')
    search_fields = ('code', 'nom', 'ifu', 'email')
    inlines = [PortefeuilleCreancierInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'type_creancier', 'actif')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'telephone', 'email', 'site_web')
        }),
        ('Informations légales', {
            'fields': ('ifu', 'rccm')
        }),
        ('Contact référent', {
            'fields': ('contact_nom', 'contact_fonction', 'contact_telephone', 'contact_email'),
            'classes': ('collapse',)
        }),
        ('Coordonnées bancaires', {
            'fields': ('banque_nom', 'banque_iban', 'banque_rib'),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('taux_commission', 'delai_reversement', 'notes')
        }),
    )


@admin.register(PortefeuilleCreancier)
class PortefeuilleCreancierAdmin(admin.ModelAdmin):
    list_display = ('creancier', 'gestionnaire', 'nb_dossiers_actifs', 'taux_recouvrement', 'date_debut_relation')
    list_filter = ('gestionnaire',)
    readonly_fields = ('nb_dossiers_actifs', 'montant_total_creances', 'montant_total_encaisse',
                       'montant_total_reverse', 'taux_recouvrement', 'derniere_maj_stats')


# ============================================
# Administration des Encaissements
# ============================================

class ImputationEncaissementInline(admin.TabularInline):
    model = ImputationEncaissement
    extra = 1


@admin.register(Encaissement)
class EncaissementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'dossier', 'montant', 'date_encaissement', 'mode_paiement',
                    'payeur_nom', 'statut', 'reversement_statut')
    list_filter = ('statut', 'reversement_statut', 'mode_paiement', 'date_encaissement')
    search_fields = ('reference', 'dossier__reference', 'payeur_nom')
    date_hierarchy = 'date_encaissement'
    inlines = [ImputationEncaissementInline]
    readonly_fields = ('reference', 'cumul_encaisse_avant', 'cumul_encaisse_apres', 'solde_restant',
                       'montant_a_reverser', 'date_validation', 'date_creation', 'date_modification')

    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'dossier', 'statut')
        }),
        ('Paiement', {
            'fields': ('montant', 'date_encaissement', 'date_valeur', 'mode_paiement',
                       'reference_paiement', 'banque_emettrice')
        }),
        ('Payeur', {
            'fields': ('payeur_nom', 'payeur_telephone', 'payeur_qualite')
        }),
        ('Cumuls et soldes', {
            'fields': ('cumul_encaisse_avant', 'cumul_encaisse_apres', 'solde_restant'),
            'classes': ('collapse',)
        }),
        ('Reversement', {
            'fields': ('montant_a_reverser', 'reversement_statut'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('date_validation', 'valide_par'),
            'classes': ('collapse',)
        }),
        ('Observations', {
            'fields': ('observations', 'piece_justificative')
        }),
    )


@admin.register(ImputationEncaissement)
class ImputationEncaissementAdmin(admin.ModelAdmin):
    list_display = ('encaissement', 'type_imputation', 'montant', 'solde_avant', 'solde_apres')
    list_filter = ('type_imputation',)
    search_fields = ('encaissement__reference',)


# ============================================
# Administration des Reversements
# ============================================

@admin.register(Reversement)
class ReversementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'creancier', 'montant', 'date_reversement',
                    'mode_reversement', 'statut')
    list_filter = ('statut', 'mode_reversement', 'date_reversement', 'creancier')
    search_fields = ('reference', 'creancier__nom', 'reference_virement', 'numero_cheque')
    date_hierarchy = 'date_creation'
    filter_horizontal = ('encaissements',)
    readonly_fields = ('reference', 'date_creation', 'date_modification')

    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'creancier', 'montant', 'statut')
        }),
        ('Mode de reversement', {
            'fields': ('mode_reversement', 'date_reversement', 'reference_virement',
                       'numero_cheque', 'banque')
        }),
        ('Encaissements concernés', {
            'fields': ('encaissements',)
        }),
        ('Preuve et observations', {
            'fields': ('preuve_reversement', 'observations')
        }),
        ('Traçabilité', {
            'fields': ('cree_par', 'effectue_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# Administration du Basculement Amiable→Forcé
# ============================================

@admin.register(BasculementAmiableForce)
class BasculementAmiableForceAdmin(admin.ModelAdmin):
    list_display = ('dossier', 'date_basculement', 'motif', 'total_reste_du', 'nouveau_total')
    list_filter = ('motif', 'date_basculement')
    search_fields = ('dossier__reference',)
    date_hierarchy = 'date_basculement'
    readonly_fields = ('date_creation',)

    fieldsets = (
        ('Dossier', {
            'fields': ('dossier', 'date_basculement', 'motif', 'motif_detail')
        }),
        ('Titre exécutoire', {
            'fields': ('type_titre', 'reference_titre', 'juridiction', 'date_titre'),
            'classes': ('collapse',)
        }),
        ('État de la créance au basculement', {
            'fields': ('montant_principal_restant', 'montant_interets_restant',
                       'montant_frais_restant', 'total_reste_du')
        }),
        ('Nouveaux frais', {
            'fields': ('depens', 'frais_justice', 'emoluments_ohada', 'nouveau_total')
        }),
        ('Données sauvegardées', {
            'fields': ('donnees_phase_amiable',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# Administration des Points Globaux Créanciers
# ============================================

@admin.register(PointGlobalCreancier)
class PointGlobalCreancierAdmin(admin.ModelAdmin):
    list_display = ('creancier', 'date_generation', 'periode_debut', 'periode_fin',
                    'nb_dossiers_total', 'taux_recouvrement')
    list_filter = ('creancier', 'date_generation')
    search_fields = ('creancier__nom',)
    date_hierarchy = 'date_generation'
    readonly_fields = ('date_creation', 'nb_dossiers_total', 'nb_dossiers_actifs',
                       'nb_dossiers_clotures', 'montant_total_creances', 'montant_total_encaisse',
                       'montant_total_reverse', 'taux_recouvrement')


# ============================================
# Administration des Envois Automatiques
# ============================================

class HistoriqueEnvoiPointInline(admin.TabularInline):
    model = HistoriqueEnvoiPoint
    extra = 0
    readonly_fields = ('date_envoi', 'statut', 'destinataires_envoyes', 'destinataires_echec')
    max_num = 10


@admin.register(EnvoiAutomatiquePoint)
class EnvoiAutomatiquePointAdmin(admin.ModelAdmin):
    list_display = ('creancier', 'frequence', 'actif', 'dernier_envoi', 'prochain_envoi')
    list_filter = ('frequence', 'actif', 'creancier')
    inlines = [HistoriqueEnvoiPointInline]
    readonly_fields = ('dernier_envoi', 'prochain_envoi', 'nb_envois_total')


@admin.register(HistoriqueEnvoiPoint)
class HistoriqueEnvoiPointAdmin(admin.ModelAdmin):
    list_display = ('envoi_config', 'date_envoi', 'statut')
    list_filter = ('statut', 'date_envoi')
    date_hierarchy = 'date_envoi'


# ============================================
# Administration des Mémoires de Cédules
# ============================================

@admin.register(AutoriteRequerante)
class AutoriteRequeranteAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type_juridiction', 'ville', 'actif')
    list_filter = ('type_juridiction', 'actif')
    search_fields = ('code', 'nom', 'ville')
    ordering = ['nom']


class ActeDestinataireInline(admin.TabularInline):
    model = ActeDestinataire
    extra = 0
    readonly_fields = ('montant_base', 'montant_copies', 'montant_pieces', 'montant_total_acte')
    fields = ('date_acte', 'type_acte', 'type_acte_autre', 'copies_supplementaires',
              'roles_pieces_jointes', 'montant_base', 'montant_copies', 'montant_pieces',
              'montant_total_acte')


class DestinataireAffaireInline(admin.TabularInline):
    model = DestinataireAffaire
    extra = 0
    readonly_fields = ('frais_transport', 'frais_mission', 'montant_total_actes',
                       'montant_total_destinataire')
    fields = ('nom', 'prenoms', 'qualite', 'localite', 'distance_km', 'type_mission',
              'frais_transport', 'frais_mission', 'montant_total_actes', 'montant_total_destinataire')
    show_change_link = True


class AffaireMemoireInline(admin.TabularInline):
    model = AffaireMemoire
    extra = 0
    readonly_fields = ('montant_total_actes', 'montant_total_transport',
                       'montant_total_mission', 'montant_total_affaire')
    fields = ('numero_parquet', 'intitule_affaire', 'date_audience',
              'montant_total_actes', 'montant_total_transport', 'montant_total_mission',
              'montant_total_affaire')
    show_change_link = True


@admin.register(Memoire)
class MemoireAdmin(admin.ModelAdmin):
    list_display = ('numero', 'mois', 'annee', 'huissier', 'autorite_requerante',
                    'get_nb_affaires', 'montant_total', 'statut')
    list_filter = ('statut', 'annee', 'mois', 'autorite_requerante', 'huissier')
    search_fields = ('numero', 'huissier__nom', 'autorite_requerante__nom')
    date_hierarchy = 'date_creation'
    inlines = [AffaireMemoireInline]
    readonly_fields = ('montant_total_actes', 'montant_total_transport', 'montant_total_mission',
                       'montant_total', 'montant_total_lettres', 'date_certification',
                       'certifie_par', 'date_creation', 'date_modification')

    fieldsets = (
        ('Identification', {
            'fields': ('numero', 'mois', 'annee', 'huissier', 'autorite_requerante')
        }),
        ('Paramètres', {
            'fields': ('residence_huissier', 'lieu_certification')
        }),
        ('Totaux (calculés automatiquement)', {
            'fields': ('montant_total_actes', 'montant_total_transport',
                       'montant_total_mission', 'montant_total', 'montant_total_lettres'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('statut', 'date_certification', 'certifie_par')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
        ('Traçabilité', {
            'fields': ('cree_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    actions = ['recalculer_totaux']

    def recalculer_totaux(self, request, queryset):
        for memoire in queryset:
            memoire.calculer_totaux()
        self.message_user(request, f'{queryset.count()} mémoire(s) recalculé(s)')
    recalculer_totaux.short_description = 'Recalculer les totaux'


@admin.register(AffaireMemoire)
class AffaireMemoireAdmin(admin.ModelAdmin):
    list_display = ('numero_parquet', 'intitule_affaire', 'memoire', 'get_nb_destinataires',
                    'get_nb_actes', 'montant_total_affaire')
    list_filter = ('memoire__annee', 'memoire__mois', 'memoire__autorite_requerante')
    search_fields = ('numero_parquet', 'intitule_affaire', 'memoire__numero')
    inlines = [DestinataireAffaireInline]
    readonly_fields = ('montant_total_actes', 'montant_total_transport',
                       'montant_total_mission', 'montant_total_affaire',
                       'date_creation', 'date_modification')

    fieldsets = (
        ('Mémoire', {
            'fields': ('memoire',)
        }),
        ('Affaire', {
            'fields': ('numero_parquet', 'intitule_affaire', 'nature_infraction', 'date_audience')
        }),
        ('Totaux (calculés automatiquement)', {
            'fields': ('montant_total_actes', 'montant_total_transport',
                       'montant_total_mission', 'montant_total_affaire'),
            'classes': ('collapse',)
        }),
        ('Affichage', {
            'fields': ('ordre_affichage',)
        }),
    )


@admin.register(DestinataireAffaire)
class DestinataireAffaireAdmin(admin.ModelAdmin):
    list_display = ('get_nom_complet', 'qualite', 'localite', 'distance_km',
                    'affaire', 'montant_total_destinataire')
    list_filter = ('qualite', 'type_mission', 'affaire__memoire__annee')
    search_fields = ('nom', 'prenoms', 'raison_sociale', 'localite',
                     'affaire__numero_parquet')
    inlines = [ActeDestinataireInline]
    readonly_fields = ('frais_transport', 'frais_mission', 'montant_total_actes',
                       'montant_total_destinataire', 'date_creation', 'date_modification')

    fieldsets = (
        ('Affaire', {
            'fields': ('affaire',)
        }),
        ('Identité', {
            'fields': ('titre', 'nom', 'prenoms', 'raison_sociale', 'qualite')
        }),
        ('Adresse', {
            'fields': ('adresse', 'localite')
        }),
        ('Frais de déplacement', {
            'fields': ('distance_km', 'type_mission', 'frais_transport', 'frais_mission'),
            'description': 'Les frais sont calculés automatiquement selon la distance. '
                          'Transport > 20 km, Mission >= 100 km.'
        }),
        ('Totaux (calculés automatiquement)', {
            'fields': ('montant_total_actes', 'montant_total_destinataire'),
            'classes': ('collapse',)
        }),
        ('Observations', {
            'fields': ('observations', 'ordre_affichage')
        }),
    )

    actions = ['recalculer_frais']

    def recalculer_frais(self, request, queryset):
        for dest in queryset:
            dest.calculer_totaux()
        self.message_user(request, f'{queryset.count()} destinataire(s) recalculé(s)')
    recalculer_frais.short_description = 'Recalculer les frais'


@admin.register(ActeDestinataire)
class ActeDestinataireAdmin(admin.ModelAdmin):
    list_display = ('get_type_acte_display', 'date_acte', 'destinataire',
                    'montant_base', 'montant_copies', 'montant_pieces', 'montant_total_acte')
    list_filter = ('type_acte', 'date_acte')
    search_fields = ('destinataire__nom', 'destinataire__prenoms',
                     'destinataire__affaire__numero_parquet')
    date_hierarchy = 'date_acte'
    readonly_fields = ('montant_base', 'montant_copies', 'montant_pieces',
                       'montant_total_acte', 'date_creation', 'date_modification')

    fieldsets = (
        ('Destinataire', {
            'fields': ('destinataire',)
        }),
        ('Acte', {
            'fields': ('date_acte', 'type_acte', 'type_acte_autre')
        }),
        ('Copies et pièces', {
            'fields': ('copies_supplementaires', 'roles_pieces_jointes')
        }),
        ('Montants (calculés automatiquement)', {
            'fields': ('montant_base', 'montant_copies', 'montant_pieces', 'montant_total_acte'),
            'description': 'Base: 4 985 F, Copies: 900 F/copie, Pièces: 1 000 F/rôle'
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
    )


@admin.register(RegistreParquet)
class RegistreParquetAdmin(admin.ModelAdmin):
    list_display = ('reference_affaire', 'memoire', 'nature_diligence', 'date_diligence',
                    'montant_emoluments')
    list_filter = ('memoire__annee', 'memoire__mois', 'date_diligence')
    search_fields = ('reference_affaire', 'nature_diligence', 'memoire__numero')
    date_hierarchy = 'date_diligence'
    readonly_fields = ('date_creation',)

    fieldsets = (
        ('Mémoire', {
            'fields': ('memoire', 'acte')
        }),
        ('Diligence', {
            'fields': ('reference_affaire', 'nature_diligence', 'date_diligence',
                       'montant_emoluments')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
    )


# ============================================
# Administration des modèles de Sécurité
# ============================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'est_systeme', 'actif', 'date_creation')
    list_filter = ('est_systeme', 'actif')
    search_fields = ('code', 'nom', 'description')
    ordering = ['nom']
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'module', 'date_creation')
    list_filter = ('module',)
    search_fields = ('code', 'nom', 'description')
    ordering = ['module', 'code']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission')
    list_filter = ('role', 'permission__module')
    search_fields = ('role__nom', 'permission__nom')


@admin.register(PermissionUtilisateur)
class PermissionUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'permission', 'autorise', 'date_modification')
    list_filter = ('autorise', 'permission__module')
    search_fields = ('utilisateur__username', 'permission__nom')
    readonly_fields = ('date_modification',)


@admin.register(SessionUtilisateur)
class SessionUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'adresse_ip', 'navigateur', 'active', 'date_creation', 'date_derniere_activite')
    list_filter = ('active', 'navigateur', 'systeme_os')
    search_fields = ('utilisateur__username', 'adresse_ip')
    date_hierarchy = 'date_creation'
    readonly_fields = ('token', 'date_creation', 'date_derniere_activite')


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ('date_heure', 'utilisateur_nom', 'action', 'module', 'objet_representation', 'adresse_ip')
    list_filter = ('action', 'module', 'date_heure')
    search_fields = ('utilisateur_nom', 'details', 'objet_representation', 'adresse_ip')
    date_hierarchy = 'date_heure'
    readonly_fields = (
        'date_heure', 'utilisateur', 'utilisateur_nom', 'action', 'module',
        'details', 'donnees_avant', 'donnees_apres', 'adresse_ip', 'user_agent',
        'objet_type', 'objet_id', 'objet_representation'
    )

    def has_add_permission(self, request):
        return False  # Les entrées d'audit ne doivent pas être créées manuellement

    def has_change_permission(self, request, obj=None):
        return False  # Les entrées d'audit ne doivent pas être modifiées

    def has_delete_permission(self, request, obj=None):
        return False  # Les entrées d'audit ne doivent pas être supprimées


@admin.register(AlerteSecurite)
class AlerteSecuriteAdmin(admin.ModelAdmin):
    list_display = ('date_heure', 'type_alerte', 'gravite', 'utilisateur_nom', 'traitee', 'adresse_ip')
    list_filter = ('type_alerte', 'gravite', 'traitee', 'date_heure')
    search_fields = ('utilisateur_nom', 'description', 'adresse_ip')
    date_hierarchy = 'date_heure'
    readonly_fields = ('date_heure', 'utilisateur_concerne', 'utilisateur_nom', 'adresse_ip', 'donnees_supplementaires')

    fieldsets = (
        ('Alerte', {
            'fields': ('type_alerte', 'gravite', 'description', 'date_heure')
        }),
        ('Utilisateur concerné', {
            'fields': ('utilisateur_concerne', 'utilisateur_nom', 'adresse_ip')
        }),
        ('Traitement', {
            'fields': ('traitee', 'date_traitement', 'traite_par', 'commentaire_traitement')
        }),
        ('Données techniques', {
            'fields': ('donnees_supplementaires',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PolitiqueSecurite)
class PolitiqueSecuriteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'mdp_longueur_min', 'mode_2fa', 'session_duree_heures', 'maintenance_active')
    readonly_fields = ('date_modification',)

    fieldsets = (
        ('Politique de mot de passe', {
            'fields': (
                'mdp_longueur_min', 'mdp_exiger_majuscule', 'mdp_exiger_minuscule',
                'mdp_exiger_chiffre', 'mdp_exiger_special', 'mdp_expiration_jours',
                'mdp_historique', 'mdp_tentatives_blocage', 'mdp_duree_blocage'
            )
        }),
        ('Sessions', {
            'fields': (
                'session_duree_heures', 'session_inactivite_minutes',
                'session_simultanees', 'session_forcer_deconnexion', 'session_multi_appareils'
            )
        }),
        ('Double authentification', {
            'fields': ('mode_2fa',)
        }),
        ('Restrictions d\'accès', {
            'fields': (
                'restriction_ip_active', 'restriction_horaires_active',
                'horaire_debut', 'horaire_fin', 'jours_autorises'
            ),
            'classes': ('collapse',)
        }),
        ('Journal d\'audit', {
            'fields': ('audit_conservation_jours', 'audit_archive_auto', 'audit_export_periodique'),
            'classes': ('collapse',)
        }),
        ('Alertes', {
            'fields': (
                'alerte_email', 'alerte_echec_connexion', 'alerte_nouvelle_ip',
                'alerte_hors_horaires', 'alerte_acces_refuse', 'alerte_export_massif',
                'alerte_modif_securite', 'alerte_utilisateur_cree', 'alerte_mdp_admin'
            ),
            'classes': ('collapse',)
        }),
        ('Maintenance', {
            'fields': ('maintenance_active', 'maintenance_message', 'maintenance_admin_autorise')
        }),
        ('Métadonnées', {
            'fields': ('date_modification', 'modifie_par'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdresseIPAutorisee)
class AdresseIPAutoriseeAdmin(admin.ModelAdmin):
    list_display = ('adresse_ip', 'description', 'active', 'date_ajout', 'ajoute_par')
    list_filter = ('active', 'date_ajout')
    search_fields = ('adresse_ip', 'description')
    readonly_fields = ('date_ajout',)


@admin.register(AdresseIPBloquee)
class AdresseIPBloqueeAdmin(admin.ModelAdmin):
    list_display = ('adresse_ip', 'raison', 'active', 'date_blocage', 'date_expiration', 'bloque_par')
    list_filter = ('active', 'date_blocage')
    search_fields = ('adresse_ip', 'raison')
    readonly_fields = ('date_blocage',)

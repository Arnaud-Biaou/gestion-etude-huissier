from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Collaborateur, Partie, Dossier, Facture, LigneFacture,
    ActeProcedure, HistoriqueCalcul, TauxLegal, MessageChatbot,
    Creancier, PortefeuilleCreancier, Encaissement, ImputationEncaissement,
    Reversement, BasculementAmiableForce, PointGlobalCreancier,
    EnvoiAutomatiquePoint, HistoriqueEnvoiPoint
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

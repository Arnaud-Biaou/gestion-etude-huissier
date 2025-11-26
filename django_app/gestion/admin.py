from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Collaborateur, Partie, Dossier, Facture,
    ActeProcedure, HistoriqueCalcul, TauxLegal, MessageChatbot,
    # Modèles Trésorerie
    Caisse, JournalCaisse, OperationTresorerie, Consignation,
    MouvementConsignation, CompteBancaire, RapprochementBancaire,
    LigneRapprochement, AuditTresorerie
)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'telephone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'telephone')}),
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
    list_display = ('reference', 'get_intitule', 'type_dossier', 'is_contentieux', 'statut', 'affecte_a', 'date_ouverture')
    list_filter = ('type_dossier', 'is_contentieux', 'statut', 'affecte_a')
    search_fields = ('reference', 'description')
    date_hierarchy = 'date_ouverture'
    filter_horizontal = ('demandeurs', 'defendeurs')


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'montant_ht', 'montant_tva', 'montant_ttc', 'date_emission', 'statut')
    list_filter = ('statut', 'date_emission')
    search_fields = ('numero', 'client')
    date_hierarchy = 'date_emission'


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
# ADMINISTRATION MODULE TRÉSORERIE
# ============================================

@admin.register(Caisse)
class CaisseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'site', 'solde_actuel', 'responsable', 'statut', 'actif')
    list_filter = ('statut', 'actif', 'site')
    search_fields = ('nom', 'site')
    list_editable = ('actif',)
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(JournalCaisse)
class JournalCaisseAdmin(admin.ModelAdmin):
    list_display = ('caisse', 'date', 'solde_ouverture', 'solde_fermeture', 'ecart', 'ouvert_par', 'ferme_par')
    list_filter = ('caisse', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('solde_theorique', 'ecart')


@admin.register(OperationTresorerie)
class OperationTresorerieAdmin(admin.ModelAdmin):
    list_display = ('reference', 'type_operation', 'categorie', 'montant', 'date_operation', 'caisse', 'statut')
    list_filter = ('type_operation', 'categorie', 'statut', 'mode_paiement', 'caisse')
    search_fields = ('reference', 'emetteur', 'beneficiaire', 'motif')
    date_hierarchy = 'date_operation'
    readonly_fields = ('reference', 'date_creation', 'date_modification', 'date_approbation', 'date_annulation')
    raw_id_fields = ('dossier', 'partie', 'consignation')

    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'type_operation', 'categorie', 'montant', 'date_operation')
        }),
        ('Paiement', {
            'fields': ('mode_paiement', 'reference_paiement', 'caisse')
        }),
        ('Liens', {
            'fields': ('dossier', 'partie', 'consignation')
        }),
        ('Tiers', {
            'fields': ('emetteur', 'beneficiaire', 'motif')
        }),
        ('Justificatif', {
            'fields': ('justificatif',)
        }),
        ('Workflow', {
            'fields': ('statut', 'approuve_par', 'date_approbation', 'motif_rejet')
        }),
        ('Annulation', {
            'fields': ('annule_par', 'date_annulation', 'motif_annulation'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('cree_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Consignation)
class ConsignationAdmin(admin.ModelAdmin):
    list_display = ('reference', 'client', 'dossier', 'montant_initial', 'montant_restant', 'statut', 'date_reception')
    list_filter = ('statut', 'date_reception')
    search_fields = ('reference', 'objet', 'debiteur')
    date_hierarchy = 'date_reception'
    readonly_fields = ('reference', 'date_creation', 'date_modification')
    raw_id_fields = ('client', 'dossier')


@admin.register(MouvementConsignation)
class MouvementConsignationAdmin(admin.ModelAdmin):
    list_display = ('consignation', 'type_mouvement', 'montant', 'date_mouvement', 'mode_paiement')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('consignation__reference', 'observations')
    date_hierarchy = 'date_mouvement'
    raw_id_fields = ('consignation', 'operation')


@admin.register(CompteBancaire)
class CompteBancaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'banque', 'numero_compte', 'type_compte', 'solde_actuel', 'actif')
    list_filter = ('banque', 'type_compte', 'actif')
    search_fields = ('nom', 'banque', 'numero_compte', 'iban')
    list_editable = ('actif',)


@admin.register(RapprochementBancaire)
class RapprochementBancaireAdmin(admin.ModelAdmin):
    list_display = ('compte', 'date_debut', 'date_fin', 'solde_releve', 'solde_comptable', 'ecart', 'statut')
    list_filter = ('compte', 'statut')
    date_hierarchy = 'date_fin'
    readonly_fields = ('ecart', 'date_creation', 'date_modification', 'date_validation')


@admin.register(LigneRapprochement)
class LigneRapprochementAdmin(admin.ModelAdmin):
    list_display = ('rapprochement', 'date_releve', 'libelle_releve', 'montant_releve', 'operation', 'statut')
    list_filter = ('statut', 'rapprochement')
    search_fields = ('libelle_releve',)
    raw_id_fields = ('rapprochement', 'operation')


@admin.register(AuditTresorerie)
class AuditTresorerieAdmin(admin.ModelAdmin):
    list_display = ('action', 'entite_type', 'entite_reference', 'utilisateur', 'date_creation')
    list_filter = ('action', 'entite_type', 'date_creation')
    search_fields = ('entite_reference', 'description')
    date_hierarchy = 'date_creation'
    readonly_fields = ('action', 'entite_type', 'entite_id', 'entite_reference', 'description',
                       'donnees_avant', 'donnees_apres', 'utilisateur', 'adresse_ip', 'date_creation')

"""
Administration Django pour le module Citations
"""

from django.contrib import admin
from .models import (
    Localite, BaremeTarifaire, AutoriteRequerante, CeduleReception,
    DestinataireCedule, ActeSignification, FraisSignification,
    Memoire, LigneMemoire, ValidationMemoire, RegistreParquet,
    ConfigurationCitations
)


# =============================================================================
# LOCALITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS
# =============================================================================

@admin.register(Localite)
class LocaliteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'commune', 'departement', 'distance_parakou', 'distance_cotonou', 'actif')
    list_filter = ('departement', 'actif')
    search_fields = ('nom', 'commune', 'departement')
    ordering = ('nom',)


# =============================================================================
# BARÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMES TARIFAIRES
# =============================================================================

@admin.register(BaremeTarifaire)
class BaremeTarifaireAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'type_bareme', 'montant', 'article_reference', 'actif')
    list_filter = ('type_bareme', 'actif')
    search_fields = ('code', 'libelle')
    ordering = ('type_bareme', 'code')


# =============================================================================
# AUTORITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS REQUÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂRANTES
# =============================================================================

@admin.register(AutoriteRequerante)
class AutoriteRequeranteAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'sigle', 'type_autorite', 'ville', 'actif')
    list_filter = ('type_autorite', 'actif')
    search_fields = ('nom', 'sigle', 'code')
    ordering = ('nom',)


# =============================================================================
# CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES DE CITATION
# =============================================================================

class DestinataireCeduleInline(admin.TabularInline):
    model = DestinataireCedule
    extra = 1
    fields = ('type_destinataire', 'type_personne', 'nom', 'prenoms', 'raison_sociale', 'localite', 'distance_km')


@admin.register(CeduleReception)
class CeduleReceptionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'numero_parquet', 'autorite_requerante', 'date_reception', 'date_audience', 'urgence', 'statut')
    list_filter = ('statut', 'urgence', 'autorite_requerante', 'nature_acte')
    search_fields = ('reference', 'numero_parquet', 'nature_infraction')
    date_hierarchy = 'date_reception'
    ordering = ('-date_reception',)
    inlines = [DestinataireCeduleInline]

    fieldsets = (
        ('Informations gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rales', {
            'fields': ('reference', 'date_reception', 'autorite_requerante', 'urgence', 'statut')
        }),
        ('Affaire', {
            'fields': ('numero_parquet', 'nature_infraction', 'nature_acte', 'juridiction')
        }),
        ('Audience', {
            'fields': ('date_audience', 'heure_audience')
        }),
        ('Documents', {
            'fields': ('nombre_pieces_jointes', 'document_cedule', 'observations')
        }),
    )


# =============================================================================
# DESTINATAIRES
# =============================================================================

@admin.register(DestinataireCedule)
class DestinataireCeduleAdmin(admin.ModelAdmin):
    list_display = ('get_nom_complet', 'cedule', 'type_destinataire', 'type_personne', 'localite', 'distance_km')
    list_filter = ('type_destinataire', 'type_personne')
    search_fields = ('nom', 'prenoms', 'raison_sociale')
    raw_id_fields = ('cedule', 'localite')


# =============================================================================
# ACTES DE SIGNIFICATION
# =============================================================================

class FraisSignificationInline(admin.StackedInline):
    model = FraisSignification
    extra = 0
    readonly_fields = ('sous_total_signification', 'total_general')


@admin.register(ActeSignification)
class ActeSignificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'date_signification', 'modalite_remise', 'nombre_copies', 'get_montant')
    list_filter = ('modalite_remise', 'date_signification')
    search_fields = ('destinataire__nom', 'destinataire__prenoms', 'destinataire__raison_sociale')
    date_hierarchy = 'date_signification'
    raw_id_fields = ('destinataire',)
    inlines = [FraisSignificationInline]

    def get_montant(self, obj):
        if hasattr(obj, 'frais_signification'):
            return f"{obj.frais_signification.total_general:,.0f} FCFA"
        return "-"
    get_montant.short_description = 'Montant'


# =============================================================================
# FRAIS DE SIGNIFICATION
# =============================================================================

@admin.register(FraisSignification)
class FraisSignificationAdmin(admin.ModelAdmin):
    list_display = ('acte', 'sous_total_signification', 'frais_transport', 'frais_mission', 'total_general')
    search_fields = ('acte__destinataire__nom',)
    readonly_fields = ('sous_total_signification', 'total_general', 'detail_calcul')


# =============================================================================
# MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES
# =============================================================================

class LigneMemoireInline(admin.TabularInline):
    model = LigneMemoire
    extra = 0
    fields = ('numero_ordre', 'cedule', 'destinataire', 'montant_ligne')
    readonly_fields = ('montant_ligne',)
    raw_id_fields = ('cedule', 'destinataire', 'acte')


class ValidationMemoireInline(admin.TabularInline):
    model = ValidationMemoire
    extra = 0
    readonly_fields = ('type_validation', 'date_validation', 'validateur', 'validateur_nom', 'observations')


@admin.register(Memoire)
class MemoireAdmin(admin.ModelAdmin):
    list_display = ('numero_memoire', 'get_periode', 'autorite_requerante', 'montant_total', 'statut')
    list_filter = ('statut', 'autorite_requerante', 'annee')
    search_fields = ('numero_memoire', 'nom_huissier')
    date_hierarchy = 'date_creation'
    ordering = ('-annee', '-mois')
    inlines = [LigneMemoireInline, ValidationMemoireInline]

    fieldsets = (
        ('Informations gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rales', {
            'fields': ('numero_memoire', 'mois', 'annee', 'autorite_requerante', 'statut')
        }),
        ('Huissier', {
            'fields': ('huissier', 'nom_huissier', 'juridiction_huissier')
        }),
        ('Montants', {
            'fields': ('montant_total', 'montant_en_lettres')
        }),
        ('Circuit de validation', {
            'fields': ('date_certification', 'date_soumission', 'date_visa', 'vise_par',
                      'date_taxe', 'taxe_par', 'date_paiement'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('document_memoire', 'reference_requisition', 'document_requisition',
                      'reference_executoire', 'document_executoire'),
            'classes': ('collapse',)
        }),
        ('Rejet', {
            'fields': ('motif_rejet',),
            'classes': ('collapse',)
        }),
    )

    def get_periode(self, obj):
        return f"{obj.get_mois_display()} {obj.annee}"
    get_periode.short_description = 'PÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©riode'


# =============================================================================
# LIGNES DE MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRE
# =============================================================================

@admin.register(LigneMemoire)
class LigneMemoireAdmin(admin.ModelAdmin):
    list_display = ('memoire', 'numero_ordre', 'cedule', 'destinataire', 'montant_ligne')
    list_filter = ('memoire__annee', 'memoire__mois')
    search_fields = ('memoire__numero_memoire', 'cedule__numero_parquet')
    raw_id_fields = ('memoire', 'cedule', 'destinataire', 'acte')


# =============================================================================
# REGISTRE PARQUET
# =============================================================================

@admin.register(RegistreParquet)
class RegistreParquetAdmin(admin.ModelAdmin):
    list_display = ('reference_affaire', 'nature_diligence', 'date_acte', 'montant_emoluments')
    list_filter = ('date_acte',)
    search_fields = ('reference_affaire', 'nature_diligence')
    date_hierarchy = 'date_acte'


# =============================================================================
# CONFIGURATION
# =============================================================================

@admin.register(ConfigurationCitations)
class ConfigurationCitationsAdmin(admin.ModelAdmin):
    list_display = ('ville_residence', 'tarif_km', 'seuil_transport_km', 'seuil_mission_km')

    fieldsets = (
        ('RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sidence', {
            'fields': ('ville_residence',)
        }),
        ('BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes Article 81', {
            'fields': ('tarif_premier_original', 'tarif_deuxieme_original', 'tarif_copie',
                      'tarif_mention_repertoire', 'tarif_vacation')
        }),
        ('BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes Articles 82, 45, 89', {
            'fields': ('tarif_role', 'tarif_km')
        }),
        ('Seuils de distance', {
            'fields': ('seuil_transport_km', 'seuil_mission_km')
        }),
        ('Frais de mission Groupe II', {
            'fields': ('frais_mission_1_repas', 'frais_mission_2_repas', 'frais_mission_journee')
        }),
        ('ParamÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨tres de gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ration', {
            'fields': ('prefixe_cedule', 'prefixe_memoire')
        }),
    )

    def has_add_permission(self, request):
        # EmpÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªcher l'ajout de plusieurs configurations
        return not ConfigurationCitations.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

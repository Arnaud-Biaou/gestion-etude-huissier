from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CloudConnection, DossierVirtuel, Document, VersionDocument,
    ModeleDocument, SignatureElectronique, PartageDocument,
    AccesPartage, AuditDocument, GenerationDocument,
    ConfigurationDocuments, NumeroActe
)


@admin.register(CloudConnection)
class CloudConnectionAdmin(admin.ModelAdmin):
    list_display = ['nom_compte', 'service', 'statut', 'est_principal', 'pourcentage_affiche', 'derniere_sync']
    list_filter = ['service', 'statut', 'est_principal']
    search_fields = ['nom_compte', 'email_compte']
    readonly_fields = ['id', 'date_connexion', 'derniere_sync']

    def pourcentage_affiche(self, obj):
        pct = obj.pourcentage_utilise
        color = '#2f855a' if pct < 70 else ('#c05621' if pct < 90 else '#c53030')
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, pct
        )
    pourcentage_affiche.short_description = "Utilisation"


@admin.register(DossierVirtuel)
class DossierVirtuelAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_dossier', 'chemin', 'dossier_juridique', 'est_systeme']
    list_filter = ['type_dossier', 'est_systeme']
    search_fields = ['nom', 'chemin']
    raw_id_fields = ['parent', 'dossier_juridique']
    readonly_fields = ['id', 'date_creation', 'date_modification']


class VersionDocumentInline(admin.TabularInline):
    model = VersionDocument
    extra = 0
    readonly_fields = ['numero_version', 'taille', 'hash_md5', 'date', 'auteur']


class SignatureInline(admin.TabularInline):
    model = SignatureElectronique
    extra = 0
    readonly_fields = ['date_demande', 'date_signature']


class PartageInline(admin.TabularInline):
    model = PartageDocument
    extra = 0
    readonly_fields = ['token', 'nombre_acces', 'date_creation']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_document', 'statut', 'taille_affichee', 'dossier_juridique', 'version', 'date_creation']
    list_filter = ['type_document', 'statut', 'est_genere', 'est_modele']
    search_fields = ['nom', 'nom_original', 'description', 'contenu_texte']
    raw_id_fields = ['dossier', 'dossier_juridique', 'document_parent']
    readonly_fields = ['id', 'hash_md5', 'hash_sha256', 'date_creation', 'date_modification']
    inlines = [VersionDocumentInline, SignatureInline, PartageInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'nom_original', 'type_document', 'description', 'statut')
        }),
        ('Fichier', {
            'fields': ('fichier', 'taille', 'mime_type', 'extension')
        }),
        ('Organisation', {
            'fields': ('dossier', 'dossier_juridique')
        }),
        ('Cloud', {
            'fields': ('cloud_connection', 'cloud_id', 'chemin_cloud', 'chemin_local'),
            'classes': ('collapse',)
        }),
        ('Versioning', {
            'fields': ('version', 'document_parent'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('hash_md5', 'hash_sha256', 'est_modele', 'est_genere', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Traçabilité', {
            'fields': ('cree_par', 'modifie_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def taille_affichee(self, obj):
        return obj.taille_humaine
    taille_affichee.short_description = "Taille"


@admin.register(ModeleDocument)
class ModeleDocumentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'type_modele', 'format_sortie', 'actif', 'est_systeme', 'ordre_affichage']
    list_filter = ['type_modele', 'format_sortie', 'actif', 'est_systeme']
    search_fields = ['nom', 'code', 'description']
    readonly_fields = ['id', 'date_creation', 'date_modification']
    ordering = ['ordre_affichage', 'nom']

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'type_modele', 'description', 'actif', 'est_systeme', 'ordre_affichage')
        }),
        ('Template', {
            'fields': ('contenu_template', 'format_sortie', 'fichier_template')
        }),
        ('Variables', {
            'fields': ('variables', 'variables_exemple'),
            'classes': ('collapse',)
        }),
        ('Mise en page', {
            'fields': ('avec_entete', 'avec_pied_page', 'orientation', 'marge_haut', 'marge_bas', 'marge_gauche', 'marge_droite'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SignatureElectronique)
class SignatureElectroniqueAdmin(admin.ModelAdmin):
    list_display = ['signataire_nom', 'document', 'type_signature', 'statut', 'date_demande', 'date_signature']
    list_filter = ['type_signature', 'statut']
    search_fields = ['signataire_nom', 'signataire_email', 'document__nom']
    raw_id_fields = ['document', 'signataire_utilisateur']
    readonly_fields = ['id', 'date_demande', 'hash_document', 'certificat']


@admin.register(PartageDocument)
class PartageDocumentAdmin(admin.ModelAdmin):
    list_display = ['get_objet', 'type_partage', 'destinataire_nom', 'nombre_acces', 'est_expire_affiche', 'date_creation']
    list_filter = ['type_partage', 'actif']
    search_fields = ['destinataire_nom', 'destinataire_email', 'token']
    raw_id_fields = ['document', 'dossier']
    readonly_fields = ['id', 'token', 'nombre_acces', 'date_creation']

    def get_objet(self, obj):
        return obj.document or obj.dossier
    get_objet.short_description = "Document/Dossier"

    def est_expire_affiche(self, obj):
        if obj.est_expire:
            return format_html('<span style="color: #c53030;">Expiré</span>')
        return format_html('<span style="color: #2f855a;">Actif</span>')
    est_expire_affiche.short_description = "État"


@admin.register(AuditDocument)
class AuditDocumentAdmin(admin.ModelAdmin):
    list_display = ['action', 'get_objet', 'utilisateur', 'date', 'ip']
    list_filter = ['action', 'date']
    search_fields = ['document__nom', 'dossier__nom', 'utilisateur__username']
    readonly_fields = ['id', 'document', 'dossier', 'action', 'details', 'utilisateur', 'date', 'ip', 'user_agent']
    date_hierarchy = 'date'

    def get_objet(self, obj):
        return obj.document or obj.dossier
    get_objet.short_description = "Document/Dossier"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GenerationDocument)
class GenerationDocumentAdmin(admin.ModelAdmin):
    list_display = ['modele', 'statut', 'dossier_juridique', 'date_demande', 'duree_generation']
    list_filter = ['statut', 'modele__type_modele']
    search_fields = ['modele__nom', 'dossier_juridique__reference']
    raw_id_fields = ['modele', 'document_genere', 'dossier_juridique', 'facture']
    readonly_fields = ['id', 'date_demande', 'date_generation', 'duree_generation']


@admin.register(ConfigurationDocuments)
class ConfigurationDocumentsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Stockage', {
            'fields': ('stockage_local_path', 'limite_upload_mo', 'types_autorises')
        }),
        ('Étude', {
            'fields': ('logo_etude', 'nom_etude', 'adresse_etude', 'telephone_etude', 'email_etude', 'ifu_etude', 'rccm_etude')
        }),
        ('Huissier', {
            'fields': ('nom_huissier', 'qualite_huissier', 'signature_huissier', 'cachet_etude')
        }),
        ('Partage', {
            'fields': ('duree_partage_defaut', 'autoriser_partage_public')
        }),
        ('Corbeille', {
            'fields': ('duree_retention_corbeille',)
        }),
        ('OCR', {
            'fields': ('ocr_actif',)
        }),
        ('Audit', {
            'fields': ('audit_actif', 'duree_retention_audit')
        }),
    )

    def has_add_permission(self, request):
        # Singleton pattern
        return not ConfigurationDocuments.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NumeroActe)
class NumeroActeAdmin(admin.ModelAdmin):
    list_display = ['annee', 'dernier_numero']
    ordering = ['-annee']


# =============================================================================
# VERSION DOCUMENT (STANDALONE)
# =============================================================================

@admin.register(VersionDocument)
class VersionDocumentAdmin(admin.ModelAdmin):
    list_display = ['document', 'numero_version', 'taille_affichee', 'auteur', 'date']
    list_filter = ['date']
    search_fields = ['document__nom', 'auteur__username', 'commentaire']
    raw_id_fields = ['document', 'auteur']
    readonly_fields = ['id', 'numero_version', 'taille', 'hash_md5', 'date']
    date_hierarchy = 'date'

    def taille_affichee(self, obj):
        if obj.taille:
            if obj.taille < 1024:
                return f"{obj.taille} o"
            elif obj.taille < 1024 * 1024:
                return f"{obj.taille / 1024:.1f} Ko"
            else:
                return f"{obj.taille / (1024 * 1024):.1f} Mo"
        return "-"
    taille_affichee.short_description = "Taille"


# =============================================================================
# ACCÈS PARTAGE (STANDALONE)
# =============================================================================

@admin.register(AccesPartage)
class AccesPartageAdmin(admin.ModelAdmin):
    list_display = ['partage', 'date_acces', 'ip', 'action']
    list_filter = ['action', 'date_acces']
    search_fields = ['partage__token', 'ip', 'user_agent']
    raw_id_fields = ['partage']
    readonly_fields = ['id', 'date_acces']
    date_hierarchy = 'date_acces'

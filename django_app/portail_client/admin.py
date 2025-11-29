"""
Administration Django pour le Portail Client
"""

from django.contrib import admin
from .models import (
    ClientPortail,
    AccesDocument,
    MessagePortail,
    NotificationClient,
    DemandeContact
)


@admin.register(ClientPortail)
class ClientPortailAdmin(admin.ModelAdmin):
    list_display = [
        'code_client',
        'nom_complet',
        'email',
        'type_client',
        'est_actif',
        'compte_bloque',
        'date_derniere_connexion'
    ]
    list_filter = ['type_client', 'est_actif', 'compte_bloque', 'email_verifie']
    search_fields = ['code_client', 'nom_complet', 'email', 'telephone']
    readonly_fields = ['code_client', 'date_derniere_connexion', 'tentatives_connexion', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('code_client', 'email', 'telephone', 'nom_complet', 'type_client')
        }),
        ('Liaison', {
            'fields': ('partie',)
        }),
        ('Sécurité', {
            'fields': ('est_actif', 'compte_bloque', 'email_verifie', 'tentatives_connexion', 'date_derniere_connexion')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.code_client:
            obj.code_client = ClientPortail.generer_code_client()
        super().save_model(request, obj, form, change)

    actions = ['debloquer_comptes', 'activer_comptes', 'desactiver_comptes']

    @admin.action(description="Débloquer les comptes sélectionnés")
    def debloquer_comptes(self, request, queryset):
        updated = queryset.update(compte_bloque=False, tentatives_connexion=0)
        self.message_user(request, f"{updated} compte(s) débloqué(s).")

    @admin.action(description="Activer les comptes sélectionnés")
    def activer_comptes(self, request, queryset):
        updated = queryset.update(est_actif=True)
        self.message_user(request, f"{updated} compte(s) activé(s).")

    @admin.action(description="Désactiver les comptes sélectionnés")
    def desactiver_comptes(self, request, queryset):
        updated = queryset.update(est_actif=False)
        self.message_user(request, f"{updated} compte(s) désactivé(s).")


@admin.register(AccesDocument)
class AccesDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'titre',
        'client',
        'type_document',
        'dossier',
        'paiement_requis',
        'est_paye',
        'nombre_telechargements',
        'date_mise_disposition'
    ]
    list_filter = ['type_document', 'paiement_requis', 'est_paye']
    search_fields = ['titre', 'description', 'client__nom_complet', 'client__code_client']
    raw_id_fields = ['client', 'dossier']
    readonly_fields = ['date_mise_disposition', 'date_premier_telechargement', 'nombre_telechargements']


@admin.register(MessagePortail)
class MessagePortailAdmin(admin.ModelAdmin):
    list_display = ['sujet', 'client', 'est_de_client', 'dossier', 'lu', 'created_at']
    list_filter = ['est_de_client', 'lu', 'created_at']
    search_fields = ['sujet', 'contenu', 'client__nom_complet']
    raw_id_fields = ['client', 'dossier']
    readonly_fields = ['created_at', 'date_lecture']

    actions = ['marquer_comme_lu', 'marquer_comme_non_lu']

    @admin.action(description="Marquer comme lu")
    def marquer_comme_lu(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(lu=True, date_lecture=timezone.now())
        self.message_user(request, f"{updated} message(s) marqué(s) comme lu(s).")

    @admin.action(description="Marquer comme non lu")
    def marquer_comme_non_lu(self, request, queryset):
        updated = queryset.update(lu=False, date_lecture=None)
        self.message_user(request, f"{updated} message(s) marqué(s) comme non lu(s).")


@admin.register(NotificationClient)
class NotificationClientAdmin(admin.ModelAdmin):
    list_display = ['titre', 'client', 'type_notification', 'lu', 'created_at']
    list_filter = ['type_notification', 'lu', 'created_at']
    search_fields = ['titre', 'message', 'client__nom_complet']
    raw_id_fields = ['client']
    readonly_fields = ['created_at']


@admin.register(DemandeContact)
class DemandeContactAdmin(admin.ModelAdmin):
    list_display = ['nom', 'email', 'telephone', 'statut', 'created_at', 'traite_par']
    list_filter = ['statut', 'created_at']
    search_fields = ['nom', 'email', 'telephone', 'message']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Informations du contact', {
            'fields': ('nom', 'email', 'telephone', 'message')
        }),
        ('Traitement', {
            'fields': ('statut', 'traite_par', 'date_traitement', 'notes_internes')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['marquer_traite', 'marquer_archive']

    @admin.action(description="Marquer comme traité")
    def marquer_traite(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(statut='traite', traite_par=request.user, date_traitement=timezone.now())
        self.message_user(request, f"{updated} demande(s) marquée(s) comme traitée(s).")

    @admin.action(description="Archiver")
    def marquer_archive(self, request, queryset):
        updated = queryset.update(statut='archive')
        self.message_user(request, f"{updated} demande(s) archivée(s).")

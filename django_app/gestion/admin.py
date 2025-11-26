from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Collaborateur, Partie, Dossier, Facture,
    ActeProcedure, HistoriqueCalcul, TauxLegal, MessageChatbot
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

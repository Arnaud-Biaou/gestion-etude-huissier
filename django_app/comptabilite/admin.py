from django.contrib import admin
from .models import (
    ExerciceComptable, CompteComptable, Journal, EcritureComptable,
    LigneEcriture, TypeOperation, ParametrageFiscal, DeclarationTVA,
    RapportComptable, ConfigurationComptable, Lettrage
)


@admin.register(ExerciceComptable)
class ExerciceComptableAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'date_debut', 'date_fin', 'statut', 'est_premier_exercice')
    list_filter = ('statut', 'est_premier_exercice')
    search_fields = ('libelle',)
    ordering = ('-date_debut',)


@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display = ('numero', 'libelle', 'classe', 'type_compte', 'solde_normal', 'actif')
    list_filter = ('classe', 'type_compte', 'solde_normal', 'actif')
    search_fields = ('numero', 'libelle')
    ordering = ('numero',)
    list_per_page = 50


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'type_journal', 'actif')
    list_filter = ('type_journal', 'actif')
    search_fields = ('code', 'libelle')
    ordering = ('code',)


class LigneEcritureInline(admin.TabularInline):
    model = LigneEcriture
    extra = 2
    raw_id_fields = ('compte',)


@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ('numero', 'date', 'journal', 'libelle', 'statut', 'origine', 'total_debit_display')
    list_filter = ('statut', 'origine', 'journal', 'exercice')
    search_fields = ('numero', 'libelle', 'reference')
    date_hierarchy = 'date'
    ordering = ('-date', '-numero')
    inlines = [LigneEcritureInline]
    raw_id_fields = ('facture', 'dossier', 'cree_par')

    def total_debit_display(self, obj):
        return f"{obj.total_debit:,.0f} FCFA"
    total_debit_display.short_description = 'Montant'


@admin.register(LigneEcriture)
class LigneEcritureAdmin(admin.ModelAdmin):
    list_display = ('ecriture', 'compte', 'libelle', 'debit', 'credit')
    list_filter = ('compte__classe',)
    search_fields = ('libelle', 'ecriture__numero', 'compte__numero')
    raw_id_fields = ('ecriture', 'compte')


@admin.register(TypeOperation)
class TypeOperationAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'journal', 'compte_debit', 'compte_credit', 'ordre_affichage', 'actif')
    list_filter = ('journal', 'actif')
    search_fields = ('code', 'libelle')
    ordering = ('ordre_affichage',)
    raw_id_fields = ('compte_debit', 'compte_credit')


@admin.register(ParametrageFiscal)
class ParametrageFiscalAdmin(admin.ModelAdmin):
    list_display = ('exercice', 'taux_tva', 'periodicite_declaration_tva')
    raw_id_fields = ('compte_tva_collectee', 'compte_tva_deductible', 'compte_tva_a_payer')


@admin.register(DeclarationTVA)
class DeclarationTVAAdmin(admin.ModelAdmin):
    list_display = ('exercice', 'periode_debut', 'periode_fin', 'tva_collectee', 'tva_deductible', 'tva_a_payer', 'statut')
    list_filter = ('statut', 'exercice')
    ordering = ('-periode_debut',)


@admin.register(RapportComptable)
class RapportComptableAdmin(admin.ModelAdmin):
    list_display = ('type_rapport', 'exercice', 'periode_debut', 'periode_fin', 'date_generation')
    list_filter = ('type_rapport', 'exercice')
    ordering = ('-date_generation',)


@admin.register(ConfigurationComptable)
class ConfigurationComptableAdmin(admin.ModelAdmin):
    list_display = ('est_configure', 'date_configuration', 'mode_saisie_defaut')

    def has_add_permission(self, request):
        # Ne permettre qu'une seule instance
        return not ConfigurationComptable.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Lettrage)
class LettrageAdmin(admin.ModelAdmin):
    list_display = ('code', 'compte', 'montant', 'est_partiel', 'date_lettrage', 'lettre_par')
    list_filter = ('est_partiel', 'compte__classe', 'date_lettrage')
    search_fields = ('code', 'compte__numero', 'compte__libelle')
    ordering = ('-date_lettrage',)
    filter_horizontal = ('lignes',)
    raw_id_fields = ('compte', 'lettre_par')

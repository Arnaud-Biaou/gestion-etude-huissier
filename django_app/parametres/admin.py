"""
Administration Django pour le module Paramètres
"""

from django.contrib import admin
from .models import (
    ConfigurationEtude, SiteAgence, TypeDossier, StatutDossier,
    ModeleDocument, Localite, TauxLegal, JourFerie, TypeActe,
    Juridiction, HistoriqueSauvegarde, JournalModification, ModeleTypeBail
)


@admin.register(ConfigurationEtude)
class ConfigurationEtudeAdmin(admin.ModelAdmin):
    list_display = ['nom_etude', 'adresse_ville', 'email', 'est_configure', 'date_modification']
    readonly_fields = ['date_modification', 'date_configuration']
    fieldsets = (
        ('Identité de l\'étude', {
            'fields': (
                'nom_etude', 'titre', 'juridiction',
                'adresse_rue', 'adresse_quartier', 'adresse_ville', 'adresse_bp',
                'telephone_fixe', 'telephone_mobile1', 'telephone_mobile2',
                'email', 'site_web', 'numero_ifu', 'numero_agrement', 'date_installation'
            )
        }),
        ('Logo et couleurs', {
            'fields': ('logo', 'couleur_principale', 'couleur_secondaire')
        }),
        ('Coordonnées bancaires', {
            'fields': (
                'banque_nom', 'banque_code', 'banque_guichet', 'banque_compte',
                'banque_cle', 'banque_iban', 'banque_titulaire',
                'mobile_money_operateur', 'mobile_money_numero'
            ),
            'classes': ['collapse']
        }),
        ('Paramètres dossiers', {
            'fields': ('dossier_prefixe', 'dossier_numero_depart'),
            'classes': ['collapse']
        }),
        ('Paramètres facturation', {
            'fields': (
                'facture_prefixe', 'tva_applicable', 'tva_taux',
                'mecef_nim', 'mecef_token', 'mecef_mode',
                'facture_mentions_legales', 'facture_conditions_paiement',
                'facture_delai_paiement', 'facture_penalites_retard'
            ),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ('est_configure', 'date_configuration', 'date_modification', 'modifie_par'),
            'classes': ['collapse']
        }),
    )


@admin.register(SiteAgence)
class SiteAgenceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'adresse', 'telephone', 'responsable', 'est_principal', 'actif']
    list_filter = ['est_principal', 'actif']
    search_fields = ['nom', 'adresse', 'responsable']


@admin.register(TypeDossier)
class TypeDossierAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'couleur', 'actif', 'ordre']
    list_filter = ['actif']
    search_fields = ['code', 'libelle']
    ordering = ['ordre', 'libelle']


@admin.register(StatutDossier)
class StatutDossierAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'couleur', 'est_cloture', 'actif', 'ordre']
    list_filter = ['est_cloture', 'actif']
    search_fields = ['code', 'libelle']
    ordering = ['ordre', 'libelle']


@admin.register(ModeleDocument)
class ModeleDocumentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie', 'actif', 'date_creation', 'date_modification']
    list_filter = ['categorie', 'actif']
    search_fields = ['nom']
    readonly_fields = ['date_creation', 'date_modification']


@admin.register(Localite)
class LocaliteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'departement', 'commune', 'distance_km', 'actif']
    list_filter = ['departement', 'actif']
    search_fields = ['nom', 'commune']
    ordering = ['departement', 'nom']


@admin.register(TauxLegal)
class TauxLegalAdmin(admin.ModelAdmin):
    list_display = ['annee', 'semestre', 'taux', 'date_debut', 'date_fin', 'source']
    list_filter = ['annee', 'semestre']
    ordering = ['-annee', '-semestre']


@admin.register(JourFerie)
class JourFerieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'jour_mois', 'mois', 'est_mobile', 'actif']
    list_filter = ['est_mobile', 'actif']
    search_fields = ['nom']


@admin.register(TypeActe)
class TypeActeAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'categorie', 'montant_defaut', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['code', 'libelle']


@admin.register(Juridiction)
class JuridictionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type', 'ville', 'telephone', 'actif']
    list_filter = ['type', 'ville', 'actif']
    search_fields = ['nom', 'ville']


@admin.register(HistoriqueSauvegarde)
class HistoriqueSauvegardeAdmin(admin.ModelAdmin):
    list_display = ['date', 'taille_formatee', 'statut', 'emplacement']
    list_filter = ['statut']
    readonly_fields = ['date', 'taille', 'statut', 'emplacement', 'message']
    ordering = ['-date']


@admin.register(JournalModification)
class JournalModificationAdmin(admin.ModelAdmin):
    list_display = ['date', 'utilisateur', 'section', 'champ']
    list_filter = ['section', 'utilisateur']
    search_fields = ['champ', 'ancienne_valeur', 'nouvelle_valeur']
    readonly_fields = ['date', 'utilisateur', 'section', 'champ', 'ancienne_valeur', 'nouvelle_valeur']
    ordering = ['-date']


@admin.register(ModeleTypeBail)
class ModeleTypeBailAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'modele_document', 'actif']
    list_filter = ['actif']
    search_fields = ['code', 'libelle']

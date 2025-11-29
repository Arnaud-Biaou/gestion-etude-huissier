"""
Administration Django pour le module Paramètres
"""

from django.contrib import admin
from .models import (
    ConfigurationEtude, SiteAgence, TypeDossier, StatutDossier,
    ModeleDocument, Localite, TauxLegal, JourFerie, TypeActe,
    Juridiction, HistoriqueSauvegarde, JournalModification, ModeleTypeBail,
    TrancheIPTS, ConfigurationEnteteDocument, EnteteJuridiction
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
    list_display = ['annee', 'taux', 'date_publication', 'reference_arrete']
    list_filter = ['annee']
    ordering = ['-annee']


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
    list_display = ['nom_court', 'type_juridiction', 'ville', 'cour_appel_rattachement', 'actif', 'ordre']
    list_filter = ['type_juridiction', 'actif', 'cour_appel_rattachement']
    search_fields = ['nom', 'nom_court', 'ville']
    ordering = ['ordre']

    fieldsets = (
        ('Identification', {
            'fields': ('nom', 'nom_court', 'type_juridiction', 'classe_tpi', 'ville', 'adresse', 'telephone')
        }),
        ('Hierarchie', {
            'fields': ('cour_appel_rattachement',),
            'description': "Pour les TPI, selectionnez la Cour d'Appel de rattachement"
        }),
        ('Autorites - Parquet', {
            'fields': ('titre_procureur', 'nom_procureur', 'titre_procureur_general', 'nom_procureur_general')
        }),
        ('Autorites - Siege', {
            'fields': ('titre_president', 'nom_president', 'nom_president_cour')
        }),
        ('Parametres', {
            'fields': ('actif', 'ordre')
        }),
    )


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


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLES FISCAUX ET PAIE
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(TrancheIPTS)
class TrancheIPTSAdmin(admin.ModelAdmin):
    """Administration du barème IPTS (Impôt Progressif sur Traitements et Salaires)"""
    list_display = ['ordre', 'montant_min', 'montant_max', 'taux', 'date_debut', 'date_fin', 'est_actif']
    list_filter = ['est_actif', 'date_debut']
    ordering = ['ordre']
    fieldsets = (
        ('Tranche', {
            'fields': ('ordre', 'montant_min', 'montant_max', 'taux')
        }),
        ('Période d\'application', {
            'fields': ('date_debut', 'date_fin', 'est_actif')
        }),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# EN-TÊTES ET PIEDS DE PAGE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(ConfigurationEnteteDocument)
class ConfigurationEnteteDocumentAdmin(admin.ModelAdmin):
    """Configuration des en-têtes et pieds de page pour les documents"""
    list_display = ['type_document', 'utiliser_entete_image', 'utiliser_pied_image', 'est_actif', 'updated_at']
    list_filter = ['type_document', 'est_actif', 'utiliser_entete_image']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Type de document', {
            'fields': ('type_document', 'est_actif')
        }),
        ('En-tête', {
            'fields': (
                'utiliser_entete_image', 'entete_image', 'entete_hauteur',
                'entete_marge_haut', 'entete_marge_gauche', 'entete_marge_droite', 'entete_centrer'
            ),
            'classes': ['collapse']
        }),
        ('Pied de page', {
            'fields': (
                'utiliser_pied_image', 'pied_image', 'pied_hauteur',
                'pied_marge_bas', 'pied_centrer', 'pied_texte'
            ),
            'classes': ['collapse']
        }),
        ('Marges du corps', {
            'fields': ('corps_marge_haut', 'corps_marge_bas'),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(EnteteJuridiction)
class EnteteJuridictionAdmin(admin.ModelAdmin):
    """Configuration des en-têtes hiérarchiques des juridictions"""
    list_display = ['code', 'nom', 'niveau', 'juridiction_superieure', 'afficher_embleme', 'est_actif', 'ordre_affichage']
    list_filter = ['niveau', 'est_actif', 'afficher_embleme']
    search_fields = ['code', 'nom', 'nom_complet']
    ordering = ['niveau', 'ordre_affichage']
    raw_id_fields = ['juridiction_superieure']

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'nom', 'nom_complet', 'niveau')
        }),
        ('Hiérarchie', {
            'fields': ('juridiction_superieure',)
        }),
        ('Affichage', {
            'fields': ('afficher_embleme', 'devise', 'logo', 'ordre_affichage')
        }),
        ('Statut', {
            'fields': ('est_actif',)
        }),
    )

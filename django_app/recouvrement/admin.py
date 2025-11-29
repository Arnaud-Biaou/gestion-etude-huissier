"""
Admin du module Recouvrement de Créances
"""

from django.contrib import admin
from .models import (
    DossierRecouvrement,
    PointGlobalCreancier,
    EnvoiAutomatiquePoint,
    PaiementRecouvrement,
    ImputationManuelle,
    HistoriqueActionRecouvrement,
)


@admin.register(DossierRecouvrement)
class DossierRecouvrementAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'creancier', 'debiteur', 'type_recouvrement',
        'statut', 'montant_principal', 'montant_encaisse', 'date_ouverture'
    ]
    list_filter = ['type_recouvrement', 'statut', 'date_ouverture']
    search_fields = ['reference', 'creancier__nom', 'debiteur__nom']
    date_hierarchy = 'date_ouverture'
    readonly_fields = ['date_creation', 'date_modification']


@admin.register(PointGlobalCreancier)
class PointGlobalCreancierAdmin(admin.ModelAdmin):
    list_display = [
        'creancier', 'date_generation', 'periode_debut', 'periode_fin',
        'nombre_dossiers', 'total_creances', 'taux_recouvrement', 'statut'
    ]
    list_filter = ['statut', 'date_generation']
    search_fields = ['creancier__nom']
    date_hierarchy = 'date_generation'
    readonly_fields = [
        'date_generation', 'nombre_dossiers', 'nombre_en_cours',
        'nombre_clotures_succes', 'nombre_clotures_echec',
        'nombre_amiable', 'nombre_force', 'total_creances',
        'total_encaisse', 'total_reverse', 'total_reste_du',
        'taux_recouvrement', 'total_frais_procedure', 'total_emoluments',
        'total_honoraires_amiable', 'total_retenu'
    ]


@admin.register(EnvoiAutomatiquePoint)
class EnvoiAutomatiquePointAdmin(admin.ModelAdmin):
    list_display = ['creancier', 'actif', 'frequence', 'jour_envoi', 'dernier_envoi', 'prochain_envoi']
    list_filter = ['actif', 'frequence']
    search_fields = ['creancier__nom']


@admin.register(PaiementRecouvrement)
class PaiementRecouvrementAdmin(admin.ModelAdmin):
    list_display = [
        'dossier', 'date_paiement', 'montant', 'mode_paiement',
        'impute_principal', 'impute_interets', 'montant_a_reverser', 'est_reverse'
    ]
    list_filter = ['mode_paiement', 'est_reverse', 'date_paiement']
    search_fields = ['dossier__reference', 'reference_paiement']
    date_hierarchy = 'date_paiement'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ImputationManuelle)
class ImputationManuelleAdmin(admin.ModelAdmin):
    list_display = ['paiement', 'date_imputation', 'type_imputation', 'montant']
    list_filter = ['type_imputation', 'date_imputation']
    readonly_fields = ['created_at']


@admin.register(HistoriqueActionRecouvrement)
class HistoriqueActionRecouvrementAdmin(admin.ModelAdmin):
    list_display = ['dossier', 'date_action', 'type_action', 'cree_par']
    list_filter = ['type_action', 'date_action']
    search_fields = ['dossier__reference', 'description']
    readonly_fields = ['date_action']

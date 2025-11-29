"""
Admin du module Recouvrement de Créances
"""

from django.contrib import admin
from .models import DossierRecouvrement, PointGlobalCreancier, EnvoiAutomatiquePoint


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

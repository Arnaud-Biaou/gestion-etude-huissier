"""
Administration du module Trésorerie
"""

from django.contrib import admin
from .models import (
    CompteBancaire, MouvementTresorerie, RapprochementBancaire,
    PrevisionTresorerie, AlerteTresorerie
)


@admin.register(CompteBancaire)
class CompteBancaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'banque', 'type_compte', 'solde_actuel', 'statut']
    list_filter = ['type_compte', 'statut', 'banque']
    search_fields = ['nom', 'numero', 'banque']
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(MouvementTresorerie)
class MouvementTresorerieAdmin(admin.ModelAdmin):
    list_display = ['date_mouvement', 'compte', 'type_mouvement', 'montant', 'libelle', 'statut']
    list_filter = ['type_mouvement', 'categorie', 'statut', 'mode_paiement', 'compte']
    search_fields = ['libelle', 'reference', 'tiers']
    date_hierarchy = 'date_mouvement'
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(RapprochementBancaire)
class RapprochementBancaireAdmin(admin.ModelAdmin):
    list_display = ['compte', 'date_fin', 'solde_releve', 'solde_comptable', 'ecart', 'statut']
    list_filter = ['statut', 'compte']
    date_hierarchy = 'date_fin'
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(PrevisionTresorerie)
class PrevisionTresorerieAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'type_prevision', 'montant', 'date_prevue', 'statut']
    list_filter = ['type_prevision', 'statut', 'periodicite', 'compte']
    search_fields = ['libelle']
    date_hierarchy = 'date_prevue'
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(AlerteTresorerie)
class AlerteTresorerieAdmin(admin.ModelAdmin):
    list_display = ['type_alerte', 'niveau', 'message', 'lue', 'traitee', 'cree_le']
    list_filter = ['type_alerte', 'niveau', 'lue', 'traitee']
    readonly_fields = ['id', 'cree_le']

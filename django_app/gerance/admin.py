"""
Administration du module Gérance Immobilière
"""

from django.contrib import admin
from .models import (
    Proprietaire, BienImmobilier, Locataire, Bail, Loyer,
    Quittance, EtatDesLieux, Incident, ReversementProprietaire
)


@admin.register(Proprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'type_proprietaire', 'telephone', 'email', 'actif']
    list_filter = ['type_proprietaire', 'actif', 'ville']
    search_fields = ['nom', 'prenom', 'telephone', 'email']
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(BienImmobilier)
class BienImmobilierAdmin(admin.ModelAdmin):
    list_display = ['reference', 'designation', 'type_bien', 'proprietaire', 'loyer_mensuel', 'statut']
    list_filter = ['type_bien', 'statut', 'ville']
    search_fields = ['reference', 'designation', 'adresse']
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(Locataire)
class LocataireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'type_locataire', 'telephone', 'email', 'actif']
    list_filter = ['type_locataire', 'actif']
    search_fields = ['nom', 'prenom', 'telephone', 'email']
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(Bail)
class BailAdmin(admin.ModelAdmin):
    list_display = ['reference', 'bien', 'locataire', 'date_debut', 'date_fin', 'loyer_mensuel', 'statut']
    list_filter = ['type_bail', 'statut']
    search_fields = ['reference', 'bien__designation', 'locataire__nom']
    date_hierarchy = 'date_debut'
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(Loyer)
class LoyerAdmin(admin.ModelAdmin):
    list_display = ['bail', 'mois', 'annee', 'montant_total', 'montant_paye', 'statut']
    list_filter = ['statut', 'annee', 'mois']
    search_fields = ['bail__reference', 'bail__locataire__nom']
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(Quittance)
class QuittanceAdmin(admin.ModelAdmin):
    list_display = ['numero', 'loyer', 'date_emission', 'montant']
    date_hierarchy = 'date_emission'
    readonly_fields = ['id', 'cree_le']


@admin.register(EtatDesLieux)
class EtatDesLieuxAdmin(admin.ModelAdmin):
    list_display = ['bail', 'type_etat', 'date_etat', 'etat_general']
    list_filter = ['type_etat', 'etat_general']
    date_hierarchy = 'date_etat'
    readonly_fields = ['id', 'cree_le']


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['titre', 'bien', 'type_incident', 'priorite', 'statut', 'date_signalement']
    list_filter = ['type_incident', 'priorite', 'statut']
    search_fields = ['titre', 'description', 'bien__designation']
    date_hierarchy = 'date_signalement'
    readonly_fields = ['id', 'cree_le', 'modifie_le']


@admin.register(ReversementProprietaire)
class ReversementProprietaireAdmin(admin.ModelAdmin):
    list_display = ['proprietaire', 'mois', 'annee', 'total_loyers', 'honoraires', 'montant_reverse', 'statut']
    list_filter = ['statut', 'annee']
    search_fields = ['proprietaire__nom']
    readonly_fields = ['id', 'cree_le', 'modifie_le']

"""
Configuration de l'administration Django pour le module Agenda
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RendezVous, Tache, Etiquette, ParticipantExterne,
    DocumentRdv, DocumentTache, RappelRdv, RappelTache,
    CommentaireTache, SousTacheChecklist, Notification,
    JourneeAgenda, ReportTache, ConfigurationAgenda,
    StatistiquesAgenda, HistoriqueAgenda,
    VueSauvegardee, ParticipationRdv
)


# =============================================================================
# INLINES
# =============================================================================

class DocumentRdvInline(admin.TabularInline):
    model = DocumentRdv
    extra = 0
    readonly_fields = ['date_ajout', 'ajoute_par']


class RappelRdvInline(admin.TabularInline):
    model = RappelRdv
    extra = 0


class DocumentTacheInline(admin.TabularInline):
    model = DocumentTache
    extra = 0
    readonly_fields = ['date_ajout', 'ajoute_par']


class RappelTacheInline(admin.TabularInline):
    model = RappelTache
    extra = 0


class CommentaireTacheInline(admin.TabularInline):
    model = CommentaireTache
    extra = 0
    readonly_fields = ['date_creation', 'auteur']


class SousTacheChecklistInline(admin.TabularInline):
    model = SousTacheChecklist
    extra = 0
    readonly_fields = ['date_completion', 'complete_par']


class ReportTacheInline(admin.TabularInline):
    model = ReportTache
    extra = 0
    readonly_fields = ['date_creation', 'reporte_par']
    fk_name = 'tache'


class ParticipationRdvInline(admin.TabularInline):
    model = ParticipationRdv
    extra = 0
    readonly_fields = ['date_reponse', 'date_notification']


# =============================================================================
# ADMIN RENDEZ-VOUS
# =============================================================================

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'type_rdv', 'date_debut_formatee', 'statut_badge',
        'priorite_badge', 'createur', 'est_actif'
    ]
    list_filter = ['type_rdv', 'statut', 'priorite', 'est_actif', 'date_debut']
    search_fields = ['titre', 'description', 'lieu']
    date_hierarchy = 'date_debut'
    readonly_fields = ['date_creation', 'date_modification']
    filter_horizontal = ['dossiers', 'collaborateurs_assignes', 'participants_externes']
    inlines = [ParticipationRdvInline, DocumentRdvInline, RappelRdvInline]

    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'type_rdv', 'description')
        }),
        ('Date et heure', {
            'fields': ('date_debut', 'date_fin', 'journee_entiere')
        }),
        ('Lieu', {
            'fields': ('lieu', 'adresse', 'latitude', 'longitude')
        }),
        ('Participants', {
            'fields': ('createur', 'collaborateurs_assignes', 'participants_externes')
        }),
        ('Dossiers liés', {
            'fields': ('dossiers',)
        }),
        ('Statut et priorité', {
            'fields': ('statut', 'priorite', 'couleur')
        }),
        ('Récurrence', {
            'fields': ('type_recurrence', 'jours_semaine', 'jour_mois', 'date_fin_recurrence', 'rdv_parent'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification', 'est_actif'),
            'classes': ('collapse',)
        }),
    )

    def date_debut_formatee(self, obj):
        return obj.date_debut.strftime('%d/%m/%Y %H:%M')
    date_debut_formatee.short_description = 'Date début'

    def statut_badge(self, obj):
        couleurs = {
            'planifie': '#3498db',
            'confirme': '#2ecc71',
            'en_cours': '#f39c12',
            'termine': '#27ae60',
            'reporte': '#e74c3c',
            'annule': '#95a5a6',
        }
        couleur = couleurs.get(obj.statut, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            couleur, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def priorite_badge(self, obj):
        couleurs = {
            'basse': '#27ae60',
            'normale': '#3498db',
            'haute': '#f39c12',
            'urgente': '#e74c3c',
        }
        couleur = couleurs.get(obj.priorite, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            couleur, obj.get_priorite_display()
        )
    priorite_badge.short_description = 'Priorité'


# =============================================================================
# ADMIN TÂCHES
# =============================================================================

@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'type_tache', 'date_echeance', 'statut_badge',
        'priorite_badge', 'responsable', 'progression_bar', 'est_active'
    ]
    list_filter = ['type_tache', 'statut', 'priorite', 'est_active', 'date_echeance', 'statut_delegation']
    search_fields = ['titre', 'description']
    date_hierarchy = 'date_echeance'
    readonly_fields = ['date_creation', 'date_modification', 'date_terminaison', 'date_delegation']
    filter_horizontal = ['etiquettes', 'co_responsables']
    inlines = [SousTacheChecklistInline, CommentaireTacheInline, DocumentTacheInline, RappelTacheInline, ReportTacheInline]

    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'type_tache', 'description')
        }),
        ('Dates', {
            'fields': ('date_echeance', 'heure_echeance', 'date_debut')
        }),
        ('Attribution', {
            'fields': ('createur', 'responsable', 'co_responsables')
        }),
        ('Liaison avec dossiers', {
            'fields': ('dossier', 'partie_concernee', 'acte_lie')
        }),
        ('Statut et priorité', {
            'fields': ('statut', 'priorite', 'couleur', 'etiquettes')
        }),
        ('Suivi', {
            'fields': ('temps_estime', 'temps_passe', 'progression')
        }),
        ('Délégation', {
            'fields': ('statut_delegation', 'date_delegation', 'instructions_delegation', 'demande_compte_rendu'),
            'classes': ('collapse',)
        }),
        ('Récurrence', {
            'fields': ('type_recurrence', 'jours_semaine', 'jour_mois', 'date_fin_recurrence', 'tache_parent'),
            'classes': ('collapse',)
        }),
        ('Hiérarchie', {
            'fields': ('tache_parente', 'ordre'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification', 'date_terminaison', 'est_active'),
            'classes': ('collapse',)
        }),
    )

    def statut_badge(self, obj):
        couleurs = {
            'a_faire': '#3498db',
            'en_cours': '#f39c12',
            'en_attente': '#95a5a6',
            'terminee': '#27ae60',
            'annulee': '#e74c3c',
            'reportee': '#9b59b6',
        }
        couleur = couleurs.get(obj.statut, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            couleur, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def priorite_badge(self, obj):
        couleurs = {
            'basse': '#27ae60',
            'normale': '#3498db',
            'haute': '#f39c12',
            'urgente': '#e74c3c',
        }
        couleur = couleurs.get(obj.priorite, '#3498db')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            couleur, obj.get_priorite_display()
        )
    priorite_badge.short_description = 'Priorité'

    def progression_bar(self, obj):
        progression = obj.progression_calculee
        couleur = '#27ae60' if progression == 100 else '#3498db'
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; line-height: 20px;">{:.0f}%</div></div>',
            progression, couleur, progression
        )
    progression_bar.short_description = 'Progression'


# =============================================================================
# ADMIN ÉTIQUETTES
# =============================================================================

@admin.register(Etiquette)
class EtiquetteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'couleur_preview', 'description', 'createur', 'date_creation']
    search_fields = ['nom', 'description']

    def couleur_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            obj.couleur, obj.nom
        )
    couleur_preview.short_description = 'Aperçu'


# =============================================================================
# ADMIN PARTICIPANTS EXTERNES
# =============================================================================

@admin.register(ParticipantExterne)
class ParticipantExterneAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_participant', 'email', 'telephone', 'partie_liee']
    list_filter = ['type_participant']
    search_fields = ['nom', 'email', 'telephone']


# =============================================================================
# ADMIN NOTIFICATIONS
# =============================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'destinataire', 'type_notification', 'est_lu', 'date_creation']
    list_filter = ['type_notification', 'est_lu', 'canal']
    search_fields = ['titre', 'message', 'destinataire__username']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation', 'date_lecture']


# =============================================================================
# ADMIN JOURNÉE AGENDA
# =============================================================================

@admin.register(JourneeAgenda)
class JourneeAgendaAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'utilisateur', 'est_cloturee', 'taux_realisation',
        'nb_rdv_prevus', 'nb_taches_prevues', 'type_cloture'
    ]
    list_filter = ['est_cloturee', 'type_cloture', 'date']
    date_hierarchy = 'date'
    readonly_fields = ['date_creation', 'date_modification', 'bilan_json']

    def taux_realisation(self, obj):
        if obj.bilan_json and 'taux_realisation' in obj.bilan_json:
            taux = obj.bilan_json['taux_realisation']
            couleur = '#27ae60' if taux >= 80 else '#f39c12' if taux >= 50 else '#e74c3c'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                couleur, taux
            )
        return '-'
    taux_realisation.short_description = 'Taux'


# =============================================================================
# ADMIN HISTORIQUE
# =============================================================================

@admin.register(HistoriqueAgenda)
class HistoriqueAgendaAdmin(admin.ModelAdmin):
    list_display = ['type_objet', 'action', 'utilisateur', 'date_creation', 'adresse_ip']
    list_filter = ['type_objet', 'action', 'date_creation']
    search_fields = ['utilisateur__username', 'details']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation', 'details', 'anciennes_valeurs', 'nouvelles_valeurs']


# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

@admin.register(ConfigurationAgenda)
class ConfigurationAgendaAdmin(admin.ModelAdmin):
    list_display = [
        'heure_debut_journee', 'heure_fin_journee', 'duree_rdv_defaut',
        'activer_cloture_auto', 'activer_notifications_email'
    ]

    def has_add_permission(self, request):
        # Ne permettre qu'une seule configuration
        if ConfigurationAgenda.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# ADMIN STATISTIQUES
# =============================================================================

@admin.register(StatistiquesAgenda)
class StatistiquesAgendaAdmin(admin.ModelAdmin):
    list_display = [
        'type_periode', 'date_debut', 'date_fin', 'utilisateur',
        'nb_rdv_total', 'nb_taches_total', 'taux_realisation_rdv', 'taux_realisation_taches'
    ]
    list_filter = ['type_periode', 'date_debut']
    date_hierarchy = 'date_debut'
    readonly_fields = ['date_generation']


# =============================================================================
# ADMIN REPORT TÂCHE
# =============================================================================

@admin.register(ReportTache)
class ReportTacheAdmin(admin.ModelAdmin):
    list_display = ['tache', 'date_origine', 'nouvelle_date', 'type_report', 'reporte_par', 'date_creation']
    list_filter = ['type_report', 'date_creation']
    search_fields = ['tache__titre', 'raison']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation']


# =============================================================================
# ADMIN VUES SAUVEGARDÉES
# =============================================================================

@admin.register(VueSauvegardee)
class VueSauvegardeeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'utilisateur', 'est_par_defaut', 'ordre', 'created_at']
    list_filter = ['est_par_defaut', 'created_at']
    search_fields = ['nom', 'description', 'utilisateur__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations', {
            'fields': ('utilisateur', 'nom', 'description')
        }),
        ('Filtres', {
            'fields': ('filtres',)
        }),
        ('Options', {
            'fields': ('est_par_defaut', 'ordre')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# =============================================================================
# ADMIN PARTICIPATION RDV
# =============================================================================

@admin.register(ParticipationRdv)
class ParticipationRdvAdmin(admin.ModelAdmin):
    list_display = ['rdv', 'participant_display', 'statut_presence_badge', 'date_reponse', 'notifie']
    list_filter = ['statut_presence', 'notifie']
    search_fields = ['rdv__titre', 'collaborateur__nom', 'participant_externe__nom']
    readonly_fields = ['date_reponse', 'date_notification']

    def participant_display(self, obj):
        if obj.collaborateur:
            return f"[Collaborateur] {obj.collaborateur}"
        elif obj.participant_externe:
            return f"[Externe] {obj.participant_externe.nom}"
        return "-"
    participant_display.short_description = 'Participant'

    def statut_presence_badge(self, obj):
        couleurs = {
            'invite': '#6c757d',
            'confirme': '#28a745',
            'decline': '#dc3545',
            'present': '#007bff',
            'absent': '#dc3545',
            'excuse': '#ffc107',
        }
        couleur = couleurs.get(obj.statut_presence, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            couleur, obj.get_statut_presence_display()
        )
    statut_presence_badge.short_description = 'Statut présence'

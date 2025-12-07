"""
Administration Django pour le module Chatbot.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SessionConversation, Message, ActionDemandee,
    CommandeVocale, TemplateReponse, EtapeGuidage,
    StatistiquesUtilisation, ConfigurationChatbot,
    RaccourciUtilisateur
)


@admin.register(SessionConversation)
class SessionConversationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'utilisateur', 'titre', 'canal', 'est_active',
        'nombre_messages', 'date_creation', 'date_derniere_activite'
    ]
    list_filter = ['canal', 'est_active', 'mode_guide_actif', 'date_creation']
    search_fields = ['utilisateur__username', 'utilisateur__email', 'titre']
    readonly_fields = ['id', 'date_creation', 'date_derniere_activite', 'date_expiration']
    date_hierarchy = 'date_creation'

    def nombre_messages(self, obj):
        return obj.messages.count()
    nombre_messages.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session_link', 'type_message', 'contenu_court',
        'est_vocal', 'intention_detectee', 'date_creation'
    ]
    list_filter = ['type_message', 'est_vocal', 'intention_detectee', 'date_creation']
    search_fields = ['contenu', 'session__utilisateur__username']
    readonly_fields = ['id', 'date_creation']

    def session_link(self, obj):
        return format_html(
            '<a href="/admin/chatbot/sessionconversation/{}/change/">{}</a>',
            obj.session.id, str(obj.session.id)[:8]
        )
    session_link.short_description = 'Session'

    def contenu_court(self, obj):
        return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
    contenu_court.short_description = 'Contenu'


@admin.register(ActionDemandee)
class ActionDemandeeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'type_commande', 'statut_colored', 'montant_formate',
        'confirmation_requise', 'validation_humaine_requise',
        'validateur', 'date_creation'
    ]
    list_filter = [
        'statut', 'type_commande', 'niveau_criticite',
        'confirmation_requise', 'validation_humaine_requise',
        'date_creation'
    ]
    search_fields = ['description', 'message__session__utilisateur__username']
    readonly_fields = [
        'id', 'date_creation', 'date_execution',
        'rbac_verifie', 'rbac_autorise', 'raison_refus_rbac'
    ]
    actions = ['valider_actions', 'refuser_actions']

    def statut_colored(self, obj):
        colors = {
            'en_attente': '#ffc107',
            'en_cours': '#17a2b8',
            'confirmation_requise': '#fd7e14',
            'validation_requise': '#6f42c1',
            'executee': '#28a745',
            'annulee': '#6c757d',
            'refusee': '#dc3545',
            'erreur': '#dc3545',
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_colored.short_description = 'Statut'

    def montant_formate(self, obj):
        if obj.montant_concerne:
            return f"{obj.montant_concerne:,.0f} FCFA"
        return "-"
    montant_formate.short_description = 'Montant'

    def valider_actions(self, request, queryset):
        count = 0
        for action in queryset.filter(statut='validation_requise'):
            action.valider(request.user, 'Validé en lot via admin')
            action.executer()
            count += 1
        self.message_user(request, f'{count} action(s) validée(s) et exécutée(s).')
    valider_actions.short_description = 'Valider les actions sélectionnées'

    def refuser_actions(self, request, queryset):
        count = queryset.filter(statut='validation_requise').update(statut='refusee')
        self.message_user(request, f'{count} action(s) refusée(s).')
    refuser_actions.short_description = 'Refuser les actions sélectionnées'


@admin.register(CommandeVocale)
class CommandeVocaleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'transcription_normalisee_courte', 'langue_detectee',
        'score_confiance', 'transcription_correcte', 'date_creation'
    ]
    list_filter = ['langue_detectee', 'transcription_correcte', 'date_creation']
    search_fields = ['transcription_brute', 'transcription_normalisee']
    readonly_fields = ['id', 'date_creation']

    def transcription_normalisee_courte(self, obj):
        return obj.transcription_normalisee[:50] + '...' if len(obj.transcription_normalisee) > 50 else obj.transcription_normalisee
    transcription_normalisee_courte.short_description = 'Transcription'


@admin.register(TemplateReponse)
class TemplateReponseAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'type_commande', 'categorie', 'actif']
    list_filter = ['categorie', 'type_commande', 'actif']
    search_fields = ['code', 'titre', 'contenu']
    readonly_fields = ['date_creation', 'date_modification']


@admin.register(EtapeGuidage)
class EtapeGuidageAdmin(admin.ModelAdmin):
    list_display = ['mode', 'numero_etape', 'titre', 'type_reponse', 'champ_obligatoire', 'actif']
    list_filter = ['mode', 'type_reponse', 'champ_obligatoire', 'actif']
    ordering = ['mode', 'numero_etape']


@admin.register(StatistiquesUtilisation)
class StatistiquesUtilisationAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'utilisateur', 'nombre_sessions', 'nombre_messages',
        'nombre_commandes_vocales', 'nombre_actions_executees', 'taux_succes_actions'
    ]
    list_filter = ['date']
    date_hierarchy = 'date'


@admin.register(ConfigurationChatbot)
class ConfigurationChatbotAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Général', {
            'fields': ('actif', 'nom_assistant', 'message_bienvenue')
        }),
        ('Sécurité', {
            'fields': (
                'seuil_confirmation_fcfa', 'duree_retention_jours',
                'ecritures_critiques_validation'
            )
        }),
        ('Reconnaissance vocale', {
            'fields': (
                'reconnaissance_vocale_active', 'langue_defaut',
                'seuil_confiance_vocal'
            )
        }),
        ('WebSocket', {
            'fields': ('timeout_session_minutes', 'max_messages_par_session')
        }),
        ('Notifications', {
            'fields': (
                'notifier_validations_en_attente', 'email_notifications'
            )
        }),
    )

    def has_add_permission(self, request):
        # Singleton: empêcher la création de multiples configurations
        return not ConfigurationChatbot.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RaccourciUtilisateur)
class RaccourciUtilisateurAdmin(admin.ModelAdmin):
    list_display = [
        'raccourci', 'utilisateur', 'type_commande',
        'nombre_utilisations', 'actif'
    ]
    list_filter = ['type_commande', 'actif']
    search_fields = ['raccourci', 'utilisateur__username']

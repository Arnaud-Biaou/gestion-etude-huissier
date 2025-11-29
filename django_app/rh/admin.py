"""
Administration du module Ressources Humaines
"""

from django.contrib import admin
from .models import (
    CategorieEmploye, Poste, Site,
    Employe, DocumentEmploye,
    Contrat, AvenantContrat,
    ElementPaie, PeriodePaie, BulletinPaie, LigneBulletinPaie,
    TypeConge, Conge, SoldeConge, TypeAbsence, Absence, Pointage,
    Pret, EcheancePret,
    DeclarationSociale,
    CritereEvaluation, Evaluation, NoteCritereEvaluation,
    Formation, ParticipationFormation,
    TypeSanction, Sanction,
    FinContrat,
    ConfigurationRH
)


# =============================================================================
# CONFIGURATION DE BASE
# =============================================================================

@admin.register(CategorieEmploye)
class CategorieEmployeAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'niveau', 'coefficient', 'salaire_minimum', 'duree_essai_mois')
    list_filter = ('niveau',)
    search_fields = ('code', 'libelle')
    ordering = ('niveau', 'code')


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'categorie', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('code', 'libelle')
    ordering = ('categorie__niveau', 'libelle')


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'est_principal', 'actif')
    list_filter = ('est_principal', 'actif')
    search_fields = ('nom', 'adresse')


# =============================================================================
# EMPLOYÉS
# =============================================================================

class DocumentEmployeInline(admin.TabularInline):
    model = DocumentEmploye
    extra = 0
    fields = ('type_document', 'titre', 'fichier', 'date_document')


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenoms', 'poste', 'type_contrat', 'statut', 'date_embauche')
    list_filter = ('statut', 'type_contrat', 'categorie', 'site', 'sexe')
    search_fields = ('matricule', 'nom', 'prenoms', 'numero_cnss', 'numero_ifu')
    date_hierarchy = 'date_embauche'
    ordering = ('nom', 'prenoms')
    inlines = [DocumentEmployeInline]

    fieldsets = (
        ('Informations personnelles', {
            'fields': (
                ('matricule', 'statut'),
                ('nom', 'prenoms'),
                ('date_naissance', 'lieu_naissance'),
                ('sexe', 'situation_matrimoniale', 'nombre_enfants'),
                ('nationalite', 'numero_cni'),
            )
        }),
        ('Contacts', {
            'fields': (
                'adresse',
                ('telephone', 'telephone_secondaire'),
                'email',
            )
        }),
        ('Contact urgence', {
            'fields': (
                ('contact_urgence_nom', 'contact_urgence_telephone'),
                'contact_urgence_relation',
            ),
            'classes': ('collapse',)
        }),
        ('Informations professionnelles', {
            'fields': (
                ('date_embauche', 'date_fin_contrat'),
                'type_contrat',
                ('categorie', 'poste'),
                ('site', 'superieur'),
                'salaire_base',
            )
        }),
        ('Informations légales', {
            'fields': (
                ('numero_cnss', 'numero_ifu', 'numero_cip'),
            )
        }),
        ('Coordonnées bancaires', {
            'fields': (
                'banque',
                ('rib_code_banque', 'rib_code_guichet'),
                ('rib_numero_compte', 'rib_cle'),
            ),
            'classes': ('collapse',)
        }),
        ('Système', {
            'fields': ('utilisateur',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentEmploye)
class DocumentEmployeAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_document', 'titre', 'date_document', 'date_upload')
    list_filter = ('type_document', 'date_upload')
    search_fields = ('employe__nom', 'employe__prenoms', 'titre')
    date_hierarchy = 'date_upload'


# =============================================================================
# CONTRATS
# =============================================================================

class AvenantContratInline(admin.TabularInline):
    model = AvenantContrat
    extra = 0
    fields = ('reference', 'type_avenant', 'date_effet', 'description')


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ('reference', 'employe', 'type_contrat', 'date_debut', 'date_fin', 'statut')
    list_filter = ('type_contrat', 'statut', 'categorie')
    search_fields = ('reference', 'employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_debut'
    inlines = [AvenantContratInline]


@admin.register(AvenantContrat)
class AvenantContratAdmin(admin.ModelAdmin):
    list_display = ('reference', 'contrat', 'type_avenant', 'date_effet')
    list_filter = ('type_avenant',)
    search_fields = ('reference', 'contrat__employe__nom')
    date_hierarchy = 'date_effet'


# =============================================================================
# PAIE
# =============================================================================

@admin.register(ElementPaie)
class ElementPaieAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'type_element', 'nature', 'est_imposable', 'est_cotisable', 'actif')
    list_filter = ('type_element', 'nature', 'est_imposable', 'est_cotisable', 'actif')
    search_fields = ('code', 'libelle')


@admin.register(PeriodePaie)
class PeriodePaieAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'annee', 'mois', 'date_debut', 'date_fin', 'statut')
    list_filter = ('annee', 'statut')
    ordering = ('-annee', '-mois')


class LigneBulletinPaieInline(admin.TabularInline):
    model = LigneBulletinPaie
    extra = 0
    fields = ('element', 'libelle', 'base', 'taux', 'montant')


@admin.register(BulletinPaie)
class BulletinPaieAdmin(admin.ModelAdmin):
    list_display = ('reference', 'employe', 'periode', 'salaire_brut', 'net_a_payer', 'statut')
    list_filter = ('statut', 'periode__annee', 'periode__mois')
    search_fields = ('reference', 'employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_creation'
    inlines = [LigneBulletinPaieInline]

    readonly_fields = (
        'total_gains', 'salaire_brut', 'base_cotisable', 'base_imposable',
        'cnss_salariale', 'cnss_patronale', 'ipts', 'vps',
        'total_retenues', 'net_a_payer',
        'cumul_brut', 'cumul_cnss', 'cumul_ipts', 'cumul_net',
    )


# =============================================================================
# CONGÉS ET ABSENCES
# =============================================================================

@admin.register(TypeConge)
class TypeCongeAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'duree_max', 'est_paye', 'decompte_solde', 'actif')
    list_filter = ('est_paye', 'decompte_solde', 'actif')
    search_fields = ('code', 'libelle')


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_conge', 'date_debut', 'date_fin', 'nombre_jours', 'statut')
    list_filter = ('statut', 'type_conge')
    search_fields = ('employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_debut'


@admin.register(SoldeConge)
class SoldeCongeAdmin(admin.ModelAdmin):
    list_display = ('employe', 'annee', 'jours_acquis', 'jours_pris', 'jours_reportes', 'solde_disponible')
    list_filter = ('annee',)
    search_fields = ('employe__nom', 'employe__prenoms')


@admin.register(TypeAbsence)
class TypeAbsenceAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'impacte_salaire', 'taux_retenue', 'actif')
    list_filter = ('impacte_salaire', 'actif')


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_absence', 'date_debut', 'date_fin', 'nombre_jours', 'justifie')
    list_filter = ('type_absence', 'justifie')
    search_fields = ('employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_debut'


@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display = ('employe', 'date', 'heure_arrivee', 'heure_depart', 'present', 'retard_minutes')
    list_filter = ('present', 'date')
    search_fields = ('employe__nom', 'employe__prenoms')
    date_hierarchy = 'date'


# =============================================================================
# PRÊTS
# =============================================================================

class EcheancePretInline(admin.TabularInline):
    model = EcheancePret
    extra = 0
    fields = ('numero', 'date_echeance', 'montant', 'statut', 'bulletin')


@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ('reference', 'employe', 'type_pret', 'montant', 'montant_rembourse', 'solde_restant', 'statut')
    list_filter = ('type_pret', 'statut')
    search_fields = ('reference', 'employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_demande'
    inlines = [EcheancePretInline]


# =============================================================================
# DÉCLARATIONS
# =============================================================================

@admin.register(DeclarationSociale)
class DeclarationSocialeAdmin(admin.ModelAdmin):
    list_display = ('type_declaration', 'annee', 'periode_debut', 'periode_fin',
                    'nombre_salaries', 'total_cotisations', 'statut')
    list_filter = ('type_declaration', 'annee', 'statut')
    date_hierarchy = 'periode_debut'


# =============================================================================
# ÉVALUATIONS
# =============================================================================

@admin.register(CritereEvaluation)
class CritereEvaluationAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'coefficient', 'actif')
    list_filter = ('actif',)
    search_fields = ('code', 'libelle')


class NoteCritereEvaluationInline(admin.TabularInline):
    model = NoteCritereEvaluation
    extra = 0


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('employe', 'evaluateur', 'date_evaluation', 'note_globale', 'statut')
    list_filter = ('statut',)
    search_fields = ('employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_evaluation'
    inlines = [NoteCritereEvaluationInline]


# =============================================================================
# FORMATIONS
# =============================================================================

class ParticipationFormationInline(admin.TabularInline):
    model = ParticipationFormation
    extra = 0
    fields = ('employe', 'statut', 'note')


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('intitule', 'type_formation', 'organisme', 'date_debut', 'date_fin', 'cout', 'statut')
    list_filter = ('type_formation', 'statut')
    search_fields = ('intitule', 'organisme')
    date_hierarchy = 'date_debut'
    inlines = [ParticipationFormationInline]


@admin.register(ParticipationFormation)
class ParticipationFormationAdmin(admin.ModelAdmin):
    list_display = ('formation', 'employe', 'statut', 'note')
    list_filter = ('statut',)
    search_fields = ('employe__nom', 'employe__prenoms', 'formation__intitule')


# =============================================================================
# DISCIPLINE
# =============================================================================

@admin.register(TypeSanction)
class TypeSanctionAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'niveau', 'duree_max_jours')
    list_filter = ('niveau',)
    search_fields = ('code', 'libelle')


@admin.register(Sanction)
class SanctionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'employe', 'type_sanction', 'date_faits', 'statut')
    list_filter = ('type_sanction', 'statut')
    search_fields = ('reference', 'employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_faits'


# =============================================================================
# FINS DE CONTRAT
# =============================================================================

@admin.register(FinContrat)
class FinContratAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_rupture', 'date_notification', 'date_fin_effective',
                    'total_solde_compte', 'statut')
    list_filter = ('type_rupture', 'statut')
    search_fields = ('employe__nom', 'employe__prenoms')
    date_hierarchy = 'date_fin_effective'

    readonly_fields = (
        'indemnite_preavis', 'indemnite_licenciement', 'indemnite_conges',
        'prorata_13eme_mois', 'autres_indemnites', 'total_solde_compte',
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

@admin.register(ConfigurationRH)
class ConfigurationRHAdmin(admin.ModelAdmin):
    list_display = ('nom_entreprise', 'numero_cnss_employeur', 'numero_ifu_employeur', 'est_configure')

    def has_add_permission(self, request):
        # Ne permettre qu'une seule instance
        return not ConfigurationRH.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# LIGNES BULLETIN DE PAIE (STANDALONE)
# =============================================================================

@admin.register(LigneBulletinPaie)
class LigneBulletinPaieAdmin(admin.ModelAdmin):
    list_display = ('bulletin', 'element', 'libelle', 'base', 'taux', 'montant')
    list_filter = ('element__type_element', 'element__nature', 'bulletin__periode')
    search_fields = ('bulletin__reference', 'bulletin__employe__nom', 'libelle', 'element__code')
    raw_id_fields = ('bulletin', 'element')


# =============================================================================
# ÉCHÉANCES DE PRÊT (STANDALONE)
# =============================================================================

@admin.register(EcheancePret)
class EcheancePretAdmin(admin.ModelAdmin):
    list_display = ('pret', 'numero', 'date_echeance', 'montant', 'statut', 'bulletin')
    list_filter = ('statut', 'date_echeance')
    search_fields = ('pret__reference', 'pret__employe__nom', 'pret__employe__prenoms')
    raw_id_fields = ('pret', 'bulletin')
    date_hierarchy = 'date_echeance'


# =============================================================================
# NOTES CRITÈRE ÉVALUATION (STANDALONE)
# =============================================================================

@admin.register(NoteCritereEvaluation)
class NoteCritereEvaluationAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'critere', 'note', 'commentaire_apercu')
    list_filter = ('critere', 'note')
    search_fields = ('evaluation__employe__nom', 'evaluation__employe__prenoms', 'critere__libelle', 'commentaire')
    raw_id_fields = ('evaluation', 'critere')

    def commentaire_apercu(self, obj):
        if obj.commentaire:
            return obj.commentaire[:50] + '...' if len(obj.commentaire) > 50 else obj.commentaire
        return '-'
    commentaire_apercu.short_description = 'Commentaire'

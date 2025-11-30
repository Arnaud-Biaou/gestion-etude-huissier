# -*- coding: utf-8 -*-
"""
Forms Phase 4 - Facturation E-MECeF

Formulaires pour la gestion de la facturation avec ventilation
par groupe de taxation E-MECeF (A=Exonéré, B=Taxable).
"""

from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal

from .models import (
    ActeDossier, Dossier, Facture, LigneFacture,
    VentilationLigneFacture, GroupeTaxation, CreanceAIB
)


class ActeDossierForm(forms.ModelForm):
    """Formulaire de création/modification d'un acte de dossier"""

    class Meta:
        model = ActeDossier
        fields = [
            'dossier', 'type_acte', 'date_acte', 'numero_acte',
            'nombre_feuillets', 'observations'
        ]
        widgets = {
            'dossier': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'type_acte': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date_acte': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'numero_acte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EXE-2025-XXXX',
                'readonly': True
            }),
            'nombre_feuillets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer automatiquement le numéro d'acte si nouveau
        if not self.instance.pk:
            self.initial['numero_acte'] = ActeDossier.generer_numero()


class FactureForm(forms.ModelForm):
    """Formulaire de création/modification d'une facture E-MECeF"""

    class Meta:
        model = Facture
        fields = [
            'dossier', 'client', 'ifu', 'regime_fiscal', 'prelevable_aib',
            'date_emission', 'date_echeance', 'observations'
        ]
        widgets = {
            'dossier': forms.Select(attrs={
                'class': 'form-select',
            }),
            'client': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du client'
            }),
            'ifu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IFU (13 chiffres)',
                'maxlength': 13
            }),
            'regime_fiscal': forms.Select(attrs={
                'class': 'form-select',
            }),
            'prelevable_aib': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'date_emission': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def clean_ifu(self):
        """Valide le format de l'IFU (13 chiffres)"""
        ifu = self.cleaned_data.get('ifu')
        if ifu and len(ifu) != 13:
            raise forms.ValidationError("L'IFU doit contenir exactement 13 chiffres")
        if ifu and not ifu.isdigit():
            raise forms.ValidationError("L'IFU doit contenir uniquement des chiffres")
        return ifu


class LigneFactureForm(forms.ModelForm):
    """Formulaire pour une ligne de facture"""

    class Meta:
        model = LigneFacture
        fields = ['description', 'acte_dossier', 'quantite', 'prix_unitaire', 'ordre']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Description de l'acte"
            }),
            'acte_dossier': forms.Select(attrs={
                'class': 'form-select',
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
            }),
            'ordre': forms.HiddenInput(),
        }


class VentilationForm(forms.ModelForm):
    """Formulaire de ventilation d'une ligne facture par groupe E-MECeF"""

    class Meta:
        model = VentilationLigneFacture
        fields = ['nature', 'groupe_taxation', 'description', 'montant_ht', 'ordre']
        widgets = {
            'nature': forms.Select(attrs={
                'class': 'form-select',
            }),
            'groupe_taxation': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description de la ventilation'
            }),
            'montant_ht': forms.NumberInput(attrs={
                'class': 'form-control montant-ht',
                'min': 0,
                'step': 1,
            }),
            'ordre': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger uniquement les groupes A et B (principaux pour étude huissier)
        self.fields['groupe_taxation'].queryset = GroupeTaxation.objects.filter(
            code__in=['A', 'B']
        )


# Formsets pour gestion des lignes et ventilations
LigneFactureFormSet = inlineformset_factory(
    Facture,
    LigneFacture,
    form=LigneFactureForm,
    extra=1,
    can_delete=True
)

VentilationFormSet = inlineformset_factory(
    LigneFacture,
    VentilationLigneFacture,
    form=VentilationForm,
    extra=3,  # 3 ventilations par défaut (timbre, enreg, honoraires)
    can_delete=True
)


class CreanceAIBForm(forms.ModelForm):
    """Formulaire pour ajuster une créance AIB"""

    class Meta:
        model = CreanceAIB
        fields = ['client_type', 'statut']
        widgets = {
            'client_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select',
            }),
        }


class RechercheFactureForm(forms.Form):
    """Formulaire de recherche de factures"""

    numero = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro facture'
        })
    )
    client = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom client'
        })
    )
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Facture.STATUT_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    regime_fiscal = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les régimes')] + list(Facture.REGIME_FISCAL_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

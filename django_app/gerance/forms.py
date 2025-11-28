"""
CORRECTION #30: Formulaires du module Gerance Immobiliere avec validation
"""

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

from .models import (
    Proprietaire, BienImmobilier, Locataire, Bail, Loyer,
    Quittance, EtatDesLieux, Incident, ReversementProprietaire
)


class ProprietaireForm(forms.ModelForm):
    """Formulaire de creation/modification d'un proprietaire"""

    class Meta:
        model = Proprietaire
        fields = [
            'type_proprietaire', 'nom', 'prenom', 'civilite',
            'adresse', 'ville', 'code_postal', 'pays',
            'telephone', 'telephone_secondaire', 'email',
            'numero_ifu', 'numero_rccm',
            'banque', 'numero_compte', 'iban',
            'taux_honoraires', 'mode_reversement', 'jour_reversement',
            'notes'
        ]
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Nettoyer le numero de telephone
            telephone = re.sub(r'[^\d+]', '', telephone)
            if len(telephone) < 8:
                raise ValidationError("Le numero de telephone doit contenir au moins 8 chiffres.")
        return telephone

    def clean_taux_honoraires(self):
        taux = self.cleaned_data.get('taux_honoraires')
        if taux is not None:
            if taux < 0 or taux > 100:
                raise ValidationError("Le taux d'honoraires doit etre entre 0 et 100%.")
        return taux

    def clean_jour_reversement(self):
        jour = self.cleaned_data.get('jour_reversement')
        if jour is not None:
            if jour < 1 or jour > 28:
                raise ValidationError("Le jour de reversement doit etre entre 1 et 28.")
        return jour

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verifier le format de l'email
            validator = EmailValidator()
            try:
                validator(email)
            except ValidationError:
                raise ValidationError("Veuillez entrer une adresse email valide.")
        return email


class BienImmobilierForm(forms.ModelForm):
    """Formulaire de creation/modification d'un bien immobilier"""

    class Meta:
        model = BienImmobilier
        fields = [
            'proprietaire', 'reference', 'designation', 'type_bien',
            'adresse', 'quartier', 'ville', 'code_postal',
            'surface', 'nombre_pieces', 'etage', 'meuble',
            'parking', 'garage', 'jardin', 'piscine', 'climatisation', 'gardiennage',
            'loyer_mensuel', 'charges_mensuelles', 'depot_garantie',
            'statut', 'date_acquisition', 'date_fin_mandat',
            'description', 'notes'
        ]
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_reference(self):
        reference = self.cleaned_data.get('reference')
        if reference:
            # Verifier l'unicite de la reference
            qs = BienImmobilier.objects.filter(reference=reference)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Cette reference existe deja.")
        return reference

    def clean_loyer_mensuel(self):
        loyer = self.cleaned_data.get('loyer_mensuel')
        if loyer is not None and loyer < 0:
            raise ValidationError("Le loyer ne peut pas etre negatif.")
        return loyer

    def clean_charges_mensuelles(self):
        charges = self.cleaned_data.get('charges_mensuelles')
        if charges is not None and charges < 0:
            raise ValidationError("Les charges ne peuvent pas etre negatives.")
        return charges

    def clean_depot_garantie(self):
        depot = self.cleaned_data.get('depot_garantie')
        if depot is not None and depot < 0:
            raise ValidationError("Le depot de garantie ne peut pas etre negatif.")
        return depot

    def clean_surface(self):
        surface = self.cleaned_data.get('surface')
        if surface is not None and surface <= 0:
            raise ValidationError("La surface doit etre superieure a 0.")
        return surface


class LocataireForm(forms.ModelForm):
    """Formulaire de creation/modification d'un locataire"""

    class Meta:
        model = Locataire
        fields = [
            'type_locataire', 'nom', 'prenom', 'civilite',
            'date_naissance', 'lieu_naissance', 'nationalite',
            'type_piece', 'numero_piece', 'date_expiration_piece',
            'telephone', 'telephone_secondaire', 'email',
            'profession', 'employeur', 'revenu_mensuel',
            'contact_urgence_nom', 'contact_urgence_telephone', 'contact_urgence_lien',
            'garant_nom', 'garant_telephone', 'garant_adresse',
            'notes'
        ]
        widgets = {
            'garant_adresse': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            telephone = re.sub(r'[^\d+]', '', telephone)
            if len(telephone) < 8:
                raise ValidationError("Le numero de telephone doit contenir au moins 8 chiffres.")
        return telephone

    def clean_revenu_mensuel(self):
        revenu = self.cleaned_data.get('revenu_mensuel')
        if revenu is not None and revenu < 0:
            raise ValidationError("Le revenu mensuel ne peut pas etre negatif.")
        return revenu

    def clean(self):
        cleaned_data = super().clean()
        type_locataire = cleaned_data.get('type_locataire')
        nom = cleaned_data.get('nom')

        if type_locataire == 'societe' and not nom:
            self.add_error('nom', "La raison sociale est obligatoire pour une societe.")

        return cleaned_data


class BailForm(forms.ModelForm):
    """Formulaire de creation/modification d'un bail"""

    class Meta:
        model = Bail
        fields = [
            'bien', 'locataire', 'type_bail',
            'date_debut', 'date_fin', 'duree_mois',
            'loyer_mensuel', 'charges_mensuelles', 'depot_garantie', 'depot_verse',
            'jour_paiement', 'mode_paiement',
            'taux_revision', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_date_fin(self):
        date_debut = self.cleaned_data.get('date_debut')
        date_fin = self.cleaned_data.get('date_fin')

        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise ValidationError("La date de fin doit etre posterieure a la date de debut.")
        return date_fin

    def clean_loyer_mensuel(self):
        loyer = self.cleaned_data.get('loyer_mensuel')
        if loyer is not None and loyer <= 0:
            raise ValidationError("Le loyer mensuel doit etre superieur a 0.")
        return loyer

    def clean_jour_paiement(self):
        jour = self.cleaned_data.get('jour_paiement')
        if jour is not None:
            if jour < 1 or jour > 28:
                raise ValidationError("Le jour de paiement doit etre entre 1 et 28.")
        return jour

    def clean_duree_mois(self):
        duree = self.cleaned_data.get('duree_mois')
        if duree is not None and duree < 1:
            raise ValidationError("La duree doit etre d'au moins 1 mois.")
        return duree

    def clean(self):
        cleaned_data = super().clean()
        bien = cleaned_data.get('bien')

        # Verifier que le bien n'a pas deja un bail actif
        if bien and not self.instance.pk:
            bail_actif = Bail.objects.filter(bien=bien, statut='actif').exists()
            if bail_actif:
                self.add_error('bien', "Ce bien a deja un bail actif.")

        return cleaned_data


class LoyerForm(forms.ModelForm):
    """Formulaire de gestion des loyers"""

    class Meta:
        model = Loyer
        fields = [
            'bail', 'mois', 'annee', 'date_echeance',
            'montant_loyer', 'montant_charges', 'montant_total',
            'montant_paye', 'penalites', 'statut', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_mois(self):
        mois = self.cleaned_data.get('mois')
        if mois is not None:
            if mois < 1 or mois > 12:
                raise ValidationError("Le mois doit etre entre 1 et 12.")
        return mois

    def clean_montant_paye(self):
        montant_paye = self.cleaned_data.get('montant_paye')
        montant_total = self.cleaned_data.get('montant_total')

        if montant_paye is not None and montant_paye < 0:
            raise ValidationError("Le montant paye ne peut pas etre negatif.")

        if montant_paye is not None and montant_total is not None:
            if montant_paye > montant_total:
                raise ValidationError("Le montant paye ne peut pas depasser le montant total.")

        return montant_paye


class IncidentForm(forms.ModelForm):
    """Formulaire de signalement d'incident"""

    class Meta:
        model = Incident
        fields = [
            'bien', 'bail', 'type_incident', 'priorite',
            'titre', 'description',
            'cout_estime', 'a_charge_de',
            'intervenant', 'telephone_intervenant',
            'notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_cout_estime(self):
        cout = self.cleaned_data.get('cout_estime')
        if cout is not None and cout < 0:
            raise ValidationError("Le cout estime ne peut pas etre negatif.")
        return cout


class EtatDesLieuxForm(forms.ModelForm):
    """Formulaire d'etat des lieux"""

    class Meta:
        model = EtatDesLieux
        fields = [
            'bail', 'type_etat', 'date_etat',
            'compteur_eau', 'compteur_electricite', 'compteur_gaz',
            'observations', 'nombre_cles', 'detail_cles',
            'etat_general', 'signe_bailleur', 'signe_locataire', 'date_signature',
            'notes'
        ]
        widgets = {
            'detail_cles': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ReversementForm(forms.ModelForm):
    """Formulaire de reversement proprietaire"""

    class Meta:
        model = ReversementProprietaire
        fields = [
            'proprietaire', 'mois', 'annee',
            'total_loyers', 'honoraires', 'autres_deductions', 'montant_reverse',
            'date_reversement', 'mode_reversement', 'reference_paiement',
            'statut', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_mois(self):
        mois = self.cleaned_data.get('mois')
        if mois is not None:
            if mois < 1 or mois > 12:
                raise ValidationError("Le mois doit etre entre 1 et 12.")
        return mois

    def clean(self):
        cleaned_data = super().clean()
        total_loyers = cleaned_data.get('total_loyers') or Decimal('0')
        honoraires = cleaned_data.get('honoraires') or Decimal('0')
        autres_deductions = cleaned_data.get('autres_deductions') or Decimal('0')
        montant_reverse = cleaned_data.get('montant_reverse')

        # Verifier la coherence des montants
        calcul_attendu = total_loyers - honoraires - autres_deductions
        if montant_reverse and abs(montant_reverse - calcul_attendu) > Decimal('0.01'):
            self.add_error('montant_reverse',
                f"Le montant a reverser devrait etre {calcul_attendu} "
                f"(total - honoraires - deductions)."
            )

        return cleaned_data


# Formulaires de recherche et filtres

class ProprietaireFilterForm(forms.Form):
    """Formulaire de filtre pour les proprietaires"""
    type_proprietaire = forms.ChoiceField(
        choices=[('', 'Tous')] + list(Proprietaire.TYPES),
        required=False
    )
    q = forms.CharField(max_length=100, required=False, label='Recherche')


class BienFilterForm(forms.Form):
    """Formulaire de filtre pour les biens"""
    statut = forms.ChoiceField(
        choices=[('', 'Tous')] + list(BienImmobilier.STATUTS),
        required=False
    )
    type_bien = forms.ChoiceField(
        choices=[('', 'Tous')] + list(BienImmobilier.TYPES_BIEN),
        required=False
    )
    proprietaire = forms.ModelChoiceField(
        queryset=Proprietaire.objects.filter(actif=True),
        required=False,
        empty_label='Tous'
    )
    q = forms.CharField(max_length=100, required=False, label='Recherche')


class BailFilterForm(forms.Form):
    """Formulaire de filtre pour les baux"""
    statut = forms.ChoiceField(
        choices=[('', 'Tous'), ('all', 'Tous')] + list(Bail.STATUTS),
        required=False
    )
    type_bail = forms.ChoiceField(
        choices=[('', 'Tous')] + list(Bail.TYPES_BAIL),
        required=False
    )
    q = forms.CharField(max_length=100, required=False, label='Recherche')


class LoyerFilterForm(forms.Form):
    """Formulaire de filtre pour les loyers"""
    mois = forms.IntegerField(min_value=1, max_value=12, required=False)
    annee = forms.IntegerField(min_value=2020, max_value=2030, required=False)
    statut = forms.ChoiceField(
        choices=[('', 'Tous')] + list(Loyer.STATUTS),
        required=False
    )


class IncidentFilterForm(forms.Form):
    """Formulaire de filtre pour les incidents"""
    statut = forms.ChoiceField(
        choices=[('', 'Tous')] + list(Incident.STATUTS),
        required=False
    )
    priorite = forms.ChoiceField(
        choices=[('', 'Toutes')] + list(Incident.PRIORITES),
        required=False
    )
    q = forms.CharField(max_length=100, required=False, label='Recherche')

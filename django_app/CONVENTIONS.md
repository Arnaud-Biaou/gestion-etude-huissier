# Conventions de développement - Étude Me BIAOU

## 1. Nommage des champs

### Timestamps
- Création : `date_creation` (DateTimeField, auto_now_add=True)
- Modification : `date_modification` (DateTimeField, auto_now=True)

### FK Créateur
- Champ : `cree_par`
- Related_name : `{model_plural}_crees`

### Booléens
- Préfixe `est_` : est_actif, est_client_assujetti_aib

## 2. Numérotation automatique

| Modèle | Format | Exemple |
|--------|--------|---------|
| Dossier | {175+n}_{MMYY}_MAB | 176_1225_MAB |
| Facture | FAC-{YYYY}-{NNNNN} | FAC-2025-00001 |
| Proforma | PRO-{YYYY}-{NNNNN} | PRO-2025-00001 |
| Avoir | AVO-{YYYY}-{NNNNN} | AVO-2025-00001 |

## 3. Fiscalité béninoise

### Groupes de taxation MECeF
- **A** : Exonéré (débours, frais) → TVA 0%
- **B** : Taxable → TVA 18%
- **E** : TPS → 0% sur facture (5% annuel)

### AIB (Acompte Impôt Bénéfices)
- Taux : 3%
- Appliqué si : `est_client_assujetti_aib = True`
- Calcul : `montant_aib = montant_ht * 0.03`
- Net à payer : `montant_ttc - montant_aib`

## 4. Affichage des parties

### Convention "C/" (versus)
- Format : `{Demandeur} C/ {Défendeur}`
- Avec multiples : `{Demandeur} C/ {Défendeur} et 2 autres`
- Méthode : `dossier.get_intitule_parties()`

### Rôles des parties
- `demandeur` : Partie demanderesse (créancier)
- `defendeur` : Partie défenderesse (débiteur)
- `tiers` : Tiers intervenant

## 5. Structure des modèles

### Modèle de base recommandé
```python
class MonModele(models.Model):
    # Champs métier
    ...

    # Métadonnées
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        'rh.Employe',
        on_delete=models.SET_NULL,
        null=True,
        related_name='monmodeles_crees'
    )

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Mon modèle"
        verbose_name_plural = "Mes modèles"
```

## 6. API JSON

### Format de réponse standard
```json
{
    "success": true,
    "data": {...},
    "message": "Opération réussie"
}
```

### Format d'erreur
```json
{
    "success": false,
    "error": "Description de l'erreur"
}
```

---
*Généré le : 2025-12-06*

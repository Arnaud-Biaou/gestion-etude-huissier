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
```
Demandeur C/ Défendeur
```

### Convention "et X autres"
```
1 partie  : DUPONT Jean
2 parties : DUPONT Jean et 1 autre
3+ parties: DUPONT Jean et 2 autres
```

### Exemple complet
```
BANQUE XYZ et 1 autre C/ DUPONT Jean et 3 autres
```

## 5. Structure des lignes de facturation

### Type Acte
- honoraires + timbre + enregistrement = montant_ht
- TVA sur honoraires uniquement (ou selon groupe)

### Type Débours
- prix_unitaire × quantité = montant_ht
- Généralement exonéré (groupe A)

---
*Dernière mise à jour : 2025-12-06*

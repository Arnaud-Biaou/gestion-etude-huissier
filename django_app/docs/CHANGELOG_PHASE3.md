# Changelog - PHASE 3 (Audit Complet Module Dossier)

**Date :** Novembre 2025
**Système :** Django Gestion Étude Huissier (Bénin)
**Conformité :** OHADA + Loi 2024-10 + Décret 2017-066

---

## RÉSUMÉ EXÉCUTIF

| Catégorie | Avant | Après | Impact |
|-----------|-------|-------|--------|
| **Calcul intérêts** | Statique (bug) | Dynamique + majoration 50% | Loi 2024-10 conforme |
| **Émoluments** | Barème incorrect | Décret 2017-066 | Conformité légale |
| **Statuts** | Non validés | Transitions strictes | Zéro corruption |
| **Type titre** | Texte libre | 6 choix | Cohérence métier |
| **Performance** | Lente | Indexes optimisés | Requêtes accélérées |
| **Montants négatifs** | Acceptés | Refusés | Validation stricte |

---

## CORRECTIONS CRITIQUES

### CRIT-01 : Race Condition Génération Références
- **Commit :** `5402fcd`
- **Problème :** 2 dossiers créés simultanément → références dupliquées
- **Solution :** Retry automatique + transaction atomique + IntegrityError
- **Code :** `gestion/views.py` (nouveau_dossier avec retry loop)
- **Impact :** Zéro risque de collision

### CRIT-02 : Transaction Non-Atomique Basculement
- **Commit :** `3217e0b`
- **Problème :** `basculement.save()` puis `dossier.save()` → corruption possible
- **Solution :** Décorateur `@transaction.atomic`
- **Code :** `gestion/models.py:basculer_vers_force()`
- **Impact :** Atomicité garantie

### CRIT-03 : Indexes Manquants
- **Commit :** `fa5362b`
- **Problème :** Requêtes lentes sur statut, type_dossier, phase, dates
- **Solution :** 5 indexes DB ajoutés + Meta.indexes
- **Migration :** `0018_add_dossier_indexes.py`
- **Impact :** Performance améliorée

---

## CORRECTIONS IMPORTANTES

### IMP-02 : Validation Transitions Statut
- **Commit :** `5b32d65`
- **Problème :** cloture→actif possible (devrait être terminal)
- **Solution :** Dict `TRANSITIONS_PERMISES` + méthode `changer_statut()`
- **Code :**
  - `gestion/models.py` (Dossier)
  - `recouvrement/models.py` (DossierRecouvrement)
- **Impact :** Transitions validées, état terminal protégé

### IMP-03 : Valeurs Hardcodées
- **Commit :** `2559252`
- **Problème :** prefix=175, suffix="MAB" en dur dans code
- **Solution :** `ConfigurationEtude.dossier_numero_cabinet` + `.dossier_initiales_huissier`
- **Migration :** `parametres/0005_add_dossier_reference_config.py`
- **Impact :** Configurabilité, zéro hardcoding

### IMP-04 : N+1 Queries
- **Commit :** `a231833`
- **Problème :** `demandeurs.first() + defendeurs.first()` → requêtes excessives
- **Solution :** `prefetch_related('dossier__demandeurs', 'dossier__defendeurs')`
- **Code :** `gestion/views.py` (api_encaissements_liste)
- **Impact :** Réduction significative des requêtes

---

## CORRECTIONS LÉGALES (Conformité)

### LG-01 : Date d'Exécutorité
- **Commit :** `a42b1c0`
- **Migration :** `0019_add_date_executoire.py`
- **Champ :** `Dossier.date_executoire` (DateField, null=True, blank=True)
- **Raison :** Calcul majoration 50% (Loi 2024-10, Art. 3)
- **Impact :** Majoration 50% après 2 mois d'exécutorité

### LG-02 : Type Titre Exécutoire (Choices)
- **Commit :** `a42b1c0`
- **Migration :** `0019_add_date_executoire.py`
- **Avant :** CharField(100, blank=True) → texte libre
- **Après :** CharField(20, choices=6 options) → cohérent
- **Options :** jugement, ordonnance, acte_notarie, pv_conciliation, protet, autre
- **Impact :** Cohérence métier, données structurées

### LG-03 : Barème Émoluments Décret 2017-066
- **Commit :** `b3bee16`
- **Problème :**
  ```
  Ancien (INCORRECT) : Barème simplifié non conforme
  Exemple 15M : ~490,000 FCFA (faux)

  Nouveau (CONFORME Décret 2017-066) :
  Forcé : 0-5M:10%, 5-20M:3.5%, 20-50M:2%, >50M:1%
  Exemple 15M : 850,000 FCFA (correct)
  ```
- **Changement :** `BasculementAmiableForce.calculer_emoluments_ohada()`
  → utilise `calculer_emoluments_force()` de `recouvrement.services.baremes`
- **Impact :** Conforme Décret 2017-066

### LG-04 : Calcul Intérêts Dynamique + Majoration 50%
- **Commit :** `4d25348`
- **Problème :**
  ```python
  # Avant : valeur statique
  interets_restant = self.montant_interets or 0
  ```
- **Solution :**
  ```python
  # Après : calcul dynamique avec majoration
  from recouvrement.services.calcul_interets import CalculateurInteretsOHADA
  calculateur = CalculateurInteretsOHADA()
  calcul = calculateur.calculer_avec_majoration(
      principal=self.montant_creance,
      date_debut=self.date_creance,
      date_fin=timezone.now().date(),
      date_decision_executoire=self.date_executoire
  )
  interets_calcules = calcul['total']
  ```
- **Impact :** Intérêts calculés dynamiquement avec taux UEMOA + majoration 50%

---

## AMÉLIORATIONS MINEURES

### MIN-01 : Incohérence null/blank sur cree_par
- **Commit :** `7cf2582`
- **Problème :** `null=True, blank=False` (incohérent)
- **Solution :** `null=True, blank=True`
- **Impact :** Cohérence Django

### MIN-03 : MinValueValidator sur montants
- **Commit :** `af7b900`
- **Champs :** montant_creance, montant_principal, montant_interets,
  montant_frais, montant_emoluments, montant_depens, montant_accessoires
- **Solution :** `validators=[MinValueValidator(Decimal('0'))]`
- **Impact :** Montants négatifs impossibles

### MIN-04 : type_dossier optionnel → obligatoire
- **Commit :** `53d5b5d`
- **Migration :** `0020_make_type_dossier_required.py`
- **Avant :** `blank=True` (optionnel)
- **Après :** `default='recouvrement'` (obligatoire avec default)
- **Impact :** Tous les dossiers ont un type

---

## TESTS AJOUTÉS

### Fichier : `gestion/tests/test_phase3_validations.py`
- **Commit :** `76f23f4`
- **Classes de tests :**
  - `TestDossierValidations` : Validations champs
  - `TestStatutTransitions` : Transitions de statut
  - `TestEmolumentsDecret2017066` : Barèmes conformes
  - `TestTauxUEMOA` : Taux légaux
  - `TestCalculInteretsMajoration` : Majoration 50%
  - `TestDateExecutoire` : Champ date_executoire
  - `TestTypeTitreExecutoire` : Choices type_titre

---

## MIGRATIONS CRÉÉES

| Migration | Description |
|-----------|-------------|
| `gestion/0018_add_dossier_indexes.py` | Indexes de performance |
| `gestion/0019_add_date_executoire.py` | date_executoire + TYPE_TITRE_EXECUTOIRE_CHOICES |
| `gestion/0020_make_type_dossier_required.py` | type_dossier obligatoire |
| `parametres/0005_add_dossier_reference_config.py` | Configuration référence |

---

## FICHIERS MODIFIÉS

### Modèles
- `gestion/models.py` : Dossier, BasculementAmiableForce
- `recouvrement/models.py` : DossierRecouvrement
- `parametres/models.py` : ConfigurationEtude

### Vues
- `gestion/views.py` : nouveau_dossier, modifier_dossier, api_encaissements_liste
- `recouvrement/views.py` : modifier_dossier_recouvrement

### Services
- `recouvrement/services/baremes.py` : (existant, utilisé maintenant)
- `recouvrement/services/calcul_interets.py` : (existant, intégré)

---

## RÉFÉRENCES LÉGALES

| Référence | Application |
|-----------|-------------|
| **Décret 2017-066** | Barèmes émoluments recouvrement |
| **Loi 2024-10 Art. 3** | Majoration 50% après 2 mois d'exécutorité |
| **Article 33 AUPSRVE (OHADA)** | Types de titres exécutoires |
| **Article 1254 Code Civil** | Ordre d'imputation (intérêts → principal) |
| **Taux UEMOA** | Taux légaux annuels (BCEAO) |

---

## COMMANDES DE DÉPLOIEMENT

```bash
# Appliquer les migrations
python manage.py migrate gestion
python manage.py migrate parametres

# Initialiser les taux UEMOA
python manage.py init_taux_legaux

# Lancer les tests
python manage.py test gestion.tests.test_phase3_validations -v 2

# Vérifier l'intégrité
python manage.py check
```

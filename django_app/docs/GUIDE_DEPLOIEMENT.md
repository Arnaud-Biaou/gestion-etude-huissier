# Guide de Déploiement - Corrections Phase 3

## 📋 Résumé des Corrections

Ce guide documente les corrections apportées au système de gestion d'étude d'huissier pour la conformité légale Bénin/OHADA.

### Corrections Critiques (CRIT)
| ID | Problème | Solution | Commit |
|----|----------|----------|--------|
| CRIT-01 | Race condition `generer_reference()` | Retry mechanism avec `transaction.atomic` | `5402fcd` |
| CRIT-02 | Transaction non-atomique `basculer_vers_force()` | Ajout `@transaction.atomic` | `3217e0b` |
| CRIT-03 | Indexes DB manquants | Migration `0018_add_dossier_indexes` | `fa5362b` |

### Corrections Importantes (IMP)
| ID | Problème | Solution | Commit |
|----|----------|----------|--------|
| IMP-02 | Pas de validation transitions statut | `changer_statut()` avec `TRANSITIONS_PERMISES` | `5b32d65` |
| IMP-03 | Valeurs hardcodées référence | `ConfigurationEtude` externalisé | `2559252` |
| IMP-04 | N+1 queries `get_intitule()` | `prefetch_related` ajouté | `a231833` |

### Conformité Légale
| Élément | Solution | Commit |
|---------|----------|--------|
| Date d'exécutorité | Nouveau champ `date_executoire` | `a42b1c0` |
| Types de titres OHADA | `TYPE_TITRE_EXECUTOIRE_CHOICES` (6 types) | `a42b1c0` |
| Émoluments Décret 2017-066 | `calculer_emoluments_ohada()` corrigé | `b3bee16` |
| Intérêts + majoration 50% | `CalculateurInteretsOHADA` intégré | `4d25348` |

### Améliorations Mineures
| ID | Problème | Solution | Commit |
|----|----------|----------|--------|
| MIN-01 | Incohérence null/blank `cree_par` | `blank=True` ajouté | `7cf2582` |
| MIN-03 | Pas de validation montants | `MinValueValidator(0)` | `af7b900` |
| MIN-04 | `type_dossier` optionnel | Obligatoire + default | `53d5b5d` |

---

## 🚀 Étapes de Déploiement

### Étape 1 : Préparer l'environnement

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Se placer dans le répertoire Django
cd django_app

# Vérifier les dépendances
pip install -r requirements.txt
```

### Étape 2 : Sauvegarder la base de données

```bash
# PostgreSQL
pg_dump -U postgres etude_huissier > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

### Étape 3 : Appliquer les migrations

```bash
# Vérifier l'état des migrations
python manage.py showmigrations gestion parametres

# Appliquer les migrations gestion
python manage.py migrate gestion

# Appliquer les migrations parametres
python manage.py migrate parametres

# Vérifier le succès
python manage.py showmigrations gestion parametres | grep -E "^\[X\]"
```

**Migrations à appliquer :**
- `gestion.0018_add_dossier_indexes` - Indexes de performance
- `gestion.0019_add_date_executoire` - Champ date_executoire + TYPE_TITRE_EXECUTOIRE_CHOICES
- `gestion.0020_make_type_dossier_required` - type_dossier obligatoire
- `parametres.0005_add_dossier_reference_config` - Configuration référence dossier

### Étape 4 : Initialiser les taux légaux UEMOA

```bash
# Charger les taux 2010-2025
python manage.py init_taux_legaux

# Vérifier
python manage.py shell -c "from parametres.models import TauxLegal; print(TauxLegal.objects.count(), 'taux chargés')"
```

### Étape 5 : Vérifier l'intégrité

```bash
# Check Django
python manage.py check

# Lancer les tests
python manage.py test gestion.tests.test_phase3_validations -v 2

# Vérifier la syntaxe des modèles
python manage.py makemigrations --check --dry-run
```

### Étape 6 : Redémarrer les services

```bash
# Gunicorn
sudo systemctl restart gunicorn

# Nginx (si applicable)
sudo systemctl reload nginx

# Celery (si applicable)
sudo systemctl restart celery
```

---

## ✅ Validation Post-Déploiement

### Test 1 : Création de dossier

```python
from gestion.models import Dossier
from decimal import Decimal

# Vérifier le default type_dossier
d = Dossier()
assert d.type_dossier == 'recouvrement', "Default type_dossier incorrect"

# Vérifier la validation montant négatif
from django.core.exceptions import ValidationError
d = Dossier(reference='TEST', montant_creance=Decimal('-100'))
try:
    d.full_clean()
    assert False, "Devrait rejeter montant négatif"
except ValidationError:
    pass  # OK
```

### Test 2 : Transitions de statut

```python
from gestion.models import Dossier

d = Dossier.objects.create(reference='TEST_STATUT', type_dossier='recouvrement')

# Transition valide
d.changer_statut('urgent')
assert d.statut == 'urgent'

# Transition invalide (cloture sans motif)
try:
    d.changer_statut('cloture')
    assert False, "Devrait exiger un motif"
except ValueError:
    pass  # OK
```

### Test 3 : Émoluments Décret 2017-066

```python
from decimal import Decimal
from recouvrement.services.baremes import calculer_emoluments_force

# Test avec 15M FCFA
emoluments = calculer_emoluments_force(Decimal('15000000'))
assert emoluments == Decimal('850000'), f"Attendu 850000, obtenu {emoluments}"
```

### Test 4 : Configuration externalisée

```python
from parametres.models import ConfigurationEtude

config = ConfigurationEtude.get_instance()
print(f"Numéro cabinet: {config.dossier_numero_cabinet}")
print(f"Initiales huissier: {config.dossier_initiales_huissier}")
```

---

## 📁 Fichiers Modifiés

### Modèles
```
django_app/gestion/models.py
├── TYPE_TITRE_EXECUTOIRE_CHOICES (nouveau)
├── TRANSITIONS_PERMISES (nouveau)
├── changer_statut() (nouveau)
├── date_executoire (nouveau champ)
├── titre_executoire_type (avec choices)
├── type_dossier (default='recouvrement')
├── montant_* (avec MinValueValidator)
├── basculer_vers_force() (calcul intérêts + majoration)
└── calculer_emoluments_ohada() (Décret 2017-066)

django_app/recouvrement/models.py
├── TRANSITIONS_PERMISES (nouveau)
└── changer_statut() (nouveau)

django_app/parametres/models.py
├── dossier_numero_cabinet (nouveau)
└── dossier_initiales_huissier (nouveau)
```

### Vues
```
django_app/gestion/views.py
├── nouveau_dossier() (retry mechanism)
├── modifier_dossier() (utilise changer_statut)
└── api_encaissements_liste() (prefetch_related)

django_app/recouvrement/views.py
└── modifier_dossier_recouvrement() (utilise changer_statut)
```

### Migrations
```
django_app/gestion/migrations/
├── 0018_add_dossier_indexes.py
├── 0019_add_date_executoire.py
└── 0020_make_type_dossier_required.py

django_app/parametres/migrations/
└── 0005_add_dossier_reference_config.py
```

### Tests
```
django_app/gestion/tests/
├── __init__.py
└── test_phase3_validations.py
```

---

## 🔧 Rollback (si nécessaire)

### Restaurer la base de données

```bash
# PostgreSQL
psql -U postgres etude_huissier < backup_YYYYMMDD_HHMMSS.sql

# SQLite
cp db.sqlite3.backup_YYYYMMDD_HHMMSS db.sqlite3
```

### Annuler les migrations

```bash
# Attention : perte de données possible
python manage.py migrate gestion 0017_import_tables_update
python manage.py migrate parametres 0004_add_hr_parameters_and_ipts_bareme
```

---

## 📞 Support

En cas de problème :
1. Vérifier les logs : `tail -f /var/log/gunicorn/error.log`
2. Vérifier les migrations : `python manage.py showmigrations`
3. Tester manuellement dans le shell Django : `python manage.py shell`

---

## 📚 Références Légales

- **Décret 2017-066** : Barèmes de recouvrement (amiable et forcé)
- **Loi 2024-10 Article 3** : Majoration 50% des intérêts après 2 mois d'exécutorité
- **Article 33 AUPSRVE (OHADA)** : Types de titres exécutoires
- **Article 1254 Code Civil** : Ordre d'imputation (intérêts avant principal)
- **Taux légaux UEMOA** : Publiés annuellement par la BCEAO

# Guide Utilisateur - PHASE 3 (Nouvelles Fonctionnalités)

## Résumé des changements

Votre système a été mis à jour pour être **100% conforme aux lois béninoises**.
Cette page explique ce qui a changé et comment l'utiliser.

---

## 1. DATE D'EXÉCUTORITÉ (NOUVEAU - IMPORTANT !)

### Qu'est-ce que c'est ?

La **date d'exécutorité** est la date à laquelle un titre juridique (jugement, acte notarié, etc.)
devient exécutoire, c'est-à-dire qu'on peut procéder à une saisie-exécution.

**Exemples :**
- Jugement prononcé le 15 janvier 2024 → Exécutoire le 29 janvier 2024 (délai appel 15 jours)
- Acte notarié du 1er janvier 2024 → Exécutoire immédiatement (1er janvier)

### Comment la remplir ?

**Lors de la création d'un dossier :**
```
Formulaire Création Dossier
├─ Référence : [auto-générée]
├─ Type de dossier : Recouvrement ← OBLIGATOIRE (avant : optionnel)
├─ Montant créance : 5,000,000 FCFA
├─ Date créance : 01/01/2024
├─ Date exécutorité : [NOUVEAU] 29/01/2024 ← REMPLIR ICI
├─ Type titre exécutoire : [NOUVEAU] Jugement ← REMPLIR ICI
└─ Créancier : [sélectionner]
```

### Pourquoi c'est important ?

**Majoration 50% des intérêts (Loi 2024-10) :**

Si le dossier est en recouvrement **forcé** et que la date d'exécutorité date de **plus de 2 mois** :
- Les intérêts sont **majorés de 50%**
- Exemple : 100,000 FCFA d'intérêts → 150,000 FCFA avec majoration

**Formule :**
```
Intérêts majorés = Intérêts normaux × 1.5

Exemple :
- Montant principal : 10,000,000 FCFA
- Taux UEMOA 2024 : 5.0336%
- Période : 1 an
- Intérêts normaux = 503,360 FCFA
- Avec majoration 50% = 755,040 FCFA
```

### Checklist :

- [ ] Dossier en recouvrement **forcé** ?
- [ ] Date exécutorité > 2 mois ago ?
- [ ] Type titre rempli (Jugement/Acte/Protêt) ?

**Si OUI à tous → Majoration 50% s'applique automatiquement**

---

## 2. TYPE DE TITRE EXÉCUTOIRE (NOUVEAU)

### Qu'est-ce que c'est ?

Le type de titre exécutoire définit le document qui permet l'exécution forcée.

### Choix disponibles

| Type | Exemple | Utilisation |
|------|---------|------------|
| **Jugement** | Jugement Tribunal TPI | Décision judiciaire (plus courant) |
| **Ordonnance** | Ordonnance du Président TPI | Ordonnance en cours de procédure |
| **Acte notarié** | Acte signé chez un notaire | Reconnaissance de dette notariée |
| **PV Conciliation** | Procès-verbal de conciliation | Accord homologué par tribunal |
| **Protêt** | Protêt cambaire | Non-paiement chèque/traite |
| **Autre** | (À spécifier) | Titres moins courants |

### Règle simple

**Le type doit correspondre au titre que vous possédez.**
Si vous n'êtes pas sûr, demandez au créancier.

---

## 3. MONTANTS NÉGATIFS REFUSÉS (CORRECTION)

### Changement

- **Avant :** Vous pouviez saisir `-1000 FCFA` (erreur silencieuse)
- **Après :** Le système refuse les montants négatifs

### Résultat
```
Vous tentez : Montant = -1000 FCFA
Système refuse : "Ensure this value is greater than or equal to 0"
→ Vous corrigez à 1000 FCFA
```

**Impact :** Zéro donnée corrompue dans la base.

---

## 4. TYPE DE DOSSIER OBLIGATOIRE (CORRECTION)

### Changement

- **Avant :** Type de dossier optionnel (vide accepté)
- **Après :** Type obligatoire (default = "Recouvrement")

### Impact sur vous
```
Création dossier
├─ Si vous oubliez le type
│  → Erreur : "Ce champ est obligatoire"
│  → Vous choisissez "Recouvrement" (ou autre)
└─ Auto-rempli avec "Recouvrement" par défaut
```

---

## 5. TRANSITIONS DE STATUT VALIDÉES (CORRECTION)

### Qu'est-ce qui change ?

**Avant :**
```
Statuts possibles : actif, urgent, archive, cloture
Transitions : N'importe quelle transition acceptée
Risque : Dossier clôturé → relancé (confus)
```

**Après :**
```
Transitions autorisées :
  actif ↔ urgent (aller-retour libre)
  actif ↔ archive (aller-retour libre)
  urgent ↔ archive (aller-retour libre)
  Quelconque → cloture (état final)

ATTENTION : cloture → autre (INTERDIT ! Terminal)
```

### Cas d'usage

| Cas | Avant | Après |
|-----|-------|-------|
| Clôturer dossier | Possible | Possible |
| Réouvrir clôturé | Possible (BUG) | INTERDIT (CORRECT) |
| Passer actif→urgent | Possible | Possible |
| Passer urgent→cloture | Possible | Possible |

### Attention

**Si vous devez vraiment réouvrir un dossier clôturé :**
1. Contactez l'admin
2. Admin réouvrira manuellement via base de données
3. Cela ne devrait JAMAIS arriver en procédure normale

---

## 6. ÉMOLUMENTS CONFORMES (CORRECTION DISCRÈTE)

### Qu'est-ce qui a changé ?

- **Ancien barème (INCORRECT) :** 10% sur tout → 15M FCFA = 1,500,000 FCFA
- **Nouveau barème (CONFORME) :** Décret 2017-066 → 15M FCFA = 850,000 FCFA

### Comparaison par montant

| Montant | Ancien | Nouveau | Différence |
|---------|--------|---------|-----------|
| 1M FCFA | 100K | 100K | 0 |
| 5M FCFA | 500K | 500K | 0 |
| 15M FCFA | ~490K | 850K | +360K |
| 50M FCFA | ~1,000K | 1,525K | +525K |

### Impact

- **Pour le débiteur :** Émoluments conformes à la loi
- **Pour vous :** Calcul automatique conforme au Décret

---

## FAQ

### Q1 : Mon dossier est déjà en production. Qu'est-ce qui change pour moi ?

**R :** Rien pour les dossiers existants. Les nouveaux champs (date_executoire, etc.) s'appliqueront
aux nouveaux dossiers créés après la mise à jour.

### Q2 : J'ai oublié la date d'exécutorité. Peux-je l'ajouter après ?

**R :** Oui ! Allez dans Modifier Dossier → Date exécutorité → Sauvegarder.

### Q3 : Pourquoi la majoration 50% ne s'applique pas ?

**R :** Vérifiez :
- [ ] Dossier en recouvrement **forcé** (pas amiable) ?
- [ ] Date exécutorité saisie ?
- [ ] Date exécutorité > 2 mois passé ?

### Q4 : Les dossiers clôturés peuvent-ils être rouverts ?

**R :** Non (nouvellement). C'est une protection contre les erreurs.
Si vraiment nécessaire, contactez l'admin pour intervention manuelle.

### Q5 : Les émoluments vont-ils augmenter ou diminuer pour mes clients ?

**R :** Les émoluments sont maintenant conformes au Décret 2017-066.
Cela correspond à la vraie loi, pas à une estimation.

---

## ASSISTANCE

Si vous avez des questions :
1. Relisez ce guide
2. Contactez votre administrateur
3. Consultez le système d'aide dans Django Admin

# Architecture Technique - Étude Me BIAOU

## 1. Vue d'ensemble
- Framework : Django 4.x
- Base de données : PostgreSQL
- Applications : 10

## 2. Applications Django

| App | Modèles | Description |
|-----|---------|-------------|
| gestion | ~70 | Cœur métier (dossiers, factures, proformas, créanciers) |
| parametres | 16 | Configuration globale |
| documents | 12 | GED avec versioning |
| comptabilite | 11 | SYSCOHADA |
| rh | 29 | Ressources humaines |
| agenda | 22 | RDV et tâches |
| tresorerie | 5 | Comptes et mouvements |
| gerance | 10 | Gestion locative |
| recouvrement | 6 | Suivi créances |
| portail_client | 5 | Accès clients |

## 3. Modèles principaux

### Facturation
- **Facture** : Avec AIB (3%), TVA, intégration MECeF
- **LigneFacture** : Type acte/débours, groupe taxation A/B/E
- **Proforma** : Devis convertible en facture
- **LigneProforma** : Structure identique à LigneFacture

### Fiscalité béninoise
- **Groupe A** : Exonéré (débours) - 0%
- **Groupe B** : TVA 18% (clients publics)
- **Groupe E** : TPS (0% sur facture, 5% annuel CA)
- **AIB** : Retenue 3% pour clients assujettis

### Dossiers
- **Dossier** : Référence, parties, montants créance
- **Partie** : Physique/morale, identification OHADA
- Convention affichage : "Demandeur C/ Défendeur et X autres"

## 4. Intégrations externes
- **MECeF** : API DGI Bénin (normalisation factures)
- **Drive** : Stockage documents (à configurer)
- **SMS** : Notifications (à configurer)

## 5. Conventions de code
- Timestamps : date_creation / date_modification
- FK créateur : cree_par
- Booléens : est_actif, est_client_assujetti_aib

## 6. Migrations
- Total : 59 migrations appliquées
- Dernière : 0021_add_proforma_models (gestion)

---
*Généré le : 2025-12-06*
*Version : 2.1.1*

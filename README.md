# 📋 Application de Gestion - Étude Me BIAOU

Application de gestion complète pour étude d'huissier de justice au Bénin.

## 🏛️ Présentation

Cette application permet de gérer l'ensemble des activités d'une étude d'huissier de justice :

- **Gestion des dossiers** : Création, suivi et archivage des dossiers (contentieux et non contentieux)
- **Calcul de recouvrement OHADA** : Calcul des intérêts légaux, émoluments et frais de procédure
- **Facturation MECeF** : Génération de factures normalisées conformes à la réglementation béninoise
- **Trésorerie** : Gestion des caisses et mouvements financiers
- **Drive** : Stockage et organisation des documents
- **GRH** : Gestion des collaborateurs et des accès

## 🛠️ Technologies utilisées

- **Frontend** : React 18 + Vite
- **Icônes** : Lucide React
- **Styles** : CSS personnalisé avec variables CSS

## 📦 Installation

### Prérequis
- Node.js 18+ installé sur votre machine
- npm ou yarn

### Étapes

1. **Cloner le dépôt**
```bash
git clone https://github.com/VOTRE_USERNAME/gestion-etude-huissier.git
cd gestion-etude-huissier
```

2. **Installer les dépendances**
```bash
npm install
```

3. **Lancer le serveur de développement**
```bash
npm run dev
```

4. **Ouvrir dans le navigateur**
```
http://localhost:3000
```

## 🏗️ Structure du projet

```
gestion-etude-huissier/
├── index.html          # Page HTML principale
├── package.json        # Dépendances et scripts
├── vite.config.js      # Configuration Vite
├── README.md           # Documentation
└── src/
    ├── main.jsx        # Point d'entrée React
    └── App.jsx         # Composant principal avec tous les modules
```

## 📚 Modules disponibles

| Module | Description | Statut |
|--------|-------------|--------|
| Tableau de bord | Vue d'ensemble de l'activité | ✅ Fonctionnel |
| Dossiers | Gestion complète des dossiers | ✅ Fonctionnel |
| Facturation | Factures et mémoires | ✅ Fonctionnel |
| Calcul Recouvrement | Calculs OHADA complets | ✅ Fonctionnel |
| Trésorerie | Gestion des caisses | 🚧 En cours |
| Comptabilité | SYSCOHADA | 🚧 En cours |
| RH | Gestion du personnel | 🚧 En cours |
| Drive | Stockage documents | ✅ Basique |
| Gérance | Gestion locative | 🚧 En cours |
| Agenda | Planning et RDV | 🚧 En cours |

## ⚖️ Conformité juridique

L'application respecte :
- **OHADA** : Calcul des intérêts selon les Actes Uniformes
- **UEMOA** : Taux légaux d'intérêt annuels
- **Loi 2024-10 Bénin** : Majoration des intérêts (+50%)
- **MECeF** : Facturation électronique normalisée

## 👤 Auteur

**Maître Martial Arnaud BIAOU**  
Huissier de Justice près le TPI et la Cour d'Appel de Parakou  
Bénin

## 📄 Licence

Propriétaire - Tous droits réservés © 2025

# CLAUDE.md - Gestion Etude Huissier

## Project Overview

This is a comprehensive legal management application for a bailiff's office (Etude d'Huissier de Justice) in Benin, West Africa. The application manages legal cases, debt recovery, invoicing, accounting, document management, scheduling, and HR functions.

**Author**: Maitre Martial Arnaud BIAOU - Huissier de Justice pres le TPI et la Cour d'Appel de Parakou, Benin

## Technology Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Custom CSS with CSS variables (no framework)
- **Icons**: Lucide React
- **Structure**: Monolithic single-page application in `src/App.jsx`

### Backend
- **Framework**: Django 5.0+
- **Database**: SQLite (development), configurable for production
- **Language**: Python 3.x
- **Authentication**: Django built-in auth with custom Utilisateur model

### Dependencies
```
# Python (requirements.txt)
Django>=5.0
Pillow>=10.0
reportlab>=4.0
qrcode>=7.4
python-dateutil>=2.8
openpyxl>=3.1
PyPDF2>=3.0
python-docx>=1.0
```

## Project Structure

```
gestion-etude-huissier/
├── src/                          # React Frontend
│   ├── App.jsx                   # Main monolithic React component
│   └── main.jsx                  # React entry point
├── django_app/                   # Django Backend
│   ├── manage.py
│   ├── etude_huissier/           # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── gestion/                  # Core module (dossiers, factures, parties)
│   ├── comptabilite/             # Accounting (SYSCOHADA compliant)
│   ├── documents/                # Document management & cloud storage
│   ├── agenda/                   # Calendar, tasks, reminders
│   ├── tresorerie/               # Treasury/cash management
│   ├── rh/                       # Human resources
│   ├── gerance/                  # Property management
│   ├── parametres/               # Application settings
│   ├── templates/                # Django HTML templates
│   └── static/                   # Static files (CSS)
├── package.json                  # Node.js dependencies
├── vite.config.js                # Vite configuration
├── requirements.txt              # Python dependencies
└── README.md
```

## Django Apps Description

### `gestion` (Core)
Main application module containing:
- **Utilisateur**: Custom user model extending AbstractUser with roles (admin, huissier, clerc_principal, clerc, secretaire)
- **Collaborateur**: Staff members of the office
- **Partie**: Legal parties (physical or moral persons)
- **Dossier**: Legal cases with phases (amiable/force), types (recouvrement, expulsion, constat, signification, saisie)
- **Facture/LigneFacture**: Invoicing with MECeF compliance
- **Creancier**: Creditors and portfolio management
- **Encaissement/Reversement**: Payment collection and disbursement tracking
- **ActeProcedure**: Legal procedure acts with tariffs
- **Memoire**: Fee statements for court authorities (cedules)

### `comptabilite` (Accounting)
SYSCOHADA-compliant accounting:
- **ExerciceComptable**: Fiscal years
- **CompteComptable**: Chart of accounts (Classes 1-9)
- **Journal**: Accounting journals (AC, VE, BQ, CA, OD, AN, CL)
- **EcritureComptable/LigneEcriture**: Journal entries
- **Lettrage**: Account reconciliation
- **DeclarationTVA**: VAT declarations
- **RapportComptable**: Financial reports (balance, trial balance, ledger)

### `documents` (Document Management)
- **CloudConnection**: Cloud storage integration (Google Drive, Dropbox, OneDrive, S3)
- **DossierVirtuel**: Virtual folder structure with bailiff-specific types
- **Document**: File storage with versioning and hashing
- **ModeleDocument**: Document templates with variables
- **SignatureElectronique**: Electronic signatures
- **PartageDocument**: Document sharing with links

### `agenda` (Scheduling)
- **RendezVous**: Appointments with recurrence support
- **Tache**: Tasks with delegation, subtasks, and progress tracking
- **Notification**: System notifications
- **JourneeAgenda**: Daily agenda closure and reporting
- **ConfigurationAgenda**: Scheduling settings

### `tresorerie` (Treasury)
Cash flow management, bank accounts, reconciliation

### `rh` (Human Resources)
Employee management, payroll, leave tracking, contracts

### `gerance` (Property Management)
Rental property management, leases, rent collection

### `parametres` (Settings)
Application configuration and parameters

## Key Business Rules

### Legal Compliance
- **OHADA**: Interest calculations follow OHADA (Organisation pour l'Harmonisation en Afrique du Droit des Affaires) rules
- **UEMOA**: Legal interest rates from UEMOA (West African Economic and Monetary Union)
- **Benin Law 2024-10**: 50% interest rate increase provision
- **MECeF**: Electronic invoicing compliance (Machine Electronique Certifiee de Facturation)
- **SYSCOHADA**: African accounting standards

### Case Reference Format
References follow pattern: `{NUMBER}_{MMYY}_{INITIALS}` (e.g., `175_1124_MAB`)

New format for dossiers: `{ANNEE}-{NUM} {TYPE} {PARTIES}` with automatic Drive folder naming

### Case Phases
1. **Phase Amiable**: Amicable recovery phase
2. **Phase Forcee**: Forced execution phase (requires titre executoire)

### Payment Imputation Order
When payments are received, they are imputed in this order:
1. Frais (fees)
2. Interets (interest)
3. Principal (principal amount)

### Document Folder Structure (Drive)
Each legal case gets 7 standard subfolders:
1. Projets d'actes
2. Actes formalises
3. Pieces
4. Courrier arrivee
5. Courrier depart
6. Factures
7. Actes exterieurs

## Development Commands

### Frontend (React/Vite)
```bash
# Install dependencies
npm install

# Start development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend (Django)
```bash
cd django_app

# Install Python dependencies
pip install -r ../requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize data
python manage.py init_data         # Core data
python manage.py init_comptabilite # Accounting chart
python manage.py init_rh           # HR data
python manage.py init_documents    # Document templates

# Run development server (port 8000)
python manage.py runserver

# Run tests
python manage.py test
```

### Management Commands
```bash
# Agenda
python manage.py cloturer_journee      # Close daily agenda
python manage.py generer_recurrences   # Generate recurring events
python manage.py traiter_rappels       # Process reminders
python manage.py calculer_statistiques # Calculate stats
python manage.py verifier_escalades    # Check escalations
```

## Code Conventions

### Python/Django
- Use French for model field names and verbose_names
- Use `verbose_name` and `verbose_name_plural` for all models
- Custom user model: `gestion.Utilisateur`
- Use UUID primary keys for documents module
- Singleton pattern for configuration models (use `get_or_create(pk=1)`)
- Decimal fields use `decimal_places=0` for CFA Franc amounts (no cents)

### React/JavaScript
- Single monolithic component in `App.jsx`
- Inline CSS styles in the component
- French UI text
- CSS variables defined in `:root` for theming

### Database
- Currency: CFA Franc (FCFA) - no decimal places
- Timezone: `Africa/Porto-Novo`
- Language: `fr-fr`

## Important Models and Their Relationships

```
Utilisateur (Custom User)
    └── Collaborateur (1:1)

Dossier (Legal Case)
    ├── Creancier (FK)
    ├── Demandeurs [Partie] (M2M)
    ├── Defendeurs [Partie] (M2M)
    ├── Factures (1:M)
    ├── Encaissements (1:M)
    └── Documents (1:M)

Facture
    └── LigneFacture (1:M)

EcritureComptable
    └── LigneEcriture (1:M)

RendezVous / Tache
    ├── Dossier (M2M / FK)
    ├── Collaborateurs (M2M)
    └── Documents (1:M)
```

## Configuration Settings

### Django Settings (django_app/etude_huissier/settings.py)
- `AUTH_USER_MODEL = 'gestion.Utilisateur'`
- `TIME_ZONE = 'Africa/Porto-Novo'`
- `LANGUAGE_CODE = 'fr-fr'`
- `FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800` (50 MB)
- Session expires after 24 hours

### Key URLs
- `/admin/` - Django admin
- `/login/`, `/logout/` - Authentication
- `/comptabilite/` - Accounting module
- `/documents/` - Document management
- `/agenda/` - Calendar and tasks
- `/tresorerie/` - Treasury
- `/rh/` - Human resources
- `/gerance/` - Property management
- `/parametres/` - Settings
- `/` - Main gestion module

## Testing

```bash
cd django_app

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test gestion
python manage.py test comptabilite
python manage.py test agenda
```

## Common Tasks

### Adding a New Model
1. Define model in `{app}/models.py` with French verbose names
2. Register in `{app}/admin.py` with appropriate fieldsets
3. Create migration: `python manage.py makemigrations {app}`
4. Apply migration: `python manage.py migrate`
5. Add URL routes if needed in `{app}/urls.py`
6. Create templates in `templates/{app}/`

### Adding a New View/Template
1. Create view in `{app}/views.py`
2. Add URL in `{app}/urls.py`
3. Create template in `templates/{app}/{template_name}.html`
4. Extend `base.html` for consistent styling

### Modifying the Frontend
- All React code is in `src/App.jsx`
- Styles are embedded in the `styles` constant
- Use existing CSS classes and variables for consistency

## Security Notes

- DEBUG should be False in production
- Change SECRET_KEY in production
- Configure ALLOWED_HOSTS properly
- Use HTTPS in production
- Enable proper CSRF protection
- Validate file uploads

## Localization

- UI Language: French
- Currency: CFA Franc (FCFA)
- Date Format: DD/MM/YYYY
- Number Format: French (space as thousand separator)
- Legal terminology follows Benin/OHADA conventions

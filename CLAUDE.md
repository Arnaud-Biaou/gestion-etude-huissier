# CLAUDE.md - AI Assistant Guide for Gestion Etude Huissier

## Project Overview

**Application:** Legal Practice Management System for a Bailiff's Office (Étude d'Huissier de Justice)
**Owner:** Maître Martial Arnaud BIAOU - Huissier de Justice, Parakou, Benin
**License:** Proprietary - All rights reserved © 2025

This is a full-stack web application for managing a bailiff's legal practice in Benin, handling cases, billing, debt recovery, document management, treasury, and HR.

## Technology Stack

### Backend
- **Framework:** Django 5.2.8
- **Database:** SQLite3 (development), PostgreSQL-ready
- **Python:** 3.x
- **Key Libraries:**
  - `Pillow` - Image processing
  - `reportlab` - PDF generation
  - `qrcode` - QR code generation
  - `python-dateutil` - Date calculations (OHADA)
  - `openpyxl` - Excel exports
  - `PyPDF2` - PDF manipulation
  - `python-docx` - Word documents

### Frontend
- **Framework:** React 18.2.0
- **Build Tool:** Vite 5.0.0
- **Icons:** Lucide React

## Project Structure

```
gestion-etude-huissier/
├── django_app/                    # Django backend
│   ├── manage.py                  # Django CLI
│   ├── etude_huissier/            # Project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── gestion/                   # Core management (main app)
│   │   ├── models.py              # 40+ models
│   │   ├── views.py               # 100+ views
│   │   ├── urls.py                # 150+ endpoints
│   │   ├── services/              # Business logic
│   │   └── management/commands/   # CLI commands
│   │
│   ├── recouvrement/              # Debt recovery
│   ├── documents/                 # Document management
│   ├── tresorerie/                # Treasury
│   ├── parametres/                # Settings
│   ├── comptabilite/              # Accounting
│   ├── portail_client/            # Client portal
│   ├── rh/                        # Human resources
│   ├── gerance/                   # Real estate
│   ├── agenda/                    # Calendar
│   │
│   ├── templates/                 # HTML templates (133 files)
│   └── static/                    # CSS/JS assets
│
├── src/                           # React frontend
│   ├── main.jsx
│   └── App.jsx
│
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies
└── vite.config.js                 # Vite configuration
```

## Django Apps Overview

| App | Purpose | Status |
|-----|---------|--------|
| `gestion` | Core: cases, invoices, parties, creditors | ✅ Functional |
| `recouvrement` | Debt recovery, OHADA interest calculations | ✅ Functional |
| `documents` | Document management, cloud storage | ✅ Functional |
| `tresorerie` | Bank accounts, cash flow | 🚧 In progress |
| `parametres` | Global configuration, jurisdictions | ✅ Functional |
| `portail_client` | Client portal access | ✅ Functional |
| `comptabilite` | SYSCOHADA accounting | 🚧 In progress |
| `rh` | HR & personnel | 🚧 In progress |
| `gerance` | Real estate management | 🚧 In progress |
| `agenda` | Calendar & scheduling | 🚧 In progress |

## Development Commands

### Backend (Django)

```bash
# Navigate to Django directory
cd django_app

# Run development server
python manage.py runserver

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Initialize default data
python manage.py init_data

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Collect static files (production)
python manage.py collectstatic
```

### Frontend (React)

```bash
# Install dependencies
npm install

# Run dev server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Key Models (gestion app)

- **Utilisateur** - Custom user model with roles
- **Dossier** - Legal case/file
- **Partie** - Legal party (plaintiff/defendant)
- **Creancier** - Creditor with portfolio tracking
- **Facture/LigneFacture** - Invoice system
- **Encaissement** - Collections received
- **Reversement** - Remittances to creditors
- **Memoire** - Fee memoranda
- **ActeSecurise** - Secure acts with QR verification
- **ActeProcedure** - Legal acts/documents

## Key Models (recouvrement app)

- **DossierRecouvrement** - Recovery case
- **PaiementRecouvrement** - Recovery payments
- **PointGlobalCreancier** - Multi-file creditor summaries
- **ImputationManuelle** - Manual payment allocation

## Important Business Logic

### OHADA Interest Calculation (`recouvrement/services/calcul_interets.py`)
- Dies a quo (start day) counts
- Dies ad quem (end day) does not count
- 365-day civil year base
- +50% after 2 months (Benin Law 2024-10)

### Payment Allocation Priority
1. Fees (frais)
2. Emoluments
3. Interest (intérêts)
4. Principal

### Invoice Compliance
- MECeF normalization for Benin
- 18% TVA standard rate
- Automated numbering

## URL Patterns

### Authentication
- `/login/` - Login
- `/logout/` - Logout
- `/password-reset/` - Password reset

### Core Endpoints
- `/` - Dashboard
- `/dossiers/` - Case list
- `/dossiers/nouveau/` - Create case
- `/dossiers/<id>/` - Case detail
- `/facturation/` - Invoicing
- `/memoires/` - Memoranda
- `/creanciers/` - Creditors
- `/encaissements/` - Collections
- `/reversements/` - Remittances

### API Endpoints
- `api/calculer-interets/` - Interest calculation
- `api/calculer-emoluments/` - Fee calculation
- `api/sauvegarder-facture/` - Save invoice
- `api/creanciers/` - Creditor CRUD
- `api/dashboard/` - Analytics

### Public Endpoints (No Auth)
- `verification/` - Act verification
- `v/<code>/` - Short verification link

## Code Conventions

### Python/Django

1. **Models:**
   - Use UUIDs for sensitive models
   - Include `created_at`/`updated_at` or `date_creation`/`date_modification`
   - Define `to_dict()` for API serialization
   - Use explicit `on_delete` policies
   - Include `verbose_name` in Meta

2. **Views:**
   - Use `@login_required` decorator
   - Use `@admin_required` for admin-only views
   - Return JSON for API endpoints
   - Handle errors with try/except

3. **Services:**
   - Place complex business logic in `services/` directory
   - Create dedicated service classes for domain operations

### Templates

- Extend from `base.html`
- Organize by app in `templates/<app_name>/`
- Use Django template tags

### JavaScript/React

- Components in `src/`
- Use Lucide React for icons
- CSS variables for theming

## User Roles

| Role | Access Level |
|------|--------------|
| `admin` | Full access |
| `huissier` | Bailiff access |
| `clerc_principal` | Senior clerk |
| `clerc` | Clerk |
| `secretaire` | Secretary (limited) |

## Legal Compliance

This application implements:
- **OHADA** - Uniform Acts on debt recovery
- **UEMOA** - Legal interest rates
- **Benin Law 2024-10** - Interest rate increases
- **MECeF** - Electronic invoicing
- **SYSCOHADA** - Accounting standards

## Testing

Test files are located in each app:
- `django_app/gestion/tests.py`
- `django_app/comptabilite/tests.py`
- `django_app/agenda/tests.py`

Run tests with:
```bash
cd django_app
python manage.py test
```

## Environment Variables

For production, set:
- `DJANGO_SECRET_KEY` - Secret key
- `DJANGO_DEBUG=False` - Disable debug mode

## Database

Development uses SQLite (`db.sqlite3`). For production, configure PostgreSQL in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'etude_huissier',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Common Tasks

### Adding a New Feature

1. Create/update models in `models.py`
2. Run migrations: `makemigrations` + `migrate`
3. Add views in `views.py`
4. Create URL patterns in `urls.py`
5. Add templates in `templates/<app>/`
6. Update tests

### Adding API Endpoint

1. Add view function with JSON response
2. Add URL pattern with `api/` prefix
3. Handle authentication with decorators
4. Return proper HTTP status codes

### Generating PDFs

Use `reportlab` for PDF generation. See examples in:
- `gestion/pdf_memoire.py`
- `recouvrement/services/pdf_decompte.py`
- `recouvrement/services/pdf_point_global.py`

## File Locations

| File Type | Location |
|-----------|----------|
| Django settings | `django_app/etude_huissier/settings.py` |
| Main URLs | `django_app/etude_huissier/urls.py` |
| Core models | `django_app/gestion/models.py` |
| Core views | `django_app/gestion/views.py` |
| Templates | `django_app/templates/` |
| Static files | `django_app/static/` |
| React app | `src/App.jsx` |

## Important Notes for AI Assistants

1. **Language:** This is a French application for Benin. UI text, comments, and documentation should be in French.

2. **Legal Domain:** The application deals with legal procedures. Be careful with terminology (huissier, acte, signification, etc.).

3. **OHADA Compliance:** Interest calculations must follow OHADA rules strictly.

4. **Security:** The app handles sensitive legal and financial data. Follow security best practices.

5. **Custom User Model:** Always use `gestion.Utilisateur`, not Django's default User.

6. **Decimal Precision:** Use `Decimal` for all financial calculations, never `float`.

7. **Timezone:** Application uses `Africa/Porto-Novo` timezone.

8. **Date Format:** Use French date format (DD/MM/YYYY).

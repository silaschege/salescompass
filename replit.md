# SalesCompass CRM - Replit Setup

## Overview
SalesCompass is a comprehensive multi-tenant B2B CRM platform built with Django 5.1. It includes features for managing leads, opportunities, accounts, cases, billing, marketing campaigns, automation workflows, and more.

**Status**: Successfully configured for Replit environment (December 4, 2025)

## Quick Start

### Access the Application
- The development server runs automatically on startup
- Access the web interface through the Replit webview
- Admin panel: `/admin/`
- Login credentials: 
  - Email: `admin@salescompass.io`
  - Password: `Admin123!`

### Development Server
The Django development server is configured to run on `0.0.0.0:5000` and starts automatically via the workflow.

## Project Structure

```
salescompass/
├── core/                   # Main Django project directory
│   ├── salescompass/       # Django settings and configuration
│   │   ├── settings.py     # Main settings file
│   │   ├── urls.py         # URL routing
│   │   └── wsgi.py         # WSGI configuration
│   ├── accounts/           # Account management module
│   ├── leads/              # Lead management module
│   ├── opportunities/      # Sales opportunities module
│   ├── cases/              # Customer support cases
│   ├── billing/            # Billing and subscriptions
│   ├── marketing/          # Marketing campaigns
│   ├── automation/         # Workflow automation
│   ├── dashboard/          # Customizable dashboards
│   ├── reports/            # Reporting engine
│   └── ... (20+ other modules)
├── requirements.txt        # Python dependencies
└── replit.md              # This file
```

## Technology Stack

### Backend
- **Django 5.2.9** - Web framework
- **Python 3.12** - Programming language
- **PostgreSQL** - Database (Replit built-in Neon-backed)
- **Django REST Framework** - API development
- **Gunicorn/Daphne** - Production WSGI/ASGI server

### Optional Services (not running by default)
- **Celery** - Asynchronous task processing (configured for eager mode)
- **Redis** - Caching and message broker (optional)
- **Elasticsearch** - Full-text search (optional)
- **Channels** - WebSocket support (using in-memory layer)

## Configuration Changes for Replit

### Settings Modified
1. **Static Files**: Added `STATIC_ROOT` for collectstatic
2. **Security**: Production-ready security settings with environment variable support
   - SECRET_KEY: Mandatory in production (REPLIT_DEPLOYMENT=1)
   - DEBUG: Forced to False in production
   - ALLOWED_HOSTS: Dynamic based on Replit environment variables
   - CSRF_TRUSTED_ORIGINS: Properly configured for production
   - Security headers: HSTS, secure cookies, proxy SSL header, etc.
3. **Channels Layer**: Automatically uses Redis when available, falls back to in-memory
4. **Celery**: Smart configuration - eager mode when no broker, async when Redis available
5. **ASGI Deployment**: Uses Daphne for WebSocket/Channels support

## Key Features

### Core CRM Modules
- **Leads**: Lead capture, qualification, and pipeline management
- **Opportunities**: Sales pipeline and deal tracking
- **Accounts**: Company and contact management
- **Cases**: Customer support ticket system
- **Automation**: Workflow builder and automation engine
- **Marketing**: Email campaigns and drip marketing
- **Billing**: Subscription management and invoicing
- **Reports**: Custom report builder
- **Dashboard**: Customizable widget-based dashboards

### Platform Features
- **Multi-tenancy**: Complete tenant isolation
- **Role-based Access Control**: Fine-grained permissions
- **Audit Logs**: Comprehensive activity tracking
- **Feature Flags**: A/B testing and gradual rollouts
- **API**: RESTful API with authentication
- **NPS**: Net Promoter Score tracking
- **Commissions**: Sales commission calculations

## Database

### Current Setup
- Using SQLite for development (db.sqlite3)
- Database is already migrated with all tables created
- Superuser account created: `admin` / `admin123`

### To Use PostgreSQL (Production)
1. Create a Replit PostgreSQL database
2. Update `DATABASES` in settings.py:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PGDATABASE'),
        'USER': os.getenv('PGUSER'),
        'PASSWORD': os.getenv('PGPASSWORD'),
        'HOST': os.getenv('PGHOST'),
        'PORT': os.getenv('PGPORT'),
    }
}
```
3. Run migrations: `python manage.py migrate`

## Deployment

### Current Configuration
- **Type**: Autoscale deployment
- **Server**: Daphne (ASGI server for Channels/WebSocket support)
- **Command**: `cd core && daphne -b 0.0.0.0 -p 5000 salescompass.asgi:application`

### To Deploy
1. Set the `SECRET_KEY` environment variable (required for production)
2. Click the "Deploy" button in Replit
3. The application will automatically run in production mode with:
   - DEBUG forced to False
   - HTTPS enforcement
   - Secure cookies and headers
4. Optionally set `REDIS_URL` for async tasks and real-time features
5. Consider switching to PostgreSQL for production database

## Common Tasks

### Run Migrations
```bash
cd core && python manage.py migrate
```

### Create Superuser
```bash
cd core && python manage.py createsuperuser
```

### Collect Static Files
```bash
cd core && python manage.py collectstatic
```

### Access Django Shell
```bash
cd core && python manage.py shell
```

### Run Tests
```bash
cd core && python manage.py test
```

## Optional Services Setup

### Enable Redis (for Celery and Channels)
If you want to enable asynchronous tasks and real-time features:
1. Install Redis via Replit or use an external Redis service
2. Update settings.py to use Redis for Celery and Channels
3. Start Celery worker: `celery -A salescompass worker -l info`
4. Start Celery beat: `celery -A salescompass beat -l info`

### Enable Elasticsearch (for search)
1. Set up an Elasticsearch instance
2. Configure ELASTICSEARCH_HOST in environment variables
3. Run: `cd core && python manage.py elasticsearch_setup`

## Troubleshooting

### Static Files Not Loading
Run: `cd core && python manage.py collectstatic --noinput`

### Database Issues
- Check that migrations are applied: `python manage.py migrate`
- View migration status: `python manage.py showmigrations`

### Port Already in Use
The workflow is configured to use port 5000. If there are issues, restart the workflow.

## Recent Changes (Dec 4, 2025)

### Initial Setup
- ✅ Installed Python 3.11 and all required dependencies
- ✅ Configured Django settings for Replit environment
- ✅ Ran database migrations (SQLite)
- ✅ Created superuser account (admin/admin123)
- ✅ Configured Channels to use in-memory layer
- ✅ Configured Celery for eager execution
- ✅ Set up development server workflow on port 5000
- ✅ Created .gitignore for Python/Django
- ✅ Configured deployment with Gunicorn
- ✅ Collected static files

### Infrastructure Enhancements (Dec 4, 2025)
- ✅ **Event Bus System** (`core/core/event_bus.py`)
  - Centralized event routing to automation, engagement, audit logs
  - Async/sync processing based on Celery availability
  - Cross-module communication without tight coupling

- ✅ **Audit Logging Middleware** (`core/core/audit_middleware.py`)
  - Automatic audit logging for sensitive operations
  - IP address and user agent tracking
  - State before/after capture for model changes

- ✅ **Feature Flag Middleware** (`core/core/feature_flag_middleware.py`)
  - URL-based feature flag enforcement
  - Template context processor for feature checks
  - Superuser/staff bypass for testing

- ✅ **Email Service** (`core/communication/email_service.py`)
  - SendGrid integration with API
  - SMTP fallback for development
  - Template-based emails

- ✅ **Wazo Telephony Adapter** (`core/communication/wazo_adapter.py`)
  - Call initiation and control
  - SMS messaging
  - Call logging to CRM

- ✅ **Stripe Payment Adapter** (`core/billing/stripe_adapter.py`)
  - Customer management
  - Subscription CRUD
  - Checkout sessions and billing portal
  - Webhook handling

- ✅ **Infrastructure Metrics** (`core/infrastructure/metrics.py`)
  - API call tracking
  - Model operation tracking
  - System health checks

- ✅ **Product Catalog Consolidation**
  - Resolved duplication between sales and products modules
  - sales module now references products.Product

## Integration Configuration

To enable the integrations, set these environment variables:

### SendGrid (Email)
```
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Stripe (Payments)
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Wazo (Telephony)
```
WAZO_API_URL=https://your-wazo-server.com
WAZO_API_KEY=your_wazo_api_key
WAZO_TENANT_UUID=your_tenant_uuid
```

### Redis (Async Processing)
```
REDIS_URL=redis://localhost:6379
```

## User Preferences
- Development database: PostgreSQL (Replit built-in)
- Async services (Celery/Redis): Disabled by default (can be enabled)
- Search (Elasticsearch): Not configured (optional)

## Architecture Overview

### Module Categories
- **Core Apps**: core, tenants, accounts, dashboard, billing
- **Feature Apps**: sales, leads, products, opportunities, proposals, cases, communication, engagement, nps, marketing, reports, automation, settings_app, learn, tasks, commissions, developer
- **Control Plane Apps**: infrastructure, audit_logs, feature_flags, global_alerts

### Builders Available
- Dashboard Builder (widget-based dashboards)
- Workflow/Automation Builder (visual workflow design)
- Landing Page Builder (marketing)
- Email Template Builder
- Report Builder

## Control Plane - ACTIVATED

### Feature Flags (20 flags seeded)
Access via `/admin/feature_flags/featureflag/`

**Active Flags (13):**
- API v2, API Rate Limiting, Audit Logging
- Leads, Opportunities, Cases, NPS, Marketing, Automation, Engagement, Commissions modules
- Custom Fields, Webhooks

**Inactive Flags (7):** Ready for gradual rollout
- Beta Features, New Reports, Advanced Analytics
- Multi-Currency, Email Integration, Telephony Integration, Stripe Billing

### Usage in Code

**URL-based enforcement (settings.py):**
```python
FEATURE_FLAG_URL_RULES = {
    '/beta/': 'beta_features',
    '/api/v2/': 'api_v2',
    '/new-reports/': 'new_reports',
}
```

**Decorator-based:**
```python
from core.feature_flag_middleware import require_feature

@require_feature('new_reports')
def new_reports_view(request):
    ...
```

**Template-based:**
```django
{% if features.new_reports %}
    <a href="/new-reports/">Try New Reports</a>
{% endif %}
```

### Audit Logging
All POST/PUT/PATCH/DELETE requests to sensitive paths are automatically logged:
- `/admin/`, `/api/`, `/billing/`, `/settings/`, `/users/`, `/roles/`, `/tenants/`

View logs at `/admin/audit_logs/auditlog/`

### Seed New Flags
```bash
cd core && python manage.py seed_feature_flags
```

## Next Steps
1. Configure integration API keys (SendGrid, Stripe, Wazo)
2. Enable Redis for async processing if needed
3. Review feature flags in admin panel
4. Set up audit log retention policy

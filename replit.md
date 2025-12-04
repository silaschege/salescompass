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
  - Username: `admin`
  - Password: `admin123`

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
- **Django 5.1.2** - Web framework
- **Python 3.11** - Programming language
- **SQLite** - Database (default for development)
- **Django REST Framework** - API development
- **Gunicorn** - Production WSGI server

### Optional Services (not running by default)
- **Celery** - Asynchronous task processing (configured for eager mode)
- **Redis** - Caching and message broker (optional)
- **Elasticsearch** - Full-text search (optional)
- **Channels** - WebSocket support (using in-memory layer)

## Configuration Changes for Replit

### Settings Modified
1. **Static Files**: Added `STATIC_ROOT` for collectstatic
2. **Channels Layer**: Using `InMemoryChannelLayer` instead of Redis
3. **Celery**: Configured for eager execution (runs tasks synchronously)
4. **ALLOWED_HOSTS**: Already set to `['*']` for development

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
- **Server**: Gunicorn with 4 workers
- **Command**: `gunicorn --chdir core --bind 0.0.0.0:5000 --workers 4 salescompass.wsgi:application`

### To Deploy
1. Click the "Deploy" button in Replit
2. The application will use Gunicorn in production mode
3. Consider switching to PostgreSQL for production

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

## User Preferences
- Development database: SQLite (can be switched to PostgreSQL)
- Async services (Celery/Redis): Disabled by default (can be enabled)
- Search (Elasticsearch): Not configured (optional)

## Next Steps
1. Explore the application through the webview
2. Login to admin panel at `/admin/`
3. Review the various CRM modules
4. Consider enabling PostgreSQL for production use
5. Optionally enable Redis and Celery for background tasks

# SalesCompass CRM

A comprehensive multi-tenant B2B CRM platform built with Django 5.1.

## Features

- **Multi-Tenant Architecture** - Complete tenant isolation with role-based access
- **Sales Management** - Leads, opportunities, pipeline, forecasting
- **Customer Engagement** - Engagement tracking, next-best-actions, NPS surveys
- **Marketing Automation** - Campaigns, email templates, landing pages, A/B testing
- **Support Cases** - Case management with SLA tracking
- **Dashboard Builder** - Customizable drag-and-drop dashboards
- **Automation Engine** - Visual workflow builder with event triggers
- **Telephony Integration** - Wazo Platform for VoIP/call center
- **Reporting & Analytics** - Custom reports with scheduled exports
- **API** - RESTful API with token authentication

## Tech Stack

- **Backend**: Django 5.1.2, Django REST Framework
- **Database**: PostgreSQL 15
- **Task Queue**: Celery with Redis
- **Real-time**: Django Channels with WebSocket
- **Search**: Elasticsearch 7+
- **Telephony**: Wazo Platform

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-org/salescompass.git
cd salescompass
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Option A: Docker (Recommended)
```bash
cd core
docker-compose up -d
```

### 3. Option B: Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r core/requirements.txt

# Set up database
export DATABASE_URL="postgres://user:password@localhost:5432/salescompass"
cd core
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 4. Start Celery workers (for background tasks)
```bash
celery -A salescompass worker -l info
celery -A salescompass beat -l info
```

## Project Structure

```
salescompass/
├── core/                    # Django project
│   ├── accounts/           # Account & contact management
│   ├── automation/         # Workflow automation
│   ├── billing/            # Subscriptions & payments
│   ├── cases/              # Customer support
│   ├── dashboard/          # Dashboard builder
│   ├── engagement/         # Customer engagement
│   ├── leads/              # Lead management
│   ├── marketing/          # Campaign management
│   ├── opportunities/      # Sales pipeline
│   ├── reports/            # Reporting & analytics
│   ├── salescompass/       # Project settings
│   ├── tenants/            # Multi-tenant management
│   └── ...
├── ml_models/              # Machine learning infrastructure
└── docker-compose.yml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required in production |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (dev only) |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `DEBUG` | Enable debug mode | `True` in development |
| `ELASTICSEARCH_HOST` | Elasticsearch URL | `http://localhost:9200` |

## Running Tests

```bash
cd core
python manage.py test
```

## API Documentation

After starting the server, visit:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

## License

Proprietary - All rights reserved

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
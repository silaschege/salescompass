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

- **Backend**: Django 5.1.2, FastAPI (ML Engine)
- **Database**: PostgreSQL 15, Redis 7
- **Task Queue**: Celery with Redis
- **Real-time**: Django Channels with WebSocket
- **Search**: Elasticsearch 7+
- **Infrastructure**: Docker Compose, Nginx

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (Recommended)

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
docker-compose up -d
```

### 3. Option B: Manual Setup

#### Start the ML Engine (FastAPI)
```bash
cd ml_models
pip install -r requirements.txt
uvicorn main:app --port 8001
```

#### Start the CRM (Django)
```bash
cd core
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Project Structure

```
salescompass/
├── core/                    # Main CRM Platform (Django)
│   ├── infrastructure/     # ML API Client & Infrastructure tools
│   └── ... (apps)
├── ml_models/              # Decoupled ML Engine (FastAPI)
│   ├── core/               # Knowledge Graph & Ontology
│   ├── engine/             # Algorithms & Agents
│   └── main.py             # Inference API
└── docker-compose.yml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required in production |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (dev only) |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ML_SERVICE_URL` | Base URL for ML Inference | `http://localhost:8001/api/v1/ml/` |
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
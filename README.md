```markdown|CODE_EDIT_BLOCK|/home/silaskimani/Documents/replit/git/salescompass/README.md
# SalesCompass CRM

A comprehensive multi-tenant B2B CRM platform built with Django 5.1, featuring integrated AI/ML capabilities, telephony integration, and extensive business modules.

## Features

### Core CRM Features
- **Multi-Tenant Architecture** - Complete tenant isolation with role-based access control
- **Sales Management** - Leads, opportunities, pipeline, forecasting and deal tracking
- **Customer Engagement** - Engagement tracking, next-best-actions, NPS surveys
- **Marketing Automation** - Campaigns, email templates, landing pages, A/B testing
- **Support Cases** - Case management with SLA tracking
- **Customer Portal** - Self-service portal for customers
- **Dashboard Builder** - Customizable drag-and-drop dashboards

### Business Applications
- **Accounting** - Financial management and reporting
- **Billing & Payments** - Subscription management and payment processing
- **Inventory Management** - Stock tracking and product management
- **POS System** - Point of sale integration
- **HR Management** - Employee records and management
- **Project Management** - Task and project tracking
- **Procurement & Purchasing** - Supplier and purchase order management
- **Expense Tracking** - Expense management and approval workflows
- **Manufacturing** - Production planning and tracking
- **Logistics & Supply Chain** - Shipping and logistics coordination
- **Loyalty Programs** - Customer rewards and retention systems
- **Commissions** - Sales commission calculations and tracking
- **Proposals** - Professional proposal generation and tracking
- **E-commerce** - Online store integration
- **NPS Surveys** - Net Promoter Score collection and analysis
- **Quality Control** - Product and service quality tracking
- **Reports & Analytics** - Custom reports with scheduled exports
- **Communication** - Integrated messaging and notifications
- **Automation Engine** - Visual workflow builder with event triggers
- **Feature Flags** - Dynamic feature management
- **Global Alerts** - System-wide notification system

### Advanced Integrations
- **Telephony Integration** - Wazo Platform for VoIP/call center with SMS/MMS support
- **Machine Learning Engine** - Predictive analytics, lead scoring, forecasting
- **API** - RESTful API with token authentication
- **Real-time Communication** - WebSocket support via Django Channels
- **Search** - Elasticsearch integration for advanced search capabilities

## Tech Stack

### Backend
- **Framework**: Django 5.1.2 (Python 3.12+)
- **ML Engine**: FastAPI (Python 3.12+) with asynchronous processing
- **API Framework**: Django REST Framework + DRF Spectacular
- **Task Queue**: Celery with Redis
- **Real-time**: Django Channels with WebSocket support
- **Authentication**: Custom auth system with role-based permissions

### Databases & Storage
- **Primary DB**: PostgreSQL 15+ (with pgvector for ML embeddings)
- **Cache & Sessions**: Redis 7+ (with Redis Sentinel for high availability)
- **Search Engine**: Elasticsearch 7+ for full-text search
- **File Storage**: S3-compatible storage for documents and media

### Infrastructure
- **Containerization**: Docker & Docker Compose with multi-container orchestration
- **Web Server**: Nginx as reverse proxy
- **Message Broker**: Redis for Celery task queues
- **Monitoring**: Built-in system monitoring and logging

### Machine Learning & Analytics
- **ML Frameworks**: Scikit-learn, Pandas, XGBoost, Sentence Transformers, PyTorch
- **Knowledge Graph**: Custom ontological reasoning engine
- **Prediction Services**: Lead scoring, win probability, revenue forecasting
- **NLP**: Sentiment analysis and natural language processing

## Architecture Overview

### Core Modules
The system is organized into multiple Django applications:

- **access_control**: Role-based access control and permissions
- **accounting**: Financial transactions and reporting
- **accounts**: User and organization management
- **api**: REST API endpoints
- **assets**: Asset management and tracking
- **audit_logs**: Comprehensive audit trail
- **automation**: Workflow automation engine
- **billing**: Subscription and payment processing
- **cases**: Support ticket system
- **commissions**: Sales commission calculations
- **communication**: Internal and external messaging
- **customer_portal**: Customer-facing interface
- **dashboard**: Customizable dashboard builder
- **ecommerce**: E-commerce functionality
- **engagement**: Customer engagement tracking
- **expenses**: Expense management
- **feature_flags**: Feature toggle management
- **hr**: Human resources management
- **inventory**: Inventory tracking and management
- **leads**: Lead management and qualification
- **loyalty**: Customer loyalty programs
- **manufacturing**: Production and manufacturing processes
- **marketing**: Marketing campaign management
- **nps**: Net Promoter Score surveys
- **opportunities**: Sales opportunity tracking
- **pos**: Point of sale system
- **products**: Product catalog management
- **projects**: Project management
- **proposals**: Proposal generation and tracking
- **purchasing**: Procurement and purchasing
- **quality_control**: Quality assurance processes
- **reports**: Reporting and analytics
- **sales**: Sales pipeline management
- **suppliers**: Supplier management
- **tasks**: Task and workflow management
- **tenants**: Multi-tenant architecture
- **wazo**: Telephony integration with Wazo Platform

### ML Engine Architecture
The ML engine is a separate FastAPI application that provides:
- **Core**: Knowledge graph and ontological reasoning
- **Engine**: ML models and prediction algorithms
- **Services**: NLP, sentiment analysis, and recommendation services
- **Infrastructure**: Compliance logging and model monitoring

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose v2+
- Elasticsearch 7+
- Node.js (for asset compilation, if needed)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/silaschege/salescompass.git
cd salescompass
```

### 2. Set up environment variables
```bash
cd core
cp .env.example .env
# Edit .env with your configuration
```

### 3. Option A: Docker (Recommended)

Start the complete system with all services:
```bash
cd core
docker-compose up -d
```

Access the application at `http://localhost:8000`
Access the ML engine at `http://localhost:8001`

### 3. Option B: Manual Setup

#### Start the ML Engine (FastAPI)
```bash
cd ml_models
pip install -r requirements.txt
uvicorn main:app --port 8001
```

#### Install core dependencies and start CRM (Django)
```bash
cd core
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata initial_data.json  # if available
python manage.py runserver
```

#### Start Celery workers (for background tasks)
```bash
cd core
celery -A salescompass worker -l info
```

#### Start Celery Beat (for scheduled tasks)
```bash
cd core
celery -A salescompass beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| [SECRET_KEY](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L24-L24) | Django secret key | Required in production |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (dev only) |
| [REDIS_URL](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L285-L285) | Redis connection URL | `redis://localhost:6379/0` |
| [ML_SERVICE_URL](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L498-L498) | Base URL for ML Inference | `http://localhost:8001/api/v1/ml/` |
| [DEBUG](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L25-L25) | Enable debug mode | `True` in development |
| [ELASTICSEARCH_HOST](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L350-L350) | Elasticsearch URL | `http://localhost:9200` |
| `STRIPE_API_KEY` | Stripe payment processing key | Optional |
| [WAZO_AUTH_URL](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L391-L391) | Wazo authentication service URL | `http://wazo-auth:9497` |
| [WAZO_CONFD_URL](file:///home/silaskimani/Documents/replit/git/salescompass/core/salescompass/settings.py#L394-L394) | Wazo configuration service URL | `http://wazo-confd:9486` |

### Wazo Telephony Integration
The system includes comprehensive integration with Wazo Platform for:
- Voice calls (SIP/VoIP)
- SMS and MMS messaging
- Call recording and analytics
- Contact center functionality
- Real-time presence and status

## Running Tests

### Core CRM Tests
```bash
cd core
python manage.py test
```

### ML Engine Tests
```bash
cd ml_models
python -m pytest
```

## API Documentation

After starting the server, visit:
- **CRM API**: `http://localhost:8000/api/schema/swagger-ui/` or `http://localhost:8000/api/schema/redoc/`
- **ML Engine API**: `http://localhost:8001/docs` (interactive Swagger UI)

## Deployment

For a detailed step-by-step deployment guide, please refer to the [Implementation Plan](.gemini/antigravity/brain/9efab295-5152-468f-aeb1-82ee11fd6fba/implementation_plan.md).

### Production Deployment
For production environments, ensure:
1. Set `DEBUG=False`
2. Configure proper database (PostgreSQL recommended)
3. Set up Redis for caching and sessions
4. Configure SSL certificates
5. Set up proper logging
6. Configure static file serving

### Scaling Recommendations
- Separate database, cache, and application servers
- Load balancer for multiple application instances
- CDN for static assets
- Message queue for background tasks
- Monitoring and alerting systems

## Development Guidelines

### Code Standards
- Follow PEP 8 for Python code
- Use Django best practices
- Write comprehensive tests for all features
- Document APIs using DRF Spectacular
- Use type hints where appropriate

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes following code standards
4. Add tests for new functionality
5. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For support, please contact the development team or refer to the documentation in the `docs/` directory.
```
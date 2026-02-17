```markdown|CODE_EDIT_BLOCK|/home/silaskimani/Documents/replit/git/salescompass/README.md
# SalesCompass CRM

A comprehensive multi-tenant B2B CRM platform built with Django 5.1, featuring integrated AI/ML capabilities, telephony integration, and extensive business modules.

## Features

### Domain Map

Instead of 50+ random apps, the system is logically grouped into 6 functional clusters:

#### 1. CRM Core 🤝
*Everything related to the customer lifecycle and portals.*
*   **`accounts`**: User and organization management. Includes `Contact` model.
*   **`customer_portal`**: Client-facing portal for self-service.
*   **`leads`**: Potential prospects and lead qualification.
*   **`opportunities`**: Deal pipeline and sales opportunities.
*   **`sales`**: Sales quotas, forecasting, and deal closing.

#### 2. Communication & Engagement 💬
*Multi-channel interactions and customer feedback.*
*   **`communication`**: Integrated messaging (Email, SMS, WhatsApp).
*   **`engagement`**: Tracking customer activity and signals.
*   **`marketing`**: Drip campaigns and marketing automation.
*   **`loyalty`**: Customer rewards and retention programs.
*   **`nps`**: Net Promoter Score collection and analysis.
*   **`wazo`**: Telephony integration (SIP/VoIP/Call Center).

#### 3. Finance & Commerce 💰
*Revenue management, supply chain, and operations.*
*   **`billing`**: Subscription management and platform-level billing (Stripe).
*   **`invoicing`**: Tenant-to-Customer invoicing, payments, credit/debit notes.
*   **`accounting`**: General ledger, journal entries, and financial reporting.
*   **`purchasing`**: Procurement, POs, and GRN processing.
*   **`expenses`**: Employee and operational expense management.
*   **`hr`**: Employee records, payroll, and HR management.
*   **`assets`**: Asset tracking and management.
*   **`commissions`**: Sales commission calculations.
*   **`proposals`**: Quote generation and contract management.
*   **`products`**: Product catalog and pricing inventory.
*   **`suppliers`**: Vendor and supplier management.
*   **`inventory`**: Stock management and warehousing.
*   **`pos`**: Point of Sale system.

#### 4. Support & Success 🆘
*Post-sales service and customer education.*
*   **`cases`**: Customer support tickets and SLA tracking.
*   **`learn`**: Learning Management System (LMS).

#### 5. Tools & Reporting 🛠️
*Internal utilities, production, and analytics.*
*   **`automation`**: Visual workflow engine with event triggers.
*   **`reports`**: Analytics engine and custom reporting.
*   **`tasks`**: Internal user tasks and reminders.
*   **`projects`**: Project accounting and management (PSA).
*   **`manufacturing`**: MRP and production tracking.
*   **`logistics`**: Shipping and fulfillment coordination.
*   **`quality_control`**: QMS and inspections.
*   **`ecommerce`**: Mini-portal and online store functionality.
*   **`developer`**: API introspection and developer utilities.

#### 6. Platform Foundation 🏗️
*Core services that power the multi-tenant SaaS.*
*   **`core`**: Base users, common utilities, and shared abstractions.
*   **`tenants`**: Multi-tenancy isolation layer (Shared DB, Shared Schema).
*   **`dashboard`**: Main UI shell and widget system.
*   **`access_control`**: Advanced permission policies (RBAC/ABAC).
*   **`infrastructure`**: System metrics, health checks, and tasks.
*   **`audit_logs`**: Compliance and security logging.
*   **`feature_flags`**: Dynamic feature toggles.
*   **`global_alerts`**: System-wide notifications.
*   **`settings_app`**: Tenant configuration UI.

---

## Architecture Overview

SalesCompass is a multi-tenant CRM platform built on Django 5.1. It uses a **Shared Database, Shared Schema** approach for multi-tenancy, with data access automatically scoped at the middleware layer.

### ML Engine Architecture
The ML engine is a decoupled FastAPI application that provides:
- **Core Intelligence**: Knowledge graph and ontological reasoning.
- **Predictive Engine**: Lead scoring, win probability, and revenue forecasting.
- **Cognitive Services**: NLP, sentiment analysis, and event validation.
- **Audit & Monitoring**: Compliance logging and model performance tracking.

## Tech Stack

### 🚀 Backend
- **Framework**: Django 5.1.2 (Python 3.12+)
- **ML Engine**: FastAPI 2.0 (Decoupled Microservice)
- **API Framework**: Django REST Framework + DRF Spectacular (OpenAPI)
- **Task Queue**: Celery with Redis for background processing
- **Real-time**: Django Channels for WebSockets
- **Permissions**: Custom Role-Based Access Control (RBAC)

### 📊 Databases & Storage
- **Primary DB**: PostgreSQL 15+ (with pgvector support)
- **Cache**: Redis 7+ (Sessions & Task Broker)
- **Search Engine**: Elasticsearch 7+ for full-text search
- **File Storage**: S3-compatible storage for media and documents

---

## Getting Started

### Prerequisites
- Python 3.12+
- Docker & Docker Compose v2+
- PostgreSQL 15+
- Redis 7+

### ⚡ Quick Start (Docker)
The easiest way to get started is using the unified Docker Compose setup:

1. **Clone & Enter**:
   ```bash
   git clone https://github.com/silaschege/salescompass.git
   cd salescompass/core
   ```
2. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env to set your keys
   ```
3. **Launch Platform**:
   ```bash
   docker-compose up -d
   ```

#### 🌐 Access Points
- **CRM Dashboard**: [http://localhost:8000](http://localhost:8000)
- **ML Engine API**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🔥 Configuration

| Variable | Description | Default |
|:---|:---|:---|
| `SECRET_KEY` | Django security token | *Required* |
| `DATABASE_URL` | PostgreSQL connection string | `db.sqlite3` (dev) |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ML_SERVICE_URL` | Base URL for ML Inference | `http://localhost:8001/api/v1/ml/` |
| `DEBUG` | Development mode toggle | `True` |
| `ELASTICSEARCH_HOST` | Search engine URL | `http://localhost:9200` |

---

## Running Tests

### Core CRM
```bash
cd core
pytest
```

### ML Engine
```bash
cd ml_models
pytest
```

---

## Deployment & Scaling

For a step-by-step production guide, view the [Implementation Plan](.gemini/antigravity/brain/9efab295-5152-468f-aeb1-82ee11fd6fba/implementation_plan.md).

### Production Checklist
1. ✅ Set `DEBUG=False` in environment.
2. ✅ Configure PostgreSQL & Redis production instances.
3. ✅ Set up SSL via Nginx/Certbot ([setup_ssl.sh](core/scripts/setup_ssl.sh)).
4. ✅ Serve static files via Nginx or CDN.

---

## Development Guidelines

- **Standards**: Follow PEP 8 and Django best practices.
- **Documentation**: All new API endpoints must include docstrings for Spectacular.
- **Testing**: Maintain >80% code coverage.

## License

Proprietary - All rights reserved.

---

## Support

For technical assistance, contact the development team or refer to the `docs/` directory.
```
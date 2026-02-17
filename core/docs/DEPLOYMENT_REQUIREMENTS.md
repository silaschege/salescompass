# SalesCompass Core - Deployment Requirements

**Version**: 2.0  
**Last Updated**: 2026-01-21  
**Status**: Production-Ready

---

## Executive Summary

SalesCompass is a comprehensive multi-tenant B2B CRM platform built on Django 5.1. This document outlines all deployment requirements, including infrastructure, services, environment configuration, and operational considerations for production deployment.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Hardware Requirements](#2-hardware-requirements)
3. [Software Prerequisites](#3-software-prerequisites)
4. [Core Services](#4-core-services)
5. [Environment Configuration](#5-environment-configuration)
6. [Database Setup](#6-database-setup)
7. [Application Modules](#7-application-modules)
8. [External Integrations](#8-external-integrations)
9. [Security Requirements](#9-security-requirements)
10. [Scaling Considerations](#10-scaling-considerations)
11. [Deployment Procedures](#11-deployment-procedures)
12. [Monitoring & Health Checks](#12-monitoring--health-checks)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCER                            │
│                    (Nginx / Cloud LB)                           │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │                               │
    ┌─────────────▼─────────────┐   ┌─────────────▼─────────────┐
    │     CRM PLATFORM          │   │    ML ENGINE              │
    │     (Django 5.1)          │   │    (FastAPI)              │
    │     Port: 8000            │   │    Port: 8001             │
    └─────────────┬─────────────┘   └─────────────┬─────────────┘
                  │                               │
    ┌─────────────▼───────────────────────────────▼─────────────┐
    │                    SHARED INFRASTRUCTURE                   │
    ├───────────────┬───────────────┬───────────────────────────┤
    │  PostgreSQL   │     Redis     │      Elasticsearch        │
    │  (Port 5432)  │  (Port 6379)  │      (Port 9200)          │
    └───────────────┴───────────────┴───────────────────────────┘
                  │
    ┌─────────────▼─────────────────────────────────────────────┐
    │                  WAZO TELEPHONY PLATFORM                   │
    ├──────────┬──────────┬──────────┬──────────┬───────────────┤
    │ wazo-auth│wazo-confd│wazo-calld│wazo-chatd│   Asterisk    │
    │  (9497)  │  (9486)  │  (9500)  │  (9304)  │  (SIP/RTP)    │
    └──────────┴──────────┴──────────┴──────────┴───────────────┘
```

### Component Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| CRM Platform | Django 5.1.2 | Core CRM application |
| ML Engine | FastAPI 0.115.0 | AI/ML inference microservice |
| Task Queue | Celery 5.3+ | Async task processing |
| Real-time | Django Channels 4.0+ | WebSocket connections |
| Database | PostgreSQL 15 | Primary data store |
| Cache/Broker | Redis 7 | Caching, Celery broker, Channels |
| Search | Elasticsearch 7+ | Full-text search |
| Telephony | Wazo Platform | VoIP/Call center |

---

## 2. Hardware Requirements

### Minimum (Development/Testing)

| Resource | Specification |
|----------|---------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Storage | 50 GB SSD |
| Network | 100 Mbps |

### Recommended (Production)

| Resource | Specification |
|----------|---------------|
| CPU | 8+ cores |
| RAM | 32 GB |
| Storage | 500 GB NVMe SSD |
| Network | 1 Gbps |

### High Availability (Enterprise)

| Resource | Specification |
|----------|---------------|
| CPU | 16+ cores per node |
| RAM | 64 GB per node |
| Storage | 1 TB NVMe SSD (replicated) |
| Network | 10 Gbps |
| Nodes | 3+ (for clustering) |

---

## 3. Software Prerequisites

### Required

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | CRM runtime |
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Cache, broker, channels |
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Service orchestration |

### Optional (Recommended for Production)

| Software | Version | Purpose |
|----------|---------|---------|
| Nginx | 1.24+ | Reverse proxy, SSL termination |
| Elasticsearch | 7.17+ | Full-text search |
| Wazo Platform | Latest | Telephony integration |

---

## 4. Core Services

### 4.1 Docker Compose Services

The complete deployment includes these containerized services:

```yaml
# Core Application Services
services:
  web:              # Django CRM (Port 8000)
  redis:            # Cache & Message Broker (Port 6379)
  db:               # PostgreSQL Database (Port 5432)

# Wazo Telephony Platform
  wazo-db:          # Wazo PostgreSQL (Port 5432)
  wazo-auth:        # Authentication (Port 9497)
  wazo-confd:       # Configuration Daemon (Port 9486)
  wazo-call-logd:   # Call Logging (Port 9295)
  wazo-agentd:      # Agent Management (Port 9493)
  wazo-amid:        # AMI Bridge (Port 4573)
  wazo-calld:       # Call Daemon (Port 9500)
  wazo-chatd:       # Chat/SMS Daemon (Port 9304)
  wazo-webhookd:    # Webhook Daemon (Port 9300)
  asterisk:         # PBX Core (SIP 5060, ARI 8088)
```

### 4.2 Port Requirements

| Port | Protocol | Service | Notes |
|------|----------|---------|-------|
| 8000 | TCP | Django CRM | Web application |
| 8001 | TCP | ML Engine | Inference API |
| 5432 | TCP | PostgreSQL | Database |
| 6379 | TCP | Redis | Cache/Broker |
| 9200 | TCP | Elasticsearch | Search |
| 5060 | UDP/TCP | Asterisk SIP | Telephony signaling |
| 8088 | TCP | Asterisk ARI | WebSocket API |
| 10000-10100 | UDP | RTP Media | Voice/video |
| 9497 | TCP | Wazo Auth | Authentication |
| 9500 | TCP | Wazo Calld | Call control |
| 9304 | TCP | Wazo Chatd | Messaging |

### 4.3 Persistent Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | CRM database |
| `wazo_db` | `/var/lib/postgresql/data` | Wazo database |
| `redis_data` | `/data` | Redis persistence |
| `asterisk_recordings` | `/var/spool/asterisk/recording` | Call recordings |
| `asterisk_voicemail` | `/var/spool/asterisk/voicemail` | Voicemail storage |
| `asterisk_logs` | `/var/log/asterisk` | PBX logs |

---

## 5. Environment Configuration

### 5.1 Required Variables (Production)

```bash
# Django Core
SECRET_KEY=<generate-unique-key>
DEBUG=False
DATABASE_URL=postgres://user:password@db:5432/salescompass
REDIS_URL=redis://redis:6379/0

# Security
ALLOWED_HOSTS=crm.yourdomain.com,www.crm.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://crm.yourdomain.com
```

### 5.2 Wazo Platform Configuration

```bash
# Core API
WAZO_API_URL=http://wazo-auth:9497
WAZO_API_KEY=<your-wazo-api-key>
WAZO_TENANT_UUID=<your-tenant-uuid>

# Service URLs (Docker network)
WAZO_AUTH_URL=http://wazo-auth:9497
WAZO_CALLD_URL=http://wazo-calld:9500
WAZO_CHATD_URL=http://wazo-chatd:9304
WAZO_CONFD_URL=http://wazo-confd:9486
WAZO_AGENTD_URL=http://wazo-agentd:9493
WAZO_CALL_LOG_URL=http://wazo-call-logd:9295
WAZO_WEBHOOKD_URL=http://wazo-webhookd:9300

# Webhook Security
WAZO_WEBHOOK_SECRET=<hmac-secret>
WAZO_DEFAULT_SMS_NUMBER=+1234567890
```

### 5.3 External Integrations

```bash
# Twilio (SIP Trunk & WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=<auth-token>
TWILIO_SIP_DOMAIN=salescompass
TWILIO_SIP_USERNAME=<sip-username>
TWILIO_SIP_PASSWORD=<sip-password>
TWILIO_CALLER_ID=+1234567890
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WHATSAPP_SANDBOX=False

# SendGrid (Email)
SENDGRID_API_KEY=<sendgrid-key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Stripe (Billing)
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Elasticsearch
ELASTICSEARCH_HOST=http://elasticsearch:9200
ELASTICSEARCH_INDEX_PREFIX=salescompass
ELASTICSEARCH_USE_SSL=False

# ML Service
ML_SERVICE_URL=http://ml-engine:8001/api/v1/ml/
```

### 5.4 WebRTC Configuration

```bash
WEBRTC_ENABLED=True
STUN_SERVER=stun:stun.l.google.com:19302
TURN_SERVER=turn:your-turn-server.com:3478
TURN_USERNAME=<turn-username>
TURN_PASSWORD=<turn-password>
```

---

## 6. Database Setup

### 6.1 PostgreSQL Configuration

**Production Settings** (`postgresql.conf`):

```conf
# Memory
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 50MB
maintenance_work_mem = 2GB

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 64MB
max_wal_size = 4GB
min_wal_size = 1GB

# Connections
max_connections = 200
```

### 6.2 Initial Setup

```bash
# Create database and user
createdb salescompass
createuser -P salescompass_user

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE salescompass TO salescompass_user;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6.3 Backup Strategy

```bash
# Daily backup command
pg_dump -Fc -U salescompass_user -d salescompass > backup_$(date +%Y%m%d).dump

# Restore command
pg_restore -U salescompass_user -d salescompass backup_YYYYMMDD.dump
```

---

## 7. Application Modules

### 7.1 Platform Foundation

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `core` | Base users, authentication, utilities | - |
| `tenants` | Multi-tenancy isolation | core |
| `dashboard` | Main UI shell, widget builder | core, tenants |
| `access_control` | RBAC/ABAC Policies | core, tenants |
| `infrastructure` | Metrics, health monitoring | core |
| `audit_logs` | Compliance logging | core |
| `feature_flags` | Feature toggles | core |
| `global_alerts` | System notifications | core |
| `settings_app` | Tenant configuration UI | tenants |

### 7.2 CRM Core

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `accounts` | Account management | core, tenants |
| `leads` | Lead capture & scoring | core, ML |
| `opportunities` | Pipeline management | leads, accounts |
| `sales` | Sales activities tracking | opportunities |

### 7.3 Finance & Commerce

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `billing` | Subscription & invoicing | tenants, Stripe |
| `commissions` | Sales commission tracking | sales |
| `proposals` | Quote generation | opportunities, products |
| `products` | Product catalog | tenants |

### 7.4 Communication & Engagement

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `communication` | Email, calls, SMS, WhatsApp | Wazo, Twilio, SendGrid |
| `engagement` | Engagement tracking & scoring | core, ML |
| `marketing` | Campaigns, automation | communication |
| `nps` | Net Promoter Score surveys | engagement |
| `wazo` | Telephony integration | Wazo Platform |

### 7.5 Support & Success

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `cases` | Case management with SLA | accounts, communication |
| `learn` | Learning Management System | core |

### 7.6 Tools & Reporting

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `automation` | Visual workflow builder | Celery |
| `reports` | Analytics & scheduled exports | All modules |
| `tasks` | User task management | core |
| `developer` | API introspection tools | - |

---

## 8. External Integrations

### 8.1 Required Integrations

| Integration | Purpose | Required For |
|-------------|---------|--------------|
| PostgreSQL | Primary database | All features |
| Redis | Caching, Celery, Channels | Async tasks, real-time |

### 8.2 Optional Integrations

| Integration | Purpose | Features Enabled |
|-------------|---------|------------------|
| Wazo Platform | VoIP/Call center | Calling, call analytics |
| Twilio | SIP trunk, WhatsApp | PSTN calls, messaging |
| SendGrid | Transactional email | Email delivery |
| Stripe | Payment processing | Billing, subscriptions |
| Elasticsearch | Full-text search | Global search |
| ML Engine (FastAPI) | AI/ML inference | Lead scoring, predictions |

### 8.3 ML Engine Requirements

The ML Engine is a separate FastAPI microservice requiring:

```bash
# Python dependencies
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
pandas==2.2.3
scikit-learn==1.5.2
sentence-transformers==2.3.1
torch>=2.2.0
pgvector==0.2.5

# Run command
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## 9. Security Requirements

### 9.1 Production Security Settings

The following are automatically enabled when `DEBUG=False`:

```python
# SSL/HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 9.2 Authentication

- Custom User model: `core.User`
- Multi-tenant isolation via `TenantAwareModel`
- Role-Based Access Control (RBAC)
- API Token authentication for REST endpoints

### 9.3 Network Security

| Zone | Access | Notes |
|------|--------|-------|
| Public | Load balancer only | HTTPS required |
| Application | Internal network | No direct internet |
| Database | Application only | Firewalled |
| Redis | Application only | No external access |

---

## 10. Scaling Considerations

### 10.1 Horizontal Scaling

| Component | Scaling Strategy |
|-----------|------------------|
| Django/Gunicorn | Add worker processes/pods |
| Celery Workers | Add consumer processes |
| Redis | Redis Cluster or Sentinel |
| PostgreSQL | Read replicas for queries |
| Elasticsearch | Multi-node cluster |

### 10.2 Celery Workers

```bash
# Production worker configuration
celery -A salescompass worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000

# Beat scheduler (single instance)
celery -A salescompass beat --loglevel=info
```

### 10.3 Scheduled Tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `check_due_reports` | Every 5 min | Report generation |
| `process_drip_enrollments` | Every 10 min | Marketing automation |
| `calculate_tenant_usage` | Every 6 hours | Usage metering |

---

## 11. Deployment Procedures

### 11.1 Docker Compose Deployment

```bash
# Clone repository
git clone https://github.com/your-org/salescompass.git
cd salescompass

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 11.2 Production Checklist

- [ ] Set `SECRET_KEY` to a unique, secure value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] Set up PostgreSQL with proper credentials
- [ ] Configure Redis for production
- [ ] Set up SSL certificates
- [ ] Configure Nginx as reverse proxy
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up backup automation
- [ ] Configure email (SendGrid/SMTP)
- [ ] Set up Stripe webhooks (if using billing)
- [ ] Configure Wazo webhooks (if using telephony)

### 11.3 Nginx Configuration

```nginx
upstream salescompass {
    server web:8000;
}

server {
    listen 80;
    server_name crm.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name crm.yourdomain.com;

    ssl_certificate /etc/ssl/certs/salescompass.crt;
    ssl_certificate_key /etc/ssl/private/salescompass.key;

    location / {
        proxy_pass http://salescompass;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://salescompass;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }
}
```

---

## 12. Monitoring & Health Checks

### 12.1 Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/health/` | Application health |
| `/api/schema/swagger-ui/` | API documentation |
| `/api/schema/redoc/` | ReDoc API docs |

### 12.2 Key Metrics

| Metric | Alert Threshold |
|--------|-----------------|
| Response time (p95) | > 500ms |
| Error rate | > 1% |
| Database connections | > 80% pool |
| Redis memory | > 80% |
| Celery queue depth | > 1000 tasks |
| Disk usage | > 80% |

### 12.3 Log Locations

| Service | Location |
|---------|----------|
| Django | stdout/stderr (container logs) |
| Celery | stdout/stderr |
| PostgreSQL | `/var/log/postgresql/` |
| Redis | `/var/log/redis/` |
| Nginx | `/var/log/nginx/` |
| Asterisk | `/var/log/asterisk/` |

---

## Appendix A: Quick Reference Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Run tests
docker-compose exec web python manage.py test

# Collect static files
docker-compose exec web python manage.py collectstatic

# Start Celery worker
docker-compose exec web celery -A salescompass worker -l info

# Start Celery beat
docker-compose exec web celery -A salescompass beat -l info

# Start ML Engine
cd ml_models && uvicorn main:app --port 8001 --reload
```

---

## Appendix B: Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection refused | Check `DATABASE_URL`, verify PostgreSQL is running |
| Redis connection error | Check `REDIS_URL`, verify Redis is running |
| Celery tasks not executing | Verify Redis connection, check worker logs |
| WebSocket not connecting | Check Channels config, verify Redis for channels |
| Static files 404 | Run `collectstatic`, check Nginx static config |
| Email not sending | Verify `SENDGRID_API_KEY`, check spam folder |

---

*Document maintained by SalesCompass Engineering Team*

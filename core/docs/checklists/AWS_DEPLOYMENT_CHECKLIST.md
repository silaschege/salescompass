# SalesCompass CRM - AWS Deployment Checklist

## Overview

This checklist covers all steps needed to deploy SalesCompass CRM on AWS infrastructure. It encompasses infrastructure provisioning, application configuration, security hardening, and operational readiness.

---

## 1. AWS Account & IAM Setup

- [ ] Create dedicated AWS account (or use existing with separate OU)
- [ ] Enable MFA on root account
- [ ] Create IAM users/roles for deployment (least privilege)
- [ ] Create deployment IAM role for CI/CD pipeline
- [ ] Set up AWS Organizations billing alerts
- [ ] Configure CloudTrail for audit logging
- [ ] Set up AWS Config for compliance monitoring
- [ ] Tag strategy defined (Environment, Project, Owner, CostCenter)

---

## 2. Networking (VPC & Subnets)

- [ ] Create VPC with CIDR block (e.g., `10.0.0.0/16`)
- [ ] Create public subnets (2+ AZs) for load balancer
- [ ] Create private subnets (2+ AZs) for application servers
- [ ] Create isolated subnets (2+ AZs) for databases
- [ ] Set up Internet Gateway for public subnets
- [ ] Set up NAT Gateway for private subnet outbound access
- [ ] Configure route tables for each subnet tier
- [ ] Create security groups:
  - [ ] ALB security group (inbound 80, 443)
  - [ ] App server security group (inbound from ALB only on 8000)
  - [ ] Database security group (inbound from app servers only on 5432)
  - [ ] Redis security group (inbound from app servers only on 6379)
  - [ ] Elasticsearch security group (inbound from app servers only on 9200)
  - [ ] Wazo/Asterisk security group (SIP 5060, RTP 10000-10100, API ports)
- [ ] Set up VPC Flow Logs for network monitoring

---

## 3. Database (RDS PostgreSQL)

- [ ] Provision RDS PostgreSQL 15+ instance
  - [ ] Instance class: `db.r6g.large` minimum for production
  - [ ] Multi-AZ deployment enabled
  - [ ] Storage: 100GB gp3 with auto-scaling
  - [ ] Enable automated backups (30-day retention)
  - [ ] Enable Performance Insights
- [ ] Set strong master password (store in AWS Secrets Manager)
- [ ] Configure parameter group:
  - [ ] `shared_buffers = 8GB`
  - [ ] `effective_cache_size = 24GB`
  - [ ] `work_mem = 50MB`
  - [ ] `max_connections = 200`
- [ ] Create database: `salescompass`
- [ ] Create application user with limited privileges
- [ ] Set up read replicas (if needed for reporting)
- [ ] Configure backup window during low-traffic hours
- [ ] Test backup restoration procedure

### Wazo Database (if self-hosting Wazo)
- [ ] Provision separate RDS PostgreSQL 13+ for Wazo
- [ ] Or use separate database on same instance

---

## 4. Caching & Message Broker (ElastiCache Redis)

- [ ] Provision ElastiCache Redis 7+ cluster
  - [ ] Node type: `cache.r6g.large` minimum
  - [ ] Cluster mode for HA (or single-node for staging)
  - [ ] Enable at-rest and in-transit encryption
  - [ ] Enable automatic failover
- [ ] Configure Redis for three roles:
  - [ ] Celery broker (DB 0)
  - [ ] Django Channels layer (DB 1)
  - [ ] Application cache (DB 2)
- [ ] Set `maxmemory-policy allkeys-lru`
- [ ] Configure backup/snapshot schedule

---

## 5. Search (OpenSearch / Elasticsearch)

- [ ] Provision Amazon OpenSearch Service (or self-hosted Elasticsearch)
  - [ ] Instance type: `r6g.large.search` minimum
  - [ ] 2+ data nodes across AZs
  - [ ] Enable fine-grained access control
  - [ ] Enable encryption at rest and in transit
- [ ] Create index prefix: `salescompass`
- [ ] Configure OpenSearch access policies (VPC-only access)
- [ ] Set up index lifecycle management

---

## 6. Application Deployment (ECS / EC2)

### Option A: ECS Fargate (Recommended)
- [ ] Create ECR repository for application image
- [ ] Update Dockerfile for production:
  - [ ] Use `gunicorn` instead of `runserver`
  - [ ] Add `daphne` for ASGI/WebSocket support
  - [ ] Install system dependencies (libpq, etc.)
  - [ ] Set `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`
- [ ] Create ECS cluster
- [ ] Define task definitions:
  - [ ] **Web** task (Django/Gunicorn, port 8000)
  - [ ] **Worker** task (Celery worker)
  - [ ] **Beat** task (Celery beat scheduler - single instance)
  - [ ] **Channels** task (Daphne for WebSockets)
- [ ] Create ECS services with desired count
- [ ] Configure auto-scaling policies (CPU/memory based)
- [ ] Set up health checks for each service

### Option B: EC2 Instances
- [ ] Launch EC2 instances (t3.xlarge+ for production)
- [ ] Install Docker and Docker Compose
- [ ] Configure user data script for bootstrapping
- [ ] Set up Auto Scaling Group
- [ ] Configure Launch Template

### ML Engine Service
- [ ] Create separate ECR repository for ML service
- [ ] Define ML Engine task (FastAPI/Uvicorn, port 8001)
- [ ] Configure GPU instances if needed (`g4dn.xlarge`)
- [ ] Set `ML_SERVICE_URL` environment variable

---

## 7. Load Balancer & DNS

- [ ] Create Application Load Balancer (ALB)
  - [ ] HTTPS listener (port 443) with SSL certificate
  - [ ] HTTP listener (port 80) with redirect to HTTPS
  - [ ] WebSocket support enabled
- [ ] Register SSL/TLS certificate via ACM (AWS Certificate Manager)
  - [ ] Request certificate for `crm.yourdomain.com`
  - [ ] Validate domain ownership (DNS or email)
- [ ] Configure target groups:
  - [ ] Web target group (port 8000, health check `/api/health/`)
  - [ ] WebSocket target group (path `/ws/*`, stickiness enabled)
  - [ ] ML Engine target group (port 8001)
- [ ] Set up Route 53 DNS:
  - [ ] Create hosted zone for domain
  - [ ] A record (alias) pointing to ALB
  - [ ] Configure health checks
- [ ] Enable ALB access logging to S3

---

## 8. Static Files & Media (S3 + CloudFront)

- [ ] Create S3 bucket for static files (`salescompass-static`)
- [ ] Create S3 bucket for media uploads (`salescompass-media`)
  - [ ] Enable versioning
  - [ ] Configure lifecycle policies
  - [ ] Enable server-side encryption (SSE-S3 or SSE-KMS)
- [ ] Set up CloudFront distribution for static assets
  - [ ] Connect to S3 static bucket as origin
  - [ ] Configure caching headers (30-day expiry)
  - [ ] Enable gzip/brotli compression
- [ ] Configure Django `django-storages` for S3:
  - [ ] `STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'`
  - [ ] `DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'`
- [ ] Run `collectstatic` and upload to S3
- [ ] Configure CORS on media bucket if needed

---

## 9. Environment Variables & Secrets

- [ ] Store all secrets in AWS Secrets Manager:
  - [ ] `SECRET_KEY` (generate unique)
  - [ ] `DATABASE_URL`
  - [ ] `REDIS_URL`
  - [ ] `STRIPE_SECRET_KEY`
  - [ ] `STRIPE_WEBHOOK_SECRET`
  - [ ] `SENDGRID_API_KEY`
  - [ ] `WAZO_API_KEY`
  - [ ] `TWILIO_AUTH_TOKEN`
  - [ ] `TWILIO_SIP_PASSWORD`
- [ ] Set non-secret environment variables in task definition / .env:
  - [ ] `DEBUG=False`
  - [ ] `ALLOWED_HOSTS=crm.yourdomain.com`
  - [ ] `CSRF_TRUSTED_ORIGINS=https://crm.yourdomain.com`
  - [ ] `ELASTICSEARCH_HOST=https://your-opensearch-endpoint`
  - [ ] `ML_SERVICE_URL=http://ml-engine:8001/api/v1/ml/`
  - [ ] `CELERY_TIMEZONE=Africa/Nairobi`
- [ ] Verify all env vars from `.env.example` are configured
- [ ] Test secrets rotation procedure

---

## 10. Django Production Settings

- [ ] Set `DEBUG=False`
- [ ] Set unique `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with actual domain
- [ ] Configure `CSRF_TRUSTED_ORIGINS` with HTTPS domain
- [ ] Verify security settings activate when `DEBUG=False`:
  - [ ] `SECURE_SSL_REDIRECT = True`
  - [ ] `SECURE_PROXY_SSL_HEADER` for ALB
  - [ ] `SESSION_COOKIE_SECURE = True`
  - [ ] `CSRF_COOKIE_SECURE = True`
  - [ ] `SECURE_HSTS_SECONDS = 31536000`
  - [ ] `X_FRAME_OPTIONS = 'DENY'`
- [ ] Configure production logging (CloudWatch integration)
- [ ] Switch Channel Layers to Redis backend (already in settings)
- [ ] Run `python manage.py check --deploy` for Django deployment checks
- [ ] Run `python manage.py migrate` on production database
- [ ] Run `python manage.py createsuperuser` for admin access
- [ ] Run `python manage.py collectstatic --noinput`

---

## 11. Celery & Async Tasks

- [ ] Deploy Celery worker service (separate container/process)
- [ ] Deploy Celery beat scheduler (single instance only)
- [ ] Verify scheduled tasks are running:
  - [ ] `check_due_reports` (every 5 min)
  - [ ] `process_drip_enrollments` (every 10 min)
  - [ ] `calculate_tenant_usage` (every 6 hours)
- [ ] Configure Celery worker concurrency (`--concurrency=4`)
- [ ] Set task time limit (`CELERY_TASK_TIME_LIMIT = 1800`)
- [ ] Configure dead letter queue for failed tasks
- [ ] Monitor Celery queue depth via CloudWatch

---

## 12. Wazo Telephony Platform (Optional)

- [ ] Deploy Wazo services on ECS or dedicated EC2:
  - [ ] wazo-auth, wazo-confd, wazo-calld, wazo-chatd
  - [ ] wazo-call-logd, wazo-agentd, wazo-amid, wazo-webhookd
  - [ ] asterisk (requires UDP ports for SIP/RTP)
- [ ] Configure security groups for telephony ports
- [ ] Set up SIP trunk with Twilio (if using PSTN)
- [ ] Configure webhook callback URL to point to ALB
- [ ] Test inbound/outbound calling
- [ ] Configure call recording storage (S3)

---

## 13. Monitoring & Observability

- [ ] Set up CloudWatch for:
  - [ ] Application logs (Django, Celery, Channels)
  - [ ] ECS/EC2 metrics (CPU, memory, network)
  - [ ] RDS metrics (connections, IOPS, replication lag)
  - [ ] ElastiCache metrics (memory, evictions, connections)
  - [ ] ALB metrics (request count, latency, 5xx errors)
- [ ] Create CloudWatch alarms:
  - [ ] High CPU utilization (> 80%)
  - [ ] High memory utilization (> 80%)
  - [ ] HTTP 5xx error rate (> 1%)
  - [ ] RDS connection count (> 80% of max)
  - [ ] Celery queue depth (> 1000 tasks)
  - [ ] Disk usage (> 80%)
  - [ ] Response time p95 (> 500ms)
- [ ] Set up SNS notifications for alarm triggers
- [ ] Configure health check endpoints:
  - [ ] `/api/health/` - Application health
  - [ ] `/api/schema/swagger-ui/` - API documentation
- [ ] Set up AWS X-Ray for distributed tracing (optional)
- [ ] Consider Prometheus + Grafana stack for detailed metrics

---

## 14. CI/CD Pipeline

- [ ] Set up GitHub Actions / AWS CodePipeline:
  - [ ] Build Docker image on push to main
  - [ ] Push image to ECR
  - [ ] Run migrations
  - [ ] Deploy to ECS (rolling update)
  - [ ] Run smoke tests
- [ ] Configure staging environment (separate ECS cluster)
- [ ] Implement blue/green deployment strategy
- [ ] Set up automatic rollback on health check failure
- [ ] Configure branch protection rules on main

---

## 15. Backup & Disaster Recovery

- [ ] RDS automated backups (30-day retention)
- [ ] RDS snapshots before major deployments
- [ ] S3 versioning and cross-region replication for media
- [ ] Redis snapshot backups (daily)
- [ ] Document and test recovery procedures:
  - [ ] Database restore from backup
  - [ ] Application rollback procedure
  - [ ] DNS failover to secondary region (if applicable)
- [ ] Define RPO (Recovery Point Objective): < 1 hour
- [ ] Define RTO (Recovery Time Objective): < 4 hours

---

## 16. Security Hardening

- [ ] Enable AWS WAF on ALB (OWASP Top 10 rules)
- [ ] Enable AWS Shield Standard (DDoS protection)
- [ ] Configure VPC endpoint for S3 (avoid internet traffic)
- [ ] Enable encryption at rest for all services
- [ ] Enable encryption in transit (TLS everywhere)
- [ ] Run AWS Trusted Advisor security checks
- [ ] Conduct penetration testing (AWS allows without approval for most services)
- [ ] Enable GuardDuty for threat detection
- [ ] Review and rotate all secrets quarterly
- [ ] Set up AWS Config rules for compliance

---

## 17. Cost Optimization

- [ ] Use Reserved Instances or Savings Plans for predictable workloads
- [ ] Right-size instances based on actual utilization
- [ ] Enable S3 Intelligent-Tiering for media storage
- [ ] Set up billing alerts and budgets
- [ ] Review and clean up unused resources monthly
- [ ] Consider Spot Instances for Celery workers

---

## 18. Pre-Launch Verification

- [ ] Run Django deployment checklist: `python manage.py check --deploy`
- [ ] Load test with realistic traffic patterns
- [ ] Test all 44 application modules load successfully
- [ ] Test user registration and login flow
- [ ] Test multi-tenant data isolation
- [ ] Test Celery task execution
- [ ] Test WebSocket connections (Channels)
- [ ] Test email delivery (SendGrid)
- [ ] Test payment processing (Stripe)
- [ ] Test telephony (Wazo/Twilio) if applicable
- [ ] Test PDF generation (WeasyPrint)
- [ ] Test search functionality (Elasticsearch)
- [ ] Verify static files served via CloudFront
- [ ] Verify media uploads to S3
- [ ] Test backup and restore procedures
- [ ] Document runbook for common operations

---

## AWS Service Summary

| Service | Purpose | Required |
|---------|---------|----------|
| VPC | Network isolation | ✅ |
| ECS Fargate / EC2 | Application hosting | ✅ |
| RDS PostgreSQL | Primary database | ✅ |
| ElastiCache Redis | Cache, broker, channels | ✅ |
| ALB | Load balancing & SSL | ✅ |
| ACM | SSL certificates | ✅ |
| Route 53 | DNS management | ✅ |
| S3 | Static files & media | ✅ |
| CloudFront | CDN for static assets | ✅ |
| ECR | Container registry | ✅ |
| Secrets Manager | Secrets storage | ✅ |
| CloudWatch | Monitoring & logging | ✅ |
| OpenSearch | Full-text search | Optional |
| WAF | Web application firewall | Recommended |
| CodePipeline | CI/CD | Recommended |
| X-Ray | Distributed tracing | Optional |

---

## Estimated Monthly Cost (Production)

| Resource | Specification | Est. Cost/Month |
|----------|---------------|-----------------|
| ECS Fargate (web) | 2 vCPU, 4GB RAM × 2 tasks | ~$150 |
| ECS Fargate (worker) | 1 vCPU, 2GB RAM × 2 tasks | ~$60 |
| RDS PostgreSQL | db.r6g.large, Multi-AZ | ~$400 |
| ElastiCache Redis | cache.r6g.large | ~$200 |
| ALB | Standard usage | ~$30 |
| S3 + CloudFront | 50GB storage, 100GB transfer | ~$15 |
| OpenSearch | r6g.large × 2 nodes | ~$300 |
| Route 53 | 1 hosted zone | ~$1 |
| Secrets Manager | 10 secrets | ~$5 |
| CloudWatch | Logs + metrics | ~$30 |
| **Total** | | **~$1,190/mo** |

*Costs vary by region and usage patterns. Excludes Wazo telephony infrastructure.*

---

**Last Updated**: 2026-02-20  
**Maintained By**: Development Team  
**Status**: Living Document

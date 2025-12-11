# SalesCompass CRM - Improvements Roadmap

**Created**: 2025-12-10  
**Status**: Active  
**Project**: SalesCompass Multi-Tenant B2B CRM

---

## Executive Summary

This document outlines the improvements needed for SalesCompass based on a comprehensive codebase analysis. Items are organized by priority and effort level.

---

## 🔴 Critical Priority (Immediate)

### 1. Documentation

| Item | Status | Effort | Notes |
|------|--------|--------|-------|
| Update README.md | ⬜ TODO | Low | Currently only "# salescompass" |
| Enable API docs (Swagger) | ⬜ TODO | Low | Uncomment `drf_spectacular` in settings |
| Create `.env.example` | ⬜ TODO | Low | Document required environment variables |
| Developer onboarding guide | ⬜ TODO | Medium | Setup, architecture, workflows |

**Action**: Uncomment in `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'drf_spectacular',  # Line ~126
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

---

### 2. Testing Suite

| Item | Status | Effort | Notes |
|------|--------|--------|-------|
| Unit tests for core models | ⬜ TODO | Medium | CLV calculations, User model |
| Unit tests for engagement | ⬜ TODO | Medium | Scoring, event tracking |
| Integration tests | ⬜ TODO | High | Lead→Opportunity, automation triggers |
| API endpoint tests | ⬜ TODO | Medium | REST API coverage |
| Template rendering tests | ⬜ TODO | Low | Prevent syntax errors |

**Priority Files**:
- `core/core/models.py` - CLV calculation methods
- `engagement/models.py` - Engagement scoring
- `automation/models.py` - Workflow execution

---

### 3. Database Migration

| Item | Status | Effort | Notes |
|------|--------|--------|-------|
| PostgreSQL migration | ⬜ TODO | Medium | Docker already configured |
| Create migration script | ⬜ TODO | Low | SQLite → PostgreSQL data |
| Update production settings | ⬜ TODO | Low | `DATABASE_URL` environment |

**Current**: SQLite3 (2.6MB)  
**Target**: PostgreSQL 15 via Docker Compose

---

### 4. Fix Navigation 404s

| Broken Link | Issue | Fix |
|-------------|-------|-----|
| `dashboard:cockpit` | 404 | Create/fix view in `dashboard/views.py` |
| `dashboard:admin_dashboard` | 404 | Create/fix view |
| `dashboard:manager_dashboard` | 404 | Create/fix view |
| `dashboard:support_dashboard` | 404 | Create/fix view |
| `commissions:list` | 404 | Add URL pattern |
| `commissions:history` | 404 | Add URL pattern |

---

## 🟡 Medium Priority (1-2 Months)

### 5. Security Hardening

| Item | Status | Effort |
|------|--------|--------|
| API rate limiting | ⬜ TODO | Low |
| Input validation audit | ⬜ TODO | Medium |
| CSRF verification | ⬜ TODO | Low |
| Security headers monitoring | ⬜ TODO | Low |
| Complete RBAC audit | ⬜ TODO | Medium |

**Implementation** - Add to `settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

### 6. Performance Optimization

| Item | Status | Effort | Impact |
|------|--------|--------|--------|
| Add database indexes | ⬜ TODO | Low | High |
| Query optimization (N+1) | ⬜ TODO | Medium | High |
| Implement caching layer | ⬜ TODO | Medium | High |
| Profile slow endpoints | ⬜ TODO | Medium | Medium |

**Key Indexes Needed**:
```python
class Meta:
    indexes = [
        models.Index(fields=['tenant', 'created_at']),
        models.Index(fields=['tenant', 'status']),
    ]
```

---

### 7. Complete Orphaned Templates

**High-Value** (analytics, builders):
| Template | App | Action |
|----------|-----|--------|
| `workflow_builder` | automation | ✅ Linked |
| `template_builder` | marketing | ✅ Linked |
| `builder` | reports | ✅ Linked |
| `dashboard` | commissions | ⬜ Add nav link |

---

### 8. CI/CD Pipeline

| Item | Status | Platform |
|------|--------|----------|
| Automated testing | ⬜ TODO | GitHub Actions |
| Code quality (flake8) | ⬜ TODO | GitHub Actions |
| Auto migrations | ⬜ TODO | GitHub Actions |
| Staging deployment | ⬜ TODO | Replit/Docker |

---

## 🟢 Long-Term Vision (3-6 Months)

### 9. ML & AI Deployment

| Item | Status | Effort |
|------|--------|--------|
| Lead scoring model | ⬜ TODO | High |
| Churn prediction | ⬜ TODO | High |
| NBA recommendations | ⬜ TODO | High |
| Real-time inference | ⬜ TODO | Medium |

**Existing Infrastructure**: `ml_models/` (24 files)

---

### 10. Engagement Module Roadmap

**Phase 1** (Sprint 1-2):
- [ ] Engagement score decay algorithm
- [ ] Disengaged accounts report
- [ ] Auto-NBA creation rules
- [ ] Mobile responsive improvements

**Phase 2** (Sprint 3-5):
- [ ] Predictive churn risk modeling
- [ ] Enhanced webhook system (retries)
- [ ] Engagement playbooks
- [ ] Advanced dashboard widgets

**Phase 3** (Sprint 6-8):
- [ ] ML-based NBA recommendations
- [ ] Multi-touch attribution
- [ ] GraphQL API

---

### 11. External Integrations

| Integration | Priority | Effort |
|-------------|----------|--------|
| LinkedIn Sales Navigator | High | High |
| HubSpot/Marketo | High | Medium |
| Gainsight/ChurnZero | Medium | Medium |
| Google Calendar | Medium | Low |
| Slack/Teams | Medium | Low |

---

### 12. Enterprise Features

| Feature | Status | Effort |
|---------|--------|--------|
| SSO (SAML/OAuth) | ⬜ TODO | High |
| Advanced audit logging | ⬜ TODO | Medium |
| Data retention policies | ⬜ TODO | Medium |
| GDPR compliance | ⬜ TODO | High |

---

## 📊 Code Quality

### 13. Complete Reference Data Migration

**Issue**: Models have both old choice fields and new FK fields

| Model | Old Field | New FK Field |
|-------|-----------|--------------|
| SystemConfiguration | `data_type` | `data_type_ref` |
| SystemEventLog | `event_type` | `event_type_ref` |
| SystemHealthCheck | `check_type` | `check_type_ref` |
| MaintenanceWindow | `status` | `status_ref` |
| PerformanceMetric | `metric_type` | `metric_type_ref` |
| SystemNotification | `notification_type` | `notification_type_ref` |

**Action**: Migrate data to ref fields, then remove old choice fields

---

### 14. Error Handling

| Item | Status | Effort |
|------|--------|--------|
| Integrate Sentry | ⬜ TODO | Low |
| Custom 404/500 pages | ⬜ TODO | Low |
| Graceful external service degradation | ⬜ TODO | Medium |

---

## 🎯 Quick Wins (Today)

| # | Task | Effort |
|---|------|--------|
| 1 | Update README.md | 30 min |
| 2 | Enable API docs | 5 min |
| 3 | Create `.env.example` | 15 min |
| 4 | Add drf-spectacular to requirements | 5 min |
| 5 | Fix/remove broken nav links | 30 min |

---

## Priority Matrix

```
                    IMPACT
              Low    Medium    High
         ┌─────────┬─────────┬─────────┐
    Low  │         │ Indexes │ README  │
         │         │ Cache   │ API Docs│
  E      ├─────────┼─────────┼─────────┤
  F Med  │ Custom  │ Security│ Testing │
  F      │ Errors  │ Audit   │ Orphans │
  O      ├─────────┼─────────┼─────────┤
  R High │ GraphQL │ ML/AI   │ DB Migr │
  T      │ SSO     │ Integr. │ CI/CD   │
         └─────────┴─────────┴─────────┘
```

---

## Next Steps

1. **Week 1**: Quick wins + documentation
2. **Week 2-3**: Testing suite foundation
3. **Week 4**: Database migration to PostgreSQL
4. **Month 2**: Performance + security
5. **Month 3+**: ML deployment + integrations

---

*Last Updated: 2025-12-10*

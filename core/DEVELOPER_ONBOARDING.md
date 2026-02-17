# Developer Onboarding Guide

Welcome to the SalesCompass engineering team! This guide will help you understand the system architecture and find your way around the codebase.

## System Architecture

SalesCompass is a multi-tenant CRM platform built on Django. While the codebase uses a flat directory structure for simplicity, the applications are logically grouped into functional **Domains**.

### Domain Map

Instead of 28 random apps, think of the system in these 6 clusters:

#### 1. CRM Core 🤝
*Everything related to the customer lifecycle.*
*   **`accounts`**: The heart of the system. Companies we do business with. Includes `Contact` model.
*   **`leads`**: Potential customers. Unqualified prospects.
*   **`opportunities`**: Deals in progress. The sales pipeline.
*   **`sales`**: Sales logic, quotas, and forecasting.

#### 2. Communication & Engagement 💬
*How we interact with customers.*
*   **`communication`**: Omni-channel inbox (Email, SMS, WhatsApp).
*   **`engagement`**: Tracking user activity/signals.
*   **`marketing`**: Drip campaigns and lists.
*   **`nps`**: Net Promoter Score surveys.
*   **`wazo`**: Telephony integration (SIP/VoIP).

#### 3. Finance & Commerce 💰
*Money management.*
*   **`billing`**: Subscriptions, Invoices, and Payment Gateways (Stripe).
*   **`commissions`**: Sales commission calculations.
*   **`proposals`**: Quotes and contracts generation.
*   **`products`**: Product catalog and pricing.

#### 4. Support & Success 🆘
*Post-sales service.*
*   **`cases`**: Customer support tickets and SLA management.
*   **`learn`**: Learning Management System (LMS) for customer education.

#### 5. Platform Foundation 🏗️
*The bedrock services that power everything else.*
*   **`core`**: Base users, abstractions, and shared utilities.
*   **`tenants`**: The logical isolation layer. **Everything is multi-tenant**.
*   **`dashboard`**: The main UI shell and widget system.
*   **`access_control`**: Deep permission policies (RBAC/ABAC).
*   **`audit_logs`**: Security compliance logging.
*   **`feature_flags`**: Dynamic feature toggling.
*   **`infrastructure`**: System metrics and background tasks.
*   **`global_alerts`**: System-wide notifications.
*   **`settings_app`**: Tenant-level configuration UI.

#### 6. Developer & Tools 🛠️
*Internal utilities.*
*   **`automation`**: Workflow engine (Zapier-like internal automation).
*   **`tasks`**: Internal user tasks and reminders.
*   **`developer`**: Tools for API testing and system introspection.
*   **`reports`**: Analytics and reporting engine.

---

## Key Concepts

### Multi-Tenancy
We use a **Shared Database, Shared Schema** approach.
*   Almost every model inherits from `TenantAwareModel` (in `tenants.models`).
*   Data access is automatically scoped by `middleware.DataVisibilityMiddleware`.
*   **Never** forget to include `tenant=request.user.tenant` when creating objects.

### Permissions
We use a custom Policy-Based access control.
*   See `core/object_permissions.py` in each app.
*   Standard Django permissions (`add_account`, `view_account`) are just the entry point.
*   Real access is determined by Policies (e.g., "Can view accounts in my territory").

### Event Bus
We prefer **Event-Driven Architecture** for cross-app updates.
*   Don't import `Billing` into `Leads` directly if you can avoid it.
*   Emit an event: `event_bus.emit('lead_converted', lead=lead)`.
*   Listeners in other apps react to it.

## Getting Started

1.  **Environment**: Ensure `.env` is set up (see `.env.example`).
2.  **Database**:
    ```bash
    python manage.py migrate
    ```
3.  **Run Server**:
    ```bash
    python manage.py runserver
    ```
4.  **Run Tests**:
    ```bash
    pytest
    # or
    python manage.py test core.tests
    ```

## Contributing
Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for style guides and pull request protocols.

# SalesCompass CRM - Commissions Module Master Implementation Checklist

## Current Implementation Status ✅

### Core Models & Database
- [x] **CommissionPlan** with basis (revenue, margin, ACV, MRR) and period
- [x] **CommissionRule** for flat/tiered rates per product/category
- [x] **UserCommissionPlan** to assign plans to users
- [x] **Quota** for sales targets
- [x] **Commission** for earned records linked to Opportunity
- [x] **Adjustment** for bonuses, deductions, and clawbacks
- [x] **CommissionPayment** for payout tracking

### Views & UI
- [x] Commissions dashboard
- [x] Admin for managing plans
- [ ] Rep self-service statement view
- [ ] Quota attainment progress widget

### Integration
- [x] Link to Opportunities
- [x] Link to Products (category rules)
- [ ] Payroll/Accounting export

---

## Recommended Additional Functionalities 🚀

### 1. Rep Experience & Self-Service
- [ ] **My Earnings Dashboard**
  - [ ] Current period commission estimate (real-time)
  - [ ] Historical earnings trend
  - [ ] Commission statement download (PDF)

- [ ] **Quota Tracking**
  - [ ] Visual progress bar (Attainment %)
  - [ ] Pace indicator (On/Off track vs. goal)
  - [ ] What-if calculator ("If I close $X, I earn $Y")

### 2. Plan Design & Flexibility
- [ ] **Advanced Plans**
  - [ ] Multi-tier accelerators (e.g., 10% up to $100k, 15% above)
  - [ ] Decelerators for underperformance
  - [ ] Split commissions (team deals)
  - [ ] Overlay commissions (Sales Engineers, Managers)

- [ ] **Plan Builder UI**
  - [ ] Visual plan designer for admins
  - [ ] "Clone Plan" functionality
  - [ ] Plan versioning and effective dating

### 3. Forecasting & Modeling
- [ ] **Payout Forecasting**
  - [ ] Projected payouts for the period
  - [ ] Budget vs. Actual variance
  - [ ] Monte Carlo payout range simulations

### 4. Disputes & Adjustments
- [ ] **Dispute Workflow**
  - [ ] Rep-initiated dispute form
  - [ ] Manager review and resolution
  - [ ] Audit log of adjustments

### 5. Reporting & Compliance
- [ ] **Audit & Compliance**
  - [ ] Commission calculation audit trail
  - [ ] Approvals log for payments
  - [ ] Export for payroll/accounting (CSV, API)

- [ ] **Team Dashboards**
  - [ ] Leaderboard by earnings
  - [ ] Team vs. Individual comparison

---

## Implementation Priority Recommendations

### Phase 1: Rep Experience (Sprint 1-2)
1.  "My Earnings" dashboard for reps
2.  Quota attainment widget
3.  Commission statement export (PDF)

### Phase 2: Advanced Plans (Sprint 3-4)
1.  Accelerator/Decelerator logic
2.  Split commission rules
3.  Visual Plan Builder

### Phase 3: Forecasting & Compliance (Sprint 5+)
1.  Payout forecasting
2.  Dispute workflow
3.  Payroll integration export

---

## Success Metrics
1.  **Payout Accuracy**: Reduction in disputes.
2.  **Rep Motivation**: Increase in quota attainment rates.
3.  **Admin Efficiency**: Time saved in plan management.

---

## Notes
> [!WARNING]
> **Model Duplication**: There appears to be a `CommissionRule` and `Commission` model in both `core/commissions/models.py` and `core/sales/models.py`. This should be audited and consolidated to a single source of truth.

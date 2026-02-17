# Navigation Audit Report
**Generated**: 2026-02-06 09:56:01  
**Project**: SalesCompass CRM

---

## Executive Summary

### Overall Statistics
- **Total Templates**: 1198
- **Total URL Patterns**: 2094
- **Navigation Links Tested**: 495
- **Working Links**: 360 (72.7%)
- **Broken Links**: 135 (27.3%)
- **Orphaned Templates**: 419

### Health Score
**72.7%** ⚠️ Fair (significant fixes needed)

---

## 🔴 Broken Navigation Links

| # | URL Name | Source Template | Status | Issue |
|---|----------|-----------------|--------|-------|
| 1 | `dashboard:drill_down` | base.html | No Reverse Match | Cannot resolve URL pattern: dashboard:drill_down |
| 2 | `billing:portal` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 3 | `billing:revenue_overview` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 4 | `billing:mrr_analytics` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 5 | `billing:arr_analytics` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 6 | `billing:churn_rates` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 7 | `billing:revenue_forecast` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 8 | `billing:invoice_paid` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 9 | `billing:invoice_overdue` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 10 | `billing:invoice_void_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 11 | `billing:reconciliation` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 12 | `billing:plan_limits` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 13 | `billing:proration_calculator` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 14 | `billing:lifecycle_events` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 15 | `billing:renewal_tracking` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 16 | `billing:cancellation_management` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 17 | `billing:invoice_generation` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 18 | `billing:dunning_management` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 19 | `billing:failed_payments` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 20 | `billing:payment_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 21 | `billing:payment_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 22 | `billing:payment_gateway_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 23 | `billing:tenant_payment_config` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 24 | `billing:payment_method_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 25 | `billing:tenant_billing_search` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 26 | `billing:credit_adjustment` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 27 | `billing:plan_tier_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 28 | `billing:subscription_status_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 29 | `billing:adjustment_type_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 30 | `billing:payment_provider_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 31 | `billing:payment_type_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 32 | `billing:payment_provider_config_list` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 33 | `assets:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 34 | `assets:asset_disclosure_report` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 35 | `assets:run_depreciation` | base.html | HTTP 405 | 405 |
| 36 | `automation:workflow_builder` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 37 | `loyalty:program_setup` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 38 | `cases:case_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 39 | `cases:case_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 40 | `cases:case_kanban` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 41 | `cases:detractor_kanban` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 42 | `cases:csat_response_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 43 | `cases:case_comment_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 44 | `cases:case_comment_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 45 | `cases:case_attachment_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 46 | `cases:case_attachment_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 47 | `cases:sla_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 48 | `cases:sla_policy_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 49 | `cases:sla_policy_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 50 | `learn:article_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 51 | `learn:search` | base.html | Error | base.html |
| 52 | `learn:usage_analytics` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 53 | `tenants:tenant_onboarding_signup` | base.html | Error | base.html |
| 54 | `tenants:member_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 55 | `expenses:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 56 | `wazo:webhooks` | base.html | HTTP 405 | 405 |
| 57 | `purchasing:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 58 | `accounting:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 59 | `customer_portal:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'associated_accounts' |
| 60 | `customer_portal:invoice_list` | base.html | Error | 'AnonymousUser' object has no attribute 'associated_accounts' |
| 61 | `customer_portal:proposal_list` | base.html | Error | 'AnonymousUser' object has no attribute 'associated_accounts' |
| 62 | `customer_portal:ticket_list` | base.html | Error | 'AnonymousUser' object has no attribute 'associated_accounts' |
| 63 | `proposals:proposal_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 64 | `proposals:proposal_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 65 | `proposals:proposal_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 66 | `proposals:template_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 67 | `proposals:template_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 68 | `proposals:approvals_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 69 | `proposals:approval_template_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 70 | `proposals:manage_approval_templates` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 71 | `proposals:analytics` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 72 | `proposals:events` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 73 | `audit_logs:list` | base.html | No Reverse Match | Cannot resolve URL pattern: audit_logs:list |
| 74 | `tasks:undone_work` | base.html | Error | Field 'id' expected a number but got <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f21bee618b0>>. |
| 75 | `opportunities:pipeline_kanban` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 76 | `opportunities:stage_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 77 | `opportunities:type_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 78 | `opportunities:sales_velocity_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 79 | `opportunities:forecast_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 80 | `opportunities:opportunity_funnel_analysis` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 81 | `opportunities:win_loss_analysis` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 82 | `opportunities:assignment_rule_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 83 | `ecommerce:index` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 84 | `ecommerce:cart_view` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 85 | `accounts:accounts_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 86 | `accounts:account_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 87 | `accounts:account_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 88 | `accounts:account_kanban` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 89 | `accounts:bulk_import_upload` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 90 | `accounts:contact_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 91 | `accounts:contact_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 92 | `nps:nps_survey_create` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant_id' |
| 93 | `nps:create_nps_ab_test` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant_id' |
| 94 | `hr:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 95 | `hr:attendance` | base.html | Error | 'AnonymousUser' object has no attribute 'employee_profile' |
| 96 | `sales:sales_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 97 | `sales:revenue_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 98 | `sales:sale_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 99 | `sales:sale_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 100 | `sales:territory_performance_dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant_id' |
| 101 | `sales:territory_assignment_optimization_dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant_id' |
| 102 | `sales:territory_comparison_tool` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant_id' |
| 103 | `sales:commission_dashboard` | base.html | Error | Field 'id' expected a number but got <SimpleLazyObject: <django.contrib.auth.models.AnonymousUser object at 0x7f21be4ce9c0>>. |
| 104 | `products:governance_dashboard` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 105 | `products:product_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 106 | `products:product_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 107 | `products:category_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 108 | `products:category_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 109 | `products:productbundle_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 110 | `products:productbundle_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 111 | `products:pricelist_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 112 | `products:coupon_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 113 | `products:promotion_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 114 | `products:competitorproduct_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 115 | `products:competitorproduct_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 116 | `products:competitor_mapping` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 117 | `products:productcomparison_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 118 | `products:productcomparison_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 119 | `products:comparison` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 120 | `products:productdependency_list` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 121 | `products:productdependency_create` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 122 | `products:bulk_label_print` | base.html | Error | Reverse for 'login' not found. 'login' is not a valid view function or pattern name. |
| 123 | `manufacturing:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 124 | `logistics:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 125 | `quality_control:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 126 | `projects:dashboard` | base.html | Error | 'AnonymousUser' object has no attribute 'tenant' |
| 127 | `global_alerts:alert_list` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alert_list |
| 128 | `global_alerts:alert_create` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alert_create |
| 129 | `global_alerts:active_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:active_alerts |
| 130 | `global_alerts:scheduled_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:scheduled_alerts |
| 131 | `global_alerts:alerts_by_type` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alerts_by_type |
| 132 | `global_alerts:alerts_by_severity` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alerts_by_severity |
| 133 | `global_alerts:global_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:global_alerts |
| 134 | `global_alerts:tenant_specific` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:tenant_specific |
| 135 | `global_alerts:analytics` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:analytics |

---

## 🟢 Working Navigation Links

Total: 360 links working correctly

---

## 🔍 Orphaned Templates Analysis


### Access_Control (6 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `available_apps` | `access_control:available_apps`, `access_control:available_apps_list` | 🔍 Review manually |
| `delete_access` | `access_control:delete_access`, `access_control:delete_access_list` | 🔍 Review manually |
| `edit_access` | `access_control:edit_access`, `access_control:edit_access_list` | 🔍 Review manually |
| `role_access_detail` | `access_control:role_access_detail`, `access_control:role_access_detail_list` | 🔍 Review manually |
| `tenant_access_detail` | `access_control:tenant_access_detail`, `access_control:tenant_access_detail_list` | 🔍 Review manually |
| `user_access_detail` | `access_control:user_access_detail`, `access_control:user_access_detail_list` | 🔍 Review manually |

### Accounting (14 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `bank_statement_import` | `accounting:bank_statement_import`, `accounting:bank_statement_import_list` | 🔍 Review manually |
| `bank_statement_list` | `accounting:bank_statement_list`, `accounting:bank_statement_list_list` | 🔍 Review manually |
| `coa_detail` | `accounting:coa_detail`, `accounting:coa_detail_list` | 🔍 Review manually |
| `fiscal_management/close_period` | `accounting:fiscal_management_close_period`, `accounting:fiscal_management_close_period_list` | 🔍 Review manually |
| `journal_detail` | `accounting:journal_detail`, `accounting:journal_detail_list` | 🔍 Review manually |
| `reconciliation_detail` | `accounting:reconciliation_detail`, `accounting:reconciliation_detail_list` | 🔍 Review manually |
| `reports/balance_sheet` | `accounting:reports_balance_sheet`, `accounting:reports_balance_sheet_list` | 🟢 Add to navigation |
| `reports/cash_flow` | `accounting:reports_cash_flow`, `accounting:reports_cash_flow_list` | 🟢 Add to navigation |
| `reports/custom_report_list` | `accounting:reports_custom_report_list`, `accounting:reports_custom_report_list_list` | 🟢 Add to navigation |
| `reports/custom_report_run` | `accounting:reports_custom_report_run`, `accounting:reports_custom_report_run_list` | 🟢 Add to navigation |
| `reports/general_ledger` | `accounting:reports_general_ledger`, `accounting:reports_general_ledger_list` | 🟢 Add to navigation |
| `reports/income_statement` | `accounting:reports_income_statement`, `accounting:reports_income_statement_list` | 🟢 Add to navigation |
| `reports/trial_balance` | `accounting:reports_trial_balance`, `accounting:reports_trial_balance_list` | 🟢 Add to navigation |
| `reports/vat_return` | `accounting:reports_vat_return`, `accounting:reports_vat_return_list` | 🟢 Add to navigation |

### Accounts (15 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `account_analytics` | `accounts:account_analytics`, `accounts:account_analytics_list` | 🟢 Add to navigation |
| `account_detail` | `accounts:account_detail`, `accounts:account_detail_list` | 🔍 Review manually |
| `admin/mfa_management` | `accounts:admin_mfa_management`, `accounts:admin_mfa_management_list` | 🔍 Review manually |
| `admin/user_access_review` | `accounts:admin_user_access_review`, `accounts:admin_user_access_review_list` | 🔍 Review manually |
| `admin/user_activity` | `accounts:admin_user_activity`, `accounts:admin_user_activity_list` | 🔍 Review manually |
| `admin/user_bulk_operations` | `accounts:admin_user_bulk_operations`, `accounts:admin_user_bulk_operations_list` | 🔍 Review manually |
| `admin/user_list` | `accounts:admin_user_list`, `accounts:admin_user_list_list` | 🔍 Review manually |
| `admin/user_management_dashboard` | `accounts:admin_user_management_dashboard`, `accounts:admin_user_management_dashboard_list` | 🟢 Add to navigation |
| `admin/user_role_management` | `accounts:admin_user_role_management`, `accounts:admin_user_role_management_list` | 🔍 Review manually |
| `bulk_imports/map_fields` | `accounts:bulk_imports_map_fields`, `accounts:bulk_imports_map_fields_list` | 🔍 Review manually |
| `bulk_imports/preview` | `accounts:bulk_imports_preview`, `accounts:bulk_imports_preview_list` | 🟡 Keep as action/API endpoint |
| `bulk_imports/upload` | `accounts:bulk_imports_upload`, `accounts:bulk_imports_upload_list` | 🔍 Review manually |
| `contacts/account_contact_list` | `accounts:contacts_account_contact_list`, `accounts:contacts_account_contact_list_list` | 🔍 Review manually |
| `contacts/contact_detail` | `accounts:contacts_contact_detail`, `accounts:contacts_contact_detail_list` | 🔍 Review manually |
| `contacts/contact_list` | `accounts:contacts_contact_list`, `accounts:contacts_contact_list_list` | 🔍 Review manually |

### Assets (4 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `asset_detail` | `assets:asset_detail`, `assets:asset_detail_list` | 🔍 Review manually |
| `depreciation_schedule` | `assets:depreciation_schedule`, `assets:depreciation_schedule_list` | 🔍 Review manually |
| `ifrs_disclosure_report` | `assets:ifrs_disclosure_report`, `assets:ifrs_disclosure_report_list` | 🟢 Add to navigation |
| `mobile_audit` | `assets:mobile_audit`, `assets:mobile_audit_list` | 🔍 Review manually |

### Audit_Logs (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `dashboard` | `audit_logs:dashboard`, `audit_logs:dashboard_list` | 🟢 Add to navigation |
| `log_detail` | `audit_logs:log_detail`, `audit_logs:log_detail_list` | 🔍 Review manually |

### Automation (15 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `approval_response` | `automation:approval_response`, `automation:approval_response_list` | 🔍 Review manually |
| `confirm_delete` | `automation:confirm_delete`, `automation:confirm_delete_list` | 🔍 Review manually |
| `custom_code_execution_log_list` | `automation:custom_code_execution_log_list`, `automation:custom_code_execution_log_list_list` | 🔍 Review manually |
| `custom_code_snippet_detail` | `automation:custom_code_snippet_detail`, `automation:custom_code_snippet_detail_list` | 🔍 Review manually |
| `custom_code_snippet_list` | `automation:custom_code_snippet_list`, `automation:custom_code_snippet_list_list` | 🔍 Review manually |
| `detail` | `automation:detail`, `automation:detail_list` | 🔍 Review manually |
| `form` | `automation:form`, `automation:form_list` | 🔍 Review manually |
| `forms` | `automation:forms`, `automation:forms_list` | 🔍 Review manually |
| `log_detail` | `automation:log_detail`, `automation:log_detail_list` | 🔍 Review manually |
| `version_history` | `automation:version_history`, `automation:version_history_list` | 🔍 Review manually |
| `webhook_log_detail` | `automation:webhook_log_detail`, `automation:webhook_log_detail_list` | 🔍 Review manually |
| `workflow_action_detail` | `automation:workflow_action_detail`, `automation:workflow_action_detail_list` | 🔍 Review manually |
| `workflow_execution_detail` | `automation:workflow_execution_detail`, `automation:workflow_execution_detail_list` | 🔍 Review manually |
| `workflow_template_detail` | `automation:workflow_template_detail`, `automation:workflow_template_detail_list` | 🔍 Review manually |
| `workflow_trigger_detail` | `automation:workflow_trigger_detail`, `automation:workflow_trigger_detail_list` | 🔍 Review manually |

### Billing (13 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `billing_history` | `billing:billing_history`, `billing:billing_history_list` | 🔍 Review manually |
| `credit_adjustment_list` | `billing:credit_adjustment_list`, `billing:credit_adjustment_list_list` | 🔍 Review manually |
| `credit_adjustment_management` | `billing:credit_adjustment_management`, `billing:credit_adjustment_management_list` | 🔍 Review manually |
| `invoice_detail` | `billing:invoice_detail`, `billing:invoice_detail_list` | 🔍 Review manually |
| `invoice_overdue_list` | `billing:invoice_overdue_list`, `billing:invoice_overdue_list_list` | 🔍 Review manually |
| `invoice_paid_list` | `billing:invoice_paid_list`, `billing:invoice_paid_list_list` | 🔍 Review manually |
| `plan_detail` | `billing:plan_detail`, `billing:plan_detail_list` | 🔍 Review manually |
| `plan_edit` | `billing:plan_edit`, `billing:plan_edit_list` | 🔍 Review manually |
| `plan_tier_confrim_delete` | `billing:plan_tier_confrim_delete`, `billing:plan_tier_confrim_delete_list` | 🔍 Review manually |
| `pricing_config` | `billing:pricing_config`, `billing:pricing_config_list` | 🔍 Review manually |
| `subscription_cancel_confirm` | `billing:subscription_cancel_confirm`, `billing:subscription_cancel_confirm_list` | 🔍 Review manually |
| `subscription_detail` | `billing:subscription_detail`, `billing:subscription_detail_list` | 🔍 Review manually |
| `upgrade_required` | `billing:upgrade_required`, `billing:upgrade_required_list` | 🔍 Review manually |

### Cases (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `case_detail` | `cases:case_detail`, `cases:case_detail_list` | 🔍 Review manually |
| `csat_thank_you` | `cases:csat_thank_you`, `cases:csat_thank_you_list` | 🔍 Review manually |

### Commissions (8 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `commission_list` | `commissions:commission_list`, `commissions:commission_list_list` | 🔍 Review manually |
| `commissionplanversion_list` | `commissions:commissionplanversion_list`, `commissions:commissionplanversion_list_list` | 🔍 Review manually |
| `payment_detail` | `commissions:payment_detail`, `commissions:payment_detail_list` | 🔍 Review manually |
| `payment_list` | `commissions:payment_list`, `commissions:payment_list_list` | 🔍 Review manually |
| `plan_builder` | `commissions:plan_builder`, `commissions:plan_builder_list` | 🟢 Add to navigation |
| `plan_version_detail` | `commissions:plan_version_detail`, `commissions:plan_version_detail_list` | 🔍 Review manually |
| `statement_pdf` | `commissions:statement_pdf`, `commissions:statement_pdf_list` | 🟡 Keep as action/API endpoint |
| `statement_web` | `commissions:statement_web`, `commissions:statement_web_list` | 🔍 Review manually |

### Communication (20 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `call_analytics` | `communication:call_analytics`, `communication:call_analytics_list` | 🟢 Add to navigation |
| `call_log_detail` | `communication:call_log_detail`, `communication:call_log_detail_list` | 🔍 Review manually |
| `call_log_list` | `communication:call_log_list`, `communication:call_log_list_list` | 🔍 Review manually |
| `email_compose` | `communication:email_compose`, `communication:email_compose_list` | 🔍 Review manually |
| `email_config_list` | `communication:email_config_list`, `communication:email_config_list_list` | 🔍 Review manually |
| `email_list` | `communication:email_list`, `communication:email_list_list` | 🔍 Review manually |
| `feedback_list` | `communication:feedback_list`, `communication:feedback_list_list` | 🔍 Review manually |
| `history_detail` | `communication:history_detail`, `communication:history_detail_list` | 🔍 Review manually |
| `history_list` | `communication:history_list`, `communication:history_list_list` | 🔍 Review manually |
| `linkedin_inmail` | `communication:linkedin_inmail`, `communication:linkedin_inmail_list` | 🔍 Review manually |
| `notification_template_list` | `communication:notification_template_list`, `communication:notification_template_list_list` | 🔍 Review manually |
| `signature_list` | `communication:signature_list`, `communication:signature_list_list` | 🔍 Review manually |
| `sms_list` | `communication:sms_list`, `communication:sms_list_list` | 🔍 Review manually |
| `sms_send` | `communication:sms_send`, `communication:sms_send_list` | 🔍 Review manually |
| `ticket_detail` | `communication:ticket_detail`, `communication:ticket_detail_list` | 🔍 Review manually |
| `ticket_list` | `communication:ticket_list`, `communication:ticket_list_list` | 🔍 Review manually |
| `unified_inbox` | `communication:unified_inbox`, `communication:unified_inbox_list` | 🔍 Review manually |
| `whatsapp_conversation` | `communication:whatsapp_conversation`, `communication:whatsapp_conversation_list` | 🔍 Review manually |
| `whatsapp_send` | `communication:whatsapp_send`, `communication:whatsapp_send_list` | 🔍 Review manually |
| `whatsapp_template_list` | `communication:whatsapp_template_list`, `communication:whatsapp_template_list_list` | 🔍 Review manually |

### Core (43 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `shared/_loading_spinner` | `core:shared__loading_spinner`, `core:shared__loading_spinner_list` | 🔍 Review manually |
| `shared/_pagination` | `core:shared__pagination`, `core:shared__pagination_list` | 🔍 Review manually |
| `components/_empty_state` | `core:components__empty_state`, `core:components__empty_state_list` | 🔍 Review manually |
| `components/_loading_spinner` | `core:components__loading_spinner`, `core:components__loading_spinner_list` | 🔍 Review manually |
| `components/_pagination` | `core:components__pagination`, `core:components__pagination_list` | 🔍 Review manually |
| `components/_table_header` | `core:components__table_header`, `core:components__table_header_list` | 🔍 Review manually |
| `403` | `core:403`, `core:403_list` | 🔍 Review manually |
| `admin/configuration_audit` | `core:admin_configuration_audit`, `core:admin_configuration_audit_list` | 🔍 Review manually |
| `admin/data_management` | `core:admin_data_management`, `core:admin_data_management_list` | 🔍 Review manually |
| `admin/environment_variables` | `core:admin_environment_variables`, `core:admin_environment_variables_list` | 🔍 Review manually |
| `admin/feature_toggle_management` | `core:admin_feature_toggle_management`, `core:admin_feature_toggle_management_list` | 🔍 Review manually |
| `admin/system_configuration` | `core:admin_system_configuration`, `core:admin_system_configuration_list` | 🔍 Review manually |
| `admin/system_maintenance` | `core:admin_system_maintenance`, `core:admin_system_maintenance_list` | 🔍 Review manually |
| `assignment_rule_type_list` | `core:assignment_rule_type_list`, `core:assignment_rule_type_list_list` | 🔍 Review manually |
| `base_module` | `core:base_module`, `core:base_module_list` | 🔍 Review manually |
| `dynamic_choices_dashboard` | `core:dynamic_choices_dashboard`, `core:dynamic_choices_dashboard_list` | 🟢 Add to navigation |
| `feature_disabled` | `core:feature_disabled`, `core:feature_disabled_list` | 🔍 Review manually |
| `field_type_list` | `core:field_type_list`, `core:field_type_list_list` | 🔍 Review manually |
| `model_choice_list` | `core:model_choice_list`, `core:model_choice_list_list` | 🔍 Review manually |
| `module_choice_list` | `core:module_choice_list`, `core:module_choice_list_list` | 🔍 Review manually |
| `module_label_list` | `core:module_label_list`, `core:module_label_list_list` | 🔍 Review manually |
| `patterns/form_view` | `core:patterns_form_view`, `core:patterns_form_view_list` | 🔍 Review manually |
| `patterns/list_view` | `core:patterns_list_view`, `core:patterns_list_view_list` | 🔍 Review manually |
| `security/ip_whitelist_management` | `core:security_ip_whitelist_management`, `core:security_ip_whitelist_management_list` | 🔍 Review manually |
| `security/security_dashboard` | `core:security_security_dashboard`, `core:security_security_dashboard_list` | 🟢 Add to navigation |
| `system_config_type_list` | `core:system_config_type_list`, `core:system_config_type_list_list` | 🔍 Review manually |
| `logged_in/app_selection` | `core:logged_in_app_selection`, `core:logged_in_app_selection_list` | 🔍 Review manually |
| `logged_in/app_settings` | `core:logged_in_app_settings`, `core:logged_in_app_settings_list` | 🔍 Review manually |
| `public/api` | `core:public_api`, `core:public_api_list` | 🔍 Review manually |
| `public/company` | `core:public_company`, `core:public_company_list` | 🔍 Review manually |
| `public/customer` | `core:public_customer`, `core:public_customer_list` | 🔍 Review manually |
| `public/index` | `core:public_index`, `core:public_index_list` | 🔍 Review manually |
| `public/integrations` | `core:public_integrations`, `core:public_integrations_list` | 🔍 Review manually |
| `public/login` | `core:public_login`, `core:public_login_list` | 🔍 Review manually |
| `public/mfa_verify` | `core:public_mfa_verify`, `core:public_mfa_verify_list` | 🔍 Review manually |
| `public/pricing` | `core:public_pricing`, `core:public_pricing_list` | 🔍 Review manually |
| `public/product` | `core:public_product`, `core:public_product_list` | 🔍 Review manually |
| `public/products` | `core:public_products`, `core:public_products_list` | 🔍 Review manually |
| `public/solutions` | `core:public_solutions`, `core:public_solutions_list` | 🔍 Review manually |
| `public/support` | `core:public_support`, `core:public_support_list` | 🔍 Review manually |
| `public/try` | `core:public_try`, `core:public_try_list` | 🔍 Review manually |
| `shared/_loading_spinner` | `core:shared__loading_spinner`, `core:shared__loading_spinner_list` | 🔍 Review manually |
| `shared/_pagination` | `core:shared__pagination`, `core:shared__pagination_list` | 🔍 Review manually |

### Dashboard (3 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `bi/drill_down` | `dashboard:bi_drill_down`, `dashboard:bi_drill_down_list` | 🔍 Review manually |
| `bi/explorer` | `dashboard:bi_explorer`, `dashboard:bi_explorer_list` | 🔍 Review manually |
| `render` | `dashboard:render`, `dashboard:render_list` | 🔍 Review manually |

### Developer (1 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `documentation` | `developer:documentation`, `developer:documentation_list` | 🔍 Review manually |

### Ecommerce (6 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `cart` | `ecommerce:cart`, `ecommerce:cart_list` | 🔍 Review manually |
| `checkout` | `ecommerce:checkout`, `ecommerce:checkout_list` | 🔍 Review manually |
| `order_confirmation` | `ecommerce:order_confirmation`, `ecommerce:order_confirmation_list` | 🔍 Review manually |
| `order_detail` | `ecommerce:order_detail`, `ecommerce:order_detail_list` | 🔍 Review manually |
| `product_detail` | `ecommerce:product_detail`, `ecommerce:product_detail_list` | 🔍 Review manually |
| `product_list` | `ecommerce:product_list`, `ecommerce:product_list_list` | 🔍 Review manually |

### Engagement (10 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `event_detail` | `engagement:event_detail`, `engagement:event_detail_list` | 🔍 Review manually |
| `experiment_detail` | `engagement:experiment_detail`, `engagement:experiment_detail_list` | 🔍 Review manually |
| `nba_list` | `engagement:nba_list`, `engagement:nba_list_list` | 🔍 Review manually |
| `next_best_action_detail` | `engagement:next_best_action_detail`, `engagement:next_best_action_detail_list` | 🔍 Review manually |
| `partials/feed` | `engagement:partials_feed`, `engagement:partials_feed_list` | 🔍 Review manually |
| `playbook_clone` | `engagement:playbook_clone`, `engagement:playbook_clone_list` | 🔍 Review manually |
| `playbook_detail` | `engagement:playbook_detail`, `engagement:playbook_detail_list` | 🔍 Review manually |
| `playbook_execution_complete` | `engagement:playbook_execution_complete`, `engagement:playbook_execution_complete_list` | 🔍 Review manually |
| `playbook_execution_detail` | `engagement:playbook_execution_detail`, `engagement:playbook_execution_detail_list` | 🔍 Review manually |
| `playbook_execution_start` | `engagement:playbook_execution_start`, `engagement:playbook_execution_start_list` | 🔍 Review manually |

### Expenses (3 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `approval_workflow` | `expenses:approval_workflow`, `expenses:approval_workflow_list` | 🔍 Review manually |
| `card_import` | `expenses:card_import`, `expenses:card_import_list` | 🔍 Review manually |
| `report_detail` | `expenses:report_detail`, `expenses:report_detail_list` | 🟢 Add to navigation |

### Feature_Flags (1 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `flag_detail` | `feature_flags:flag_detail`, `feature_flags:flag_detail_list` | 🔍 Review manually |

### Global_Alerts (8 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `alert_analytics` | `global_alerts:alert_analytics`, `global_alerts:alert_analytics_list` | 🟢 Add to navigation |
| `alert_configuration_list` | `global_alerts:alert_configuration_list`, `global_alerts:alert_configuration_list_list` | 🔍 Review manually |
| `alert_correlation_rule_list` | `global_alerts:alert_correlation_rule_list`, `global_alerts:alert_correlation_rule_list_list` | 🔍 Review manually |
| `alert_detail` | `global_alerts:alert_detail`, `global_alerts:alert_detail_list` | 🔍 Review manually |
| `alert_escalation_policy_list` | `global_alerts:alert_escalation_policy_list`, `global_alerts:alert_escalation_policy_list_list` | 🔍 Review manually |
| `alert_instance_detail` | `global_alerts:alert_instance_detail`, `global_alerts:alert_instance_detail_list` | 🔍 Review manually |
| `alert_instance_list` | `global_alerts:alert_instance_list`, `global_alerts:alert_instance_list_list` | 🔍 Review manually |
| `alert_preview` | `global_alerts:alert_preview`, `global_alerts:alert_preview_list` | 🟡 Keep as action/API endpoint |

### Hr (4 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `attendance_list` | `hr:attendance_list`, `hr:attendance_list_list` | 🔍 Review manually |
| `employee_detail` | `hr:employee_detail`, `hr:employee_detail_list` | 🔍 Review manually |
| `payroll_detail` | `hr:payroll_detail`, `hr:payroll_detail_list` | 🔍 Review manually |
| `payslip_detail` | `hr:payslip_detail`, `hr:payslip_detail_list` | 🔍 Review manually |

### Infrastructure (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `resource_allocation_list` | `infrastructure:resource_allocation_list`, `infrastructure:resource_allocation_list_list` | 🔍 Review manually |
| `tenant_usage_list` | `infrastructure:tenant_usage_list`, `infrastructure:tenant_usage_list_list` | 🔍 Review manually |

### Inventory (20 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `adjustment_detail` | `inventory:adjustment_detail`, `inventory:adjustment_detail_list` | 🔍 Review manually |
| `adjustment_list` | `inventory:adjustment_list`, `inventory:adjustment_list_list` | 🔍 Review manually |
| `alert_list` | `inventory:alert_list`, `inventory:alert_list_list` | 🔍 Review manually |
| `emails/low_stock_alert` | `inventory:emails_low_stock_alert`, `inventory:emails_low_stock_alert_list` | 🔍 Review manually |
| `module_nav` | `inventory:module_nav`, `inventory:module_nav_list` | 🔍 Review manually |
| `movement_list` | `inventory:movement_list`, `inventory:movement_list_list` | 🔍 Review manually |
| `reorder_list` | `inventory:reorder_list`, `inventory:reorder_list_list` | 🔍 Review manually |
| `stock_add` | `inventory:stock_add`, `inventory:stock_add_list` | 🔍 Review manually |
| `stock_detail` | `inventory:stock_detail`, `inventory:stock_detail_list` | 🔍 Review manually |
| `stock_list` | `inventory:stock_list`, `inventory:stock_list_list` | 🔍 Review manually |
| `stock_remove` | `inventory:stock_remove`, `inventory:stock_remove_list` | 🔍 Review manually |
| `stock_transfer` | `inventory:stock_transfer`, `inventory:stock_transfer_list` | 🔍 Review manually |
| `transfer_detail` | `inventory:transfer_detail`, `inventory:transfer_detail_list` | 🔍 Review manually |
| `transfer_list` | `inventory:transfer_list`, `inventory:transfer_list_list` | 🔍 Review manually |
| `transfer_receive` | `inventory:transfer_receive`, `inventory:transfer_receive_list` | 🔍 Review manually |
| `transfer_ship` | `inventory:transfer_ship`, `inventory:transfer_ship_list` | 🔍 Review manually |
| `valuation_report` | `inventory:valuation_report`, `inventory:valuation_report_list` | 🟢 Add to navigation |
| `warehouse_detail` | `inventory:warehouse_detail`, `inventory:warehouse_detail_list` | 🔍 Review manually |
| `warehouse_list` | `inventory:warehouse_list`, `inventory:warehouse_list_list` | 🔍 Review manually |
| `zone_list` | `inventory:zone_list`, `inventory:zone_list_list` | 🔍 Review manually |

### Leads (14 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `action_type_list` | `leads:action_type_list`, `leads:action_type_list_list` | 🔍 Review manually |
| `assignment_rule_list` | `leads:assignment_rule_list`, `leads:assignment_rule_list_list` | 🔍 Review manually |
| `behavioral_scoring_rule_list` | `leads:behavioral_scoring_rule_list`, `leads:behavioral_scoring_rule_list_list` | 🔍 Review manually |
| `cac_analytics` | `leads:cac_analytics`, `leads:cac_analytics_list` | 🟢 Add to navigation |
| `campaign_metrics` | `leads:campaign_metrics`, `leads:campaign_metrics_list` | 🔍 Review manually |
| `channel_metrics` | `leads:channel_metrics`, `leads:channel_metrics_list` | 🔍 Review manually |
| `demographic_scoring_rule_list` | `leads:demographic_scoring_rule_list`, `leads:demographic_scoring_rule_list_list` | 🔍 Review manually |
| `lead_analytics` | `leads:lead_analytics`, `leads:lead_analytics_list` | 🟢 Add to navigation |
| `lead_detail` | `leads:lead_detail`, `leads:lead_detail_list` | 🔍 Review manually |
| `lead_pipeline` | `leads:lead_pipeline`, `leads:lead_pipeline_list` | 🔍 Review manually |
| `marketingchannel_list` | `leads:marketingchannel_list`, `leads:marketingchannel_list_list` | 🔍 Review manually |
| `operator_type_list` | `leads:operator_type_list`, `leads:operator_type_list_list` | 🔍 Review manually |
| `web_to_lead_builder` | `leads:web_to_lead_builder`, `leads:web_to_lead_builder_list` | 🟢 Add to navigation |
| `web_to_lead_list` | `leads:web_to_lead_list`, `leads:web_to_lead_list_list` | 🔍 Review manually |

### Learn (10 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `certificate` | `learn:certificate`, `learn:certificate_list` | 🔍 Review manually |
| `course_detail` | `learn:course_detail`, `learn:course_detail_list` | 🔍 Review manually |
| `course_list` | `learn:course_list`, `learn:course_list_list` | 🔍 Review manually |
| `delete` | `learn:delete`, `learn:delete_list` | 🔍 Review manually |
| `detail` | `learn:detail`, `learn:detail_list` | 🔍 Review manually |
| `export_pdf` | `learn:export_pdf`, `learn:export_pdf_list` | 🟡 Keep as action/API endpoint |
| `form` | `learn:form`, `learn:form_list` | 🔍 Review manually |
| `learner_dashboard` | `learn:learner_dashboard`, `learn:learner_dashboard_list` | 🟢 Add to navigation |
| `lesson_player` | `learn:lesson_player`, `learn:lesson_player_list` | 🔍 Review manually |
| `search_results` | `learn:search_results`, `learn:search_results_list` | 🔍 Review manually |

### Logistics (3 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `carrier_list` | `logistics:carrier_list`, `logistics:carrier_list_list` | 🔍 Review manually |
| `shipment_detail` | `logistics:shipment_detail`, `logistics:shipment_detail_list` | 🔍 Review manually |
| `shipment_list` | `logistics:shipment_list`, `logistics:shipment_list_list` | 🔍 Review manually |

### Loyalty (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `adjust_points` | `loyalty:adjust_points`, `loyalty:adjust_points_list` | 🔍 Review manually |
| `member_detail` | `loyalty:member_detail`, `loyalty:member_detail_list` | 🔍 Review manually |

### Manufacturing (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `bom_detail` | `manufacturing:bom_detail`, `manufacturing:bom_detail_list` | 🔍 Review manually |
| `bom_list` | `manufacturing:bom_list`, `manufacturing:bom_list_list` | 🔍 Review manually |
| `production_floor` | `manufacturing:production_floor`, `manufacturing:production_floor_list` | 🔍 Review manually |
| `work_order_detail` | `manufacturing:work_order_detail`, `manufacturing:work_order_detail_list` | 🔍 Review manually |
| `work_order_list` | `manufacturing:work_order_list`, `manufacturing:work_order_list_list` | 🔍 Review manually |

### Marketing (40 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `ab_automated_test_list` | `marketing:ab_automated_test_list`, `marketing:ab_automated_test_list_list` | 🔍 Review manually |
| `ab_test_list` | `marketing:ab_test_list`, `marketing:ab_test_list_list` | 🔍 Review manually |
| `ab_test_results` | `marketing:ab_test_results`, `marketing:ab_test_results_list` | 🔍 Review manually |
| `block_type_list` | `marketing:block_type_list`, `marketing:block_type_list_list` | 🔍 Review manually |
| `budget_vs_actual` | `marketing:budget_vs_actual`, `marketing:budget_vs_actual_list` | 🔍 Review manually |
| `cac_analytics` | `marketing:cac_analytics`, `marketing:cac_analytics_list` | 🟢 Add to navigation |
| `campaign_calendar` | `marketing:campaign_calendar`, `marketing:campaign_calendar_list` | 🔍 Review manually |
| `campaign_confirm_clone` | `marketing:campaign_confirm_clone`, `marketing:campaign_confirm_clone_list` | 🔍 Review manually |
| `campaign_detail` | `marketing:campaign_detail`, `marketing:campaign_detail_list` | 🔍 Review manually |
| `campaign_performance` | `marketing:campaign_performance`, `marketing:campaign_performance_list` | 🔍 Review manually |
| `campaign_performance_analytics` | `marketing:campaign_performance_analytics`, `marketing:campaign_performance_analytics_list` | 🟢 Add to navigation |
| `campaign_performance_dashboard` | `marketing:campaign_performance_dashboard`, `marketing:campaign_performance_dashboard_list` | 🟢 Add to navigation |
| `campaign_performance_detail` | `marketing:campaign_performance_detail`, `marketing:campaign_performance_detail_list` | 🔍 Review manually |
| `campaign_performance_list` | `marketing:campaign_performance_list`, `marketing:campaign_performance_list_list` | 🔍 Review manually |
| `campaign_recipient_list` | `marketing:campaign_recipient_list`, `marketing:campaign_recipient_list_list` | 🔍 Review manually |
| `campaign_status_list` | `marketing:campaign_status_list`, `marketing:campaign_status_list_list` | 🔍 Review manually |
| `config_form_generic` | `marketing:config_form_generic`, `marketing:config_form_generic_list` | 🔍 Review manually |
| `deliverability_report` | `marketing:deliverability_report`, `marketing:deliverability_report_list` | 🟢 Add to navigation |
| `drip_campaign_detail` | `marketing:drip_campaign_detail`, `marketing:drip_campaign_detail_list` | 🔍 Review manually |
| `drip_campaign_list` | `marketing:drip_campaign_list`, `marketing:drip_campaign_list_list` | 🔍 Review manually |
| `email_campaign_list` | `marketing:email_campaign_list`, `marketing:email_campaign_list_list` | 🔍 Review manually |
| `email_category_list` | `marketing:email_category_list`, `marketing:email_category_list_list` | 🔍 Review manually |
| `email_integration_list` | `marketing:email_integration_list`, `marketing:email_integration_list_list` | 🔍 Review manually |
| `email_provider_list` | `marketing:email_provider_list`, `marketing:email_provider_list_list` | 🔍 Review manually |
| `email_template_editor` | `marketing:email_template_editor`, `marketing:email_template_editor_list` | 🟢 Add to navigation |
| `email_template_list` | `marketing:email_template_list`, `marketing:email_template_list_list` | 🔍 Review manually |
| `email_template_preview` | `marketing:email_template_preview`, `marketing:email_template_preview_list` | 🟡 Keep as action/API endpoint |
| `landing_page` | `marketing:landing_page`, `marketing:landing_page_list` | 🔍 Review manually |
| `landing_page_block_list` | `marketing:landing_page_block_list`, `marketing:landing_page_block_list_list` | 🔍 Review manually |
| `landing_page_builder` | `marketing:landing_page_builder`, `marketing:landing_page_builder_list` | 🟢 Add to navigation |
| `landing_page_list` | `marketing:landing_page_list`, `marketing:landing_page_list_list` | 🔍 Review manually |
| `message_category_list` | `marketing:message_category_list`, `marketing:message_category_list_list` | 🔍 Review manually |
| `message_template_list` | `marketing:message_template_list`, `marketing:message_template_list_list` | 🔍 Review manually |
| `message_type_list` | `marketing:message_type_list`, `marketing:message_type_list_list` | 🔍 Review manually |
| `nurture_campaign_list` | `marketing:nurture_campaign_list`, `marketing:nurture_campaign_list_list` | 🔍 Review manually |
| `pipeline_influence` | `marketing:pipeline_influence`, `marketing:pipeline_influence_list` | 🔍 Review manually |
| `roi_calculator` | `marketing:roi_calculator`, `marketing:roi_calculator_list` | 🔍 Review manually |
| `segment_list` | `marketing:segment_list`, `marketing:segment_list_list` | 🔍 Review manually |
| `segment_members` | `marketing:segment_members`, `marketing:segment_members_list` | 🔍 Review manually |
| `template_builder` | `marketing:template_builder`, `marketing:template_builder_list` | 🟢 Add to navigation |

### Nps (10 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `embed_example` | `nps:embed_example`, `nps:embed_example_list` | 🔍 Review manually |
| `escalation_action_list` | `nps:escalation_action_list`, `nps:escalation_action_list_list` | 🔍 Review manually |
| `escalation_action_log_list` | `nps:escalation_action_log_list`, `nps:escalation_action_log_list_list` | 🔍 Review manually |
| `escalation_rule_list` | `nps:escalation_rule_list`, `nps:escalation_rule_list_list` | 🔍 Review manually |
| `in_app_widget` | `nps:in_app_widget`, `nps:in_app_widget_list` | 🔍 Review manually |
| `manager_nps_alert` | `nps:manager_nps_alert`, `nps:manager_nps_alert_list` | 🔍 Review manually |
| `nps_ab_test` | `nps:nps_ab_test`, `nps:nps_ab_test_list` | 🔍 Review manually |
| `nps_trend_chart` | `nps:nps_trend_chart`, `nps:nps_trend_chart_list` | 🔍 Review manually |
| `promoter_referral_list` | `nps:promoter_referral_list`, `nps:promoter_referral_list_list` | 🔍 Review manually |
| `trend_snapshot_list` | `nps:trend_snapshot_list`, `nps:trend_snapshot_list_list` | 🔍 Review manually |

### Opportunities (4 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `kanban` | `opportunities:kanban`, `opportunities:kanban_list` | 🔍 Review manually |
| `opportunity_detail` | `opportunities:opportunity_detail`, `opportunities:opportunity_detail_list` | 🔍 Review manually |
| `opportunity_stage_list` | `opportunities:opportunity_stage_list`, `opportunities:opportunity_stage_list_list` | 🔍 Review manually |
| `pipeline_type_list` | `opportunities:pipeline_type_list`, `opportunities:pipeline_type_list_list` | 🔍 Review manually |

### Pos (17 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `components/cart_item` | `pos:components_cart_item`, `pos:components_cart_item_list` | 🔍 Review manually |
| `components/cart_summary` | `pos:components_cart_summary`, `pos:components_cart_summary_list` | 🔍 Review manually |
| `components/customer_modal` | `pos:components_customer_modal`, `pos:components_customer_modal_list` | 🔍 Review manually |
| `components/hardware_status` | `pos:components_hardware_status`, `pos:components_hardware_status_list` | 🔍 Review manually |
| `components/payment_modal` | `pos:components_payment_modal`, `pos:components_payment_modal_list` | 🔍 Review manually |
| `hardware_test` | `pos:hardware_test`, `pos:hardware_test_list` | 🔍 Review manually |
| `receipt` | `pos:receipt`, `pos:receipt_list` | 🔍 Review manually |
| `receipt_preview` | `pos:receipt_preview`, `pos:receipt_preview_list` | 🟡 Keep as action/API endpoint |
| `refund_create` | `pos:refund_create`, `pos:refund_create_list` | 🔍 Review manually |
| `refund_detail` | `pos:refund_detail`, `pos:refund_detail_list` | 🔍 Review manually |
| `report_payments` | `pos:report_payments`, `pos:report_payments_list` | 🟢 Add to navigation |
| `report_products` | `pos:report_products`, `pos:report_products_list` | 🟢 Add to navigation |
| `report_trends` | `pos:report_trends`, `pos:report_trends_list` | 🟢 Add to navigation |
| `session_close` | `pos:session_close`, `pos:session_close_list` | 🔍 Review manually |
| `session_detail` | `pos:session_detail`, `pos:session_detail_list` | 🔍 Review manually |
| `transaction_detail` | `pos:transaction_detail`, `pos:transaction_detail_list` | 🔍 Review manually |
| `transaction_void` | `pos:transaction_void`, `pos:transaction_void_list` | 🔍 Review manually |

### Products (9 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `competitorproduct_detail` | `products:competitorproduct_detail`, `products:competitorproduct_detail_list` | 🔍 Review manually |
| `dashboard_governance` | `products:dashboard_governance`, `products:dashboard_governance_list` | 🟢 Add to navigation |
| `label_sheet` | `products:label_sheet`, `products:label_sheet_list` | 🔍 Review manually |
| `label_standard` | `products:label_standard`, `products:label_standard_list` | 🔍 Review manually |
| `partials/category_row` | `products:partials_category_row`, `products:partials_category_row_list` | 🔍 Review manually |
| `product_detail` | `products:product_detail`, `products:product_detail_list` | 🔍 Review manually |
| `productbundle_detail` | `products:productbundle_detail`, `products:productbundle_detail_list` | 🔍 Review manually |
| `productcomparison_detail` | `products:productcomparison_detail`, `products:productcomparison_detail_list` | 🔍 Review manually |
| `supplier_list` | `products:supplier_list`, `products:supplier_list_list` | 🔍 Review manually |

### Projects (8 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `gantt` | `projects:gantt`, `projects:gantt_list` | 🔍 Review manually |
| `profitability_report` | `projects:profitability_report`, `projects:profitability_report_list` | 🟢 Add to navigation |
| `project_detail` | `projects:project_detail`, `projects:project_detail_list` | 🔍 Review manually |
| `project_list` | `projects:project_list`, `projects:project_list_list` | 🔍 Review manually |
| `resource_capacity` | `projects:resource_capacity`, `projects:resource_capacity_list` | 🔍 Review manually |
| `revenue_recognition` | `projects:revenue_recognition`, `projects:revenue_recognition_list` | 🔍 Review manually |
| `timesheet_detail` | `projects:timesheet_detail`, `projects:timesheet_detail_list` | 🔍 Review manually |
| `timesheet_list` | `projects:timesheet_list`, `projects:timesheet_list_list` | 🔍 Review manually |

### Proposals (13 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `approval_template_detail` | `proposals:approval_template_detail`, `proposals:approval_template_detail_list` | 🔍 Review manually |
| `approval_template_manage` | `proposals:approval_template_manage`, `proposals:approval_template_manage_list` | 🔍 Review manually |
| `client_view` | `proposals:client_view`, `proposals:client_view_list` | 🔍 Review manually |
| `confirm_delete` | `proposals:confirm_delete`, `proposals:confirm_delete_list` | 🔍 Review manually |
| `detail` | `proposals:detail`, `proposals:detail_list` | 🔍 Review manually |
| `editor` | `proposals:editor`, `proposals:editor_list` | 🟢 Add to navigation |
| `form` | `proposals:form`, `proposals:form_list` | 🔍 Review manually |
| `generate_pdf` | `proposals:generate_pdf`, `proposals:generate_pdf_list` | 🟡 Keep as action/API endpoint |
| `proposal_approval` | `proposals:proposal_approval`, `proposals:proposal_approval_list` | 🔍 Review manually |
| `proposal_detail` | `proposals:proposal_detail`, `proposals:proposal_detail_list` | 🔍 Review manually |
| `proposal_pdf` | `proposals:proposal_pdf`, `proposals:proposal_pdf_list` | 🟡 Keep as action/API endpoint |
| `send_email` | `proposals:send_email`, `proposals:send_email_list` | 🔍 Review manually |
| `signature` | `proposals:signature`, `proposals:signature_list` | 🔍 Review manually |

### Purchasing (7 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `invoice_detail` | `purchasing:invoice_detail`, `purchasing:invoice_detail_list` | 🔍 Review manually |
| `po_detail` | `purchasing:po_detail`, `purchasing:po_detail_list` | 🔍 Review manually |
| `po_receive` | `purchasing:po_receive`, `purchasing:po_receive_list` | 🔍 Review manually |
| `reconciliation` | `purchasing:reconciliation`, `purchasing:reconciliation_list` | 🔍 Review manually |
| `requisition_convert_po` | `purchasing:requisition_convert_po`, `purchasing:requisition_convert_po_list` | 🔍 Review manually |
| `requisition_detail` | `purchasing:requisition_detail`, `purchasing:requisition_detail_list` | 🔍 Review manually |
| `supplier_payment_list` | `purchasing:supplier_payment_list`, `purchasing:supplier_payment_list_list` | 🔍 Review manually |

### Quality_Control (6 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `capa_list` | `quality_control:capa_list`, `quality_control:capa_list_list` | 🔍 Review manually |
| `control_charts` | `quality_control:control_charts`, `quality_control:control_charts_list` | 🔍 Review manually |
| `library_list` | `quality_control:library_list`, `quality_control:library_list_list` | 🔍 Review manually |
| `log_list` | `quality_control:log_list`, `quality_control:log_list_list` | 🔍 Review manually |
| `ncr_list` | `quality_control:ncr_list`, `quality_control:ncr_list_list` | 🔍 Review manually |
| `rule_list` | `quality_control:rule_list`, `quality_control:rule_list_list` | 🔍 Review manually |

### Reports (6 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `detail` | `reports:detail`, `reports:detail_list` | 🔍 Review manually |
| `edit` | `reports:edit`, `reports:edit_list` | 🔍 Review manually |
| `export_email` | `reports:export_email`, `reports:export_email_list` | 🟡 Keep as action/API endpoint |
| `public_report` | `reports:public_report`, `reports:public_report_list` | 🟢 Add to navigation |
| `snapshot_list` | `reports:snapshot_list`, `reports:snapshot_list_list` | 🔍 Review manually |
| `widget` | `reports:widget`, `reports:widget_list` | 🔍 Review manually |

### Sales (8 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `product/product_dashboard` | `sales:product_product_dashboard`, `sales:product_product_dashboard_list` | 🟢 Add to navigation |
| `product/product_list` | `sales:product_product_list`, `sales:product_product_list_list` | 🔍 Review manually |
| `commission_rule_list` | `sales:commission_rule_list`, `sales:commission_rule_list_list` | 🔍 Review manually |
| `dashboard_revenue` | `sales:dashboard_revenue`, `sales:dashboard_revenue_list` | 🟢 Add to navigation |
| `forecast_dashboard` | `sales:forecast_dashboard`, `sales:forecast_dashboard_list` | 🟢 Add to navigation |
| `pipeline_kanban` | `sales:pipeline_kanban`, `sales:pipeline_kanban_list` | 🔍 Review manually |
| `sale_dashboard` | `sales:sale_dashboard`, `sales:sale_dashboard_list` | 🟢 Add to navigation |
| `sale_detail` | `sales:sale_detail`, `sales:sale_detail_list` | 🔍 Review manually |

### Settings_App (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `automation_rules` | `settings_app:automation_rules`, `settings_app:automation_rules_list` | 🔍 Review manually |
| `confirm_delete` | `settings_app:confirm_delete`, `settings_app:confirm_delete_list` | 🔍 Review manually |
| `crm_settings_list` | `settings_app:crm_settings_list`, `settings_app:crm_settings_list_list` | 🔍 Review manually |
| `score_decay_config` | `settings_app:score_decay_config`, `settings_app:score_decay_config_list` | 🔍 Review manually |
| `welcome_email` | `settings_app:welcome_email`, `settings_app:welcome_email_list` | 🔍 Review manually |

### Suppliers (1 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `supplier_detail` | `suppliers:supplier_detail`, `suppliers:supplier_detail_list` | 🔍 Review manually |

### Tasks (13 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `partials/generic_task_list` | `tasks:partials_generic_task_list`, `tasks:partials_generic_task_list_list` | 🔍 Review manually |
| `recurrence_pattern_list` | `tasks:recurrence_pattern_list`, `tasks:recurrence_pattern_list_list` | 🔍 Review manually |
| `task_activities` | `tasks:task_activities`, `tasks:task_activities_list` | 🔍 Review manually |
| `task_comments` | `tasks:task_comments`, `tasks:task_comments_list` | 🔍 Review manually |
| `task_detail` | `tasks:task_detail`, `tasks:task_detail_list` | 🔍 Review manually |
| `task_kanban` | `tasks:task_kanban`, `tasks:task_kanban_list` | 🔍 Review manually |
| `task_priority_list` | `tasks:task_priority_list`, `tasks:task_priority_list_list` | 🔍 Review manually |
| `task_sharing` | `tasks:task_sharing`, `tasks:task_sharing_list` | 🔍 Review manually |
| `task_status_list` | `tasks:task_status_list`, `tasks:task_status_list_list` | 🔍 Review manually |
| `task_template_list` | `tasks:task_template_list`, `tasks:task_template_list_list` | 🔍 Review manually |
| `task_type_list` | `tasks:task_type_list`, `tasks:task_type_list_list` | 🔍 Review manually |
| `task_unshare` | `tasks:task_unshare`, `tasks:task_unshare_list` | 🔍 Review manually |
| `task_unshare_confirm` | `tasks:task_unshare_confirm`, `tasks:task_unshare_confirm_list` | 🔍 Review manually |

### Tenants (37 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `archive_confirm` | `tenants:archive_confirm`, `tenants:archive_confirm_list` | 🔍 Review manually |
| `automated_lifecycle_rules` | `tenants:automated_lifecycle_rules`, `tenants:automated_lifecycle_rules_list` | 🔍 Review manually |
| `automated_rule_list` | `tenants:automated_rule_list`, `tenants:automated_rule_list_list` | 🔍 Review manually |
| `clone_status` | `tenants:clone_status`, `tenants:clone_status_list` | 🔍 Review manually |
| `create_automated_rule` | `tenants:create_automated_rule`, `tenants:create_automated_rule_list` | 🔍 Review manually |
| `data_isolation_audit_detail` | `tenants:data_isolation_audit_detail`, `tenants:data_isolation_audit_detail_list` | 🔍 Review manually |
| `data_preservation` | `tenants:data_preservation`, `tenants:data_preservation_list` | 🔍 Review manually |
| `data_residency_settings` | `tenants:data_residency_settings`, `tenants:data_residency_settings_list` | 🔍 Review manually |
| `data_restoration` | `tenants:data_restoration`, `tenants:data_restoration_list` | 🔍 Review manually |
| `entitlement_templates` | `tenants:entitlement_templates`, `tenants:entitlement_templates_list` | 🔍 Review manually |
| `feature_access_check` | `tenants:feature_access_check`, `tenants:feature_access_check_list` | 🔍 Review manually |
| `initiate_restoration` | `tenants:initiate_restoration`, `tenants:initiate_restoration_list` | 🔍 Review manually |
| `lifecycle_dashboard` | `tenants:lifecycle_dashboard`, `tenants:lifecycle_dashboard_list` | 🟢 Add to navigation |
| `lifecycle_event_detail` | `tenants:lifecycle_event_detail`, `tenants:lifecycle_event_detail_list` | 🔍 Review manually |
| `lifecycle_event_list` | `tenants:lifecycle_event_list`, `tenants:lifecycle_event_list_list` | 🔍 Review manually |
| `lifecycle_event_log` | `tenants:lifecycle_event_log`, `tenants:lifecycle_event_log_list` | 🔍 Review manually |
| `lifecycle_workflow_detail` | `tenants:lifecycle_workflow_detail`, `tenants:lifecycle_workflow_detail_list` | 🔍 Review manually |
| `lifecycle_workflows` | `tenants:lifecycle_workflows`, `tenants:lifecycle_workflows_list` | 🔍 Review manually |
| `logo_management` | `tenants:logo_management`, `tenants:logo_management_list` | 🔍 Review manually |
| `member_detail` | `tenants:member_detail`, `tenants:member_detail_list` | 🔍 Review manually |
| `migration_record_detail` | `tenants:migration_record_detail`, `tenants:migration_record_detail_list` | 🔍 Review manually |
| `migration_record_list` | `tenants:migration_record_list`, `tenants:migration_record_list_list` | 🔍 Review manually |
| `onboarding/branding` | `tenants:onboarding_branding`, `tenants:onboarding_branding_list` | 🔍 Review manually |
| `onboarding/signup` | `tenants:onboarding_signup`, `tenants:onboarding_signup_list` | 🔍 Review manually |
| `preservation_detail` | `tenants:preservation_detail`, `tenants:preservation_detail_list` | 🔍 Review manually |
| `preservation_list` | `tenants:preservation_list`, `tenants:preservation_list_list` | 🔍 Review manually |
| `provision_new` | `tenants:provision_new`, `tenants:provision_new_list` | 🔍 Review manually |
| `reactivate_confirm` | `tenants:reactivate_confirm`, `tenants:reactivate_confirm_list` | 🔍 Review manually |
| `signup` | `tenants:signup`, `tenants:signup_list` | 🔍 Review manually |
| `status_management` | `tenants:status_management`, `tenants:status_management_list` | 🔍 Review manually |
| `suspend_confirm` | `tenants:suspend_confirm`, `tenants:suspend_confirm_list` | 🔍 Review manually |
| `suspension_workflow` | `tenants:suspension_workflow`, `tenants:suspension_workflow_list` | 🔍 Review manually |
| `suspension_workflow_list` | `tenants:suspension_workflow_list`, `tenants:suspension_workflow_list_list` | 🔍 Review manually |
| `termination_workflow` | `tenants:termination_workflow`, `tenants:termination_workflow_list` | 🔍 Review manually |
| `termination_workflow_list` | `tenants:termination_workflow_list`, `tenants:termination_workflow_list_list` | 🔍 Review manually |
| `workflow_execution_detail` | `tenants:workflow_execution_detail`, `tenants:workflow_execution_detail_list` | 🔍 Review manually |
| `workflow_execution_list` | `tenants:workflow_execution_list`, `tenants:workflow_execution_list_list` | 🔍 Review manually |

### Wazo (1 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `components/softphone` | `wazo:components_softphone`, `wazo:components_softphone_list` | 🔍 Review manually |

---

## 📋 Recommendations

### Priority 1: Fix Broken Links

1. **dashboard:drill_down**: Cannot resolve URL pattern: dashboard:drill_down
1. **billing:portal**: Reverse for 'login' not found. 'login' is not a valid view function or pattern name.
1. **billing:revenue_overview**: 'AnonymousUser' object has no attribute 'tenant'
1. **billing:mrr_analytics**: 'AnonymousUser' object has no attribute 'tenant'
1. **billing:arr_analytics**: 'AnonymousUser' object has no attribute 'tenant'
   - ... and 130 more

### Priority 2: Add High-Value Orphans to Navigation

1. **accounts**: `account_analytics` - Likely a valuable feature
1. **accounts**: `admin/user_management_dashboard` - Likely a valuable feature
1. **audit_logs**: `dashboard` - Likely a valuable feature
1. **commissions**: `plan_builder` - Likely a valuable feature
1. **communication**: `call_analytics` - Likely a valuable feature
1. **core**: `dynamic_choices_dashboard` - Likely a valuable feature
1. **core**: `security/security_dashboard` - Likely a valuable feature
1. **global_alerts**: `alert_analytics` - Likely a valuable feature
1. **leads**: `cac_analytics` - Likely a valuable feature
1. **leads**: `lead_analytics` - Likely a valuable feature

### Priority 3: Clean Up

- Review and remove deprecated templates
- Consolidate duplicate templates
- Document intentionally orphaned templates

---

*End of Report*

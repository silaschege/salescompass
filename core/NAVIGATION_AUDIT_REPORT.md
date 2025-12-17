# Navigation Audit Report
**Generated**: 2025-12-15 17:06:35  
**Project**: SalesCompass CRM

---

## Executive Summary

### Overall Statistics
- **Total Templates**: 555
- **Total URL Patterns**: 982
- **Navigation Links Tested**: 262
- **Working Links**: 131 (50.0%)
- **Broken Links**: 131 (50.0%)
- **Orphaned Templates**: 177

### Health Score
**50.0%** ⚠️ Fair (significant fixes needed)

---

## 🔴 Broken Navigation Links

| # | URL Name | Source Template | Status | Issue |
|---|----------|-----------------|--------|-------|
| 1 | `accounts:member_list` | base.html | Error | No object permission policy registered for <class 'accounts.models.OrganizationMember'>. Register it in core.object_permissions.OBJECT_POLICIES |
| 2 | `accounts:member_create` | base.html | Error | accounts/member_form.html |
| 3 | `accounts:role_list` | base.html | Error | No object permission policy registered for <class 'accounts.models.TeamRole'>. Register it in core.object_permissions.OBJECT_POLICIES |
| 4 | `accounts:territory_list` | base.html | Error | No object permission policy registered for <class 'accounts.models.Territory'>. Register it in core.object_permissions.OBJECT_POLICIES |
| 5 | `accounts:territory_create` | base.html | Error | 'crispy_forms_tags' is not a registered tag library. Must be one of:
account_filters
admin_list
admin_modify
admin_urls
auth_extras
billing_tags
cache
core_extras
filters_extras
humanize
i18n
l10n
log
math
number_filters
rest_framework
stage_filters
static
tz |
| 6 | `dashboard:render` | base.html | HTTP 404 | 404 |
| 7 | `core:logout` | base.html | HTTP 405 | 405 |
| 8 | `developer:portal` | base.html | Error | cannot import name 'APIKey' from 'settings_app.models' (/home/silaskimani/Documents/replit/git/salescompass/core/settings_app/models.py) |
| 9 | `developer:api_keys` | base.html | Error | cannot import name 'APIKey' from 'settings_app.models' (/home/silaskimani/Documents/replit/git/salescompass/core/settings_app/models.py) |
| 10 | `developer:webhooks` | base.html | Error | cannot import name 'Webhook' from 'settings_app.models' (/home/silaskimani/Documents/replit/git/salescompass/core/settings_app/models.py) |
| 11 | `developer:analytics` | base.html | Error | cannot import name 'APIKey' from 'settings_app.models' (/home/silaskimani/Documents/replit/git/salescompass/core/settings_app/models.py) |
| 12 | `proposals:engagement_dashboard` | base.html | Error | Cannot resolve keyword 'created_at' into field. Choices are: content, email_click_count, email_opened, email_opened_at, emails, esg_section_content, esg_section_viewed, events, id, last_viewed, opportunity, opportunity_id, pdfs, sent_by, sent_by_id, status, tenant, tenant_id, title, total_view_time_sec, view_count |
| 13 | `commissions:list` | base.html | No Reverse Match | Cannot resolve URL pattern: commissions:list |
| 14 | `commissions:history` | base.html | Error | Reverse for 'list' not found. 'list' is not a valid view function or pattern name. |
| 15 | `opportunities:revenue_forecast` | base.html | Error | core/base.html |
| 16 | `nps:nps_dashboard` | base.html | Error | Cannot resolve keyword 'tenant_id' into field. Choices are: abautomatedtests, access_patterns, account, account_id, account_team_roles, account_territories, accounts, actiontypes, adjustments, adjustmenttypes, alert_configurations, alert_notifications, alert_rules_targeted, alert_suppressions, alerts, anomaly_detections, api_call_limit, api_tokens, archived_at, articleratings, articles, articleversions, articleviews, assignmentrules, assignmentruletypes, audit_reports, automated_lifecycle_events, automation_rules, automationactions, automationconditions, automationexecutionlogs, automations, behavioralscoringrules, billing_cycle_anchor, blocktypes, bundleitems, campaignattributions, campaignrecipients, campaigns, campaignstatuss, capacity_planning, case_assignment_rules, caseattachments, casecomments, cases, categorys, cloned_from, clones_created, comment, commissionpayments, commissionplans, commissionrules, commissions, communications, competitorproducts, compliance_audits, connector_configurations, contact_email, contacts, core_assignment_rule_types, core_field_types, core_model_choices, core_module_choices, core_module_labels, correlation_groups, created_at, creditadjustments, csatdetractoralerts, csatresponses, csatsurveys, customfields, dashboardconfigs, dashboardwidgets, data_preservation_records, data_restoration_records, dealsizecategorys, delivery_id, demographicscoringrules, description, domain, dynamic_setting_groups, dynamic_setting_types, dynamic_settings, emailcampaigns, emailcategorys, emailintegrations, emailproviders, emailtemplates, engagementevent, exportformats, exportjobs, feature_entitlements, feature_rollout_schedules, feedback_forms, fieldtypes, forecastsnapshots, id, industrys, infrastructure_alerts, integration_audit_logs, integration_health_checks, invoices, ip_address, is_active, is_archived, is_suspended, knowledgebasearticles, landingpageblocks, landingpages, lead_action_types, lead_assignment_rules, lead_behavioral_scoring_rules, lead_demographic_scoring_rules, lead_operator_types, leads, leadsourceanalyticss, leadsources, leadstatuss, lifecycle_events, lifecycle_workflow_executions, logo_url, marketing_email_integrations_tenant, marketingchannels, messagecategorys, messagetemplates, messagetypes, migration_destinations, migration_sources, modelchoices, module_provisions, modulechoices, modulelabels, name, notification_templates, notificationchannels, npsabresponse, npsdetractoralert, operatortypes, opportunity_assignment_rules, opportunity_pipeline_types, opportunityproducts, opportunitys, opportunitystages, organizationmembers, paymentmethods, paymentproviderconfigs, paymentproviders, payments, paymenttypes, performance_baselines, performancemetric, pipelinestages, pipelinetypes, plan, plan_id, plans, plantiers, preservation_schedules, pricingtiers, primary_color, productbundles, productcomparisons, productdependencys, products, proposalemails, proposalevents, proposalpdfs, proposals, proposaltemplates, quality_check_schedules, quotas, recurrencepatterns, reportactions, reportanalyticss, reportexports, reportformats, reportnotifications, reports, reportschedulefrequencys, reportschedules, reportsubscribers, reporttemplates, reporttypes, resource_allocations, resource_monitoring, resource_quotas, resource_reports, salesperformancemetrics, salestargets, score, secondary_color, security_incidents_affected, service_configurations, settinggroups, settings, settingtypes, slapolicys, slug, storage_limit_mb, subdomain, subscription_status, subscriptions, subscriptionstatuss, subscriptiontypes, support_tickets, survey, survey_id, suspension_reason, suspension_workflows, system_notifications, taskprioritys, tasks, taskstatuss, tasktemplates, tasktypes, teammembers, teamroles, templateformats, templatetypes, tenant_config, tenant_logs, tenant_ptr, tenant_ptr_id, tenant_settings, termination_workflows, territorys, trial_end_date, updated_at, usage_metrics, user_agent, user_limit, usercommissionplans, users, webhook_delivery_logs, webhookendpoints, webtoleadforms, widgetcategorys, widgettypes, winlossanalysiss, workflowactions, workflowexecutions, workflows, workflowtriggers |
| 17 | `nps:detractor_kanban` | base.html | Error | Cannot resolve keyword 'tenant_id' into field. Choices are: abautomatedtests, access_patterns, account_team_roles, account_territories, accounts, actiontypes, adjustments, adjustmenttypes, alert_configurations, alert_notifications, alert_rules_targeted, alert_suppressions, alerts, anomaly_detections, api_call_limit, api_tokens, archived_at, articleratings, articles, articleversions, articleviews, assigned_to, assigned_to_id, assignmentrules, assignmentruletypes, audit_reports, automated_lifecycle_events, automation_rules, automationactions, automationconditions, automationexecutionlogs, automations, behavioralscoringrules, billing_cycle_anchor, blocktypes, bundleitems, campaignattributions, campaignrecipients, campaigns, campaignstatuss, capacity_planning, case_assignment_rules, caseattachments, casecomments, cases, categorys, cloned_from, clones_created, commissionpayments, commissionplans, commissionrules, commissions, communications, competitorproducts, compliance_audits, connector_configurations, contacts, core_assignment_rule_types, core_field_types, core_model_choices, core_module_choices, core_module_labels, correlation_groups, created_at, creditadjustments, csatdetractoralerts, csatresponses, csatsurveys, customfields, dashboardconfigs, dashboardwidgets, data_preservation_records, data_restoration_records, dealsizecategorys, demographicscoringrules, description, domain, dynamic_setting_groups, dynamic_setting_types, dynamic_settings, emailcampaigns, emailcategorys, emailintegrations, emailproviders, emailtemplates, exportformats, exportjobs, feature_entitlements, feature_rollout_schedules, feedback_forms, fieldtypes, forecastsnapshots, id, industrys, infrastructure_alerts, integration_audit_logs, integration_health_checks, invoices, is_active, is_archived, is_suspended, knowledgebasearticles, landingpageblocks, landingpages, lead_action_types, lead_assignment_rules, lead_behavioral_scoring_rules, lead_demographic_scoring_rules, lead_operator_types, leads, leadsourceanalyticss, leadsources, leadstatuss, lifecycle_events, lifecycle_workflow_executions, logo_url, marketing_email_integrations_tenant, marketingchannels, messagecategorys, messagetemplates, messagetypes, migration_destinations, migration_sources, modelchoices, module_provisions, modulechoices, modulelabels, name, notes, notification_templates, notificationchannels, operatortypes, opportunity_assignment_rules, opportunity_pipeline_types, opportunityproducts, opportunitys, opportunitystages, organizationmembers, paymentmethods, paymentproviderconfigs, paymentproviders, payments, paymenttypes, performance_baselines, performancemetric, pipelinestages, pipelinetypes, plan, plan_id, plans, plantiers, preservation_schedules, pricingtiers, primary_color, productbundles, productcomparisons, productdependencys, products, proposalemails, proposalevents, proposalpdfs, proposals, proposaltemplates, quality_check_schedules, quotas, recurrencepatterns, reportactions, reportanalyticss, reportexports, reportformats, reportnotifications, reports, reportschedulefrequencys, reportschedules, reportsubscribers, reporttemplates, reporttypes, resolved_at, resource_allocations, resource_monitoring, resource_quotas, resource_reports, response, response_id, salesperformancemetrics, salestargets, secondary_color, security_incidents_affected, service_configurations, settinggroups, settings, settingtypes, slapolicys, slug, status, storage_limit_mb, subdomain, subscription_status, subscriptions, subscriptionstatuss, subscriptiontypes, support_tickets, suspension_reason, suspension_workflows, system_notifications, taskprioritys, tasks, taskstatuss, tasktemplates, tasktypes, teammembers, teamroles, templateformats, templatetypes, tenant_config, tenant_logs, tenant_ptr, tenant_ptr_id, tenant_settings, termination_workflows, territorys, trial_end_date, updated_at, usage_metrics, user_limit, usercommissionplans, users, webhook_delivery_logs, webhookendpoints, webtoleadforms, widgetcategorys, widgettypes, winlossanalysiss, workflowactions, workflowexecutions, workflows, workflowtriggers |
| 18 | `reports:dashboard` | base.html | Error | Cannot resolve keyword 'is_active' into field. Choices are: category_old, category_ref, category_ref_id, id, template_path, tenant, tenant_id, widget_created_at, widget_description, widget_is_active, widget_name, widget_type_old, widget_type_ref, widget_type_ref_id, widget_updated_at |
| 19 | `reports:list` | base.html | Error | Cannot resolve keyword 'created_at' into field. Choices are: analytics, created_by, created_by_id, exports, id, is_scheduled, last_run, last_run_status, query_config, report_created_at, report_description, report_is_active, report_name, report_type, report_type_ref, report_type_ref_id, report_updated_at, schedule_frequency, schedule_frequency_ref, schedule_frequency_ref_id, schedules, subscribers, tenant, tenant_id |
| 20 | `automation:log_list` | base.html | Error | Could not parse the remainder: '=='triggered'' from 'request.GET.status=='triggered'' |
| 21 | `automation:workflow_action_list` | base.html | Error | Reverse for 'workflow_action_create' not found. 'workflow_action_create' is not a valid view function or pattern name. |
| 22 | `global_alerts:dashboard` | base.html | Error | name 'models' is not defined |
| 23 | `global_alerts:alert_list` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alert_list |
| 24 | `global_alerts:alert_create` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alert_create |
| 25 | `global_alerts:active_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:active_alerts |
| 26 | `global_alerts:scheduled_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:scheduled_alerts |
| 27 | `global_alerts:alerts_by_type` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alerts_by_type |
| 28 | `global_alerts:alerts_by_severity` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:alerts_by_severity |
| 29 | `global_alerts:global_alerts` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:global_alerts |
| 30 | `global_alerts:tenant_specific` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:tenant_specific |
| 31 | `global_alerts:analytics` | base.html | No Reverse Match | Cannot resolve URL pattern: global_alerts:analytics |
| 32 | `reports:schedule_list` | base.html | Error | Cannot resolve keyword 'created_at' into field. Choices are: frequency, frequency_ref, frequency_ref_id, id, last_run, next_run, notifications, recipients, report, report_id, schedule_created_at, schedule_description, schedule_is_active, schedule_name, schedule_updated_at, tenant, tenant_id |
| 33 | `reports:schedule_create` | base.html | Error | BaseModelForm.__init__() got an unexpected keyword argument 'user' |
| 34 | `reports:export_list` | base.html | Error | Cannot resolve keyword 'created_at' into field. Choices are: completed_at, created_by, created_by_id, error_message, export_created_at, export_format, export_format_ref, export_format_ref_id, file, id, report, report_id, status, tenant, tenant_id |
| 35 | `reports:sales_analytics` | base.html | Error | name 'timedelta' is not defined |
| 36 | `products:product_list` | base.html | Error | Cannot resolve keyword 'is_active' into field. Choices are: auto_renewal, available_from, available_to, base_price, billing_cycle, bundleitem, carbon_footprint, category, commissionrule, comparisons, competitor_mappings, currency, dependencies, esg_certifications, esg_certified, id, is_subscription, opportunity, opportunityproduct, owner, owner_id, pricing_model, pricing_tiers, product_description, product_is_active, product_name, productbundle, required_by, sales, sales_commission_rules, sku, subscription_term, sustainability_notes, tags, tco2e_saved, tenant, tenant_id, upc |
| 37 | `learn:search` | base.html | Error | Cannot resolve keyword 'slug' into field. Choices are: article_slug, article_type, articlerating, articleview, author, author_id, category, category_id, exportjob, id, is_public, last_edited_by, last_edited_by_id, meta_description, required_role, status, summary, tags, tenant, tenant_id, title, versions |
| 38 | `learn:usage_analytics` | base.html | Error | Cannot resolve keyword 'slug' into field. Choices are: article_slug, article_type, articlerating, articleview, author, author_id, category, category_id, exportjob, id, is_public, last_edited_by, last_edited_by_id, meta_description, required_role, status, summary, tags, tenant, tenant_id, title, versions |
| 39 | `tenants:list` | base.html | Error | Reverse for 'suspend_tenant' not found. 'suspend_tenant' is not a valid view function or pattern name. |
| 40 | `tenants:data-preservation` | base.html | Error | Reverse for 'create-data-preservation' not found. 'create-data-preservation' is not a valid view function or pattern name. |
| 41 | `tenants:plan_selection` | base.html | Error | Cannot resolve keyword 'is_active' into field. Choices are: features, id, plan_created_at, plan_is_active, plan_name, plan_updated_at, price_annually, price_monthly, subscriptions, tenant, tenant_id, tenants, tier, tier_ref, tier_ref_id |
| 42 | `tenants:feature_toggles` | base.html | Error | Could not parse the remainder: '==t.id' from 'tenant.id==t.id' |
| 43 | `tenants:domain_management_list` | base.html | Error | Reverse for 'domain_management_detail' not found. 'domain_management_detail' is not a valid view function or pattern name. |
| 44 | `tenants:branding_config_list` | base.html | Error | Reverse for 'branding_config_detail' not found. 'branding_config_detail' is not a valid view function or pattern name. |
| 45 | `tenants:logo_management` | base.html | Error | Reverse for 'branding_config_detail' not found. 'branding_config_detail' is not a valid view function or pattern name. |
| 46 | `tenants:subscription_overview` | base.html | Error | Invalid field name(s) given in select_related: 'plan'. Choices are: tenant, subscription_plan, user, status_ref |
| 47 | `tenants:revenue_analytics` | base.html | Error | Invalid field name(s) given in select_related: 'plan'. Choices are: tenant, subscription_plan, user, status_ref |
| 48 | `accounts:accounts_create` | base.html | Error | BaseModelForm.__init__() got an unexpected keyword argument 'current_user' |
| 49 | `accounts:accounts_kanban` | base.html | Error | Invalid field name(s) given in select_related: 'owner'. Choices are: tenant, role, organization_membership, onboarding_workflow, engagement_status, team_member, auth_token |
| 50 | `accounts:contact_list` | base.html | Error | Contact has no field named 'esg_influence' |
| 51 | `accounts:contact_create` | base.html | Error | 'account' |
| 52 | `core:system_configuration` | base.html | Error | base.html |
| 53 | `core:dynamic_choices_dashboard` | base.html | Error | core/base.html |
| 54 | `core:environment_variables` | base.html | Error | Invalid filter: 'split' |
| 55 | `core:feature_toggle_management` | base.html | Error | Invalid filter: 'selectattr' |
| 56 | `core:configuration_audit` | base.html | Error | base.html |
| 57 | `core:system_maintenance` | base.html | Error | base.html |
| 58 | `core:data_management` | base.html | Error | base.html |
| 59 | `core:backup_management` | base.html | Error | core/admin/backup_management.html |
| 60 | `core:security_dashboard` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 61 | `core:ip_whitelist_management` | base.html | Error | base.html |
| 62 | `core:security_event_monitoring` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 63 | `core:intrusion_detection` | base.html | Error | core/security/intrusion_detection.html |
| 64 | `core:secure_credential_management` | base.html | Error | core/security/secure_credential_management.html |
| 65 | `core:compliance_dashboard` | base.html | Error | core/security/compliance_dashboard.html |
| 66 | `core:data_privacy_management` | base.html | Error | core/security/data_privacy_management.html |
| 67 | `core:security_policy_management` | base.html | Error | core/security/security_policy_management.html |
| 68 | `core:vulnerability_management` | base.html | Error | core/security/vulnerability_management.html |
| 69 | `commissions:dashboard` | base.html | Error | Reverse for 'list' not found. 'list' is not a valid view function or pattern name. |
| 70 | `marketing:campaign_performance` | base.html | Error | Invalid filter: 'floatform' |
| 71 | `dashboard:data_explorer` | base.html | Error | dashboard/bi/explorer.html |
| 72 | `audit_logs:list` | base.html | No Reverse Match | Cannot resolve URL pattern: audit_logs:list |
| 73 | `audit_logs:log_list` | base.html | Error | Reverse for 'list' not found. 'list' is not a valid view function or pattern name. |
| 74 | `audit_logs:recent_actions` | base.html | Error | Cannot resolve keyword 'timestamp' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 75 | `audit_logs:critical_events` | base.html | Error | Cannot resolve keyword 'severity' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 76 | `audit_logs:state_changes` | base.html | Error | Cannot resolve keyword 'state_after' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 77 | `audit_logs:data_modifications` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 78 | `audit_logs:security_events` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 79 | `audit_logs:soc2_report` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 80 | `audit_logs:hipaa_audit` | base.html | Error | Cannot resolve keyword 'action_type' into field. Choices are: action, audit_log_created_at, audit_log_updated_at, error_message, id, ip_address, is_successful, metadata, new_values, old_values, resource_id, resource_name, resource_type, tenant, tenant_id, user, user_agent, user_id |
| 81 | `audit_logs:export_logs` | base.html | Error | Reverse for 'list' not found. 'list' is not a valid view function or pattern name. |
| 82 | `marketing:list` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:list |
| 83 | `marketing:campaign_calendar` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:campaign_calendar |
| 84 | `marketing:create` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:create |
| 85 | `marketing:performance_list` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:performance_list |
| 86 | `marketing:performance_analytics` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:performance_analytics |
| 87 | `marketing:performance_create` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:performance_create |
| 88 | `marketing:template_list` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:template_list |
| 89 | `marketing:template_create` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:template_create |
| 90 | `marketing:template_builder` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:template_builder |
| 91 | `marketing:landing_page_list` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:landing_page_list |
| 92 | `marketing:landing_page_create` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:landing_page_create |
| 93 | `marketing:landing_page_builder` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:landing_page_builder |
| 94 | `marketing:ab_test_list` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:ab_test_list |
| 95 | `marketing:ab_test_create` | base.html | No Reverse Match | Cannot resolve URL pattern: marketing:ab_test_create |
| 96 | `leads:lead_analytics` | base.html | Error | base.html |
| 97 | `leads:lead_pipeline` | base.html | Error | base.html |
| 98 | `leads:lead_list` | base.html | Error | Reverse for 'create' not found. 'create' is not a valid view function or pattern name. |
| 99 | `leads:lead_create` | base.html | Error | Tenant matching query does not exist. |
| 100 | `leads:web_to_lead_builder` | base.html | Error | base.html |
| 101 | `leads:web_to_lead_list` | base.html | Error | base.html |
| 102 | `billing:invoice_create` | base.html | Error | billing/invoice_form.html |
| 103 | `billing:plan_create` | base.html | Error | Tenant matching query does not exist. |
| 104 | `billing:proration_calculator` | base.html | Error | Invalid block tag on line 26: 'endif', expected 'empty' or 'endfor'. Did you forget to register or load this tag? |
| 105 | `billing:tenant_billing_search` | base.html | Error | Could not parse the remainder: '=="active"' from 'request.GET.status=="active"' |
| 106 | `billing:credit_adjustment` | base.html | Error | billing/credit_adjustment_management.html |
| 107 | `sales:sales_dashboard` | base.html | Error | Cannot resolve keyword 'name' into field. Choices are: ab_tests_created, access_patterns, access_patterns_reviewed, access_reviews_conducted, access_reviews_received, acquisition_cost, activity_logs, alert_configs_created, alert_notification_preferences, alert_notifications_received, alert_rules_created, alert_rules_targeted, alerts_acknowledged, alerts_created, alerts_resolved, alerts_triggered, anomaly_analysis_performed, anomaly_detections, api_tokens, apps_approved, apps_created, articlerating, articleversion, articleview, assigned_rules, assigned_tasks, audit_logs, audit_reports_generated, audit_reports_reviewed, auth_token, authored_articles, automated_lifecycle_events_executed, automation_executions, automation_rules_created, automations_created, avg_order_value, calls_initiated, calls_received, capacity_planning_created, case_assigned_rules, caseattachment, casecomment, cases, certifications, certifications_performed, commission_adjustments, commission_payments, commission_plans, commission_records, commissions, communications_received, communications_sent, completed_migrations, compliance_audits, compliance_audits_reviewed, connectors_created, correlation_groups_assigned, correlation_rules_created, created_at, created_tasks, csatdetractoralert, customer_lifetime_value, customer_since, dashboard_configs, data_preservation_created, data_restorations_completed, data_restorations_initiated, date_joined, deleted_at, dynamicchoiceauditlog, edited_articles, email, email_campaigns_created, email_integrations, email_templates_created, emails_sent, engagement_events, engagement_status, engagementevent, escalated_cases, escalation_paths_created, escalation_policies_created, exportjob, feature_dependencies_created, feature_experiments_created, feature_flags_created, feature_impact_analyses, feature_rollout_schedules, feedback_forms_created, first_name, groups, id, incidents_assigned, incidents_reported, infrastructure_alerts_acknowledged, infrastructure_alerts_assigned, infrastructure_changes_approved, infrastructure_changes_initiated, initiated_migrations, integration_audit_logs, integration_health_checks_created, is_active, is_deleted, is_staff, is_superuser, landing_pages_created, last_login, last_mfa_login, last_name, lead, lead_assigned_rules, leads, lifecycle_rules_created, lifecycle_workflow_executions, lifecycle_workflows_created, logentry, maintenance_approved, maintenance_created, maintenance_notifications, managed_accounts, marketing_email_integrations, meetings_organized, message_templates_created, mfa_devices, mfa_enabled, mfa_secret, module_provision_workflows_created, modules_activated, modules_created, modules_deactivated, modules_installed, modules_uninstalled, next_actions, nextbestaction, notification_templates_created, notifications_created, nps_responses, npsdetractoralert, onboarding_workflow, opportunities, opportunity, opportunity_assigned_rules, organization_membership, owned_campaigns, owned_cases, password, payment_methods, preservation_strategies_created, product, proposalpdf, purchase_frequency, quality_check_schedules_created, quotas, report_analytics, report_exports_created, report_templates_created, reports_created, resource_alerts_acknowledged, resource_alerts_resolved, resource_reports_generated, resources_allocated, retention_rate, role, role_id, role_permission_audits, rollout_schedules_created, sales, sales_made, salestarget, security_incidents_affected, sent_proposals, service_configs_created, subscribed_reports, subscriptions, suppression_rules_created, suspension_workflows_approved, suspension_workflows_initiated, system_notifications, systemconfiguration, systemeventlog, tasks, team_member, tenant, tenant_clones_completed, tenant_clones_initiated, tenant_id, tenant_lifecycle_events, termination_workflows_approved, termination_workflows_initiated, tickets_assigned, tickets_closed, tickets_first_responded, tickets_resolved, tickets_submitted, tokens_created, updated_at, user_permissions, username, webhooks_created, webtoleadform, workflows_created, workflows_updated |
| 108 | `sales:sale_list` | base.html | Error | 'Product' object has no attribute 'name' |
| 109 | `sales:sale_create` | base.html | Error | Cannot resolve keyword 'status' into field. Choices are: ab_tests_created, access_patterns, access_patterns_reviewed, access_reviews_conducted, access_reviews_received, acquisition_cost, activity_logs, alert_configs_created, alert_notification_preferences, alert_notifications_received, alert_rules_created, alert_rules_targeted, alerts_acknowledged, alerts_created, alerts_resolved, alerts_triggered, anomaly_analysis_performed, anomaly_detections, api_tokens, apps_approved, apps_created, articlerating, articleversion, articleview, assigned_rules, assigned_tasks, audit_logs, audit_reports_generated, audit_reports_reviewed, auth_token, authored_articles, automated_lifecycle_events_executed, automation_executions, automation_rules_created, automations_created, avg_order_value, calls_initiated, calls_received, capacity_planning_created, case_assigned_rules, caseattachment, casecomment, cases, certifications, certifications_performed, commission_adjustments, commission_payments, commission_plans, commission_records, commissions, communications_received, communications_sent, completed_migrations, compliance_audits, compliance_audits_reviewed, connectors_created, correlation_groups_assigned, correlation_rules_created, created_at, created_tasks, csatdetractoralert, customer_lifetime_value, customer_since, dashboard_configs, data_preservation_created, data_restorations_completed, data_restorations_initiated, date_joined, deleted_at, dynamicchoiceauditlog, edited_articles, email, email_campaigns_created, email_integrations, email_templates_created, emails_sent, engagement_events, engagement_status, engagementevent, escalated_cases, escalation_paths_created, escalation_policies_created, exportjob, feature_dependencies_created, feature_experiments_created, feature_flags_created, feature_impact_analyses, feature_rollout_schedules, feedback_forms_created, first_name, groups, id, incidents_assigned, incidents_reported, infrastructure_alerts_acknowledged, infrastructure_alerts_assigned, infrastructure_changes_approved, infrastructure_changes_initiated, initiated_migrations, integration_audit_logs, integration_health_checks_created, is_active, is_deleted, is_staff, is_superuser, landing_pages_created, last_login, last_mfa_login, last_name, lead, lead_assigned_rules, leads, lifecycle_rules_created, lifecycle_workflow_executions, lifecycle_workflows_created, logentry, maintenance_approved, maintenance_created, maintenance_notifications, managed_accounts, marketing_email_integrations, meetings_organized, message_templates_created, mfa_devices, mfa_enabled, mfa_secret, module_provision_workflows_created, modules_activated, modules_created, modules_deactivated, modules_installed, modules_uninstalled, next_actions, nextbestaction, notification_templates_created, notifications_created, nps_responses, npsdetractoralert, onboarding_workflow, opportunities, opportunity, opportunity_assigned_rules, organization_membership, owned_campaigns, owned_cases, password, payment_methods, preservation_strategies_created, product, proposalpdf, purchase_frequency, quality_check_schedules_created, quotas, report_analytics, report_exports_created, report_templates_created, reports_created, resource_alerts_acknowledged, resource_alerts_resolved, resource_reports_generated, resources_allocated, retention_rate, role, role_id, role_permission_audits, rollout_schedules_created, sales, sales_made, salestarget, security_incidents_affected, sent_proposals, service_configs_created, subscribed_reports, subscriptions, suppression_rules_created, suspension_workflows_approved, suspension_workflows_initiated, system_notifications, systemconfiguration, systemeventlog, tasks, team_member, tenant, tenant_clones_completed, tenant_clones_initiated, tenant_id, tenant_lifecycle_events, termination_workflows_approved, termination_workflows_initiated, tickets_assigned, tickets_closed, tickets_first_responded, tickets_resolved, tickets_submitted, tokens_created, updated_at, user_permissions, username, webhooks_created, webtoleadform, workflows_created, workflows_updated |
| 110 | `sales:product_dashboard` | base.html | Error | Cannot resolve keyword 'is_active' into field. Choices are: auto_renewal, available_from, available_to, base_price, billing_cycle, bundleitem, carbon_footprint, category, commissionrule, comparisons, competitor_mappings, currency, dependencies, esg_certifications, esg_certified, id, is_subscription, opportunity, opportunityproduct, owner, owner_id, pricing_model, pricing_tiers, product_description, product_is_active, product_name, productbundle, required_by, sales, sales_commission_rules, sku, subscription_term, sustainability_notes, tags, tco2e_saved, tenant, tenant_id, upc |
| 111 | `sales:product_list` | base.html | Error | Cannot resolve keyword 'created_at' into field. Choices are: auto_renewal, available_from, available_to, base_price, billing_cycle, bundleitem, carbon_footprint, category, commissionrule, comparisons, competitor_mappings, currency, dependencies, esg_certifications, esg_certified, id, is_subscription, opportunity, opportunityproduct, owner, owner_id, pricing_model, pricing_tiers, product_description, product_is_active, product_name, productbundle, required_by, sales, sales_commission_rules, sku, subscription_term, sustainability_notes, tags, tco2e_saved, tenant, tenant_id, upc |
| 112 | `sales:product_create` | base.html | Error | type object 'Product' has no attribute 'PRODUCT_TYPE_CHOICES' |
| 113 | `engagement:next_best_action` | base.html | Error | Cannot resolve keyword 'name' into field. Choices are: ab_tests_created, access_patterns, access_patterns_reviewed, access_reviews_conducted, access_reviews_received, acquisition_cost, activity_logs, alert_configs_created, alert_notification_preferences, alert_notifications_received, alert_rules_created, alert_rules_targeted, alerts_acknowledged, alerts_created, alerts_resolved, alerts_triggered, anomaly_analysis_performed, anomaly_detections, api_tokens, apps_approved, apps_created, articlerating, articleversion, articleview, assigned_rules, assigned_tasks, audit_logs, audit_reports_generated, audit_reports_reviewed, auth_token, authored_articles, automated_lifecycle_events_executed, automation_executions, automation_rules_created, automations_created, avg_order_value, calls_initiated, calls_received, capacity_planning_created, case_assigned_rules, caseattachment, casecomment, cases, certifications, certifications_performed, commission_adjustments, commission_payments, commission_plans, commission_records, commissions, communications_received, communications_sent, completed_migrations, compliance_audits, compliance_audits_reviewed, connectors_created, correlation_groups_assigned, correlation_rules_created, created_at, created_tasks, csatdetractoralert, customer_lifetime_value, customer_since, dashboard_configs, data_preservation_created, data_restorations_completed, data_restorations_initiated, date_joined, deleted_at, dynamicchoiceauditlog, edited_articles, email, email_campaigns_created, email_integrations, email_templates_created, emails_sent, engagement_events, engagement_status, engagementevent, escalated_cases, escalation_paths_created, escalation_policies_created, exportjob, feature_dependencies_created, feature_experiments_created, feature_flags_created, feature_impact_analyses, feature_rollout_schedules, feedback_forms_created, first_name, groups, id, incidents_assigned, incidents_reported, infrastructure_alerts_acknowledged, infrastructure_alerts_assigned, infrastructure_changes_approved, infrastructure_changes_initiated, initiated_migrations, integration_audit_logs, integration_health_checks_created, is_active, is_deleted, is_staff, is_superuser, landing_pages_created, last_login, last_mfa_login, last_name, lead, lead_assigned_rules, leads, lifecycle_rules_created, lifecycle_workflow_executions, lifecycle_workflows_created, logentry, maintenance_approved, maintenance_created, maintenance_notifications, managed_accounts, marketing_email_integrations, meetings_organized, message_templates_created, mfa_devices, mfa_enabled, mfa_secret, module_provision_workflows_created, modules_activated, modules_created, modules_deactivated, modules_installed, modules_uninstalled, next_actions, nextbestaction, notification_templates_created, notifications_created, nps_responses, npsdetractoralert, onboarding_workflow, opportunities, opportunity, opportunity_assigned_rules, organization_membership, owned_campaigns, owned_cases, password, payment_methods, preservation_strategies_created, product, proposalpdf, purchase_frequency, quality_check_schedules_created, quotas, report_analytics, report_exports_created, report_templates_created, reports_created, resource_alerts_acknowledged, resource_alerts_resolved, resource_reports_generated, resources_allocated, retention_rate, role, role_id, role_permission_audits, rollout_schedules_created, sales, sales_made, salestarget, security_incidents_affected, sent_proposals, service_configs_created, subscribed_reports, subscriptions, suppression_rules_created, suspension_workflows_approved, suspension_workflows_initiated, system_notifications, systemconfiguration, systemeventlog, tasks, team_member, tenant, tenant_clones_completed, tenant_clones_initiated, tenant_id, tenant_lifecycle_events, termination_workflows_approved, termination_workflows_initiated, tickets_assigned, tickets_closed, tickets_first_responded, tickets_resolved, tickets_submitted, tokens_created, updated_at, user_permissions, username, webhooks_created, webtoleadform, workflows_created, workflows_updated |
| 114 | `engagement:next_best_action_create` | base.html | Error | Cannot resolve keyword 'name' into field. Choices are: ab_tests_created, access_patterns, access_patterns_reviewed, access_reviews_conducted, access_reviews_received, acquisition_cost, activity_logs, alert_configs_created, alert_notification_preferences, alert_notifications_received, alert_rules_created, alert_rules_targeted, alerts_acknowledged, alerts_created, alerts_resolved, alerts_triggered, anomaly_analysis_performed, anomaly_detections, api_tokens, apps_approved, apps_created, articlerating, articleversion, articleview, assigned_rules, assigned_tasks, audit_logs, audit_reports_generated, audit_reports_reviewed, auth_token, authored_articles, automated_lifecycle_events_executed, automation_executions, automation_rules_created, automations_created, avg_order_value, calls_initiated, calls_received, capacity_planning_created, case_assigned_rules, caseattachment, casecomment, cases, certifications, certifications_performed, commission_adjustments, commission_payments, commission_plans, commission_records, commissions, communications_received, communications_sent, completed_migrations, compliance_audits, compliance_audits_reviewed, connectors_created, correlation_groups_assigned, correlation_rules_created, created_at, created_tasks, csatdetractoralert, customer_lifetime_value, customer_since, dashboard_configs, data_preservation_created, data_restorations_completed, data_restorations_initiated, date_joined, deleted_at, dynamicchoiceauditlog, edited_articles, email, email_campaigns_created, email_integrations, email_templates_created, emails_sent, engagement_events, engagement_status, engagementevent, escalated_cases, escalation_paths_created, escalation_policies_created, exportjob, feature_dependencies_created, feature_experiments_created, feature_flags_created, feature_impact_analyses, feature_rollout_schedules, feedback_forms_created, first_name, groups, id, incidents_assigned, incidents_reported, infrastructure_alerts_acknowledged, infrastructure_alerts_assigned, infrastructure_changes_approved, infrastructure_changes_initiated, initiated_migrations, integration_audit_logs, integration_health_checks_created, is_active, is_deleted, is_staff, is_superuser, landing_pages_created, last_login, last_mfa_login, last_name, lead, lead_assigned_rules, leads, lifecycle_rules_created, lifecycle_workflow_executions, lifecycle_workflows_created, logentry, maintenance_approved, maintenance_created, maintenance_notifications, managed_accounts, marketing_email_integrations, meetings_organized, message_templates_created, mfa_devices, mfa_enabled, mfa_secret, module_provision_workflows_created, modules_activated, modules_created, modules_deactivated, modules_installed, modules_uninstalled, next_actions, nextbestaction, notification_templates_created, notifications_created, nps_responses, npsdetractoralert, onboarding_workflow, opportunities, opportunity, opportunity_assigned_rules, organization_membership, owned_campaigns, owned_cases, password, payment_methods, preservation_strategies_created, product, proposalpdf, purchase_frequency, quality_check_schedules_created, quotas, report_analytics, report_exports_created, report_templates_created, reports_created, resource_alerts_acknowledged, resource_alerts_resolved, resource_reports_generated, resources_allocated, retention_rate, role, role_id, role_permission_audits, rollout_schedules_created, sales, sales_made, salestarget, security_incidents_affected, sent_proposals, service_configs_created, subscribed_reports, subscriptions, suppression_rules_created, suspension_workflows_approved, suspension_workflows_initiated, system_notifications, systemconfiguration, systemeventlog, tasks, team_member, tenant, tenant_clones_completed, tenant_clones_initiated, tenant_id, tenant_lifecycle_events, termination_workflows_approved, termination_workflows_initiated, tickets_assigned, tickets_closed, tickets_first_responded, tickets_resolved, tickets_submitted, tokens_created, updated_at, user_permissions, username, webhooks_created, webtoleadform, workflows_created, workflows_updated |
| 115 | `infrastructure:dashboard` | base.html | Error | infrastructure/resource_monitoring_dashboard.html |
| 116 | `infrastructure:tenant_usage` | base.html | Error | infrastructure/resource_usage_report_list.html, infrastructure/resourceusagereport_list.html |
| 117 | `infrastructure:api_calls` | base.html | Error | infrastructure/resource_monitoring_list.html, infrastructure/resourcemonitoring_list.html |
| 118 | `infrastructure:storage_usage` | base.html | Error | infrastructure/resource_monitoring_list.html, infrastructure/resourcemonitoring_list.html |
| 119 | `infrastructure:db_connections` | base.html | Error | infrastructure/resource_monitoring_list.html, infrastructure/resourcemonitoring_list.html |
| 120 | `infrastructure:throttled_tenants` | base.html | Error | infrastructure/resource_quota_list.html, infrastructure/resourcequota_list.html |
| 121 | `infrastructure:system_health` | base.html | Error | infrastructure/module_health_check.html |
| 122 | `infrastructure:performance_metrics` | base.html | Error | infrastructure/real_time_monitoring.html |
| 123 | `infrastructure:resource_alerts` | base.html | Error | infrastructure/resource_alert_list.html, infrastructure/resourcealert_list.html |
| 124 | `infrastructure:app_module_list` | base.html | Error | base.html |
| 125 | `infrastructure:module_dependency_list` | base.html | Error | base.html |
| 126 | `infrastructure:tenant_module_provision_list` | base.html | Error | base.html |
| 127 | `infrastructure:alert_configuration` | base.html | Error | infrastructure/alert_configuration.html |
| 128 | `tasks:create` | base.html | Error | Tenant matching query does not exist. |
| 129 | `tasks:kanban` | base.html | Error | tasks/kanban.html |
| 130 | `tasks:template_list` | base.html | Error | tasks/template_list.html, tasks/tasktemplate_list.html |
| 131 | `tasks:template_create` | base.html | Error | Unknown field(s) (default_title, default_task_type, default_priority, estimated_hours_default, default_description) specified for TaskTemplate |

---

## 🟢 Working Navigation Links

Total: 131 links working correctly

---

## 🔍 Orphaned Templates Analysis


### Accounts (16 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `account_detail` | `accounts:account_detail`, `accounts:account_detail_list` | 🔍 Review manually |
| `admin/mfa_management` | `accounts:admin_mfa_management`, `accounts:admin_mfa_management_list` | 🔍 Review manually |
| `admin/user_access_review` | `accounts:admin_user_access_review`, `accounts:admin_user_access_review_list` | 🔍 Review manually |
| `admin/user_activity` | `accounts:admin_user_activity`, `accounts:admin_user_activity_list` | 🔍 Review manually |
| `admin/user_bulk_operations` | `accounts:admin_user_bulk_operations`, `accounts:admin_user_bulk_operations_list` | 🔍 Review manually |
| `admin/user_list` | `accounts:admin_user_list`, `accounts:admin_user_list_list` | 🔍 Review manually |
| `admin/user_management_dashboard` | `accounts:admin_user_management_dashboard`, `accounts:admin_user_management_dashboard_list` | 🟢 Add to navigation |
| `admin/user_role_management` | `accounts:admin_user_role_management`, `accounts:admin_user_role_management_list` | 🔍 Review manually |
| `form` | `accounts:form`, `accounts:form_list` | 🔍 Review manually |
| `kanban` | `accounts:kanban`, `accounts:kanban_list` | 🔍 Review manually |
| `bulk_imports/map_fields` | `accounts:bulk_imports_map_fields`, `accounts:bulk_imports_map_fields_list` | 🔍 Review manually |
| `bulk_imports/preview` | `accounts:bulk_imports_preview`, `accounts:bulk_imports_preview_list` | 🟡 Keep as action/API endpoint |
| `bulk_imports/upload` | `accounts:bulk_imports_upload`, `accounts:bulk_imports_upload_list` | 🔍 Review manually |
| `contacts/account_contact_list` | `accounts:contacts_account_contact_list`, `accounts:contacts_account_contact_list_list` | 🔍 Review manually |
| `contacts/contact_detail` | `accounts:contacts_contact_detail`, `accounts:contacts_contact_detail_list` | 🔍 Review manually |
| `contacts/contact_list` | `accounts:contacts_contact_list`, `accounts:contacts_contact_list_list` | 🔍 Review manually |

### Audit_Logs (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `dashboard` | `audit_logs:dashboard`, `audit_logs:dashboard_list` | 🟢 Add to navigation |
| `log_detail` | `audit_logs:log_detail`, `audit_logs:log_detail_list` | 🔍 Review manually |

### Automation (11 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `confirm_delete` | `automation:confirm_delete`, `automation:confirm_delete_list` | 🔍 Review manually |
| `detail` | `automation:detail`, `automation:detail_list` | 🔍 Review manually |
| `form` | `automation:form`, `automation:form_list` | 🔍 Review manually |
| `forms` | `automation:forms`, `automation:forms_list` | 🔍 Review manually |
| `import` | `automation:import`, `automation:import_list` | 🔍 Review manually |
| `log_detail` | `automation:log_detail`, `automation:log_detail_list` | 🔍 Review manually |
| `rule_list` | `automation:rule_list`, `automation:rule_list_list` | 🔍 Review manually |
| `workflow_action_detail` | `automation:workflow_action_detail`, `automation:workflow_action_detail_list` | 🔍 Review manually |
| `workflow_execution_detail` | `automation:workflow_execution_detail`, `automation:workflow_execution_detail_list` | 🔍 Review manually |
| `workflow_template_detail` | `automation:workflow_template_detail`, `automation:workflow_template_detail_list` | 🔍 Review manually |
| `workflow_trigger_detail` | `automation:workflow_trigger_detail`, `automation:workflow_trigger_detail_list` | 🔍 Review manually |

### Billing (6 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `billing_history` | `billing:billing_history`, `billing:billing_history_list` | 🔍 Review manually |
| `invoice_detail` | `billing:invoice_detail`, `billing:invoice_detail_list` | 🔍 Review manually |
| `plan_detail` | `billing:plan_detail`, `billing:plan_detail_list` | 🔍 Review manually |
| `plan_edit` | `billing:plan_edit`, `billing:plan_edit_list` | 🔍 Review manually |
| `pricing_config` | `billing:pricing_config`, `billing:pricing_config_list` | 🔍 Review manually |
| `subscription_detail` | `billing:subscription_detail`, `billing:subscription_detail_list` | 🔍 Review manually |

### Cases (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `assignment_rule_list` | `cases:assignment_rule_list`, `cases:assignment_rule_list_list` | 🔍 Review manually |
| `confirm_delete` | `cases:confirm_delete`, `cases:confirm_delete_list` | 🔍 Review manually |
| `detail` | `cases:detail`, `cases:detail_list` | 🔍 Review manually |
| `form` | `cases:form`, `cases:form_list` | 🔍 Review manually |
| `knowledge_base_artical_list` | `cases:knowledge_base_artical_list`, `cases:knowledge_base_artical_list_list` | 🔍 Review manually |

### Commissions (3 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `commission_list` | `commissions:commission_list`, `commissions:commission_list_list` | 🔍 Review manually |
| `payment_detail` | `commissions:payment_detail`, `commissions:payment_detail_list` | 🔍 Review manually |
| `payment_list` | `commissions:payment_list`, `commissions:payment_list_list` | 🔍 Review manually |

### Core (31 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `admin/configuration_audit` | `core:admin_configuration_audit`, `core:admin_configuration_audit_list` | 🔍 Review manually |
| `admin/data_management` | `core:admin_data_management`, `core:admin_data_management_list` | 🔍 Review manually |
| `admin/environment_variables` | `core:admin_environment_variables`, `core:admin_environment_variables_list` | 🔍 Review manually |
| `admin/feature_toggle_management` | `core:admin_feature_toggle_management`, `core:admin_feature_toggle_management_list` | 🔍 Review manually |
| `admin/system_configuration` | `core:admin_system_configuration`, `core:admin_system_configuration_list` | 🔍 Review manually |
| `admin/system_maintenance` | `core:admin_system_maintenance`, `core:admin_system_maintenance_list` | 🔍 Review manually |
| `assignment_rule_type_list` | `core:assignment_rule_type_list`, `core:assignment_rule_type_list_list` | 🔍 Review manually |
| `base_module` | `core:base_module`, `core:base_module_list` | 🔍 Review manually |
| `clv_dashboard` | `core:clv_dashboard`, `core:clv_dashboard_list` | 🟢 Add to navigation |
| `feature_disabled` | `core:feature_disabled`, `core:feature_disabled_list` | 🔍 Review manually |
| `field_type_list` | `core:field_type_list`, `core:field_type_list_list` | 🔍 Review manually |
| `model_choice_list` | `core:model_choice_list`, `core:model_choice_list_list` | 🔍 Review manually |
| `module_choice_list` | `core:module_choice_list`, `core:module_choice_list_list` | 🔍 Review manually |
| `module_label_list` | `core:module_label_list`, `core:module_label_list_list` | 🔍 Review manually |
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
| `public/products` | `core:public_products`, `core:public_products_list` | 🔍 Review manually |
| `public/solutions` | `core:public_solutions`, `core:public_solutions_list` | 🔍 Review manually |
| `public/support` | `core:public_support`, `core:public_support_list` | 🔍 Review manually |
| `public/try` | `core:public_try`, `core:public_try_list` | 🔍 Review manually |

### Dashboard (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `bi/drill_down` | `dashboard:bi_drill_down`, `dashboard:bi_drill_down_list` | 🔍 Review manually |
| `main` | `dashboard:main`, `dashboard:main_list` | 🔍 Review manually |
| `wizard/step1` | `dashboard:wizard_step1`, `dashboard:wizard_step1_list` | 🔍 Review manually |
| `wizard/step2` | `dashboard:wizard_step2`, `dashboard:wizard_step2_list` | 🔍 Review manually |
| `wizard/step3` | `dashboard:wizard_step3`, `dashboard:wizard_step3_list` | 🔍 Review manually |

### Engagement (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `event_detail` | `engagement:event_detail`, `engagement:event_detail_list` | 🔍 Review manually |
| `next_best_action_detail` | `engagement:next_best_action_detail`, `engagement:next_best_action_detail_list` | 🔍 Review manually |

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

### Infrastructure (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `resource_allocation_list` | `infrastructure:resource_allocation_list`, `infrastructure:resource_allocation_list_list` | 🔍 Review manually |
| `tenant_usage_list` | `infrastructure:tenant_usage_list`, `infrastructure:tenant_usage_list_list` | 🔍 Review manually |

### Leads (11 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `action_type_list` | `leads:action_type_list`, `leads:action_type_list_list` | 🔍 Review manually |
| `analytics` | `leads:analytics`, `leads:analytics_list` | 🟢 Add to navigation |
| `assignment_rule_list` | `leads:assignment_rule_list`, `leads:assignment_rule_list_list` | 🔍 Review manually |
| `behavioral_scoring_rule_list` | `leads:behavioral_scoring_rule_list`, `leads:behavioral_scoring_rule_list_list` | 🔍 Review manually |
| `campaign_metrics` | `leads:campaign_metrics`, `leads:campaign_metrics_list` | 🔍 Review manually |
| `channel_metrics` | `leads:channel_metrics`, `leads:channel_metrics_list` | 🔍 Review manually |
| `demographic_scoring_rule_list` | `leads:demographic_scoring_rule_list`, `leads:demographic_scoring_rule_list_list` | 🔍 Review manually |
| `lead_detail` | `leads:lead_detail`, `leads:lead_detail_list` | 🔍 Review manually |
| `marketingchannel_list` | `leads:marketingchannel_list`, `leads:marketingchannel_list_list` | 🔍 Review manually |
| `operator_type_list` | `leads:operator_type_list`, `leads:operator_type_list_list` | 🔍 Review manually |
| `pipeline_kanban` | `leads:pipeline_kanban`, `leads:pipeline_kanban_list` | 🔍 Review manually |

### Learn (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `delete` | `learn:delete`, `learn:delete_list` | 🔍 Review manually |
| `detail` | `learn:detail`, `learn:detail_list` | 🔍 Review manually |
| `export_pdf` | `learn:export_pdf`, `learn:export_pdf_list` | 🟡 Keep as action/API endpoint |
| `form` | `learn:form`, `learn:form_list` | 🔍 Review manually |
| `search_results` | `learn:search_results`, `learn:search_results_list` | 🔍 Review manually |

### Marketing (16 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `cac_analytics` | `marketing:cac_analytics`, `marketing:cac_analytics_list` | 🟢 Add to navigation |
| `calendar` | `marketing:calendar`, `marketing:calendar_list` | 🔍 Review manually |
| `campaign_performance_analytics` | `marketing:campaign_performance_analytics`, `marketing:campaign_performance_analytics_list` | 🟢 Add to navigation |
| `campaign_performance_dashboard` | `marketing:campaign_performance_dashboard`, `marketing:campaign_performance_dashboard_list` | 🟢 Add to navigation |
| `campaign_performance_detail` | `marketing:campaign_performance_detail`, `marketing:campaign_performance_detail_list` | 🔍 Review manually |
| `campaign_performance_list` | `marketing:campaign_performance_list`, `marketing:campaign_performance_list_list` | 🔍 Review manually |
| `campaign_recipient_list` | `marketing:campaign_recipient_list`, `marketing:campaign_recipient_list_list` | 🔍 Review manually |
| `drip_campaign_detail` | `marketing:drip_campaign_detail`, `marketing:drip_campaign_detail_list` | 🔍 Review manually |
| `drip_campaign_list` | `marketing:drip_campaign_list`, `marketing:drip_campaign_list_list` | 🔍 Review manually |
| `email_integration_list` | `marketing:email_integration_list`, `marketing:email_integration_list_list` | 🔍 Review manually |
| `email_template_editor` | `marketing:email_template_editor`, `marketing:email_template_editor_list` | 🟢 Add to navigation |
| `email_template_list` | `marketing:email_template_list`, `marketing:email_template_list_list` | 🔍 Review manually |
| `email_template_preview` | `marketing:email_template_preview`, `marketing:email_template_preview_list` | 🟡 Keep as action/API endpoint |
| `landing_page_block_list` | `marketing:landing_page_block_list`, `marketing:landing_page_block_list_list` | 🔍 Review manually |
| `marketing_campaign_detail` | `marketing:marketing_campaign_detail`, `marketing:marketing_campaign_detail_list` | 🔍 Review manually |
| `marketing_campaign_list` | `marketing:marketing_campaign_list`, `marketing:marketing_campaign_list_list` | 🔍 Review manually |

### Nps (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `nps_ab_test` | `nps:nps_ab_test`, `nps:nps_ab_test_list` | 🔍 Review manually |
| `nps_trend_chart` | `nps:nps_trend_chart`, `nps:nps_trend_chart_list` | 🔍 Review manually |

### Opportunities (8 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `details` | `opportunities:details`, `opportunities:details_list` | 🔍 Review manually |
| `forecast_dashboard` | `opportunities:forecast_dashboard`, `opportunities:forecast_dashboard_list` | 🟢 Add to navigation |
| `form` | `opportunities:form`, `opportunities:form_list` | 🔍 Review manually |
| `kanban` | `opportunities:kanban`, `opportunities:kanban_list` | 🔍 Review manually |
| `opportunity_stage_list` | `opportunities:opportunity_stage_list`, `opportunities:opportunity_stage_list_list` | 🔍 Review manually |
| `pipeline_kanban` | `opportunities:pipeline_kanban`, `opportunities:pipeline_kanban_list` | 🔍 Review manually |
| `pipeline_type_list` | `opportunities:pipeline_type_list`, `opportunities:pipeline_type_list_list` | 🔍 Review manually |
| `win_loss_analysis` | `opportunities:win_loss_analysis`, `opportunities:win_loss_analysis_list` | 🔍 Review manually |

### Products (2 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `details` | `products:details`, `products:details_list` | 🔍 Review manually |
| `form` | `products:form`, `products:form_list` | 🔍 Review manually |

### Proposals (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `confirm_delete` | `proposals:confirm_delete`, `proposals:confirm_delete_list` | 🔍 Review manually |
| `detail` | `proposals:detail`, `proposals:detail_list` | 🔍 Review manually |
| `form` | `proposals:form`, `proposals:form_list` | 🔍 Review manually |
| `proposal_pdf` | `proposals:proposal_pdf`, `proposals:proposal_pdf_list` | 🟡 Keep as action/API endpoint |
| `send_email` | `proposals:send_email`, `proposals:send_email_list` | 🔍 Review manually |

### Reports (4 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `detail` | `reports:detail`, `reports:detail_list` | 🔍 Review manually |
| `export_email` | `reports:export_email`, `reports:export_email_list` | 🟡 Keep as action/API endpoint |
| `report_list` | `reports:report_list`, `reports:report_list_list` | 🟢 Add to navigation |
| `widget` | `reports:widget`, `reports:widget_list` | 🔍 Review manually |

### Sales (7 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `product/product_dashboard` | `sales:product_product_dashboard`, `sales:product_product_dashboard_list` | 🟢 Add to navigation |
| `product/product_list` | `sales:product_product_list`, `sales:product_product_list_list` | 🔍 Review manually |
| `sales_detail` | `sales:sales_detail`, `sales:sales_detail_list` | 🔍 Review manually |
| `sales_list` | `sales:sales_list`, `sales:sales_list_list` | 🔍 Review manually |
| `territory_assignment_optimization_dashboard` | `sales:territory_assignment_optimization_dashboard`, `sales:territory_assignment_optimization_dashboard_list` | 🟢 Add to navigation |
| `territory_comparison_tool` | `sales:territory_comparison_tool`, `sales:territory_comparison_tool_list` | 🔍 Review manually |
| `territory_performance_dashboard` | `sales:territory_performance_dashboard`, `sales:territory_performance_dashboard_list` | 🟢 Add to navigation |

### Settings_App (5 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `automation_rules` | `settings_app:automation_rules`, `settings_app:automation_rules_list` | 🔍 Review manually |
| `confirm_delete` | `settings_app:confirm_delete`, `settings_app:confirm_delete_list` | 🔍 Review manually |
| `crm_settings_list` | `settings_app:crm_settings_list`, `settings_app:crm_settings_list_list` | 🔍 Review manually |
| `score_decay_config` | `settings_app:score_decay_config`, `settings_app:score_decay_config_list` | 🔍 Review manually |
| `welcome_email` | `settings_app:welcome_email`, `settings_app:welcome_email_list` | 🔍 Review manually |

### Tasks (4 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `task_detail` | `tasks:task_detail`, `tasks:task_detail_list` | 🔍 Review manually |
| `task_kanban` | `tasks:task_kanban`, `tasks:task_kanban_list` | 🔍 Review manually |
| `task_list` | `tasks:task_list`, `tasks:task_list_list` | 🔍 Review manually |
| `task_template_list` | `tasks:task_template_list`, `tasks:task_template_list_list` | 🔍 Review manually |

### Tenants (16 orphans)

| Template | Possible URL Names | Recommendation |
|----------|-------------------|----------------|
| `archive_confirm` | `tenants:archive_confirm`, `tenants:archive_confirm_list` | 🔍 Review manually |
| `automated_lifecycle_rules` | `tenants:automated_lifecycle_rules`, `tenants:automated_lifecycle_rules_list` | 🔍 Review manually |
| `create_automated_rule` | `tenants:create_automated_rule`, `tenants:create_automated_rule_list` | 🔍 Review manually |
| `data_preservation` | `tenants:data_preservation`, `tenants:data_preservation_list` | 🔍 Review manually |
| `data_restoration` | `tenants:data_restoration`, `tenants:data_restoration_list` | 🔍 Review manually |
| `delete_confirm` | `tenants:delete_confirm`, `tenants:delete_confirm_list` | 🔍 Review manually |
| `initiate_restoration` | `tenants:initiate_restoration`, `tenants:initiate_restoration_list` | 🔍 Review manually |
| `lifecycle_dashboard` | `tenants:lifecycle_dashboard`, `tenants:lifecycle_dashboard_list` | 🟢 Add to navigation |
| `lifecycle_event_log` | `tenants:lifecycle_event_log`, `tenants:lifecycle_event_log_list` | 🔍 Review manually |
| `lifecycle_workflows` | `tenants:lifecycle_workflows`, `tenants:lifecycle_workflows_list` | 🔍 Review manually |
| `reactivate_confirm` | `tenants:reactivate_confirm`, `tenants:reactivate_confirm_list` | 🔍 Review manually |
| `signup` | `tenants:signup`, `tenants:signup_list` | 🔍 Review manually |
| `status_management` | `tenants:status_management`, `tenants:status_management_list` | 🔍 Review manually |
| `suspend_confirm` | `tenants:suspend_confirm`, `tenants:suspend_confirm_list` | 🔍 Review manually |
| `suspension_workflow` | `tenants:suspension_workflow`, `tenants:suspension_workflow_list` | 🔍 Review manually |
| `termination_workflow` | `tenants:termination_workflow`, `tenants:termination_workflow_list` | 🔍 Review manually |

---

## 📋 Recommendations

### Priority 1: Fix Broken Links

1. **accounts:member_list**: No object permission policy registered for <class 'accounts.models.OrganizationMember'>. Register it in core.object_permissions.OBJECT_POLICIES
1. **accounts:member_create**: accounts/member_form.html
1. **accounts:role_list**: No object permission policy registered for <class 'accounts.models.TeamRole'>. Register it in core.object_permissions.OBJECT_POLICIES
1. **accounts:territory_list**: No object permission policy registered for <class 'accounts.models.Territory'>. Register it in core.object_permissions.OBJECT_POLICIES
1. **accounts:territory_create**: 'crispy_forms_tags' is not a registered tag library. Must be one of:
account_filters
admin_list
admin_modify
admin_urls
auth_extras
billing_tags
cache
core_extras
filters_extras
humanize
i18n
l10n
log
math
number_filters
rest_framework
stage_filters
static
tz
   - ... and 126 more

### Priority 2: Add High-Value Orphans to Navigation

1. **accounts**: `admin/user_management_dashboard` - Likely a valuable feature
1. **audit_logs**: `dashboard` - Likely a valuable feature
1. **core**: `clv_dashboard` - Likely a valuable feature
1. **core**: `security/security_dashboard` - Likely a valuable feature
1. **global_alerts**: `alert_analytics` - Likely a valuable feature
1. **leads**: `analytics` - Likely a valuable feature
1. **marketing**: `cac_analytics` - Likely a valuable feature
1. **marketing**: `campaign_performance_analytics` - Likely a valuable feature
1. **marketing**: `campaign_performance_dashboard` - Likely a valuable feature
1. **opportunities**: `forecast_dashboard` - Likely a valuable feature

### Priority 3: Clean Up

- Review and remove deprecated templates
- Consolidate duplicate templates
- Document intentionally orphaned templates

---

*End of Report*

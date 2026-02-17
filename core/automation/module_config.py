"""
Module configuration for automation triggers and actions.
Defines available triggers and actions for each app in the system.
"""

MODULE_CONFIG = {
    'leads': {
        'label': 'Leads',
        'triggers': [
            {'id': 'lead_created', 'label': 'Lead Created'},
            {'id': 'lead_qualified', 'label': 'Lead Qualified'},
            {'id': 'lead_contacted', 'label': 'Lead Contacted'},
            {'id': 'lead_converted', 'label': 'Lead Converted to Account'},
        ],
        'actions': [
            {'id': 'update_lead_status', 'label': 'Update Lead Status'},
            {'id': 'update_lead_score', 'label': 'Update Lead Score'},
            {'id': 'assign_lead_owner', 'label': 'Assign Lead Owner'},
        ]
    },
    'opportunities': {
        'label': 'Opportunities',
        'triggers': [
            {'id': 'created', 'label': 'Opportunity Created'},
            {'id': 'won', 'label': 'Opportunity Won'},
            {'id': 'lost', 'label': 'Opportunity Lost'},
            {'id': 'stage_changed', 'label': 'Stage Changed'},
            {'id': 'probability_changed', 'label': 'Probability Changed'},
        ],
        'actions': [
            {'id': 'update_stage', 'label': 'Update Stage'},
            {'id': 'update_probability', 'label': 'Update Probability'},
            {'id': 'assign_owner', 'label': 'Assign Owner'},
        ]
    },
    'cases': {
        'label': 'Cases',
        'triggers': [
            {'id': 'created', 'label': 'Case Created'},
            {'id': 'escalated', 'label': 'Case Escalated'},
            {'id': 'resolved', 'label': 'Case Resolved'},
            {'id': 'reopened', 'label': 'Case Reopened'},
            {'id': 'sla_breach', 'label': 'SLA Breach'},
        ],
        'actions': [
            {'id': 'create_case', 'label': 'Create Case'},
            {'id': 'update_priority', 'label': 'Update Priority'},
            {'id': 'escalate_case', 'label': 'Escalate Case'},
            {'id': 'assign_case', 'label': 'Assign Case'},
        ]
    },
    'knowledge_base': {
        'label': 'Knowledge Base',
        'triggers': [
            {'id': 'article_created', 'label': 'Article Created'},
            {'id': 'article_published', 'label': 'Article Published'},
            {'id': 'article_updated', 'label': 'Article Updated'},
        ],
        'actions': [
            {'id': 'publish_article', 'label': 'Publish Article'},
            {'id': 'archive_article', 'label': 'Archive Article'},
        ]
    },
    'nps': {
        'label': 'NPS',
        'triggers': [
            {'id': 'detractor_submitted', 'label': 'Detractor Response (0-6)'},
            {'id': 'passive_submitted', 'label': 'Passive Response (7-8)'},
            {'id': 'promoter_submitted', 'label': 'Promoter Response (9-10)'},
        ],
        'actions': [
            {'id': 'tag_response', 'label': 'Tag NPS Response'},
        ]
    },
    'accounts': {
        'label': 'Accounts',
        'triggers': [
            {'id': 'created', 'label': 'Account Created'},
            {'id': 'health_low', 'label': 'Health Score Low'},
            {'id': 'health_high', 'label': 'Health Score High'},
            {'id': 'renewal_due', 'label': 'Renewal Due Soon'},
            {'id': 'churn_risk', 'label': 'Churn Risk Detected'},
        ],
        'actions': [
            {'id': 'update_health_score', 'label': 'Update Health Score'},
            {'id': 'update_tier', 'label': 'Update Account Tier'},
            {'id': 'assign_csm', 'label': 'Assign Customer Success Manager'},
        ]
    },
    'tasks': {
        'label': 'Tasks',
        'triggers': [
            {'id': 'created', 'label': 'Task Created'},
            {'id': 'completed', 'label': 'Task Completed'},
            {'id': 'overdue', 'label': 'Task Overdue'},
            {'id': 'due_soon', 'label': 'Task Due Soon'},
        ],
        'actions': [
            {'id': 'create_task', 'label': 'Create Task'},
            {'id': 'update_status', 'label': 'Update Task Status'},
            {'id': 'reassign_task', 'label': 'Reassign Task'},
        ]
    },
    'engagement': {
        'label': 'Engagement',
        'triggers': [
            {'id': 'milestone', 'label': 'Engagement Milestone Reached'},
            {'id': 'event_attended', 'label': 'Event Attended'},
            {'id': 'webinar_registered', 'label': 'Webinar Registered'},
            {'id': 'content_downloaded', 'label': 'Content Downloaded'},
        ],
        'actions': [
            {'id': 'log_engagement', 'label': 'Log Engagement Activity'},
            {'id': 'update_score', 'label': 'Update Engagement Score'},
        ]
    },
    'communication': {
        'label': 'Communication',
        'triggers': [
            {'id': 'email_sent', 'label': 'Email Sent'},
            {'id': 'email_opened', 'label': 'Email Opened'},
            {'id': 'email_clicked', 'label': 'Email Link Clicked'},
            {'id': 'sms_sent', 'label': 'SMS Sent'},
        ],
        'actions': [
            {'id': 'send_email', 'label': 'Send Email'},
            {'id': 'send_sms', 'label': 'Send SMS'},
        ]
    },
    'marketing': {
        'label': 'Marketing',
        'triggers': [
            {'id': 'campaign_completed', 'label': 'Campaign Completed'},
            {'id': 'form_submitted', 'label': 'Form Submitted'},
            {'id': 'unsubscribed', 'label': 'Contact Unsubscribed'},
        ],
        'actions': [
            {'id': 'add_to_campaign', 'label': 'Add to Campaign'},
            {'id': 'remove_from_campaign', 'label': 'Remove from Campaign'},
            {'id': 'update_tags', 'label': 'Update Marketing Tags'},
        ]
    },
    'sales': {
        'label': 'Sales',
        'triggers': [
            {'id': 'quote_sent', 'label': 'Quote Sent'},
            {'id': 'quote_accepted', 'label': 'Quote Accepted'},
            {'id': 'deal_closed', 'label': 'Deal Closed'},
        ],
        'actions': [
            {'id': 'generate_quote', 'label': 'Generate Quote'},
            {'id': 'update_forecast', 'label': 'Update Sales Forecast'},
        ]
    },
    'products': {
        'label': 'Products',
        'triggers': [
            {'id': 'product_purchased', 'label': 'Product Purchased'},
            {'id': 'license_expiring', 'label': 'License Expiring'},
        ],
        'actions': [
            {'id': 'update_product_interest', 'label': 'Update Product Interest'},
        ]
    },
    'proposals': {
        'label': 'Proposals',
        'triggers': [
            {'id': 'created', 'label': 'Proposal Created'},
            {'id': 'accepted', 'label': 'Proposal Accepted'},
            {'id': 'rejected', 'label': 'Proposal Rejected'},
        ],
        'actions': [
            {'id': 'send_proposal', 'label': 'Send Proposal'},
        ]
    },
    'commissions': {
        'label': 'Commissions',
        'triggers': [
            {'id': 'commission_earned', 'label': 'Commission Earned'},
            {'id': 'threshold_reached', 'label': 'Commission Threshold Reached'},
        ],
        'actions': [
            {'id': 'calculate_commission', 'label': 'Calculate Commission'},
        ]
    },
}

# Common actions available across all modules
COMMON_ACTIONS = [
    {'id': 'send_email', 'label': 'Send Email', 'category': 'communication'},
    {'id': 'send_sms', 'label': 'Send SMS', 'category': 'communication'},
    {'id': 'create_task', 'label': 'Create Task', 'category': 'tasks'},
    {'id': 'create_case', 'label': 'Create Case', 'category': 'cases'},
    {'id': 'send_webhook', 'label': 'Call Webhook', 'category': 'integrations'},
    {'id': 'send_slack_message', 'label': 'Send Slack Message', 'category': 'integrations'},
    {'id': 'update_field', 'label': 'Update Field', 'category': 'general'},
    {'id': 'run_function', 'label': 'Run Custom Function', 'category': 'advanced'},
]


def get_all_triggers():
    """Get all triggers across all modules."""
    triggers = []
    for module_key, module_data in MODULE_CONFIG.items():
        for trigger in module_data.get('triggers', []):
            triggers.append({
                'value': f"{module_key}.{trigger['id']}",
                'label': f"{module_data['label']}: {trigger['label']}",
                'module': module_key
            })
    return triggers


def get_all_actions():
    """Get all actions including module-specific and common actions."""
    actions = []
    
    # Add module-specific actions
    for module_key, module_data in MODULE_CONFIG.items():
        for action in module_data.get('actions', []):
            actions.append({
                'value': f"{module_key}.{action['id']}",
                'label': f"{module_data['label']}: {action['label']}",
                'module': module_key
            })
    
    # Add common actions
    for action in COMMON_ACTIONS:
        actions.append({
            'value': action['id'],
            'label': action['label'],
            'category': action.get('category', 'general')
        })
    
    return actions

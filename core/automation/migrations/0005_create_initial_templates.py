from django.db import migrations

def create_initial_templates(apps, schema_editor):
    WorkflowTemplate = apps.get_model('automation', 'WorkflowTemplate')
    
    templates = [
        {
            "name": "Auto-qualify leads",
            "description": "Automatically qualify leads with a score greater than 50.",
            "trigger_type": "lead.created",
            "builder_data": {
                "drawflow": {
                    "Home": {
                        "data": {
                            "1": {
                                "id": 1,
                                "name": "trigger",
                                "data": {"event_type": "lead.created"},
                                "class": "trigger",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {},
                                "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}},
                                "pos_x": 100,
                                "pos_y": 100
                            },
                            "2": {
                                "id": 2,
                                "name": "condition",
                                "data": {
                                    "field_path": "score",
                                    "operator": "gt",
                                    "value": "50"
                                },
                                "class": "condition",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}},
                                "outputs": {
                                    "output_1": {"connections": [{"node": "3", "output": "input_1"}]},
                                    "output_2": {"connections": []}
                                },
                                "pos_x": 400,
                                "pos_y": 100
                            },
                            "3": {
                                "id": 3,
                                "name": "update_field",
                                "data": {
                                    "model": "leads.Lead",
                                    "field_name": "status",
                                    "new_value": "qualified"
                                },
                                "class": "action",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "2", "input": "output_1"}]}},
                                "outputs": {},
                                "pos_x": 700,
                                "pos_y": 100
                            }
                        }
                    }
                }
            }
        },
        {
            "name": "Escalate overdue cases",
            "description": "Set priority to high and notify manager when SLA is breached.",
            "trigger_type": "case.sla_breached",
            "builder_data": {
                "drawflow": {
                    "Home": {
                        "data": {
                            "1": {
                                "id": 1,
                                "name": "trigger",
                                "data": {"event_type": "case.sla_breached"},
                                "class": "trigger",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {},
                                "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}},
                                "pos_x": 100,
                                "pos_y": 100
                            },
                            "2": {
                                "id": 2,
                                "name": "update_field",
                                "data": {
                                    "model": "cases.Case",
                                    "field_name": "priority",
                                    "new_value": "high"
                                },
                                "class": "action",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}},
                                "outputs": {"output_1": {"connections": [{"node": "3", "output": "input_1"}]}},
                                "pos_x": 400,
                                "pos_y": 100
                            },
                            "3": {
                                "id": 3,
                                "name": "send_email",
                                "data": {
                                    "to": "manager@example.com",
                                    "subject": "Case Escalation",
                                    "body": "A case has breached SLA and has been escalated."
                                },
                                "class": "action",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "2", "input": "output_1"}]}},
                                "outputs": {},
                                "pos_x": 700,
                                "pos_y": 100
                            }
                        }
                    }
                }
            }
        },
        {
            "name": "Send welcome email",
            "description": "Send a welcome email when a new account is created.",
            "trigger_type": "account.created",
            "builder_data": {
                "drawflow": {
                    "Home": {
                        "data": {
                            "1": {
                                "id": 1,
                                "name": "trigger",
                                "data": {"event_type": "account.created"},
                                "class": "trigger",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {},
                                "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}},
                                "pos_x": 100,
                                "pos_y": 100
                            },
                            "2": {
                                "id": 2,
                                "name": "send_email",
                                "data": {
                                    "to": "customer@example.com",
                                    "subject": "Welcome to SalesCompass!",
                                    "body": "We are excited to have you on board."
                                },
                                "class": "action",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}},
                                "outputs": {},
                                "pos_x": 400,
                                "pos_y": 100
                            }
                        }
                    }
                }
            }
        },
        {
            "name": "Create follow-up task",
            "description": "Create a task to follow up when an opportunity enters negotiation.",
            "trigger_type": "opportunity.stage_changed",
            "builder_data": {
                "drawflow": {
                    "Home": {
                        "data": {
                            "1": {
                                "id": 1,
                                "name": "trigger",
                                "data": {"event_type": "opportunity.stage_changed"},
                                "class": "trigger",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {},
                                "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}},
                                "pos_x": 100,
                                "pos_y": 100
                            },
                            "2": {
                                "id": 2,
                                "name": "condition",
                                "data": {
                                    "field_path": "stage",
                                    "operator": "eq",
                                    "value": "negotiation"
                                },
                                "class": "condition",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}},
                                "outputs": {
                                    "output_1": {"connections": [{"node": "3", "output": "input_1"}]},
                                    "output_2": {"connections": []}
                                },
                                "pos_x": 400,
                                "pos_y": 100
                            },
                            "3": {
                                "id": 3,
                                "name": "create_task",
                                "data": {
                                    "title": "Follow up on negotiation",
                                    "description": "Ensure all terms are clear.",
                                    "assigned_to_id": "1"
                                },
                                "class": "action",
                                "html": "...",
                                "typenode": "vue",
                                "inputs": {"input_1": {"connections": [{"node": "2", "input": "output_1"}]}},
                                "outputs": {},
                                "pos_x": 700,
                                "pos_y": 100
                            }
                        }
                    }
                }
            }
        }
    ]

    for template_data in templates:
        WorkflowTemplate.objects.create(**template_data)

class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0004_workflowtemplate'),
    ]

    operations = [
        migrations.RunPython(create_initial_templates),
    ]

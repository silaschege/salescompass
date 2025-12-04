from django.db import migrations

def create_default_stages(apps, schema_editor):
    OpportunityStage = apps.get_model('opportunities', 'OpportunityStage')
    stages = [
        {'name': 'Prospecting', 'order': 10, 'probability': 10.0},
        {'name': 'Qualification', 'order': 20, 'probability': 20.0},
        {'name': 'Proposal', 'order': 30, 'probability': 50.0},
        {'name': 'Negotiation', 'order': 40, 'probability': 80.0},
        {'name': 'Closed Won', 'order': 50, 'probability': 100.0, 'is_won': True},
        {'name': 'Closed Lost', 'order': 60, 'probability': 0.0, 'is_lost': True},
    ]
    for stage_data in stages:
        OpportunityStage.objects.create(**stage_data)

class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0002_opportunitystage_alter_opportunity_stage'),
    ]

    operations = [
        migrations.RunPython(create_default_stages),
    ]

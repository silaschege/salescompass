import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'salescompass.settings'
django.setup()

from django.db import connection
cursor = connection.cursor()

# Check what migrations are already applied
cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('billing', 'invoicing', 'projects', 'settings_app') ORDER BY app, name")
print("Current migration records:")
for row in cursor.fetchall():
    print(f"  {row[0]}.{row[1]}")

# Fake-apply projects 0003 since the DB is already correct
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, datetime('now'))",
    ['projects', '0003_alter_projectmilestone_invoice']
)
print("\nInserted projects.0003_alter_projectmilestone_invoice")

# Verify
cursor.execute("SELECT app, name FROM django_migrations WHERE app='projects' ORDER BY name")
print("\nProjects migration records after insert:")
for row in cursor.fetchall():
    print(f"  {row[0]}.{row[1]}")

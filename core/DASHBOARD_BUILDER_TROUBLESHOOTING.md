## Dashboard Builder - Troubleshooting Guide

### Issues Fixed:

1. **Function Scoping Issue**: Moved `addWidgetToRow()` function to be defined before it's called
2. **Event Listener**: Added `e.preventDefault()` to prevent default button behavior
3. **Variable Naming**: Changed `btn` to `btnEl` in loop to avoid confusion

### Testing the Dashboard Builder

**Step 1: Access the Dashboard Builder**
- Navigate to: `http://localhost:8000/dashboard/builder/`
- Login as superuser if required

**Step 2: Test Add Row**
- Click the "Add Row" button at the bottom
- A new empty row should appear in the canvas

**Step 3: Test Drag-and-Drop**
- Drag a widget from the sidebar
- Drop it into a row
- Widget should appear in the row

**Step 4: Test Click-to-Add**
- Click the ➕ icon on any widget
- A modal should open showing available rows
- Select a row or click "Add to New Row"
- Widget should be added to the selected row

**Step 5: Test Module Filter**
- Use the dropdown at the top of widgets sidebar
- Select a module (e.g., "Leads")
- Only widgets in that category should be visible

### Common Issues:

**Problem: Plus icons not visible**
- **Solution**: Make sure you have DashboardWidget objects in your database with the category field set

**Problem: Modal doesn't open**
- **Check**: Browser console (F12) for JavaScript errors
- **Verify**: Bootstrap is loaded correctly

**Problem: Drag-and-drop doesn't work**
- **Check**: Widgets have `draggable="true"` attribute
- **Verify**: JavaScript loaded without errors

### Quick Fix Commands:

```bash
# Ensure migrations are applied
python manage.py migrate dashboard

# Create sample widgets (in Django shell)
python manage.py shell
```

Then in shell:
```python
from dashboard.models import DashboardWidget

# Create sample widgets if none exist
DashboardWidget.objects.get_or_create(
    widget_type='leads',
    defaults={
        'name': 'Lead Metrics',
        'description': 'Track lead statistics',
        'category': 'leads',
        'template_path': 'dashboard/widgets/leads.html',
        'default_span': 6
    }
)

DashboardWidget.objects.get_or_create(
    widget_type='revenue',
    defaults={
        'name': 'Revenue Chart',
        'description': 'View revenue trends',
        'category': 'revenue',
        'template_path': 'dashboard/widgets/revenue.html',
        'default_span': 6
    }
)
```

### Browser Console Debugging:

Open browser console (F12) and check for:
- ✅ No red JavaScript errors
- ✅ Bootstrap loaded: `typeof bootstrap !== 'undefined'`
- ✅ Modal initialized: Check for modal-related errors

If you see errors, please share them for further troubleshooting.

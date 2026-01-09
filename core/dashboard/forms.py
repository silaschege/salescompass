from django import forms
from .models import DashboardWidget, WidgetType, WidgetCategory
from tenants.models import Tenant as TenantModel

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        fields = ['widget_type_ref', 'widget_name', 'widget_description', 'category_ref', 'template_path', 'report', 'widget_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['widget_type_ref'].queryset = WidgetType.objects.filter(tenant_id=self.tenant.id)
            self.fields['category_ref'].queryset = WidgetCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['widget_type_ref'].queryset = WidgetType.objects.none()
            self.fields['category_ref'].queryset = WidgetCategory.objects.none()


class WidgetTypeForm(forms.ModelForm):
    class Meta:
        model = WidgetType
        fields = ['widget_name', 'label', 'order', 'widget_type_is_active', 'is_system']
    
    def __init__(self, *args, **kwargs):
        # Pop the user argument if it exists, but we don't actually need to use it in this form
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class WidgetCategoryForm(forms.ModelForm):
    class Meta:
        model = WidgetCategory
        fields = ['category_name', 'label', 'order', 'widget_category_is_active', 'is_system']
    
    def __init__(self, *args, **kwargs):
        # Pop the user argument if it exists, but we don't actually need to use it in this form
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
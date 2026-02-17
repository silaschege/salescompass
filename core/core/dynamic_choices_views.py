from django.db import models
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from core.models import (
    SystemConfigType, SystemConfigCategory, SystemEventType, SystemEventSeverity,
    HealthCheckType, HealthCheckStatus, MaintenanceStatus, MaintenanceType,
    PerformanceMetricType, PerformanceEnvironment, NotificationType, NotificationPriority
) 
# Dynamic Choices Dashboard
class DynamicChoicesDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dynamic_choices_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System Config
        context['system_config_types_count'] = SystemConfigType.objects.count()
        context['system_config_categories_count'] = SystemConfigCategory.objects.count()
        
        # System Event
        context['system_event_types_count'] = SystemEventType.objects.count()
        context['system_event_severities_count'] = SystemEventSeverity.objects.count()
        
        # Health Check
        context['health_check_types_count'] = HealthCheckType.objects.count()
        context['health_check_statuses_count'] = HealthCheckStatus.objects.count()
        
        # Maintenance
        context['maintenance_statuses_count'] = MaintenanceStatus.objects.count()
        context['maintenance_types_count'] = MaintenanceType.objects.count()
        
        # Performance
        context['performance_metric_types_count'] = PerformanceMetricType.objects.count()
        context['performance_environments_count'] = PerformanceEnvironment.objects.count()
        
        # Notification
        context['notification_types_count'] = NotificationType.objects.count()
        context['notification_priorities_count'] = NotificationPriority.objects.count()
        
        return context


# System Config Type Views
class SystemConfigTypeListView(LoginRequiredMixin, ListView):
    model = SystemConfigType
    template_name = 'core/system_config_type_list.html'
    context_object_name = 'types'

class SystemConfigTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SystemConfigType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_config_type_form.html'
    success_message = "System Config Type created successfully."
    success_url = reverse_lazy('core:system_config_type_list')

class SystemConfigTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SystemConfigType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_config_type_form.html'
    success_message = "System Config Type updated successfully."
    success_url = reverse_lazy('core:system_config_type_list')

class SystemConfigTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = SystemConfigType
    template_name = 'core/system_config_type_confirm_delete.html'
    success_url = reverse_lazy('core:system_config_type_list')


# System Config Category Views
class SystemConfigCategoryListView(LoginRequiredMixin, ListView):
    model = SystemConfigCategory
    template_name = 'core/system_config_category_list.html'
    context_object_name = 'categories'

class SystemConfigCategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SystemConfigCategory
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_config_category_form.html'
    success_message = "System Config Category created successfully."
    success_url = reverse_lazy('core:system_config_category_list')

class SystemConfigCategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SystemConfigCategory
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_config_category_form.html'
    success_message = "System Config Category updated successfully."
    success_url = reverse_lazy('core:system_config_category_list')

class SystemConfigCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = SystemConfigCategory
    template_name = 'core/system_config_category_confirm_delete.html'
    success_url = reverse_lazy('core:system_config_category_list')


# System Event Type Views
class SystemEventTypeListView(LoginRequiredMixin, ListView):
    model = SystemEventType
    template_name = 'core/system_event_type_list.html'
    context_object_name = 'types'

class SystemEventTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SystemEventType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_event_type_form.html'
    success_message = "System Event Type created successfully."
    success_url = reverse_lazy('core:system_event_type_list')

class SystemEventTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SystemEventType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/system_event_type_form.html'
    success_message = "System Event Type updated successfully."
    success_url = reverse_lazy('core:system_event_type_list')

class SystemEventTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = SystemEventType
    template_name = 'core/system_event_type_confirm_delete.html'
    success_url = reverse_lazy('core:system_event_type_list')


# System Event Severity Views
class SystemEventSeverityListView(LoginRequiredMixin, ListView):
    model = SystemEventSeverity
    template_name = 'core/system_event_severity_list.html'
    context_object_name = 'severities'

class SystemEventSeverityCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SystemEventSeverity
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/system_event_severity_form.html'
    success_message = "System Event Severity created successfully."
    success_url = reverse_lazy('core:system_event_severity_list')

class SystemEventSeverityUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SystemEventSeverity
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/system_event_severity_form.html'
    success_message = "System Event Severity updated successfully."
    success_url = reverse_lazy('core:system_event_severity_list')

class SystemEventSeverityDeleteView(LoginRequiredMixin, DeleteView):
    model = SystemEventSeverity
    template_name = 'core/system_event_severity_confirm_delete.html'
    success_url = reverse_lazy('core:system_event_severity_list')


# Health Check Type Views
class HealthCheckTypeListView(LoginRequiredMixin, ListView):
    model = HealthCheckType
    template_name = 'core/health_check_type_list.html'
    context_object_name = 'types'

class HealthCheckTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = HealthCheckType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/health_check_type_form.html'
    success_message = "Health Check Type created successfully."
    success_url = reverse_lazy('core:health_check_type_list')

class HealthCheckTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HealthCheckType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/health_check_type_form.html'
    success_message = "Health Check Type updated successfully."
    success_url = reverse_lazy('core:health_check_type_list')

class HealthCheckTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = HealthCheckType
    template_name = 'core/health_check_type_confirm_delete.html'
    success_url = reverse_lazy('core:health_check_type_list')


# Health Check Status Views
class HealthCheckStatusListView(LoginRequiredMixin, ListView):
    model = HealthCheckStatus
    template_name = 'core/health_check_status_list.html'
    context_object_name = 'statuses'

class HealthCheckStatusCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = HealthCheckStatus
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/health_check_status_form.html'
    success_message = "Health Check Status created successfully."
    success_url = reverse_lazy('core:health_check_status_list')

class HealthCheckStatusUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = HealthCheckStatus
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/health_check_status_form.html'
    success_message = "Health Check Status updated successfully."
    success_url = reverse_lazy('core:health_check_status_list')

class HealthCheckStatusDeleteView(LoginRequiredMixin, DeleteView):
    model = HealthCheckStatus
    template_name = 'core/health_check_status_confirm_delete.html'
    success_url = reverse_lazy('core:health_check_status_list')


# Maintenance Status Views
class MaintenanceStatusListView(LoginRequiredMixin, ListView):
    model = MaintenanceStatus
    template_name = 'core/maintenance_status_list.html'
    context_object_name = 'statuses'

class MaintenanceStatusCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MaintenanceStatus
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/maintenance_status_form.html'
    success_message = "Maintenance Status created successfully."
    success_url = reverse_lazy('core:maintenance_status_list')

class MaintenanceStatusUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MaintenanceStatus
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/maintenance_status_form.html'
    success_message = "Maintenance Status updated successfully."
    success_url = reverse_lazy('core:maintenance_status_list')

class MaintenanceStatusDeleteView(LoginRequiredMixin, DeleteView):
    model = MaintenanceStatus
    template_name = 'core/maintenance_status_confirm_delete.html'
    success_url = reverse_lazy('core:maintenance_status_list')


# Maintenance Type Views
class MaintenanceTypeListView(LoginRequiredMixin, ListView):
    model = MaintenanceType
    template_name = 'core/maintenance_type_list.html'
    context_object_name = 'types'

class MaintenanceTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MaintenanceType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/maintenance_type_form.html'
    success_message = "Maintenance Type created successfully."
    success_url = reverse_lazy('core:maintenance_type_list')

class MaintenanceTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = MaintenanceType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/maintenance_type_form.html'
    success_message = "Maintenance Type updated successfully."
    success_url = reverse_lazy('core:maintenance_type_list')

class MaintenanceTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = MaintenanceType
    template_name = 'core/maintenance_type_confirm_delete.html'
    success_url = reverse_lazy('core:maintenance_type_list')


# Performance Metric Type Views
class PerformanceMetricTypeListView(LoginRequiredMixin, ListView):
    model = PerformanceMetricType
    template_name = 'core/performance_metric_type_list.html'
    context_object_name = 'types'

class PerformanceMetricTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PerformanceMetricType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/performance_metric_type_form.html'
    success_message = "Performance Metric Type created successfully."
    success_url = reverse_lazy('core:performance_metric_type_list')

class PerformanceMetricTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PerformanceMetricType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/performance_metric_type_form.html'
    success_message = "Performance Metric Type updated successfully."
    success_url = reverse_lazy('core:performance_metric_type_list')

class PerformanceMetricTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = PerformanceMetricType
    template_name = 'core/performance_metric_type_confirm_delete.html'
    success_url = reverse_lazy('core:performance_metric_type_list')


# Performance Environment Views
class PerformanceEnvironmentListView(LoginRequiredMixin, ListView):
    model = PerformanceEnvironment
    template_name = 'core/performance_environment_list.html'
    context_object_name = 'environments'

class PerformanceEnvironmentCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PerformanceEnvironment
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/performance_environment_form.html'
    success_message = "Performance Environment created successfully."
    success_url = reverse_lazy('core:performance_environment_list')

class PerformanceEnvironmentUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PerformanceEnvironment
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/performance_environment_form.html'
    success_message = "Performance Environment updated successfully."
    success_url = reverse_lazy('core:performance_environment_list')

class PerformanceEnvironmentDeleteView(LoginRequiredMixin, DeleteView):
    model = PerformanceEnvironment
    template_name = 'core/performance_environment_confirm_delete.html'
    success_url = reverse_lazy('core:performance_environment_list')


# Notification Type Views
class NotificationTypeListView(LoginRequiredMixin, ListView):
    model = NotificationType
    template_name = 'core/notification_type_list.html'
    context_object_name = 'types'

class NotificationTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = NotificationType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/notification_type_form.html'
    success_message = "Notification Type created successfully."
    success_url = reverse_lazy('core:notification_type_list')

class NotificationTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = NotificationType
    fields = ['name', 'display_name', 'description', 'is_active']
    template_name = 'core/notification_type_form.html'
    success_message = "Notification Type updated successfully."
    success_url = reverse_lazy('core:notification_type_list')

class NotificationTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = NotificationType
    template_name = 'core/notification_type_confirm_delete.html'
    success_url = reverse_lazy('core:notification_type_list')


# Notification Priority Views
class NotificationPriorityListView(LoginRequiredMixin, ListView):
    model = NotificationPriority
    template_name = 'core/notification_priority_list.html'
    context_object_name = 'priorities'

class NotificationPriorityCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = NotificationPriority
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/notification_priority_form.html'
    success_message = "Notification Priority created successfully."
    success_url = reverse_lazy('core:notification_priority_list')

class NotificationPriorityUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = NotificationPriority
    fields = ['name', 'display_name', 'color', 'description', 'is_active']
    template_name = 'core/notification_priority_form.html'
    success_message = "Notification Priority updated successfully."
    success_url = reverse_lazy('core:notification_priority_list')

class NotificationPriorityDeleteView(LoginRequiredMixin, DeleteView):
    model = NotificationPriority
    template_name = 'core/notification_priority_confirm_delete.html'
    success_url = reverse_lazy('core:notification_priority_list')

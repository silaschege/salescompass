from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count
from .models import AuditLog
import csv
import json
from datetime import timedelta
from django.utils import timezone


from core.views import (
    SalesCompassSuperuserListView, 
    SalesCompassSuperuserDetailView,
    SalesCompassSuperuserTemplateView
)



class AuditLogsDashboardView(SalesCompassSuperuserTemplateView):
    template_name = 'audit_logs/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Summary statistics
        context['total_logs'] = AuditLog.objects.count()
        context['recent_logs'] = AuditLog.objects.all()[:10]
        context['critical_count'] = AuditLog.objects.filter(severity='critical').count()
        context['error_count'] = AuditLog.objects.filter(severity='error').count()
        
        # Activity in last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        context['logs_24h'] = AuditLog.objects.filter(timestamp__gte=last_24h).count()
        
        return context


class AuditLogListView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        user_email = self.request.GET.get('user_email')
        action_type = self.request.GET.get('action_type')
        severity = self.request.GET.get('severity')
        tenant_id = self.request.GET.get('tenant_id')
        ip_address = self.request.GET.get('ip_address')
        search = self.request.GET.get('search')
        
        if user_email:
            queryset = queryset.filter(user_email__icontains=user_email)
        if action_type:
            queryset = queryset.filter(action_type__icontains=action_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(user_email__icontains=search) |
                Q(action_type__icontains=search)
            )
        
        return queryset


class AuditLogDetailView(SalesCompassSuperuserDetailView):
    model = AuditLog
    template_name = 'audit_logs/log_detail.html'
    context_object_name = 'log'


class RecentActionsView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/recent_actions.html'
    context_object_name = 'logs'
    paginate_by = 100
    
    def get_queryset(self):
        # Last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        return AuditLog.objects.filter(timestamp__gte=last_24h)


class CriticalEventsView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/critical_events.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        return AuditLog.objects.filter(severity__in=['critical', 'error'])


class StateChangesView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/state_changes.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        # Only logs that have state_before or state_after
        return AuditLog.objects.exclude(state_before__isnull=True, state_after__isnull=True)


class DataModificationsView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/data_modifications.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        # Filter for UPDATE, DELETE, CREATE actions
        return AuditLog.objects.filter(
            Q(action_type__icontains='UPDATE') |
            Q(action_type__icontains='DELETE') |
            Q(action_type__icontains='CREATE') |
            Q(action_type__icontains='MODIFY')
        )


class SecurityEventsView(SalesCompassSuperuserListView):
    model = AuditLog
    template_name = 'audit_logs/security_events.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        # Filter for security-related actions
        return AuditLog.objects.filter(
            Q(action_type__icontains='LOGIN') |
            Q(action_type__icontains='LOGOUT') |
            Q(action_type__icontains='AUTH') |
            Q(action_type__icontains='PERMISSION') |
            Q(action_type__icontains='ACCESS')
        )


class SOC2ReportView(SalesCompassSuperuserTemplateView):
    template_name = 'audit_logs/soc2_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # SOC2 compliance relevant logs
        context['access_logs'] = AuditLog.objects.filter(
            action_type__icontains='ACCESS'
        )[:100]
        context['change_logs'] = AuditLog.objects.exclude(
            state_before__isnull=True, state_after__isnull=True
        )[:100]
        return context


class HIPAAAuditView(SalesCompassSuperuserTemplateView):
    template_name = 'audit_logs/hipaa_audit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # HIPAA relevant logs
        context['phi_access_logs'] = AuditLog.objects.filter(
            Q(resource_type__icontains='PATIENT') |
            Q(resource_type__icontains='HEALTH') |
            Q(action_type__icontains='VIEW') |
            Q(action_type__icontains='EXPORT')
        )[:100]
        return context


class ExportLogsView(SalesCompassSuperuserTemplateView):
    template_name = 'audit_logs/export_form.html'
    
    def post(self, request, *args, **kwargs):
        # Get export parameters
        format_type = request.POST.get('format', 'csv')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Build queryset
        queryset = AuditLog.objects.all()
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        if format_type == 'csv':
            return self.export_csv(queryset)
        elif format_type == 'json':
            return self.export_json(queryset)
        
        return HttpResponse("Invalid format", status=400)
    
    def export_csv(self, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'User Email', 'Action Type', 'Resource Type', 
                        'Resource ID', 'Description', 'Severity', 'IP Address'])
        
        for log in queryset:
            writer.writerow([
                log.timestamp, log.user_email, log.action_type, log.resource_type,
                log.resource_id, log.description, log.severity, log.ip_address
            ])
        
        return response
    
    def export_json(self, queryset):
        data = []
        for log in queryset:
            data.append({
                'timestamp': log.timestamp.isoformat(),
                'user_email': log.user_email,
                'action_type': log.action_type,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'description': log.description,
                'severity': log.severity,
                'ip_address': log.ip_address,
                'state_before': log.state_before,
                'state_after': log.state_after,
            })
        
        response = JsonResponse(data, safe=False)
        response['Content-Disposition'] = 'attachment; filename="audit_logs.json"'
        return response

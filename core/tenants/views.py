from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, ListView, View, UpdateView, FormView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from .models import Tenant
from .forms import TenantSignupForm, TenantBrandingForm, TenantDomainForm, TenantSettingsForm, FeatureToggleForm
from billing.models import Plan, Subscription
from core.models import User, Role

class TenantListView(LoginRequiredMixin, ListView):
    template_name = 'tenants/list.html'
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 20

class TenantCreateView(LoginRequiredMixin, CreateView):
    template_name = 'tenants/create.html'
    form_class = TenantSignupForm
    success_url = reverse_lazy('tenants:list')

    def form_valid(self, form):
        # reuse signup logic without creating admin user
        tenant = Tenant.objects.create(name=form.cleaned_data['company_name'])
        # create a regular user (non-staff)
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']
        user.email = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password'])
        user.tenant = tenant
        user.is_staff = False
        user.save()
        login(self.request, user)
        return super().form_valid(form)

class TenantSearchView(LoginRequiredMixin, ListView):
    template_name = 'tenants/search.html'
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Tenant.objects.filter(name__icontains=query)
        return Tenant.objects.none()

class PlanSelectionView(LoginRequiredMixin, ListView):
    template_name = 'tenants/plan_selection.html'
    model = Plan
    context_object_name = 'plans'
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True)

class ProvisioningView(LoginRequiredMixin, View):
    def get(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)
        tenant_id = request.user.tenant_id
        
        if not tenant_id:
            return redirect('tenants:list')
            
        tenant = Tenant.objects.get(id=tenant_id)
        
        # Mock Payment & Subscription Creation
        with transaction.atomic():
            tenant.plan = plan
            tenant.subscription_status = 'active'
            tenant.save()
            
            Subscription.objects.create(
                tenant_id=tenant.id,
                plan=plan,
                status='active'
            )
            
        return redirect('dashboard:cockpit')


# Provisioning & Onboarding Views
class ProvisionTenantView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/provision_tenant.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.filter(subscription_status='trialing')
        return context


class SubdomainAssignmentView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/subdomain_assignment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context


class DatabaseInitializationView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/database_initialization.html'


class AdminUserSetupView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/admin_user_setup.html'


# Lifecycle Management Views
class SuspendTenantView(LoginRequiredMixin, View):
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        return render(request, 'tenants/suspend_confirm.html', {'tenant': tenant})
    
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        reason = request.POST.get('reason', '')
        tenant.suspend(reason=reason)
        messages.success(request, f'Tenant "{tenant.name}" has been suspended.')
        return redirect('tenants:list')


class ArchiveTenantView(LoginRequiredMixin, View):
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        return render(request, 'tenants/archive_confirm.html', {'tenant': tenant})
    
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        tenant.archive()
        messages.success(request, f'Tenant "{tenant.name}" has been archived.')
        return redirect('tenants:list')


class ReactivateTenantView(LoginRequiredMixin, View):
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        return render(request, 'tenants/reactivate_confirm.html', {'tenant': tenant})
    
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        tenant.reactivate()
        messages.success(request, f'Tenant "{tenant.name}" has been reactivated.')
        return redirect('tenants:list')


class DeleteTenantView(LoginRequiredMixin, View):
    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        return render(request, 'tenants/delete_confirm.html', {'tenant': tenant})
    
    def post(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        tenant.soft_delete()
        messages.success(request, f'Tenant "{tenant.name}" has been deleted.')
        return redirect('tenants:list')


# Module Entitlements Views
class FeatureTogglesView(LoginRequiredMixin, FormView):
    template_name = 'tenants/feature_toggles.html'
    form_class = FeatureToggleForm
    success_url = reverse_lazy('tenants:feature_toggles')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.GET.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            context['tenant'] = tenant
            context['features'] = tenant.settings.get('feature_toggles', {})
        context['tenants'] = Tenant.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        tenant_id = self.request.POST.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            feature_toggles = tenant.settings.get('feature_toggles', {})
            feature_name = form.cleaned_data['feature_name']
            feature_toggles[feature_name] = {
                'enabled': form.cleaned_data['enabled'],
                'description': form.cleaned_data.get('description', '')
            }
            tenant.update_settings(feature_toggles=feature_toggles)
            messages.success(self.request, f'Feature toggle "{feature_name}" updated.')
        return super().form_valid(form)


class UsageLimitsView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/usage_limits.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.filter(is_active=True)
        return context


class EntitlementTemplatesView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/entitlement_templates.html'


# Domain & Branding Views
class DomainManagementListView(LoginRequiredMixin, TemplateView):
    """List view for domain management - shows all tenants"""
    template_name = 'tenants/domain_management_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context


class DomainManagementView(LoginRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantDomainForm
    template_name = 'tenants/domain_management.html'
    success_url = reverse_lazy('tenants:domain_management')
    pk_url_kwarg = 'tenant_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Domain updated successfully.')
        return super().form_valid(form)


class SSLCertificatesView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/ssl_certificates.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.exclude(domain__isnull=True).exclude(domain='')
        return context


class BrandingConfigListView(LoginRequiredMixin, TemplateView):
    """List view for branding config - shows all tenants"""
    template_name = 'tenants/branding_config_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context


class BrandingConfigView(LoginRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantBrandingForm
    template_name = 'tenants/branding_config.html'
    success_url = reverse_lazy('tenants:branding_config')
    pk_url_kwarg = 'tenant_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Branding updated successfully.')
        return super().form_valid(form)


class LogoManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/logo_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        return context


# Billing Oversight Views
class SubscriptionOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/subscription_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        context['subscriptions'] = Subscription.objects.select_related('tenant', 'plan').all()
        return context


class RevenueAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants/revenue_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate revenue analytics
        subscriptions = Subscription.objects.filter(status='active').select_related('plan')
        total_mrr = sum(sub.plan.price for sub in subscriptions if sub.plan)
        context['total_mrr'] = total_mrr
        context['active_subscriptions'] = subscriptions.count()
        context['subscriptions'] = subscriptions
        return context


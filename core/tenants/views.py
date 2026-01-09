from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, ListView, View, UpdateView, FormView, DetailView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import (
    Tenant, Setting, SettingGroup, SettingType, TenantSettings, 
    TenantCloneHistory, WhiteLabelSettings, TenantUsageMetric, 
    TenantFeatureEntitlement, OverageAlert, NotificationTemplate, 
    Notification, AlertThreshold, TenantDataIsolationAudit, 
    TenantDataIsolationViolation, DataResidencySettings,
    TenantRole, TenantTerritory, TenantMember
)
from .forms import (
    TenantSignupForm, TenantBrandingForm, TenantDomainForm, TenantSettingsForm, 
    FeatureToggleForm, SettingForm, SettingGroupForm, SettingTypeForm,
    OnboardingTenantInfoForm, OnboardingBrandingForm, TenantExportForm,
      TenantImportForm, TenantCloneForm, WhiteLabelSettingsForm, 
      TenantUsageMetricForm, TenantUsageReportForm, TenantFeatureEntitlementForm, 
      FeatureAccessForm, BulkFeatureEntitlementForm, OverageAlertForm, NotificationForm, AlertThresholdForm, 
      TenantDataIsolationAuditForm, TenantDataIsolationViolationForm, DataIsolationAuditFilterForm, DataResidencySettingsForm,
      OnboardingUserSignupForm, SuperuserProvisionForm, TenantMemberForm
)
from .utils import track_usage, get_current_usage, get_usage_trend, check_usage_limits, generate_usage_report, check_feature_access, enforce_feature_access, get_accessible_features, perform_data_isolation_audit
import datetime

from billing.models import Plan, Subscription
from core.models import User
from accounts.models import Role
from django.contrib.messages.views import SuccessMessageMixin # Import SuccessMessageMixin
import json
from django.http import JsonResponse
from django.shortcuts import redirect
import django.db.models as models
from core.permissions import ObjectPermissionRequiredMixin


class SettingTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = SettingType
    template_name = 'tenants/setting_type_confirm_delete.html'
    success_url = reverse_lazy('tenants:setting_type_list')

    def get_queryset(self):
        return SettingType.objects.filter(tenant=self.request.user.tenant)


# Onboarding Wizard Views

class OnboardingSignupView(CreateView):
    """
    Step 0: Public Signup View.
    Creates the User account first, then redirects to the wizard.
    """
    template_name = 'tenants/onboarding/signup.html'
    form_class = OnboardingUserSignupForm
    success_url = reverse_lazy('tenants:onboarding_welcome')

    def form_valid(self, form):
        # Create user but don't commit yet to check for errors/handle login
        user = form.save()
        # Log the user in
        login(self.request, user)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'tenant') and request.user.tenant:
                return redirect('dashboard:cockpit')
            return redirect('tenants:onboarding_welcome')
        return super().dispatch(request, *args, **kwargs)


class OnboardingWizardBaseView(LoginRequiredMixin, TemplateView):
    """Base view for the onboarding wizard"""
    step = 0
    total_steps = 7
    template_name = 'tenants/onboarding/base.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'step': self.step,
            'total_steps': self.total_steps,
            'progress': int((self.step / self.total_steps) * 100),
        })
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # If user already has a tenant, redirect to dashboard
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return redirect('dashboard:cockpit')
        return super().dispatch(request, *args, **kwargs)


class OnboardingWelcomeView(OnboardingWizardBaseView):
    """Step 1: Welcome to the onboarding process"""
    step = 1
    template_name = 'tenants/onboarding/welcome.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Welcome to SalesCompass',
            'subtitle': 'Let\'s set up your account in a few simple steps'
        })
        return context
    
    def get(self, request, *args, **kwargs):
        # If user already has a tenant, redirect to dashboard
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return redirect('dashboard:cockpit')
        
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class OnboardingAdminSetupView(OnboardingWizardBaseView):
    """Step 2: Acknowledge Admin User Setup"""
    step = 2
    template_name = 'tenants/onboarding/admin_setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Admin Account',
            'subtitle': 'Review your administrative access',
            'admin_email': self.request.user.email
        })
        return context
    
    def post(self, request, *args, **kwargs):
        # We don't need to gather data here as the current user becomes the admin
        # Just confirmation step
        return redirect('tenants:onboarding_tenant_info')


class OnboardingTenantInfoView(OnboardingWizardBaseView):
    """Step 3: Collect Basic Tenant Information"""
    step = 3
    template_name = 'tenants/onboarding/tenant_info.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Company Information',
            'subtitle': 'Tell us about your organization',
            'form': OnboardingTenantInfoForm()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = OnboardingTenantInfoForm(request.POST)
        if form.is_valid():
            # Store form data in session for later use
            request.session['onboarding_tenant_info'] = {
                'company_name': form.cleaned_data['company_name'],
                'company_description': form.cleaned_data['company_description'],
                'industry': form.cleaned_data['industry'],
                'company_size': form.cleaned_data['company_size'],
                'primary_email': form.cleaned_data['primary_email']
            }
            return redirect('tenants:onboarding_plan_selection')
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


class OnboardingPlanSelectionView(OnboardingWizardBaseView):
    """Step 4: Select a Subscription Plan"""
    step = 4
    template_name = 'tenants/onboarding/plan_selection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Choose Your Plan',
            'subtitle': 'Select the plan that fits your needs',
            'plans': Plan.objects.filter(is_active=True)
        })
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            selected_plan_id = data.get('selected_plan_id')
            
            if selected_plan_id:
                # Store selected plan in session
                request.session['onboarding_selected_plan'] = selected_plan_id
            return JsonResponse({'success': True, 'redirect_url': reverse('tenants:onboarding_subdomain')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class OnboardingSubdomainView(OnboardingWizardBaseView):
    """Step 5: Subdomain Assignment"""
    step = 5
    template_name = 'tenants/onboarding/subdomain.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_name = self.request.session.get('onboarding_tenant_info', {}).get('company_name', '')
        from django.utils.text import slugify
        suggested_subdomain = slugify(company_name)
        context.update({
            'title': 'Choose Your Subdomain',
            'subtitle': 'This will be your unique URL on SalesCompass',
            'suggested_subdomain': suggested_subdomain
        })
        return context
    
    def post(self, request, *args, **kwargs):
        subdomain = request.POST.get('subdomain')
        if subdomain:
            request.session['onboarding_subdomain'] = subdomain
            return redirect('tenants:onboarding_data_residency')
        return self.get(request, *args, **kwargs)


class OnboardingDataResidencyView(OnboardingWizardBaseView):
    """Step 6: Data Residency Selection"""
    step = 6
    template_name = 'tenants/onboarding/data_residency.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import DataResidencySettings
        context.update({
            'title': 'Data Residency',
            'subtitle': 'Choose where your data lives',
            'data_regions': DataResidencySettings.DATA_REGIONS
        })
        return context
    
    def post(self, request, *args, **kwargs):
        primary_region = request.POST.get('primary_region', 'GLOBAL')
        request.session['onboarding_data_residency'] = primary_region
        return redirect('tenants:onboarding_branding')


class OnboardingBrandingView(OnboardingWizardBaseView):
    """Step 7: Configure Branding"""
    step = 7
    template_name = 'tenants/onboarding/branding.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Customize Your Brand',
            'subtitle': 'Personalize your SalesCompass experience',
            'form': OnboardingBrandingForm()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = OnboardingBrandingForm(request.POST, request.FILES)
        if form.is_valid():
            # Store branding data in session
            request.session['onboarding_branding_info'] = {
                'primary_color': form.cleaned_data['primary_color'],
                'secondary_color': form.cleaned_data['secondary_color'],
                'timezone': form.cleaned_data['timezone'],
                'date_format': form.cleaned_data['date_format'],
                'currency': form.cleaned_data['currency']
            }
            
            # Process the logo upload if provided
            if 'logo' in request.FILES:
                logo_file = request.FILES['logo']
                request.session['onboarding_logo'] = logo_file.name  # Store filename for later processing
            
            # Redirect to next step
            return redirect('tenants:onboarding_complete')
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


class OnboardingCompleteView(OnboardingWizardBaseView):
    """Step 8: Completion and Tenant Creation"""
    step = 8 # Display as 8 (Complete)
    template_name = 'tenants/onboarding/complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Setup Complete!',
            'subtitle': 'Your SalesCompass account is ready to use'
        })
        return context
    
    def get(self, request, *args, **kwargs):
        # If this is the first time accessing this page in the session, create the tenant
        if not request.session.get('tenant_created', False):
            result = self.create_tenant_from_session_data(request)
            if result:
                request.session['tenant_created'] = True
                # Redirect to avoid re-creation on page refresh
                return redirect('tenants:onboarding_complete')
            else:
                # If creation failed, redirect back to onboarding start
                return redirect('tenants:onboarding_welcome')
        
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    def create_tenant_from_session_data(self, request):
        """Create tenant and related settings from session data"""
        try:
            # Get data from session
            tenant_info = request.session.get('onboarding_tenant_info', {})
            branding_info = request.session.get('onboarding_branding_info', {})
            selected_plan_id = request.session.get('onboarding_selected_plan')
            subdomain = request.session.get('onboarding_subdomain')
            data_residency_region = request.session.get('onboarding_data_residency', 'GLOBAL')
            
            if not tenant_info:
                messages.error(request, "Tenant information is missing. Please restart the onboarding process.")
                return False
            
            with transaction.atomic():
                # Create the tenant
                tenant = Tenant.objects.create(
                    name=tenant_info['company_name'],
                    description=tenant_info.get('company_description', ''),
                    primary_color=branding_info.get('primary_color', '#6f42c1'),
                    secondary_color=branding_info.get('secondary_color', '#007bff'),
                    subdomain=subdomain,
                    tenant_admin=request.user,  # Assign the current user as the tenant admin
                )
                
                # Assign plan if selected
                if selected_plan_id:
                    try:
                        from billing.models import Plan
                        plan = Plan.objects.get(id=selected_plan_id)  # Fix: Plan is global, not per-tenant before creation
                        tenant.plan = plan
                        tenant.save()
                    except (Plan.DoesNotExist, ImportError):
                        pass  # Plan not found, continue without plan assignment
                        
                    # Create Subscription
                    if tenant.plan:
                        Subscription.objects.create(
                            tenant=tenant,
                            user=request.user,
                            subscription_plan=tenant.plan,
                            initial_status='trialing', # Assuming 'trialing' is the correct status
                            subscription_is_active=True,
                            subscription_trial_end_date=timezone.now() + timezone.timedelta(days=14) # 14 day trial default
                        )

                    # Initialize Feature Entitlements based on Plan
                    if tenant.plan:
                        # This would ideally come from a PlanFeature mapping model, simplified here
                        features = ['crm_access', 'storage_limit'] 
                        for feature_key in features:
                            TenantFeatureEntitlement.objects.create(
                                tenant=tenant,
                                feature_key=feature_key,
                                feature_name=feature_key.replace('_', ' ').title(),
                                is_enabled=True,
                                entitlement_type='plan_based'
                            )
                
                # Initialize Data Residency Settings
                DataResidencySettings.objects.create(
                    tenant=tenant,
                    primary_region=data_residency_region,
                    allowed_regions=[data_residency_region] if data_residency_region != 'GLOBAL' else ['GLOBAL']
                )

                # Initialize White Label Settings (Default)
                WhiteLabelSettings.objects.create(
                    tenant=tenant,
                    primary_color=branding_info.get('primary_color', '#6f42c1'),
                    secondary_color=branding_info.get('secondary_color', '#007bff'),
                    is_active=False
                )

                # Log Tenant Creation Lifecycle Event
                from .models import TenantLifecycleEvent
                TenantLifecycleEvent.objects.create(
                    tenant=tenant,
                    event_type='created',
                    new_value=f"Tenant created with plan: {tenant.plan.name if tenant.plan else 'None'}",
                    triggered_by=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    reason="Initial Onboarding"
                )
                
                # Create tenant settings
                tenant_settings = TenantSettings.objects.create(
                    tenant=tenant,
                    primary_color=branding_info.get('primary_color', '#6f42c1'),
                    secondary_color=branding_info.get('secondary_color', '#007bff'),
                    time_zone=branding_info.get('timezone', 'UTC'),
                    date_format=branding_info.get('date_format', '%Y-%m-%d'),
                    default_currency=branding_info.get('currency', 'USD'),
                )
                
                # Process logo upload if available
                logo_filename = request.session.get('onboarding_logo')
                if logo_filename and hasattr(tenant_settings, 'logo'):
                    # In a real implementation, you would handle the file upload here
                    pass
                
                # Assign the current user to this tenant
                user = request.user
                if not user.tenant_id:  # Only assign if user doesn't already have a tenant
                    user.tenant = tenant
                    user.save()
                
            # Add success message
            messages.success(request, f"Your organization '{tenant.name}' has been successfully created!")
            
            return True
            
        except Exception as e:
            messages.error(request, f"Error creating tenant: {str(e)}")
            return False


# Data Export/Import Views


class TenantDataExportDownloadView(LoginRequiredMixin, View):
    """View for downloading exported data"""
    def get(self, request, format_type, *args, **kwargs):
        # This would generate the actual export file
        # For now, we'll return a placeholder response
        from django.http import HttpResponse
        import json
        
        # Placeholder data
        data = {
            'message': 'This would be your exported data',
            'format': format_type,
            'tenant_id': request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
        }
        
        if format_type == 'json':
            response = HttpResponse(json.dumps(data), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="tenant_data.json"'
        elif format_type == 'csv':
            response = HttpResponse('id,name,email\n1,John Doe,john@example.com', content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="tenant_data.csv"'
        elif format_type == 'excel':
            response = HttpResponse('Excel content would go here', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="tenant_data.xlsx"'
        else:
            response = HttpResponse('Invalid format', status=400)
        
        return response


class TenantCloneView(LoginRequiredMixin, TemplateView):
    """View for cloning a tenant"""
    template_name = 'tenants/clone_tenant.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Clone Tenant',
            'subtitle': 'Create a copy of an existing tenant',
            'form': TenantCloneForm(user=self.request.user)
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = TenantCloneForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                # Get form data
                clone_type = form.cleaned_data['clone_type']
                source_tenant = form.cleaned_data['source_tenant']
                new_tenant_name = form.cleaned_data['new_tenant_name']
                new_tenant_slug = form.cleaned_data['new_tenant_slug']
                include_users = form.cleaned_data['include_users']
                include_settings = form.cleaned_data['include_settings']
                include_data = form.cleaned_data['include_data']
                include_custom_fields = form.cleaned_data['include_custom_fields']
                clone_description = form.cleaned_data['clone_description']
                
                # Check if slug is already taken
                if Tenant.objects.filter(slug=new_tenant_slug).exists():
                    form.add_error('new_tenant_slug', 'This slug is already in use. Please choose another.')
                    context = self.get_context_data(**kwargs)
                    context['form'] = form
                    return self.render_to_response(context)
                
                # Create the new tenant
                new_tenant = Tenant.objects.create(
                    name=new_tenant_name,
                    slug=new_tenant_slug,
                    description=clone_description or f'Clone of {source_tenant.name}',
                    primary_color=source_tenant.primary_color,
                    secondary_color=source_tenant.secondary_color,
                    user_limit=source_tenant.user_limit,
                    storage_limit_mb=source_tenant.storage_limit_mb,
                    api_call_limit=source_tenant.api_call_limit,
                )
                
                # Create clone history record
                clone_history = TenantCloneHistory.objects.create(
                    original_tenant=source_tenant,
                    cloned_tenant=new_tenant,
                    clone_type=clone_type,
                    initiated_by=request.user,
                    clone_options={
                        'include_users': include_users,
                        'include_settings': include_settings,
                        'include_data': include_data,
                        'include_custom_fields': include_custom_fields
                    },
                    total_steps=10,  # Placeholder for total steps
                    completed_steps=0
                )
                
                # Start the cloning process (in a real implementation, this would be done in a background task)
                self.perform_tenant_clone(
                    clone_history, 
                    source_tenant, 
                    new_tenant, 
                    include_users, 
                    include_settings, 
                    include_data, 
                    include_custom_fields
                )
                
                messages.success(request, f'Tenant "{new_tenant.name}" has been successfully cloned from "{source_tenant.name}".')
                return redirect('tenants:clone_history')
                
            except Exception as e:
                messages.error(request, f'Error cloning tenant: {str(e)}')
                context = self.get_context_data(**kwargs)
                context['form'] = form
                return self.render_to_response(context)
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)
    

    def perform_tenant_clone(self, clone_history, source_tenant, new_tenant, 
                            include_users, include_settings, include_data, include_custom_fields):
        """Perform the actual tenant cloning process"""
        try:
            # Update status to in progress
            clone_history.status = 'in_progress'
            clone_history.progress_percentage = 10.0
            clone_history.save()
            
            # Clone settings if requested
            if include_settings:
                try:
                    source_settings = source_tenant.tenant_settings
                    TenantSettings.objects.create(
                        tenant=new_tenant,
                        logo=source_settings.logo,
                        primary_color=source_settings.primary_color,
                        secondary_color=source_settings.secondary_color,
                        time_zone=source_settings.time_zone,
                        date_format=source_settings.date_format,
                        language_preference=source_settings.language_preference,
                        region=source_settings.region,
                        default_currency=source_settings.default_currency,
                        business_hours=source_settings.business_hours,
                        working_days=source_settings.working_days,
                        session_timeout_minutes=source_settings.session_timeout_minutes,
                        max_login_attempts=source_settings.max_login_attempts,
                        lockout_duration_minutes=source_settings.lockout_duration_minutes,
                        is_active=source_settings.is_active,
                    )
                    
                    clone_history.completed_steps += 1
                    clone_history.progress_percentage = 20.0
                    clone_history.save()
                except Exception as e:
                    clone_history.error_message = f"Error cloning settings: {str(e)}"
                    clone_history.status = 'failed'
                    clone_history.save()
                    return
            
            # Clone custom fields if requested
            if include_custom_fields:
                try:
                    # Import models dynamically to avoid circular imports
                    from settings_app.models import CustomField, FieldType, ModelChoice
                    
                    # Clone field types
                    for field_type in FieldType.objects.filter(tenant=source_tenant):
                        new_field_type = FieldType.objects.create(
                            tenant=new_tenant,
                            field_type_name=field_type.field_type_name,
                            label=field_type.label,
                            order=field_type.order,
                            field_type_is_active=field_type.field_type_is_active,
                            is_system=field_type.is_system
                        )
                    
                    # Clone model choices
                    for model_choice in ModelChoice.objects.filter(tenant=source_tenant):
                        new_model_choice = ModelChoice.objects.create(
                            tenant=new_tenant,
                            model_choice_name=model_choice.model_choice_name,
                            label=model_choice.label,
                            order=model_choice.order,
                            model_choice_is_active=model_choice.model_choice_is_active,
                            is_system=model_choice.is_system
                        )
                    
                    # Clone custom fields
                    for custom_field in CustomField.objects.filter(tenant=source_tenant):
                        # Find the corresponding field type and model choice in the new tenant
                        new_field_type_ref = None
                        if custom_field.field_type_ref:
                            try:
                                new_field_type_ref = FieldType.objects.get(
                                    tenant=new_tenant,
                                    field_type_name=custom_field.field_type_ref.field_type_name
                                )
                            except FieldType.DoesNotExist:
                                new_field_type_ref = None
                        
                        new_model_name_ref = None
                        if custom_field.model_name_ref:
                            try:
                                new_model_name_ref = ModelChoice.objects.get(
                                    tenant=new_tenant,
                                    model_choice_name=custom_field.model_name_ref.model_choice_name
                                )
                            except ModelChoice.DoesNotExist:
                                new_model_name_ref = None
                        
                        CustomField.objects.create(
                            tenant=new_tenant,
                            model_name=custom_field.model_name,
                            field_name=custom_field.field_name,
                            field_label=custom_field.field_label,
                            field_type=custom_field.field_type,
                            is_required=custom_field.is_required,
                            is_visible=custom_field.is_visible,
                            default_value=custom_field.default_value,
                            validation_rules=custom_field.validation_rules,
                            help_text=custom_field.help_text,
                            order=custom_field.order,
                            field_type_ref=new_field_type_ref,
                            model_name_ref=new_model_name_ref
                        )
                    
                    clone_history.completed_steps += 1
                    clone_history.progress_percentage = 30.0
                    clone_history.save()
                except Exception as e:
                    clone_history.error_message = f"Error cloning custom fields: {str(e)}"
                    clone_history.status = 'failed'
                    clone_history.save()
                    return
            
            # Clone users if requested
            if include_users:
                try:
                    from core.models import User
                    for user in User.objects.filter(tenant=source_tenant):
                        # Create new user with same details but assign to new tenant
                        new_user = User.objects.create_user(
                            username=f"{user.username}_clone_{new_tenant.id}",
                            email=user.email,
                            password=user.password,  # This will be the hashed password
                            first_name=user.first_name,
                            last_name=user.last_name,
                            tenant=new_tenant,
                            is_active=user.is_active,
                            is_staff=user.is_staff,
                            is_superuser=user.is_superuser,
                        )
                        
                        # Copy user profile if it exists
                        if hasattr(user, 'profile'):
                            from accounts.models import UserProfile
                            source_profile = user.profile
                            UserProfile.objects.create(
                                user=new_user,
                                bio=source_profile.bio,
                                phone=source_profile.phone,
                                address=source_profile.address,
                                department=source_profile.department,
                                position=source_profile.position,
                                hire_date=source_profile.hire_date,
                                is_manager=source_profile.is_manager,
                                manager=source_profile.manager,
                                profile_image=source_profile.profile_image
                            )
                    
                    clone_history.completed_steps += 1
                    clone_history.progress_percentage = 40.0
                    clone_history.save()
                except Exception as e:
                    clone_history.error_message = f"Error cloning users: {str(e)}"
                    clone_history.status = 'failed'
                    clone_history.save()
                    return
            
            # Clone business data if requested
            if include_data:
                try:
                    # Clone leads
                    from leads.models import Lead
                    for lead in Lead.objects.filter(tenant=source_tenant):
                        Lead.objects.create(
                            tenant=new_tenant,
                            first_name=lead.first_name,
                            last_name=lead.last_name,
                            company=lead.company,
                            email=lead.email,
                            phone=lead.phone,
                            status=lead.status,
                            source=lead.source,
                            # Map owner to a user in the new tenant (simplified mapping)
                            owner=new_tenant.user_set.first() if new_tenant.user_set.exists() else None,
                            title=lead.title,
                            industry=lead.industry,
                            notes=lead.notes,
                            lead_rating=lead.lead_rating,
                            lead_score=lead.lead_score,
                            converted=lead.converted,
                            converted_date=lead.converted_date,
                            address=lead.address,
                            city=lead.city,
                            state=lead.state,
                            country=lead.country,
                            zip_code=lead.zip_code,
                        )
                    
                    # Clone accounts
                    from accounts.models import Account
                    for account in Account.objects.filter(tenant=source_tenant):
                        Account.objects.create(
                            tenant=new_tenant,
                            name=account.name,
                            description=account.description,
                            website=account.website,
                            industry=account.industry,
                            number_of_employees=account.number_of_employees,
                            annual_revenue=account.annual_revenue,
                            billing_address=account.billing_address,
                            shipping_address=account.shipping_address,
                            phone=account.phone,
                            email=account.email,
                            status=account.status,
                            # Map owner to a user in the new tenant (simplified mapping)
                            owner=new_tenant.user_set.first() if new_tenant.user_set.exists() else None,
                            account_type=account.account_type,
                            # Handle parent account reference - simplified approach
                            parent_account=None,  # This would require more complex mapping
                            territory=account.territory,
                            territory_ref=account.territory_ref,
                            account_category=account.account_category,
                            account_category_ref=account.account_category_ref,
                            account_source=account.account_source,
                            account_source_ref=account.account_source_ref,
                            account_rating=account.account_rating,
                            account_rating_ref=account.account_rating_ref,
                        )
                    
                    # Clone opportunities
                    from opportunities.models import Opportunity, OpportunityStage
                    # First clone stages
                    stage_mapping = {}
                    for stage in OpportunityStage.objects.filter(tenant=source_tenant):
                        new_stage = OpportunityStage.objects.create(
                            tenant=new_tenant,
                            name=stage.name,
                            order=stage.order,
                            probability=stage.probability,
                            is_won=stage.is_won,
                            is_lost=stage.is_lost,
                        )
                        stage_mapping[stage.id] = new_stage
                    
                    # Then clone opportunities
                    for opportunity in Opportunity.objects.filter(tenant=source_tenant):
                        # Find corresponding stage in new tenant
                        new_stage = None
                        if opportunity.stage_id in [s.id for s in OpportunityStage.objects.filter(tenant=source_tenant)]:
                            # Find the matching stage in the new tenant
                            for orig_id, new_stage_obj in stage_mapping.items():
                                if orig_id == opportunity.stage_id:
                                    new_stage = new_stage_obj
                                    break
                        
                        Opportunity.objects.create(
                            tenant=new_tenant,
                            name=opportunity.name,
                            description=opportunity.description,
                            # Map account to a corresponding account in new tenant (simplified)
                            account=new_tenant.account_set.first() if new_tenant.account_set.exists() else None,
                            stage=new_stage,
                            amount=opportunity.amount,
                            close_date=opportunity.close_date,
                            probability=opportunity.probability,
                            # Map owner to a user in the new tenant (simplified mapping)
                            owner=new_tenant.user_set.first() if new_tenant.user_set.exists() else None,
                            type=opportunity.type,
                            lead_source=opportunity.lead_source,
                            next_step=opportunity.next_step,
                        )
                    
                    # Clone tasks
                    from tasks.models import Task
                    for task in Task.objects.filter(tenant=source_tenant):
                        Task.objects.create(
                            tenant=new_tenant,
                            title=task.title,
                            description=task.description,
                            status=task.status,
                            priority=task.priority,
                            due_date=task.due_date,
                            # Map assigned_to to a user in the new tenant (simplified mapping)
                            assigned_to=new_tenant.user_set.first() if new_tenant.user_set.exists() else None,
                            # Map created_by to a user in the new tenant (simplified mapping)
                            created_by=new_tenant.user_set.first() if new_tenant.user_set.exists() else None,
                            completed_at=task.completed_at,
                            task_type=task.task_type,
                            related_object_id=task.related_object_id,
                            related_object_type=task.related_object_type,
                        )
                    
                    clone_history.completed_steps += 5  # Multiple data types
                    clone_history.progress_percentage = 90.0
                    clone_history.save()
                except Exception as e:
                    clone_history.error_message = f"Error cloning data: {str(e)}"
                    clone_history.status = 'failed'
                    clone_history.save()
                    return
            
            # Complete the cloning process
            clone_history.status = 'completed'
            clone_history.progress_percentage = 100.0
            clone_history.completed_at = timezone.now()
            clone_history.completed_by = clone_history.initiated_by
            clone_history.success_message = f"Successfully cloned tenant from {source_tenant.name} to {new_tenant.name}"
            clone_history.save()
            
        except Exception as e:
            clone_history.error_message = str(e)
            clone_history.status = 'failed'
            clone_history.save()

class TenantCloneHistoryView(LoginRequiredMixin, ListView):
    """View for viewing tenant clone history"""
    model = TenantCloneHistory
    template_name = 'tenants/clone_history.html'
    context_object_name = 'clones'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by user's tenant if not superuser
        if not self.request.user.is_superuser:
            # Get all tenants where the user is associated
            user_tenant_ids = [self.request.user.tenant_id] if hasattr(self.request.user, 'tenant_id') else []
            # Also include clones where the user's tenant was the source or destination
            queryset = queryset.filter(
                models.Q(original_tenant_id__in=user_tenant_ids) |
                models.Q(cloned_tenant_id__in=user_tenant_ids)
            )
        return queryset.select_related('original_tenant', 'cloned_tenant', 'initiated_by').order_by('-started_at')


class TenantCloneStatusView(LoginRequiredMixin, DetailView):
    """View for checking the status of a specific clone operation"""
    model = TenantCloneHistory
    template_name = 'tenants/clone_status.html'
    context_object_name = 'clone_operation'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by user's tenant if not superuser
        if not self.request.user.is_superuser:
            user_tenant_ids = [self.request.user.tenant_id] if hasattr(self.request.user, 'tenant_id') else []
            queryset = queryset.filter(
                models.Q(original_tenant_id__in=user_tenant_ids) |
                models.Q(cloned_tenant_id__in=user_tenant_ids)
            )
        return queryset.select_related('original_tenant', 'cloned_tenant', 'initiated_by', 'completed_by')

class TenantDataImportView(LoginRequiredMixin, TemplateView):
    """View for importing tenant data"""
    template_name = 'tenants/data_import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Import Data',
            'subtitle': 'Import data to your organization',
            'form': TenantImportForm()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = TenantImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the import
            import_file = request.FILES.get('import_file')
            import_type = form.cleaned_data['import_type']
            overwrite_existing = form.cleaned_data['overwrite_existing']
            validate_data = form.cleaned_data['validate_data']
            
            if not import_file:
                form.add_error('import_file', 'Please select a file to import.')
                context = self.get_context_data(**kwargs)
                context['form'] = form
                return self.render_to_response(context)
            
            # In a real implementation, this would call the import service
            # For now, we'll just return a success message
            try:
                # Call the import service (would be implemented in a service class)
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f'Data import initiated for {import_type} with file {import_file.name}'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Import failed: {str(e)}'
                })
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)


class TenantListView(LoginRequiredMixin, ListView):
    template_name = 'tenants/tenant_list.html'
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 20

class TenantCreateView(LoginRequiredMixin, CreateView):
    template_name = 'tenants/signup.html'
    form_class = TenantSignupForm
    success_url = reverse_lazy('tenants:tenant_list')

    def form_valid(self, form):
        # reuse signup logic without creating admin user
        tenant = Tenant.objects.create(name=form.cleaned_data['company_name'])
        # create a regular user (non-staff)
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']
        user.email = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password1'])
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

class TenantUpdateView(UpdateView):
    model = Tenant
    template_name = 'tenants/tenant_form.html'
    fields = ['name', 'subdomain', 'is_active']
    success_url = reverse_lazy('tenants:tenant_list')

class TenantDeleteView(DeleteView):
    model = Tenant
    template_name = 'tenants/tenant_confirm_delete.html'
    success_url = reverse_lazy('tenants:tenant_list')

class TenantDetailView(DetailView):
    model = Tenant
    template_name = 'tenants/tenant_detail.html'

class TenantActivateView(View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        tenant.is_active = not tenant.is_active
        tenant.save()
        return redirect('tenant-list')

class PlanSelectionView(LoginRequiredMixin, ListView):
    template_name = 'tenants/plan_selection.html'
    model = Plan
    context_object_name = 'plans'
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True)

# Provisioning Views

class SuperuserProvisionView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    View for Superusers to provision a new Tenant and Admin User manually.
    """
    template_name = 'tenants/provision_new.html'
    form_class = SuperuserProvisionForm
    success_url = reverse_lazy('tenants:tenant_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        with transaction.atomic():
            # 1. Create User
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )

            # 2. Create Tenant
            tenant = Tenant.objects.create(
                name=form.cleaned_data['company_name'],
                subdomain=form.cleaned_data['subdomain'],
                tenant_admin=user,
                plan=form.cleaned_data['plan'] # Assign Plan directly
            )

            # 3. Create Subscription
            Subscription.objects.create(
                tenant=tenant,
                user=user,
                subscription_plan=tenant.plan,
                initial_status='active', # Superuser provisioned -> assumed active
                subscription_is_active=True,
                subscription_start_date=timezone.now()
            )

            # 4. Link User to Tenant
            user.tenant = tenant
            user.save()

            # 5. Initialize Settings (simplified - could reuse logic from OnboardingComplete)
            # Basic defaults
            DataResidencySettings.objects.create(tenant=tenant)
            WhiteLabelSettings.objects.create(tenant=tenant)
            TenantSettings.objects.create(tenant=tenant)

            # 6. Log Event
            from .models import TenantLifecycleEvent
            TenantLifecycleEvent.objects.create(
                tenant=tenant,
                event_type='provisioned',
                new_value=f"Provisioned by Superuser: {self.request.user.email}",
                triggered_by=self.request.user,
                reason="Manual Admin Provisioning"
            )

            messages.success(self.request, f"Successfully provisioned tenant '{tenant.name}' for user '{user.email}'")

        return super().form_valid(form)

class ProvisioningView(LoginRequiredMixin, View):
    def get(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)
        tenant_id = request.user.tenant_id
        
        if not tenant_id:
            return redirect('tenants:tenant_list')
            
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
            
            # Fetch entitlements and transform to the format expected by the template
            entitlements = TenantFeatureEntitlement.objects.filter(tenant=tenant)
            features = {}
            for ent in entitlements:
                features[ent.feature_name] = {
                    'enabled': ent.is_enabled,
                    'description': ent.notes,
                    'type': ent.entitlement_type,
                    'trial_active': ent.is_trial_active() if ent.entitlement_type == 'trial' else None,
                    'trial_end': ent.trial_end_date
                }
            context['features'] = features
        else:
            # Show current user's tenant features
            context['tenant'] = self.request.user.tenant
            entitlements = TenantFeatureEntitlement.objects.filter(tenant=self.request.user.tenant)
            features = {}
            for ent in entitlements:
                features[ent.feature_name] = {
                    'enabled': ent.is_enabled,
                    'description': ent.notes,
                    'type': ent.entitlement_type,
                    'trial_active': ent.is_trial_active() if ent.entitlement_type == 'trial' else None,
                    'trial_end': ent.trial_end_date
                }
            context['features'] = features
            
        context['tenants'] = Tenant.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        tenant_id = self.request.POST.get('tenant_id')
        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
        else:
            tenant = self.request.user.tenant
            
        feature_name = form.cleaned_data['feature_name']
        feature_key = feature_name.lower().replace(' ', '_')
        
        from .services import FeatureToggleService
        FeatureToggleService.enable_feature_for_tenant(
            tenant=tenant,
            feature_key=feature_key,
            feature_name=feature_name,
            entitlement_type='custom',
            notes=form.cleaned_data.get('description', '')
        )
        # Handle disable if enabled is False
        if not form.cleaned_data['enabled']:
             FeatureToggleService.disable_feature_for_tenant(tenant, feature_key)
        
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


# Setting Views
class SettingListView(LoginRequiredMixin, ListView):
    model = Setting
    template_name = 'tenants/setting_list.html'
    context_object_name = 'settings'

    def get_queryset(self):
        return Setting.objects.filter(tenant=self.request.user.tenant).select_related('group')


class SettingCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Setting
    form_class = SettingForm
    template_name = 'tenants/setting_form.html'
    success_message = "Setting created successfully."
    success_url = reverse_lazy('tenants:setting_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant'):
            form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class SettingUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Setting
    form_class = SettingForm
    template_name = 'tenants/setting_form.html'
    success_message = "Setting updated successfully."
    success_url = reverse_lazy('tenants:setting_list')

    def get_queryset(self):
        return Setting.objects.filter(tenant=self.request.user.tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs


class SettingDeleteView(LoginRequiredMixin, DeleteView):
    model = Setting
    template_name = 'tenants/setting_confirm_delete.html'
    success_url = reverse_lazy('tenants:setting_list')

    def get_queryset(self):
        return Setting.objects.filter(tenant=self.request.user.tenant)


# Setting Group Views
class SettingGroupListView(LoginRequiredMixin, ListView):
    model = SettingGroup
    template_name = 'tenants/setting_group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return SettingGroup.objects.filter(tenant=self.request.user.tenant)


class SettingGroupCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SettingGroup
    form_class = SettingGroupForm
    template_name = 'tenants/setting_group_form.html'
    success_message = "Setting Group created successfully."
    success_url = reverse_lazy('tenants:setting_group_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant'):
            form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class SettingGroupUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SettingGroup
    form_class = SettingGroupForm
    template_name = 'tenants/setting_group_form.html'
    success_message = "Setting Group updated successfully."
    success_url = reverse_lazy('tenants:setting_group_list')

    def get_queryset(self):
        return SettingGroup.objects.filter(tenant=self.request.user.tenant)


class SettingGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = SettingGroup
    template_name = 'tenants/setting_group_confirm_delete.html'
    success_url = reverse_lazy('tenants:setting_group_list')

    def get_queryset(self):
        return SettingGroup.objects.filter(tenant=self.request.user.tenant)


# Setting Type Views
class SettingTypeListView(LoginRequiredMixin, ListView):
    model = SettingType
    template_name = 'tenants/setting_type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return SettingType.objects.filter(tenant=self.request.user.tenant)


class SettingTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SettingType
    form_class = SettingTypeForm
    template_name = 'tenants/setting_type_form.html'
    success_message = "Setting Type created successfully."
    success_url = reverse_lazy('tenants:setting_type_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant'):
            form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class SettingTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SettingType
    form_class = SettingTypeForm
    template_name = 'tenants/setting_type_form.html'
    success_message = "Setting Type updated successfully."
    success_url = reverse_lazy('tenants:setting_type_list')

    def get_queryset(self):
        return SettingType.objects.filter(tenant=self.request.user.tenant)


class WhiteLabelSettingsView(LoginRequiredMixin, UpdateView):
    """View for managing white-label branding settings"""
    model = WhiteLabelSettings
    form_class = WhiteLabelSettingsForm
    template_name = 'tenants/white_label_settings.html'
    success_url = reverse_lazy('tenants:white_label_settings')
    
    def get_object(self, queryset=None):
        # Get or create the white-label settings for the current user's tenant
        tenant = self.request.user.tenant
        white_label_settings, created = WhiteLabelSettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                'brand_name': tenant.name,
                'primary_color': tenant.primary_color,
                'secondary_color': tenant.secondary_color,
            }
        )
        return white_label_settings
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'White-label branding settings updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'White-Label Branding',
            'subtitle': 'Customize your brand appearance',
        })
        return context


class TenantUsageMetricsView(LoginRequiredMixin, ListView):
    """View for displaying tenant usage metrics"""
    model = TenantUsageMetric
    template_name = 'tenants/usage_metrics.html'
    context_object_name = 'usage_metrics'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter metrics for the current user's tenant
        queryset = TenantUsageMetric.objects.filter(tenant=self.request.user.tenant)
        
        # Allow filtering by metric type
        metric_type = self.request.GET.get('metric_type', '')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Order by timestamp descending
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Usage Metrics',
            'subtitle': 'Track your tenant usage',
            'metric_types': TenantUsageMetric.METRIC_TYPES,  # Use the choices from the model
            'current_metric_type': self.request.GET.get('metric_type', ''),
        })
        return context


class TenantUsageReportView(LoginRequiredMixin, TemplateView):
    """View for generating usage reports"""
    template_name = 'tenants/usage_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Usage Report',
            'subtitle': 'Generate usage reports for your tenant',
            'form': TenantUsageReportForm(),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = TenantUsageReportForm(request.POST)
        if form.is_valid():
            # Get the data based on form inputs
            metric_type = form.cleaned_data['metric_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            include_trend = form.cleaned_data['include_trend']
            include_comparison = form.cleaned_data['include_comparison']
            
            # Generate the report
            report_data = generate_usage_report(
                tenant=request.user.tenant,
                metric_type=metric_type,
                start_date=start_date,
                end_date=end_date,
                include_trend=include_trend,
                include_comparison=include_comparison
            )
            
            context = self.get_context_data()
            context.update({
                'form': form,
                **report_data,  # Unpack the report data
                'include_trend': include_trend,
                'include_comparison': include_comparison,
            })
            
            return self.render_to_response(context)
        
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class TenantUsageAlertsView(LoginRequiredMixin, TemplateView):
    """View for managing usage alerts and limits"""
    template_name = 'tenants/usage_alerts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current usage for this tenant
        tenant = self.request.user.tenant
        current_storage = tenant.get_current_usage('storage_used_mb')
        current_api_calls = tenant.get_current_usage('api_calls')
        current_users = tenant.get_current_usage('users_total')
        
        # Get alerts for this tenant
        alerts = tenant.check_usage_limits()
        
        context.update({
            'title': 'Usage Alerts',
            'subtitle': 'Configure usage limits and alerts',
            'current_storage': current_storage,
            'current_api_calls': current_api_calls,
            'current_users': current_users,
            'tenant': tenant,
            'alerts': alerts,
        })
        return context


class TenantUsageIntegrationView(View):
    """View to handle integration with other systems for usage tracking"""
    
    @staticmethod
    def record_usage(tenant, metric_type, value, unit='', period_start=None, period_end=None):
        """
        Record usage for a tenant
        """
        if period_start is None:
            period_start = timezone.now() - timezone.timedelta(days=1)
        if period_end is None:
            period_end = timezone.now()
        
        metric = TenantUsageMetric.objects.create(
            tenant=tenant,
            metric_type=metric_type,
            value=value,
            unit=unit,
            period_start=period_start,
            period_end=period_end
        )
        return metric
    
    @staticmethod
    def get_current_usage(tenant, metric_type, period_start=None, period_end=None):
        """
        Get current usage for a tenant and metric type
        """
        if period_start is None:
            period_start = timezone.now() - timezone.timedelta(days=1)
        if period_end is None:
            period_end = timezone.now()
        
        metrics = TenantUsageMetric.objects.filter(
            tenant=tenant,
            metric_type=metric_type,
            timestamp__gte=period_start,
            timestamp__lte=period_end
        )
        
        return sum([m.value for m in metrics])


class TenantFeatureEntitlementView(LoginRequiredMixin, ListView):
    """View for displaying tenant feature entitlements"""
    model = TenantFeatureEntitlement
    template_name = 'tenants/feature_entitlements.html'
    context_object_name = 'feature_entitlements'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter feature entitlements for the current user's tenant
        return TenantFeatureEntitlement.objects.filter(tenant=self.request.user.tenant).order_by('feature_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Feature Entitlements',
            'subtitle': 'Manage feature access for your tenant',
        })
        return context


class TenantFeatureEntitlementCreateView(LoginRequiredMixin, CreateView):
    """View for creating new feature entitlements"""
    model = TenantFeatureEntitlement
    form_class = TenantFeatureEntitlementForm
    template_name = 'tenants/feature_entitlement_form.html'
    success_url = reverse_lazy('tenants:feature_entitlements')
    
    def form_valid(self, form):
        # Set the tenant to the current user's tenant
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f'Feature entitlement "{form.instance.feature_name}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Feature Entitlement',
            'subtitle': 'Add a new feature entitlement for your tenant',
            'action': 'create'
        })
        return context


class TenantFeatureEntitlementUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing feature entitlements"""
    model = TenantFeatureEntitlement
    form_class = TenantFeatureEntitlementForm
    template_name = 'tenants/feature_entitlement_form.html'
    success_url = reverse_lazy('tenants:feature_entitlements')
    
    def get_queryset(self):
        return TenantFeatureEntitlement.objects.filter(tenant=self.request.user.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, f'Feature entitlement "{form.instance.feature_name}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Feature Entitlement',
            'subtitle': 'Modify the feature entitlement',
            'action': 'update'
        })
        return context


class TenantFeatureEntitlementDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting feature entitlements"""
    model = TenantFeatureEntitlement
    template_name = 'tenants/feature_entitlement_confirm_delete.html'
    success_url = reverse_lazy('tenants:feature_entitlements')
    
    def get_queryset(self):
        return TenantFeatureEntitlement.objects.filter(tenant=self.request.user.tenant)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Feature entitlement "{self.get_object().feature_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TenantFeatureAccessCheckView(LoginRequiredMixin, TemplateView):
    """View for checking feature access"""
    template_name = 'tenants/feature_access_check.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Check Feature Access',
            'subtitle': 'Verify if a feature is available for your tenant',
            'form': FeatureAccessForm(),
            'now': timezone.now()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        form = FeatureAccessForm(request.POST)
        if form.is_valid():
            feature_key = form.cleaned_data['feature_key']
            
            from .utils import check_feature_access
            has_access = check_feature_access(request.user.tenant, feature_key)
            
            context = self.get_context_data()
            context.update({
                'form': form,
                'feature_key': feature_key,
                'has_access': has_access,
                'feature_exists': True, 
                'now': timezone.now()
            })
            
            return self.render_to_response(context)


class TenantBulkFeatureEntitlementView(LoginRequiredMixin, FormView):
    """View for bulk feature entitlement management"""
    template_name = 'tenants/bulk_feature_entitlement.html'
    form_class = BulkFeatureEntitlementForm
    success_url = reverse_lazy('tenants:feature_entitlements')
    
    def form_valid(self, form):
        features_data = form.cleaned_data # This custom form cleaning returns the list of dicts directly
        
        tenant = self.request.user.tenant
        
        from .services import FeatureToggleService
        # If the cleaner returns 'features_json' content parsed as list, we use it.
        # But wait, form.cleaned_data['features_json'] was the string? No, clean_features_json returns the parsed list?
        # In Django, if you define clean_fieldname, it returns the cleaned value for that field.
        # But form.cleaned_data will contain the key 'features_json'.
        
        # Let's check how the form is defined. "clean_features_json" returns features list.
        # So form.cleaned_data['features_json'] IS the list of features.
        
        features_list = form.cleaned_data.get('features_json', [])
        
        results = FeatureToggleService.bulk_feature_entitlement(tenant, features_list)
        
        messages.success(self.request, f'Updated {len(results)} feature(s) successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Bulk Feature Management',
            'subtitle': 'Manage multiple features at once',
        })
        return context


class FeatureEnforcementMiddleware:
    """Middleware to enforce feature limits"""
    
    @staticmethod
    def has_feature_access(user, feature_key):
        """
        Check if a user's tenant has access to a specific feature
        """
        if not hasattr(user, 'tenant') or not user.tenant:
            return False
        
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=user.tenant,
                feature_key=feature_key
            )
            return feature_entitlement.is_enabled
        except TenantFeatureEntitlement.DoesNotExist:
            # If feature entitlement doesn't exist, assume it's not available
            return False
    
    @staticmethod
    def enforce_feature_access(user, feature_key):
        """
        Enforce feature access - raise exception if user doesn't have access
        """
        if not FeatureEnforcementMiddleware.has_feature_access(user, feature_key):
            raise PermissionError(f"Feature '{feature_key}' is not available for your tenant plan.")
        
        # Check if it's a trial feature and if the trial has expired
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=user.tenant,
                feature_key=feature_key
            )
            
            if (feature_entitlement.entitlement_type == 'trial' and 
                feature_entitlement.trial_end_date and 
                timezone.now() > feature_entitlement.trial_end_date):
                raise PermissionError(f"Trial for feature '{feature_key}' has expired.")
        except TenantFeatureEntitlement.DoesNotExist:
            pass


class OverageAlertListView(LoginRequiredMixin, ListView):
    """View for displaying overage alerts"""
    model = OverageAlert
    template_name = 'tenants/overage_alerts.html'
    context_object_name = 'overage_alerts'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter overage alerts for the current user's tenant
        return OverageAlert.objects.filter(tenant=self.request.user.tenant).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Overage Alerts',
            'subtitle': 'Monitor usage overages for your tenant',
        })
        return context


class AlertThresholdListView(LoginRequiredMixin, ListView):
    """View for displaying alert thresholds"""
    model = AlertThreshold
    template_name = 'tenants/alert_thresholds.html'
    context_object_name = 'alert_thresholds'
    
    def get_queryset(self):
        # Filter alert thresholds for the current user's tenant
        return AlertThreshold.objects.filter(tenant=self.request.user.tenant).order_by('metric_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Alert Thresholds',
            'subtitle': 'Configure usage thresholds for alerts',
        })
        return context


class AlertThresholdCreateView(LoginRequiredMixin, CreateView):
    """View for creating alert thresholds"""
    model = AlertThreshold
    form_class = AlertThresholdForm
    template_name = 'tenants/alert_threshold_form.html'
    success_url = reverse_lazy('tenants:alert_thresholds')
    
    def form_valid(self, form):
        # Set the tenant to the current user's tenant
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f'Alert threshold for "{form.instance.metric_type}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Alert Threshold',
            'subtitle': 'Set a threshold for usage alerts',
            'action': 'create'
        })
        return context


class AlertThresholdUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating alert thresholds"""
    model = AlertThreshold
    form_class = AlertThresholdForm
    template_name = 'tenants/alert_threshold_form.html'
    success_url = reverse_lazy('tenants:alert_thresholds')
    
    def get_queryset(self):
        return AlertThreshold.objects.filter(tenant=self.request.user.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, f'Alert threshold for "{form.instance.metric_type}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Alert Threshold',
            'subtitle': 'Modify the alert threshold',
            'action': 'update'
        })
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """View for displaying notifications"""
    model = Notification
    template_name = 'tenants/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter notifications for the current user's tenant and user
        return Notification.objects.filter(
            tenant=self.request.user.tenant,
            user=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unread notifications count
        unread_count = Notification.objects.filter(
            tenant=self.request.user.tenant,
            user=self.request.user,
            is_read=False
        ).count()
        
        context.update({
            'title': 'Notifications',
            'subtitle': 'Your notifications',
            'unread_count': unread_count,
        })
        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    """View for marking notifications as read"""
    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    tenant=request.user.tenant,
                    user=request.user
                )
                notification.is_read = True
                notification.save()
                messages.success(request, 'Notification marked as read.')
            except Notification.DoesNotExist:
                messages.error(request, 'Notification not found.')
        else:
            messages.error(request, 'Invalid notification ID.')
        
        return redirect('tenants:notifications')


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """View for marking all notifications as read"""
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(
            tenant=request.user.tenant,
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        messages.success(request, 'All notifications marked as read.')
        return redirect('tenants:notifications')


class TenantDataExportView(LoginRequiredMixin, TemplateView):
    """View for exporting tenant data"""
    template_name = 'tenants/data_export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Export Data',
            'subtitle': 'Export your organization data',
            'form': TenantExportForm()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        # Check if user has access to data export feature
        if not FeatureEnforcementMiddleware.has_feature_access(request.user, 'data_export'):
            messages.error(request, 'You do not have access to the data export feature.')
            return redirect('tenants:data_export')
        
        form = TenantExportForm(request.POST)
        if form.is_valid():
            # Record this usage
            request.user.tenant.track_usage(
                metric_type='data_exported',
                value=1,
                unit='exports'
            )
            
            # Process the export
            data_types = form.cleaned_data['data_types']
            format_type = form.cleaned_data['format_type']
            include_attachments = form.cleaned_data['include_attachments']
            
            # In a real implementation, this would call the export service
            # For now, we'll just return a success message
            try:
                # Call the export service (would be implemented in a service class)
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f'Data export initiated for {", ".join(data_types)} in {format_type.upper()} format',
                    'download_url': f'/tenants/export/download/{format_type}/'  # Placeholder URL
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Export failed: {str(e)}'
                })
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)


class OverageAlertService:
    """Service class for handling overage alerts"""
    
    @staticmethod
    def check_usage_thresholds(tenant):
        """Check if any usage metrics have crossed their thresholds"""
        alerts_created = []
        
        # Get all active thresholds for this tenant
        thresholds = AlertThreshold.objects.filter(tenant=tenant, is_active=True)
        
        for threshold in thresholds:
            # Get the current usage for this metric
            current_usage = tenant.get_current_usage(threshold.metric_type)
            
            # Get the limit based on the metric type
            limit_value = OverageAlertService.get_limit_for_metric(tenant, threshold.metric_type)
            
            if limit_value > 0:
                usage_percentage = (current_usage / limit_value) * 100
                
                # Check if usage has crossed the threshold
                if usage_percentage >= threshold.threshold_percentage:
                    # Check if an alert already exists for this metric
                    existing_alert = OverageAlert.objects.filter(
                        tenant=tenant,
                        metric_type=threshold.metric_type,
                        is_resolved=False
                    ).first()
                    
                    if not existing_alert:
                        # Create a new overage alert
                        alert = OverageAlert.objects.create(
                            tenant=tenant,
                            metric_type=threshold.metric_type,
                            threshold_value=limit_value * (threshold.threshold_percentage / 100),
                            current_value=current_usage,
                            threshold_percentage=threshold.threshold_percentage,
                            alert_level=threshold.alert_level
                        )
                        
                        # Create a notification for the alert
                        Notification.objects.create(
                            tenant=tenant,
                            user=tenant.owner if hasattr(tenant, 'owner') else None,  # Assuming there's an owner
                            title=f"Overage Alert: {threshold.get_metric_type_display()}",
                            message=f"Your {threshold.get_metric_type_display()} usage ({current_usage}) has reached {usage_percentage:.2f}% of your limit ({limit_value}).",
                            notification_type='overage',
                            severity=threshold.alert_level,
                            delivery_method='in_app'
                        )
                        
                        alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def get_limit_for_metric(tenant, metric_type):
        """Get the limit for a specific metric type"""
        if metric_type == 'storage_used_mb':
            return tenant.storage_limit_mb
        elif metric_type == 'api_calls':
            return tenant.api_call_limit
        elif metric_type == 'users_total':
            return tenant.user_limit
        else:
            # For other metrics, we might have specific limits defined elsewhere
            # For now, return a default value or 0 to indicate no specific limit
            return 0
    
    @staticmethod
    def resolve_alert(alert_id, resolved_by):
        """Resolve an overage alert"""
        try:
            alert = OverageAlert.objects.get(id=alert_id, tenant=resolved_by.tenant)
            alert.is_resolved = True
            alert.resolved_at = timezone.now()
            alert.resolved_by = resolved_by
            alert.save()
            
            # Create a notification about the resolution
            Notification.objects.create(
                tenant=alert.tenant,
                user=resolved_by,
                title=f"Overage Alert Resolved: {alert.get_metric_type_display()}",
                message=f"The overage alert for {alert.get_metric_type_display()} has been resolved.",
                notification_type='success',
                severity='low',
                delivery_method='in_app'
            )
            
            return True
        except OverageAlert.DoesNotExist:
            return False


class ResolveOverageAlertView(LoginRequiredMixin, View):
    """View for resolving an overage alert"""
    def post(self, request, *args, **kwargs):
        alert_id = kwargs.get('pk')
        success = OverageAlertService.resolve_alert(alert_id, request.user)
        
        if success:
            messages.success(request, 'Overage alert resolved successfully.')
        else:
            messages.error(request, 'Failed to resolve overage alert.')
        
        return redirect('tenants:overage_alerts')


class TenantDataIsolationAuditListView(LoginRequiredMixin, ListView):
    """View for displaying tenant data isolation audits"""
    model = TenantDataIsolationAudit
    template_name = 'tenants/data_isolation_audits.html'
    context_object_name = 'audits'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter audits for the current user's tenant
        queryset = TenantDataIsolationAudit.objects.filter(tenant=self.request.user.tenant)
        
        # Apply filters from the form
        audit_type = self.request.GET.get('audit_type', '')
        status = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        if audit_type:
            queryset = queryset.filter(audit_type=audit_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(date_from + ":00")  # Add seconds if not present
            if parsed_date:
                queryset = queryset.filter(audit_date__gte=parsed_date)
        
        if date_to:
            from django.utils.dateparse import parse_datetime
            parsed_date = parse_datetime(date_to + ":00")  # Add seconds if not present
            if parsed_date:
                queryset = queryset.filter(audit_date__lte=parsed_date)
        
        return queryset.order_by('-audit_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Data Isolation Audits',
            'subtitle': 'Audit logs for tenant data isolation',
            'filter_form': DataIsolationAuditFilterForm(self.request.GET),
        })
        return context


class TenantDataIsolationAuditCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new data isolation audit"""
    model = TenantDataIsolationAudit
    form_class = TenantDataIsolationAuditForm
    template_name = 'tenants/data_isolation_audit_form.html'
    success_url = reverse_lazy('tenants:data_isolation_audits')
    
    def form_valid(self, form):
        # Set the tenant and auditor
        form.instance.tenant = self.request.user.tenant
        form.instance.auditor = self.request.user
        form.instance.status = 'in_progress'
        
        # Save the audit record
        response = super().form_valid(form)
        
        # Perform the audit in the background (in a real app, this would be a background task)
        self.perform_audit(form.instance)
        
        messages.success(self.request, f'Data isolation audit started successfully.')
        return response
    
    def perform_audit(self, audit):
        """Perform the actual data isolation audit"""
        from django.apps import apps
        from django.db import models
        from .models import TenantAwareModel
        
        # This is a simplified version - in a real implementation, you would check
        # for cross-tenant data access in all tenant-aware models
        violations_found = 0
        total_records = 0
        
        # Get all models that inherit from TenantAwareModel
        for model in apps.get_models():
            if issubclass(model, models.Model) and hasattr(model, 'tenant'):
                try:
                    # Check for records that don't belong to the correct tenant
                    records = model.objects.exclude(tenant=audit.tenant)
                    for record in records:
                        # Create a violation record
                        TenantDataIsolationViolation.objects.create(
                            audit=audit,
                            model_name=model.__name__,
                            record_id=record.pk,
                            field_name='tenant',
                            expected_tenant=audit.tenant,
                            actual_tenant=getattr(record, 'tenant', None),
                            violation_type='cross_tenant_access',
                            severity='high',
                            description=f'Record with ID {record.pk} in model {model.__name__} belongs to tenant {record.tenant.name if record.tenant else "None"} instead of expected tenant {audit.tenant.name}'
                        )
                        violations_found += 1
                    total_records += records.count()
                except Exception as e:
                    # Log the error but continue with other models
                    print(f"Error checking model {model.__name__}: {str(e)}")
        
        # Update the audit record with results
        audit.total_records_checked = total_records
        audit.violations_found = violations_found
        audit.status = 'failed' if violations_found > 0 else 'passed'
        audit.save()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Start Data Isolation Audit',
            'subtitle': 'Create a new audit to check tenant data isolation',
            'action': 'create'
        })
        return context


class TenantDataIsolationAuditDetailView(LoginRequiredMixin, DetailView):
    """View for displaying details of a specific data isolation audit"""
    model = TenantDataIsolationAudit
    template_name = 'tenants/data_isolation_audit_detail.html'
    context_object_name = 'audit'
    
    def get_queryset(self):
        return TenantDataIsolationAudit.objects.filter(tenant=self.request.user.tenant)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Data Isolation Audit Details',
            'subtitle': f'Audit results for {self.object.tenant.name}',
            'violations': self.object.violations.all()
        })
        return context


class TenantDataIsolationViolationListView(LoginRequiredMixin, ListView):
    """View for displaying data isolation violations"""
    model = TenantDataIsolationViolation
    template_name = 'tenants/data_isolation_violations.html'
    context_object_name = 'violations'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter violations for the current user's tenant
        return TenantDataIsolationViolation.objects.filter(
            audit__tenant=self.request.user.tenant
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Data Isolation Violations',
            'subtitle': 'List of data isolation violations found',
        })
        return context


class RunDataIsolationAuditView(LoginRequiredMixin, View):
    """View for running a data isolation audit"""
    def post(self, request, *args, **kwargs):
        # Create a new audit
        audit = TenantDataIsolationAudit.objects.create(
            tenant=request.user.tenant,
            auditor=request.user,
            audit_type='manual',
            status='in_progress',
            notes='Manually triggered data isolation audit'
        )
        
        # Perform the audit
        perform_data_isolation_audit(audit)
        
        messages.success(request, 'Data isolation audit completed successfully.')
        return redirect('tenants:data_isolation_audits')


class DataResidencySettingsView(LoginRequiredMixin, UpdateView):
    """View for managing data residency settings for a tenant"""
    model = DataResidencySettings
    form_class = DataResidencySettingsForm
    template_name = 'tenants/data_residency_settings.html'
    success_url = reverse_lazy('tenants:data_residency_settings')

    def get_object(self, queryset=None):
        # Get or create the data residency settings for the current user's tenant
        tenant = self.request.user.tenant
        data_residency_settings, created = DataResidencySettings.objects.get_or_create(
            tenant=tenant,
            defaults={
                'primary_region': 'GLOBAL',
                'encryption_enabled': True,
                'data_retention_period_months': 36,
            }
        )
        return data_residency_settings

    def form_valid(self, form):
        messages.success(self.request, "Data residency settings updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error updating data residency settings.")
        return super().form_invalid(form)


from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, ListView, View, UpdateView, FormView, DetailView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Tenant, Setting, SettingGroup, SettingType, TenantSettings, TenantCloneHistory, WhiteLabelSettings, TenantUsageMetric, TenantFeatureEntitlement, OverageAlert, NotificationTemplate, Notification, AlertThreshold, TenantDataIsolationAudit, TenantDataIsolationViolation, DataResidencySettings, TenantDataPreservation, TenantDataRestoration, TenantDataPreservationStrategy, TenantDataPreservationSchedule, AutomatedTenantLifecycleRule, AutomatedTenantLifecycleEvent, TenantLifecycleWorkflow, TenantLifecycleWorkflowExecution, TenantSuspensionWorkflow, TenantTerminationWorkflow
from .forms import (
    TenantSignupForm, TenantBrandingForm, TenantDomainForm, TenantSettingsForm, 
    FeatureToggleForm, SettingForm, SettingGroupForm, SettingTypeForm,
    OnboardingTenantInfoForm, OnboardingBrandingForm, TenantExportForm,
      TenantImportForm, TenantCloneForm, WhiteLabelSettingsForm, 
      TenantUsageMetricForm, TenantUsageReportForm, TenantFeatureEntitlementForm, 
      FeatureAccessForm, BulkFeatureEntitlementForm, OverageAlertForm, NotificationForm, AlertThresholdForm, 
      TenantDataIsolationAuditForm, TenantDataIsolationViolationForm, DataIsolationAuditFilterForm, DataResidencySettingsForm
)
from .utils import track_usage, get_current_usage, get_usage_trend, check_usage_limits, generate_usage_report, check_feature_access, enforce_feature_access, get_accessible_features, perform_data_isolation_audit
import datetime

from billing.models import Plan, Subscription
from core.models import User
from accounts.models import Role
from django.contrib.messages.views import SuccessMessageMixin # Import SuccessMessageMixin
import json
from django.http import JsonResponse
from django.shortcuts import redirect
import django.db.models as models


class TenantLifecycleDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view for tenant lifecycle management"""
    template_name = 'tenants/lifecycle_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        context['active_tenants'] = Tenant.objects.filter(is_active=True).count()
        context['suspended_tenants'] = Tenant.objects.filter(is_suspended=True).count()
        context['archived_tenants'] = Tenant.objects.filter(is_archived=True).count()
        context['automated_rules'] = AutomatedTenantLifecycleRule.objects.filter(is_active=True).count()
        context['recent_events'] = AutomatedTenantLifecycleEvent.objects.select_related('tenant', 'rule').order_by('-triggered_at')[:10]
        return context


class TenantStatusManagementView(LoginRequiredMixin, ListView):
    """View for managing tenant statuses"""
    template_name = 'tenants/status_management.html'
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Tenant.objects.all()
        status_filter = self.request.GET.get('status')
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True, is_suspended=False, is_archived=False)
            elif status_filter == 'suspended':
                queryset = queryset.filter(is_suspended=True)
            elif status_filter == 'archived':
                queryset = queryset.filter(is_archived=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        return queryset


class TenantSuspensionWorkflowView(LoginRequiredMixin, CreateView):
    """View for initiating tenant suspension workflow"""
    template_name = 'tenants/suspension_workflow.html'
    model = TenantSuspensionWorkflow
    fields = ['tenant', 'suspension_reason']
    success_url = reverse_lazy('tenants:suspension-workflows')
    
    def form_valid(self, form):
        form.instance.initiated_by = self.request.user
        messages.success(self.request, f'Suspension workflow initiated for {form.instance.tenant.name}.')
        return super().form_valid(form)


class TenantTerminationWorkflowView(LoginRequiredMixin, CreateView):
    """View for initiating tenant termination workflow"""
    template_name = 'tenants/termination_workflow.html'
    model = TenantTerminationWorkflow
    fields = ['tenant', 'termination_reason', 'data_preservation_required']
    success_url = reverse_lazy('tenants:termination-workflows')
    
    def form_valid(self, form):
        form.instance.initiated_by = self.request.user
        messages.success(self.request, f'Termination workflow initiated for {form.instance.tenant.name}.')
        return super().form_valid(form)


class AutomatedLifecycleRulesView(LoginRequiredMixin, ListView):
    """View for managing automated lifecycle rules"""
    template_name = 'tenants/automated_lifecycle_rules.html'
    model = AutomatedTenantLifecycleRule
    context_object_name = 'rules'
    paginate_by = 20
    
    def get_queryset(self):
        return AutomatedTenantLifecycleRule.objects.select_related('created_by').all()


class CreateAutomatedLifecycleRuleView(LoginRequiredMixin, CreateView):
    """View for creating automated lifecycle rules"""
    template_name = 'tenants/create_automated_rule.html'
    model = AutomatedTenantLifecycleRule
    fields = ['name', 'description', 'condition_type', 'condition_field', 'condition_operator', 'condition_value', 'action_type', 'action_parameters', 'evaluation_frequency']
    success_url = reverse_lazy('tenants:automated-lifecycle-rules')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Automated lifecycle rule "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class TenantDataPreservationView(LoginRequiredMixin, ListView):
    """View for managing tenant data preservation"""
    template_name = 'tenants/data_preservation.html'
    model = TenantDataPreservation
    context_object_name = 'preservation_records'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantDataPreservation.objects.select_related('tenant', 'created_by').all()


class TenantDataRestorationView(LoginRequiredMixin, ListView):
    """View for managing tenant data restoration"""
    template_name = 'tenants/data_restoration.html'
    model = TenantDataRestoration
    context_object_name = 'restoration_records'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantDataRestoration.objects.select_related('tenant', 'preservation_record').all()


class TenantLifecycleWorkflowsView(LoginRequiredMixin, ListView):
    """View for managing tenant lifecycle workflows"""
    template_name = 'tenants/lifecycle_workflows.html'
    model = TenantLifecycleWorkflow
    context_object_name = 'workflows'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantLifecycleWorkflow.objects.select_related('created_by').all()


class ApproveSuspensionWorkflowView(LoginRequiredMixin, View):
    """View for approving suspension workflows"""
    def post(self, request, workflow_id):
        workflow = get_object_or_404(TenantSuspensionWorkflow, id=workflow_id)
        notes = request.POST.get('approval_notes', '')
        
        workflow.approve(request.user, notes)
        messages.success(request, f'Suspension workflow for {workflow.tenant.name} approved.')
        
        return redirect('tenants:suspension-workflows')


class ApproveTerminationWorkflowView(LoginRequiredMixin, View):
    """View for approving termination workflows"""
    def post(self, request, workflow_id):
        workflow = get_object_or_404(TenantTerminationWorkflow, id=workflow_id)
        notes = request.POST.get('approval_notes', '')
        
        workflow.approve(request.user, notes)
        messages.success(request, f'Termination workflow for {workflow.tenant.name} approved.')
        
        return redirect('tenants:termination-workflows')


class TenantLifecycleEventLogView(LoginRequiredMixin, ListView):
    """View for viewing tenant lifecycle event logs"""
    template_name = 'tenants/lifecycle_event_log.html'
    model = AutomatedTenantLifecycleEvent
    context_object_name = 'events'
    paginate_by = 20
    
    def get_queryset(self):
        return AutomatedTenantLifecycleEvent.objects.select_related('tenant', 'rule', 'executed_by').order_by('-triggered_at')


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

@method_decorator(csrf_exempt, name='dispatch')
class ExecuteLifecycleRuleView(LoginRequiredMixin, View):
    """API view for executing lifecycle rules"""
    def post(self, request, rule_id):
        rule = get_object_or_404(AutomatedTenantLifecycleRule, id=rule_id)
        
        # In a real implementation, this would execute the rule logic
        # For now, we'll just log that the rule was executed
        tenants = Tenant.objects.all()
        executed_count = 0
        
        for tenant in tenants:
            # Evaluate the rule condition for each tenant
            # This is a simplified version - in a real implementation, 
            # you would have more complex logic to evaluate the condition
            condition_met = self.evaluate_condition(tenant, rule)
            
            if condition_met:
                # Execute the action for this tenant
                self.execute_action(tenant, rule)
                
                # Log the event
                AutomatedTenantLifecycleEvent.objects.create(
                    rule=rule,
                    tenant=tenant,
                    event_type='action_taken',
                    status='success',
                    details=f'Action {rule.action_type} taken for tenant {tenant.name}',
                    executed_by=request.user
                )
                executed_count += 1
        
        # Update the rule's last evaluation time
        rule.last_evaluated = timezone.now()
        rule.next_evaluation = self.calculate_next_evaluation(rule)
        rule.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Rule {rule.name} executed for {executed_count} tenants',
            'executed_count': executed_count
        })
    
    def evaluate_condition(self, tenant, rule):
        """Evaluate if the condition is met for a tenant"""
        # This is a simplified condition evaluation
        # In a real implementation, you would have more complex logic
        if rule.condition_type == 'usage_based':
            if rule.condition_field == 'storage_used' and rule.condition_operator == 'greater_than':
                # This would check the actual storage usage
                return False  # Placeholder
        elif rule.condition_type == 'billing_based':
            if rule.condition_field == 'subscription_status' and rule.condition_operator == 'equals':
                return getattr(tenant, rule.condition_field) == rule.condition_value
        elif rule.condition_type == 'time_based':
            if rule.condition_field == 'trial_end_date' and rule.condition_operator == 'less_than':
                return tenant.trial_end_date and tenant.trial_end_date < timezone.now()
        
        return False
    
    def execute_action(self, tenant, rule):
        """Execute the action for a tenant"""
        if rule.action_type == 'suspend':
            tenant.suspend(reason=f'Automated suspension by rule: {rule.name}', triggered_by=self.request.user)
        elif rule.action_type == 'terminate':
            tenant.soft_delete(triggered_by=self.request.user)
        elif rule.action_type == 'archive':
            tenant.archive(triggered_by=self.request.user)
        elif rule.action_type == 'reactivate':
            tenant.reactivate(triggered_by=self.request.user)
        # Add more actions as needed
    
    def calculate_next_evaluation(self, rule):
        """Calculate the next evaluation time based on frequency"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        if rule.evaluation_frequency == 'hourly':
            return now + timedelta(hours=1)
        elif rule.evaluation_frequency == 'daily':
            return now + timedelta(days=1)
        elif rule.evaluation_frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif rule.evaluation_frequency == 'monthly':
            return now + timedelta(days=30)
        
        return now + timedelta(days=1)  # Default to daily


class TenantRestorationView(LoginRequiredMixin, View):
    """View for initiating tenant data restoration"""
    def get(self, request, preservation_id):
        preservation = get_object_or_404(TenantDataPreservation, id=preservation_id)
        return render(request, 'tenants/initiate_restoration.html', {'preservation': preservation})
    
    def post(self, request, preservation_id):
        preservation = get_object_or_404(TenantDataPreservation, id=preservation_id)
        
        # Create a restoration record
        restoration = TenantDataRestoration.objects.create(
            tenant=preservation.tenant,
            preservation_record=preservation,
            description=f'Restoration from {preservation.preservation_type} at {preservation.preservation_date}',
            initiated_by=request.user
        )
        
        # In a real implementation, this would trigger the actual restoration process
        # For now, we'll just update the status
        restoration.status = 'completed'
        restoration.completed_at = timezone.now()
        restoration.completed_by = request.user
        restoration.total_records = 100  # Placeholder
        restoration.restored_records = 100  # Placeholder
        restoration.progress_percentage = 10.0
        restoration.save()
        
        messages.success(request, f'Data restoration completed for {preservation.tenant.name}.')
        return redirect('tenants:data-restoration')
    

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, ListView, View, UpdateView, FormView, DetailView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Tenant, Setting, SettingGroup, SettingType, TenantSettings, TenantCloneHistory, WhiteLabelSettings, TenantUsageMetric, TenantFeatureEntitlement, OverageAlert, NotificationTemplate, Notification, AlertThreshold, TenantDataIsolationAudit, TenantDataIsolationViolation, DataResidencySettings, TenantDataPreservation, TenantDataRestoration, TenantDataPreservationStrategy, TenantDataPreservationSchedule, AutomatedTenantLifecycleRule, AutomatedTenantLifecycleEvent, TenantLifecycleWorkflow, TenantLifecycleWorkflowExecution, TenantSuspensionWorkflow, TenantTerminationWorkflow
from .forms import (
    TenantSignupForm, TenantBrandingForm, TenantDomainForm, TenantSettingsForm, 
    FeatureToggleForm, SettingForm, SettingGroupForm, SettingTypeForm,
    OnboardingTenantInfoForm, OnboardingBrandingForm, TenantExportForm,
      TenantImportForm, TenantCloneForm, WhiteLabelSettingsForm, 
      TenantUsageMetricForm, TenantUsageReportForm, TenantFeatureEntitlementForm, 
      FeatureAccessForm, BulkFeatureEntitlementForm, OverageAlertForm, NotificationForm, AlertThresholdForm, 
      TenantDataIsolationAuditForm, TenantDataIsolationViolationForm, DataIsolationAuditFilterForm, DataResidencySettingsForm
)
from .utils import track_usage, get_current_usage, get_usage_trend, check_usage_limits, generate_usage_report, check_feature_access, enforce_feature_access, get_accessible_features, perform_data_isolation_audit
import datetime

from billing.models import Plan, Subscription
from core.models import User
from accounts.models import Role
from django.contrib.messages.views import SuccessMessageMixin # Import SuccessMessageMixin
import json
from django.http import JsonResponse
from django.shortcuts import redirect
import django.db.models as models


class TenantUsageMetricListView(LoginRequiredMixin, ListView):
    """View for displaying tenant usage metrics"""
    model = TenantUsageMetric
    template_name = 'tenants/usage_metric_list.html'
    context_object_name = 'usage_metrics'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter metrics for the current user's tenant
        return TenantUsageMetric.objects.filter(tenant=self.request.user.tenant).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Usage Metrics',
            'subtitle': 'Track your tenant usage metrics',
        })
        return context


class TenantUsageMetricCreateView(LoginRequiredMixin, CreateView):
    """View for creating new usage metrics"""
    model = TenantUsageMetric
    form_class = TenantUsageMetricForm
    template_name = 'tenants/usage_metric_form.html'
    success_url = reverse_lazy('tenants:usage_metric_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        # Set the tenant to the current user's tenant
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f'Usage metric "{form.instance.metric_type}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Usage Metric',
            'subtitle': 'Add a new usage metric for your tenant',
            'action': 'create'
        })
        return context


class TenantUsageMetricUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating existing usage metrics"""
    model = TenantUsageMetric
    form_class = TenantUsageMetricForm
    template_name = 'tenants/usage_metric_form.html'
    success_url = reverse_lazy('tenants:usage_metric_list')
    
    def get_queryset(self):
        return TenantUsageMetric.objects.filter(tenant=self.request.user.tenant)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'Usage metric "{form.instance.metric_type}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Usage Metric',
            'subtitle': 'Modify the usage metric',
            'action': 'update'
        })
        return context


class TenantUsageMetricDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting usage metrics"""
    model = TenantUsageMetric
    template_name = 'tenants/usage_metric_confirm_delete.html'
    success_url = reverse_lazy('tenants:usage_metric_list')
    
    def get_queryset(self):
        return TenantUsageMetric.objects.filter(tenant=self.request.user.tenant)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Usage metric "{self.get_object().metric_type}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TenantDataIsolationViolationUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating data isolation violations"""
    model = TenantDataIsolationViolation
    form_class = TenantDataIsolationViolationForm
    template_name = 'tenants/data_isolation_violation_form.html'
    success_url = reverse_lazy('tenants:data_isolation_violations')
    
    def get_queryset(self):
        return TenantDataIsolationViolation.objects.filter(audit__tenant=self.request.user.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, f'Data isolation violation for {form.instance.model_name} updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Data Isolation Violation',
            'subtitle': 'Modify the violation record',
            'action': 'update'
        })
        return context


class OverageAlertCreateView(LoginRequiredMixin, CreateView):
    """View for creating overage alerts"""
    model = OverageAlert
    form_class = OverageAlertForm
    template_name = 'tenants/overage_alert_form.html'
    success_url = reverse_lazy('tenants:overage_alerts')
    
    def form_valid(self, form):
        # Set the tenant to the current user's tenant
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f'Overage alert for "{form.instance.metric_type}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Overage Alert',
            'subtitle': 'Set up a new overage alert',
            'action': 'create'
        })
        return context


class OverageAlertUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating overage alerts"""
    model = OverageAlert
    form_class = OverageAlertForm
    template_name = 'tenants/overage_alert_form.html'
    success_url = reverse_lazy('tenants:overage_alerts')
    
    def get_queryset(self):
        return OverageAlert.objects.filter(tenant=self.request.user.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, f'Overage alert for "{form.instance.metric_type}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Overage Alert',
            'subtitle': 'Modify the overage alert',
            'action': 'update'
        })
        return context


class NotificationCreateView(LoginRequiredMixin, CreateView):
    """View for creating notifications"""
    model = Notification
    form_class = NotificationForm
    template_name = 'tenants/notification_form.html'
    success_url = reverse_lazy('tenants:notifications')
    
    def form_valid(self, form):
        # Set the tenant to the current user's tenant
        form.instance.tenant = self.request.user.tenant
        form.instance.user = self.request.user  # Set to current user by default
        messages.success(self.request, f'Notification "{form.instance.title}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Notification',
            'subtitle': 'Send a new notification',
            'action': 'create'
        })
        return context


class NotificationUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating notifications"""
    model = Notification
    form_class = NotificationForm
    template_name = 'tenants/notification_form.html'
    success_url = reverse_lazy('tenants:notifications')
    
    def get_queryset(self):
        return Notification.objects.filter(tenant=self.request.user.tenant, user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'Notification "{form.instance.title}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update Notification',
            'subtitle': 'Modify the notification',
            'action': 'update'
        })
        return context



# Tenant Member Views

class TenantMemberListView(LoginRequiredMixin, ObjectPermissionRequiredMixin, ListView):
    model = TenantMember
    template_name = 'tenants/member_list.html'
    context_object_name = 'members'
    required_permission = 'tenants.view_tenantmember'

    def get_queryset(self):
        # ObjectPermissionRequiredMixin handles the queryset filtering automatically
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Organization Members',
            'subtitle': 'Manage your team members and their roles'
        })
        return context


class TenantMemberCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = TenantMember
    form_class = TenantMemberForm
    template_name = 'tenants/member_form.html'
    success_url = reverse_lazy('tenants:member_list')
    success_message = "Member added successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Add Member',
            'subtitle': 'Add a new team member to your organization',
            'action': 'create'
        })
        return context


class TenantMemberUpdateView(LoginRequiredMixin, ObjectPermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = TenantMember
    form_class = TenantMemberForm
    template_name = 'tenants/member_form.html'
    success_url = reverse_lazy('tenants:member_list')
    success_message = "Member updated successfully."
    permission_action = 'change'
    required_permission = 'tenants.change_tenantmember'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Update {self.object.user.email}',
            'subtitle': 'Modify team member details',
            'action': 'update'
        })
        return context


class TenantMemberDeleteView(LoginRequiredMixin, ObjectPermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = TenantMember
    template_name = 'tenants/member_confirm_delete.html'
    success_url = reverse_lazy('tenants:member_list')
    success_message = "Member deleted successfully."
    permission_action = 'delete'
    required_permission = 'tenants.delete_tenantmember'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Delete Member',
            'subtitle': f'Are you sure you want to delete {self.object.user.email}?'
        })
        return context

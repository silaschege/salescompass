from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from .models import User, Role
from .admin_forms import UserCreationForm, UserUpdateForm, BulkUserUpdateForm, UserInvitationForm
from tenants.models import Tenant
from django.core.paginator import Paginator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class UserManagementDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'accounts/admin/user_management_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['tenants_count'] = Tenant.objects.count()
        context['recent_users'] = User.objects.all().order_by('-date_joined')[:10]
        return context


class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('tenant', 'role')
        
        # Apply filters
        search = self.request.GET.get('search')
        tenant_id = self.request.GET.get('tenant_id')
        role_id = self.request.GET.get('role_id')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        if is_active is not None:
            if is_active == 'active':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        context['roles'] = Role.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        context['selected_role'] = self.request.GET.get('role_id', '')
        context['selected_status'] = self.request.GET.get('is_active', '')
        return context


class UserCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'accounts/admin/user_form.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        # Set default tenant if not provided
        if not user.tenant_id and form.cleaned_data.get('tenant'):
            user.tenant = form.cleaned_data['tenant']
        user.save()
        messages.success(self.request, f"User '{user.email}' created successfully.")
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/admin/user_form.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    pk_url_kwarg = 'user_id'
    
    def form_valid(self, form):
        messages.success(self.request, f"User '{form.instance.email}' updated successfully.")
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/admin/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    pk_url_kwarg = 'user_id'
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(request, f"User '{user.email}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class UserBulkOperationsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'accounts/admin/user_bulk_operations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        context['roles'] = Role.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            messages.error(request, "No users selected.")
            return redirect('accounts:user_bulk_operations')
        
        users = User.objects.filter(id__in=user_ids)
        
        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f"Activated {users.count()} users.")
        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f"Deactivated {users.count()} users.")
        elif action == 'delete':
            users.delete()
            messages.success(request, f"Deleted {len(user_ids)} users.")
        elif action == 'change_tenant':
            tenant_id = request.POST.get('tenant_id')
            if tenant_id:
                tenant = Tenant.objects.get(id=tenant_id)
                users.update(tenant=tenant)
                messages.success(request, f"Moved {users.count()} users to tenant '{tenant.name}'.")
        elif action == 'change_role':
            role_id = request.POST.get('role_id')
            if role_id:
                role = Role.objects.get(id=role_id)
                users.update(role=role)
                messages.success(request, f"Updated role for {users.count()} users to '{role.name}'.")
        
        return redirect('accounts:user_bulk_operations')


class UserActivityView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin/user_activity.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        # This would typically connect to audit logs to show user activity
        # For now, we'll just return users with last login info
        return User.objects.exclude(last_login=None).order_by('-last_login')


class UserRoleManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'accounts/admin/user_role_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Role.objects.all()
        context['tenants'] = Tenant.objects.all()
        return context


class UserAccessReviewView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin/user_access_review.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        # Users that haven't logged in for 90 days
        from django.utils import timezone
        from datetime import timedelta
        ninety_days_ago = timezone.now() - timedelta(days=90)
        return User.objects.filter(
            Q(last_login__isnull=True) | Q(last_login__lt=ninety_days_ago)
        ).order_by('-last_login')


class MFAManagementView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin/mfa_management.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        # Filter users based on MFA status
        mfa_status = self.request.GET.get('mfa_status', 'all')
        queryset = User.objects.all()
        
        if mfa_status == 'enabled':
            queryset = queryset.filter(mfa_enabled=True)
        elif mfa_status == 'disabled':
            queryset = queryset.filter(mfa_enabled=False)
        
        return queryset.order_by('email')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mfa_status'] = self.request.GET.get('mfa_status', 'all')
        return context


class UserAccessCertificationView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'accounts/admin/user_access_certification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This would typically show access certifications requiring review
        context['pending_certifications'] = []
        return context

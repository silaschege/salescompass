from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from .controller import UnifiedAccessController
from .models import AccessControl, TenantAccessControl, RoleAccessControl, UserAccessControl
from .forms import AccessControlDefinitionForm, TenantAccessAssignmentForm
from tenants.models import Tenant
from django.db.models import Q
class SecureViewMixin:
    """
    Enhanced mixin for securing views with unified access control
    """
    required_access = None  # Set in subclass
    access_action = 'access'  # Default action
    
    def dispatch(self, request, *args, **kwargs):
        if not self.required_access:
            return super().dispatch(request, *args, **kwargs)
        
        if not UnifiedAccessController.has_access(
            request.user, 
            self.required_access, 
            self.access_action
        ):
            raise PermissionDenied("You don't have access to this resource")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add access control utilities to context
        if hasattr(self, 'required_access'):
            context['current_resource_access'] = UnifiedAccessController.has_access(
                self.request.user, self.required_access, self.access_action
            )
        
        # Add general access utilities
        context['can_access'] = lambda resource_key, action='access': UnifiedAccessController.has_access(
            self.request.user, resource_key, action
        )
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class DashboardView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'access_control/dashboard.html'
    required_access = 'access_control.dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import User
        from tenants.models import Tenant
        from access_control.role_models import Role
        
        # Get system stats
        context['stats'] = {
            'definitions': AccessControl.objects.count(),
            'tenants': Tenant.objects.count(),
            'roles': Role.objects.count(),
            'users': User.objects.count(),
        }
        
        # Get available apps for user
        available_resources = UnifiedAccessController.get_available_resources(
            self.request.user
        )
        
        context.update({
            'available_resources': available_resources,
            'user_permissions': UnifiedAccessController.get_user_permissions_summary(self.request.user)
        })
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class ManageAccessView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for managing Access Control Definitions (Master List)
    """
    template_name = 'access_control/manage_access.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search query
        query = self.request.GET.get('q', '')
        
        # Get master definitions
        access_controls = AccessControl.objects.all().order_by('name')
        if query:
            access_controls = access_controls.filter(
                Q(name__icontains=query) | 
                Q(key__icontains=query)
            )
        
        # Get tenant assignment stats
        tenants = Tenant.objects.annotate(
            access_count=Count('access_controls')
        ).order_by('name')
        if query:
            tenants = tenants.filter(name__icontains=query)

        from access_control.role_models import Role
        from core.models import User
        
        # Get role assignment stats
        roles = Role.objects.annotate(
            access_count=Count('permissions')
        ).order_by('name')
        if query:
            roles = roles.filter(name__icontains=query)
        
        # Get user assignment stats
        users = User.objects.annotate(
            access_count=Count('access_controls')
        ).order_by('email')
        if query:
            users = users.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        context.update({
            'access_controls': access_controls,
            'tenants': tenants,
            'roles': roles,
            'users': users,
            'search_query': query,
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class TenantAccessDetailView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for managing access for a specific tenant (Assignments)
    """
    template_name = 'access_control/tenant_access_detail.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = kwargs.get('tenant_id')
        
        tenant = get_object_or_404(Tenant, pk=tenant_id)
        # Get assignments for this tenant
        assignments = TenantAccessControl.objects.filter(tenant=tenant).select_related('access_control').order_by('access_control__name')
        
        context.update({
            'tenant': tenant,
            'assignments': assignments,
            'tenant_name': tenant.name,
            'form': TenantAccessAssignmentForm(initial={'tenant': tenant}), # Pre-fill tenant for modal
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class CreateAccessControlView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    Create a new Access Control Definition
    """
    template_name = 'access_control/create_access.html'
    required_access = 'access_control.create'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AccessControlDefinitionForm()
        context['action'] = 'Create Definition'
        return context
    
    def post(self, request, *args, **kwargs):
        form = AccessControlDefinitionForm(request.POST)
        if form.is_valid():
            access_control = form.save()
            messages.success(request, f'Access Control "{access_control.name}" defined successfully.')
            return redirect('access_control:manage_access')
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)

@method_decorator(staff_member_required, name='dispatch')
class EditAccessControlView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    Edit Access Control Definition
    """
    template_name = 'access_control/edit_access.html'
    required_access = 'access_control.edit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        access_control = get_object_or_404(AccessControl, pk=kwargs['pk'])
        context['form'] = AccessControlDefinitionForm(instance=access_control)
        context['access_control'] = access_control
        context['action'] = 'Edit Definition'
        return context
    
    def post(self, request, *args, **kwargs):
        access_control = get_object_or_404(AccessControl, pk=kwargs['pk'])
        form = AccessControlDefinitionForm(request.POST, instance=access_control)
        if form.is_valid():
            form.save()
            messages.success(request, f'Access Control "{access_control.name}" updated successfully.')
            return redirect('access_control:manage_access')
        return self.render_to_response(self.get_context_data(form=form))

@method_decorator(staff_member_required, name='dispatch')
class DeleteAccessControlView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'access_control/delete_access.html'
    required_access = 'access_control.delete'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        access_control = get_object_or_404(AccessControl, pk=kwargs['pk'])
        context['access_control'] = access_control
        return context
    
    def post(self, request, *args, **kwargs):
        access_control = get_object_or_404(AccessControl, pk=kwargs['pk'])
        access_control_name = access_control.name
        access_control.delete()
        messages.success(request, f'Access control "{access_control_name}" deleted successfully.')
        return redirect('access_control:manage_access')

# NEW: Assign Access to Tenant
@method_decorator(staff_member_required, name='dispatch')
class AssignTenantAccessView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    Assign a predefined Access Control to a Tenant
    """
    template_name = 'access_control/create_access.html' # Reuse create template
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial_data = {}
        tenant_id = self.request.GET.get('tenant')
        if tenant_id:
            initial_data['tenant'] = tenant_id
            target_tenant = get_object_or_404(Tenant, pk=tenant_id)
            context['target_tenant'] = target_tenant
            
            # Get existing assignments to display below form
            context['existing_assignments'] = TenantAccessControl.objects.filter(
                tenant=target_tenant
            ).select_related('access_control').order_by('access_control__name')
            
        context['form'] = TenantAccessAssignmentForm(initial=initial_data)
        context['action'] = 'Assign to Tenant'
        return context
    
    def post(self, request, *args, **kwargs):
        form = TenantAccessAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(
                request, 
                f'Assigned "{assignment.access_control.name}" to {assignment.tenant.name}.'
            )
            return redirect('access_control:tenant_access_detail', tenant_id=assignment.tenant.id)
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return self.render_to_response(context)

@method_decorator(staff_member_required, name='dispatch')
class DeleteTenantAccessView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    Remove a Tenant Access Assignment
    """
    template_name = 'access_control/delete_access_confirm.html' # Optional confirm page
    required_access = 'access_control.manage'

    def post(self, request, *args, **kwargs):
        assignment_id = kwargs.get('pk')
        assignment = get_object_or_404(TenantAccessControl, pk=assignment_id)
        tenant_id = assignment.tenant.pk
        control_name = assignment.access_control.name
        assignment.delete()
        messages.success(request, f'Access control "{control_name}" removed from tenant.')
        return redirect('access_control:tenant_access_detail', tenant_id=tenant_id)


@method_decorator(staff_member_required, name='dispatch')
class BulkDeleteTenantAccessView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    Bulk delete multiple Tenant Access Assignments
    """
    required_access = 'access_control.manage'

    def post(self, request, *args, **kwargs):
        assignment_ids = request.POST.getlist('assignment_ids')
        tenant_id = request.POST.get('tenant_id')
        
        if not assignment_ids:
            messages.warning(request, 'No assignments selected for removal.')
            return redirect('access_control:tenant_access_detail', tenant_id=tenant_id)
        
        # Delete selected assignments
        deleted_count = TenantAccessControl.objects.filter(
            pk__in=assignment_ids,
            tenant_id=tenant_id  # Security: ensure assignments belong to this tenant
        ).delete()[0]
        
        messages.success(request, f'Successfully removed {deleted_count} access control(s) from tenant.')
        return redirect('access_control:tenant_access_detail', tenant_id=tenant_id)

# NEW: API view for dynamic permission checking
class AccessControlAPIView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    required_access = 'access_control.api'
    
    def get(self, request, *args, **kwargs):
        resource_key = request.GET.get('resource')
        action = request.GET.get('action', 'access')
        
        if not resource_key:
            return JsonResponse({'error': 'Resource key is required'}, status=400)
        
        has_access = UnifiedAccessController.has_access(
            request.user, resource_key, action
        )
        
        return JsonResponse({
            'resource': resource_key,
            'action': action,
            'has_access': has_access
        })
    
    def post(self, request, *args, **kwargs):
        import json
        try:
            data = json.loads(request.body)
            resource_key = data.get('resource')
            action = data.get('action', 'access')
            
            if not resource_key:
                return JsonResponse({'error': 'Resource key is required'}, status=400)
            
            has_access = UnifiedAccessController.has_access(
                request.user, resource_key, action
            )
            
            return JsonResponse({
                'resource': resource_key,
                'action': action,
                'has_access': has_access
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class RoleAccessDetailView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for managing access for a specific role (Assignments)
    """
    template_name = 'access_control/role_access_detail.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_id = kwargs.get('role_id')
        from access_control.role_models import Role
        
        role = get_object_or_404(Role, pk=role_id)
        # Get assignments for this role
        assignments = RoleAccessControl.objects.filter(role=role).select_related('access_control').order_by('access_control__name')
        
        context.update({
            'role': role,
            'assignments': assignments,
            'role_name': role.name,
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class UserAccessDetailView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for managing access for a specific user (Assignments)
    """
    template_name = 'access_control/user_access_detail.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        from core.models import User
        
        user = get_object_or_404(User, pk=user_id)
        # Get assignments for this user
        assignments = UserAccessControl.objects.filter(user=user).select_related('access_control').order_by('access_control__name')
        
        context.update({
            'target_user': user,
            'assignments': assignments,
            'user_name': user.email, # User display name
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class TenantAccessListView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for listing all tenants with their access control summary
    """
    template_name = 'access_control/tenant_list.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all tenants with assignment count
        tenants = Tenant.objects.annotate(
            access_count=Count('access_controls')
        ).order_by('name')
        
        context.update({
            'tenants': tenants,
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class UserAccessListView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """
    View for listing all users with their access control summary
    """
    template_name = 'access_control/user_list.html'
    required_access = 'access_control.manage'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import User
        
        # Get all users with assignment count
        users = User.objects.annotate(
            access_count=Count('access_controls')
        ).order_by('email')
        
        context.update({
            'users': users,
        })
        return context
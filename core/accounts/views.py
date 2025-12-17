import json
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView,FormView
from django.http import JsonResponse
# Make sure this import is at the top
from core.object_permissions import AccountObjectPolicy, OBJECT_POLICIES
from core.permissions import ObjectPermissionRequiredMixin
from .models import Contact, OrganizationMember, TeamRole, Territory,RoleAppPermission
from .forms import AccountForm, ContactForm, BulkImportUploadForm, OrganizationMemberForm, TeamRoleForm, TerritoryForm
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction, models
from .utils import parse_accounts_csv
from leads.models import Lead
from opportunities.models import Opportunity
from django.db.models import Q
from core.models import User



class CustomLoginView(LoginView):
    template_name = 'public/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        
        # Superuser -> Admin Dashboard
        if user.is_superuser:
            return reverse_lazy('dashboard:admin_dashboard')
            
        # Role-based redirection
        if user.role:
            role_name = user.role.name.lower()
            if role_name in ['manager', 'tenant admin', 'admin']:
                return reverse_lazy('dashboard:manager_dashboard')
            elif role_name == 'support':
                return reverse_lazy('dashboard:support_dashboard')
        
        # Default -> Cockpit
        return reverse_lazy('dashboard:cockpit')




class AccountListView(ObjectPermissionRequiredMixin, ListView):
    model = User
    template_name = 'accounts/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('team_member')




class AccountDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/account_detail.html'
    context_object_name = 'account'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.object

        # Make sure contacts are available in template
        context['contacts'] = account.contacts.all()
        
        # Get all timeline events
        timeline_events = self.get_timeline_events(account)
        context['timeline_events'] = timeline_events
        
        # Get related leads
        context['account_leads'] = Lead.objects.filter(account=account)
        
        # Get related opportunities  
        context['account_opportunities'] = Opportunity.objects.filter(account=account)
        
        return context

    def get_timeline_events(self, account):
        """Get all timeline events for an account."""
        events = []
        
        # Account creation event
        events.append({
            'event_type': 'account_created',
            'title': f'Account Created: {account.name}',
            'description': f'Account created by {account.owner.email if account.owner else "System"}',
            'created_at': account.created_at,
            'account_id': account.id
        })
        
        # Lead events (both pre-conversion and post-account leads)
        leads = Lead.objects.filter(
            Q(converted_to_account=account) | Q(account=account)
        ).order_by('-created_at')
        
        for lead in leads: 
            if lead.converted_to_account == account:
                # This lead was converted TO this account
                events.append({
                    'event_type': 'lead_converted',
                    'title': f'Lead Converted: {lead.first_name} {lead.last_name}',
                    'description': f'New business lead converted to account with status: {lead.get_status_display()}',
                    'created_at': lead.updated_at,
                    'lead_id': lead.id,
                    'lead_status': lead.status,
                    'account_id': account.id
                })
            elif lead.account == account:
            # This lead is associated WITH this account (existing customer)
                source_display = lead.get_lead_source_display()
                events.append({
                    'event_type': 'lead_created',
                    'title': f'{source_display} Lead: {lead.first_name} {lead.last_name}',
                    'description': f'{source_display.lower()} opportunity for existing customer {lead.company}',
                    'created_at': lead.created_at,
                    'lead_id': lead.id,
                    'lead_status': lead.status,
                    'account_id': account.id
                })
        
        # Opportunity events
        opportunities = Opportunity.objects.filter(account=account).order_by('-created_at')
        for opp in opportunities:
            events.append({
                'event_type': 'opportunity_created',
                'title': f'Opportunity: {opp.name}',
                'description': f'Opportunity worth ${opp.amount} with stage: {opp.stage.name}',
                'created_at': opp.created_at,
                'opportunity_id': opp.id,
                'account_id': account.id
            })
        
        # Sort all events by date (newest first)
        events.sort(key=lambda x: x['created_at'], reverse=True)
        return events


class AccountCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = User
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Account '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class AccountUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = User
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Account '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class AccountDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'delete'

    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        messages.success(request, f"Account '{account.name}' deleted.")
        return super().delete(request, *args, **kwargs)


# === Bulk Import Views ===
class BulkImportUploadView(ObjectPermissionRequiredMixin, FormView):
    template_name = 'bulk_imports/upload.html'
    form_class = BulkImportUploadForm
    permission_action = 'change'
    success_url = reverse_lazy('accounts:bulk_import_map')  # You can also use reverse_lazy

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        
        # Parse and validate
        rows, errors = parse_accounts_csv(csv_file, self.request.user)
        
        if errors:
            for err in errors[:10]:
                messages.error(self.request, err)
            if len(errors) > 10:
                messages.error(self.request, f"... and {len(errors) - 10} more errors.")
            return self.form_invalid(form)

        self.request.session['bulk_import_data'] = rows
        self.request.session['bulk_import_filename'] = csv_file.name
        # return redirect('accounts:bulk_import_map')
        return super().form_valid(form) 


class BulkImportMapView(ObjectPermissionRequiredMixin,TemplateView):
    template_name = 'bulk_imports/map_fields.html'
    permission_action = 'change'

    def get(self, request, *args, **kwargs):
        rows = request.session.get('bulk_import_data')
        if not rows:
            messages.error(request, "No import data found. Please upload a file first.")
            return redirect('accounts:bulk_import_upload')
        
        sample_row = rows[0] if rows else {}
        return render(request, self.template_name, {'sample_row': sample_row})

    def post(self, request, *args, **kwargs):
        return redirect('accounts:bulk_import_preview')


class BulkImportPreviewView(ObjectPermissionRequiredMixin, FormView):
    template_name = 'bulk_imports/preview.html'
    permission_action = 'change'
    success_url = reverse_lazy('accounts:account_list')

    def get(self, request, *args, **kwargs):
        rows = request.session.get('bulk_import_data')
        if not rows:
            messages.error(request, "No data to import.")
            return redirect('accounts:bulk_import_upload')
        
        preview_rows = rows[:5]
        total_count = len(rows)
        return render(request, self.template_name, {
            'preview_rows': preview_rows,
            'total_count': total_count
        })

    def post(self, request, *args, **kwargs):
        rows = request.session.get('bulk_import_data')
        if not rows:
            messages.error(request, "No data to import.")
            return redirect('accounts:bulk_import_upload')

        success_count = 0
        error_count = 0
        errors = []

        try:
            with transaction.atomic():
                for row in rows:
                    try:
                        row['owner_id'] = request.user.id
                        if hasattr(request.user, 'tenant_id'):
                            row['tenant_id'] = request.user.tenant_id
                        User.objects.create(**row)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if error_count <= 10:
                            errors.append(str(e))
                        
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
            return redirect('accounts:bulk_import_upload')

        request.session.pop('bulk_import_data', None)
        request.session.pop('bulk_import_filename', None)

        if error_count:
            messages.warning(request, f"Imported {success_count} accounts, failed {error_count}.")
            for err in errors:
                messages.error(request, f"Error: {err}")
        else:
            messages.success(request, f"Successfully imported {success_count} accounts!")

        # return redirect('accounts:list')
        return super().form_valid(request) 




# === Kanban View ===
class AccountKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'accounts/account_kanban.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = self.get_queryset().select_related('owner')
        context['accounts'] = accounts
        return context

    def get_queryset(self):
        from core.object_permissions import AccountObjectPolicy
        return AccountObjectPolicy.get_viewable_queryset(self.request.user, User.objects.all())


# === AJAX Update Status ===
def update_account_status(request):
    """Update account status via drag-and-drop."""
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        account_id = data.get('account_id')
        new_status = data.get('status')

        if new_status not in dict(User.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)

        # Enforce object-level permission
        account = get_object_or_404(User, id=account_id)
        from core.object_permissions import AccountObjectPolicy
        if not AccountObjectPolicy.can_change(request.user, account):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        account.status = new_status
        account.save(update_fields=['status'])

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class ContactListView(ObjectPermissionRequiredMixin, ListView):
    """
    List all contacts with filtering and search capabilities.
    """
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 25
    permission_action = 'view'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('account')
        
        # Filter by account if specified
        account_id = self.request.GET.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(role__icontains=search)
            )
        
        # Filter by ESG influence
        esg_influence = self.request.GET.get('esg_influence')
        if esg_influence:
            queryset = queryset.filter(esg_influence=esg_influence)
        
        # Filter by communication preference
        comm_pref = self.request.GET.get('communication_preference')
        if comm_pref:
            queryset = queryset.filter(communication_preference=comm_pref)
        
        return queryset.order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['esg_influence_choices'] = Contact._meta.get_field('esg_influence').choices
        context['comm_pref_choices'] = Contact.COMM_PREF_CHOICES
        context['search_term'] = self.request.GET.get('search', '')
        context['selected_account'] = self.request.GET.get('account_id', '')
        
        # Get accounts for filter dropdown
        if self.request.user.is_authenticated:
            from core.object_permissions import AccountObjectPolicy
            context['filter_accounts'] = AccountObjectPolicy.get_viewable_queryset(
                self.request.user, 
                User.objects.all()
            ).order_by('name')
        else:
            context['filter_accounts'] = User.objects.none()
            
        return context


class ContactDetailView(ObjectPermissionRequiredMixin, DetailView):
    """
    Display detailed contact information.
    """
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related contacts from the same account
        context['account_contacts'] = Contact.objects.filter(
            account=self.object.account
        ).exclude(id=self.object.id)
        return context


class ContactCreateView(ObjectPermissionRequiredMixin, CreateView):
    """
    Create a new contact.
    """
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    permission_action = 'change'

    def get_success_url(self):
        return reverse_lazy('accounts:contact_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Set account from URL parameter if provided
        account_id = self.request.GET.get('account_id')
        if account_id:
            kwargs['initial'] = {'account': account_id}
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Contact '{form.instance.first_name} {form.instance.last_name}' created successfully!")
        return super().form_valid(form)


class ContactUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    """
    Update an existing contact.
    """
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    permission_action = 'change'

    def get_success_url(self):
        return reverse_lazy('accounts:contact_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Contact '{form.instance.first_name} {form.instance.last_name}' updated successfully!")
        return super().form_valid(form)


class ContactDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    """
    Delete a contact.
    """
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    permission_action = 'delete'

    def get_success_url(self):
        return reverse_lazy('accounts:contact_list')

    def delete(self, request, *args, **kwargs):
        contact = self.get_object()
        messages.success(request, f"Contact '{contact.first_name} {contact.last_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


class AccountContactListView(ContactListView):
    """
    List contacts for a specific account.
    """
    template_name = 'contacts/account_contact_list.html'

    def get_queryset(self):
        account = get_object_or_404(User, pk=self.kwargs['account_pk'])
        return Contact.objects.filter(account=account).select_related('account')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = get_object_or_404(User, pk=self.kwargs['account_pk'])
        return context



# === Organization Member Views ===
class OrganizationMemberListView(ObjectPermissionRequiredMixin, ListView):
    model = OrganizationMember
    template_name = 'accounts/member_list.html'
    context_object_name = 'team_members'
    permission_action = 'view'

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
             return qs.filter(tenant=self.request.user.tenant)
        return qs.none()

class OrganizationMemberCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = OrganizationMember
    form_class = OrganizationMemberForm
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class OrganizationMemberDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = OrganizationMember
    template_name = 'accounts/member_detail.html'
    context_object_name = 'member'
    permission_action = 'view'

class OrganizationMemberUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = OrganizationMember
    form_class = OrganizationMemberForm
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

class OrganizationMemberDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = OrganizationMember
    template_name = 'accounts/member_confirm_delete.html'
    success_url = reverse_lazy('accounts:member_list')
    permission_action = 'delete'


# === Team Role Views ===
class TeamRoleListView(ObjectPermissionRequiredMixin, ListView):
    model = TeamRole
    template_name = 'accounts/role_list.html'
    context_object_name = 'roles'
    permission_action = 'view'

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
             return qs.filter(tenant=self.request.user.tenant)
        return qs.none()

class TeamRoleCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = TeamRole
    form_class = TeamRoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('accounts:role_list')
    permission_action = 'change'

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class TeamRoleUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = TeamRole
    form_class = TeamRoleForm
    template_name = 'accounts/role_form.html'
    success_url = reverse_lazy('accounts:role_list')
    permission_action = 'change'

class TeamRoleDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = TeamRole
    template_name = 'accounts/role_confirm_delete.html'
    success_url = reverse_lazy('accounts:role_list')
    permission_action = 'delete'


# === Territory Views ===
class TerritoryListView(ObjectPermissionRequiredMixin, ListView):
    model = Territory
    template_name = 'accounts/territory_list.html'
    context_object_name = 'territories'
    permission_action = 'view'

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
             return qs.filter(tenant=self.request.user.tenant)
        return qs.none()

class TerritoryCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Territory
    form_class = TerritoryForm
    template_name = 'accounts/territory_form.html'
    success_url = reverse_lazy('accounts:territory_list')
    permission_action = 'change'

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class TerritoryUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Territory
    form_class = TerritoryForm
    template_name = 'accounts/territory_form.html'
    success_url = reverse_lazy('accounts:territory_list')
    permission_action = 'change'

class TerritoryDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Territory
    template_name = 'accounts/territory_confirm_delete.html'
    success_url = reverse_lazy('accounts:territory_list')
    permission_action = 'delete'

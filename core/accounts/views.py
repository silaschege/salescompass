
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.http import JsonResponse
from core.object_permissions import AccountObjectPolicy, OBJECT_POLICIES
from core.permissions import ObjectPermissionRequiredMixin
from .models import Contact, RoleAppPermission
from .forms import AccountForm, ContactForm, BulkImportUploadForm
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction, models

from .utils import parse_accounts_csv, get_account_kpi_data, get_accounts_summary, get_top_performing_accounts, calculate_account_health, calculate_account_engagement_score, analyze_account_revenue, get_account_health_history, get_quarter_date_range, calculate_revenue_trend, calculate_win_rate, get_account_analytics_data

from leads.models import Lead
from opportunities.models import Opportunity
from cases.models import Case
from engagement.models import EngagementEvent
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
import json
from core.models import User
from .models import *
class CustomLoginView(LoginView):
    template_name = 'public/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        
        # Superuser -> Admin Dashboard
        if user.is_superuser:
            return reverse_lazy('core:app_selection')
            
        # Role-based redirection
        if user.role:
            role_name = user.role.name.lower()
            if role_name in ['manager', 'tenant admin', 'admin']:
                return reverse_lazy('core:app_selection')
            elif role_name == 'support':
                return reverse_lazy('core:app_selection')
        
        # Default -> Cockpit
        return reverse_lazy('core:app_selection')



class AccountListView(ObjectPermissionRequiredMixin, ListView):
    model = Account
    template_name = 'accounts/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('owner', 'tenant').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['industry_choices'] = Account.INDUSTRY_CHOICES
        context['status_choices'] = Account.STATUS_CHOICES
        context['tier_choices'] = Account.TIER_CHOICES
        context['esg_choices'] = Account.ESG_CHOICES
        return context



class AccountDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Account
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
        
        # Add account statistics
        context['total_contacts'] = account.contacts.count()
        context['total_leads'] = Lead.objects.filter(account=account).count()
        context['total_opportunities'] = Opportunity.objects.filter(account=account).count()
        context['total_cases'] = Case.objects.filter(account=account).count()
        
        return context

    def get_timeline_events(self, account):
        """Get timeline events for the account"""
        events = []
        
        # Get recent events from various models
        events.extend(self._get_model_events(Lead, account, 'created_at', 'Lead Created'))
        events.extend(self._get_model_events(Opportunity, account, 'created_at', 'Opportunity Created'))
        events.extend(self._get_model_events(Case, account, 'created_at', 'Case Created'))
        events.extend(self._get_model_events(EngagementEvent, account, 'created_at', 'Engagement'))
        
        # Sort by date
        events.sort(key=lambda x: x['date'], reverse=True)
        return events

    def _get_model_events(self, model, account, date_field, event_type):
        """Helper method to get events from a model"""
        from engagement.models import EngagementEvent
        
        if model == EngagementEvent:
            items = model.objects.filter(account_company=account)
        else:
            items = model.objects.filter(account=account)
            
        return [{
            'date': getattr(item, date_field),
            'type': event_type,
            'description': str(item)
        } for item in items]





class AccountCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Account '{form.instance.account_name}' created successfully!")
        return super().form_valid(form)


class AccountUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/account_form.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Account '{form.instance.account_name}' updated successfully!")
        return super().form_valid(form)



class AccountDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Account
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('accounts:account_list')
    permission_action = 'delete'

    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        messages.success(request, f"Account '{account.account_name}' deleted.")
        return super().delete(request, *args, **kwargs)



class AccountAnalyticsView(ObjectPermissionRequiredMixin, TemplateView):
    """
    View for displaying account analytics and KPIs.
    """
    template_name = 'accounts/account_analytics.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = get_object_or_404(Account, pk=kwargs['account_pk'])
        
        # Get account analytics data
        analytics_data = get_account_analytics_data(account)
        
        context['account'] = account
        context['analytics_data'] = analytics_data
        
        return context





class AccountsDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    """
    View for displaying overall accounts dashboard.
    """
    template_name = 'accounts/accounts_dashboard.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get accounts summary
        if self.request.user.tenant_id:
            accounts_summary = get_accounts_summary(tenant_id=self.request.user.tenant_id)
        else:
            accounts_summary = get_accounts_summary()
            
        # Get top performing accounts
        top_accounts = get_top_performing_accounts(limit=5)
        
        context['accounts_summary'] = accounts_summary
        context['top_accounts'] = top_accounts
        context['industry_choices'] = Account.INDUSTRY_CHOICES
        context['esg_choices'] = Account.ESG_CHOICES
        
        return context





# === Bulk Import Views ===
class BulkImportUploadView(ObjectPermissionRequiredMixin, FormView):
    template_name = 'bulk_imports/upload.html'
    form_class = BulkImportUploadForm
    permission_action = 'change'
    success_url = reverse_lazy('accounts:bulk_import_map')

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
                        Account.objects.create(**row)
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

        return super().form_valid(request) 




# === Kanban View ===


class AccountKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'accounts/account_kanban.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = self.get_queryset()
        context['accounts'] = accounts
        return context

    def get_queryset(self):
        from core.object_permissions import AccountObjectPolicy
        return AccountObjectPolicy.get_viewable_queryset(self.request.user, Account.objects.all())

# === AJAX Update Status ===

def update_account_status(request):
    """Update account status via drag-and-drop."""
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        account_id = data.get('account_id')
        new_status = data.get('status')

        if new_status not in dict(Account.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)

        # Enforce object-level permission
        account = get_object_or_404(Account, id=account_id)
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
        context['comm_pref_choices'] = Contact._meta.get_field('communication_preference').choices
        context['search_term'] = self.request.GET.get('search', '')
        context['selected_account'] = self.request.GET.get('account_id', '')
        
        # Get accounts for filter dropdown
        if self.request.user.is_authenticated:
            from core.object_permissions import AccountObjectPolicy
            context['filter_accounts'] = AccountObjectPolicy.get_viewable_queryset(
                self.request.user, 
                Account.objects.all()  # Fixed: was User.objects.all()
            ).order_by('account_name')  # Fixed: was 'name'
        else:
            context['filter_accounts'] = Account.objects.none()
            
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
        account = get_object_or_404(Account, pk=self.kwargs['account_pk'])
        return Contact.objects.filter(account=account).select_related('account')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = get_object_or_404(Account, pk=self.kwargs['account_pk'])
        return context



def check_account_health(request, account_id):
    """API endpoint to check account health score"""
    try:
        account = Account.objects.get(id=account_id)
        return JsonResponse({
            'account_id': account_id,
            'health_score': getattr(account, 'health_score', 0),
            'status': account.status,
            'last_updated': getattr(account, 'updated_at', None).isoformat() if hasattr(account, 'updated_at') and account.updated_at else None,
            'health_history': get_account_health_history(account)
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def trigger_account_health_update(request):
    """API endpoint to trigger account health update"""
    try:
        account_ids = request.POST.getlist('account_ids')
        if not account_ids:
            return JsonResponse({'error': 'No account IDs provided'}, status=400)
        
        # Use Celery task to update account health asynchronously
        for account_id in account_ids:
            update_account_health.delay(int(account_id))
        
        return JsonResponse({
            'status': 'queued',
            'accounts_queued': len(account_ids)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def get_engagement_trend(request, account_id):
    """API endpoint to get engagement trend data"""
    try:
        account = Account.objects.get(id=account_id)
        days = int(request.GET.get('days', 30))
        
        trend_data = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            count = EngagementEvent.objects.filter(
                account=account,
                created_at__date=date
            ).count()
            
            trend_data.append({
                'date': date.isoformat(),
                'engagement_count': count
            })
        
        trend_data.reverse()
        
        return JsonResponse({
            'account_id': account_id,
            'engagement_trend': trend_data
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def get_revenue_analysis(request, account_id):
    """API endpoint to get revenue analysis data"""
    try:
        account = Account.objects.get(id=account_id)
        revenue_data = analyze_account_revenue(account)
        
        # Format dates for JSON
        formatted_historical = []
        for item in revenue_data['historical_revenue']:
            formatted_historical.append({
                'quarter': item['quarter'],
                'start_date': item['start_date'].isoformat(),
                'end_date': item['end_date'].isoformat(),
                'value': float(item['value']),
                'deal_count': item['deal_count']
            })
        
        return JsonResponse({
            'account_id': account_id,
            'total_pipeline_value': float(revenue_data['total_pipeline_value']),
            'total_closed_value': float(revenue_data['total_closed_value']),
            'win_rate': revenue_data['win_rate'],
            'historical_revenue': formatted_historical,
            'revenue_trend': revenue_data['revenue_trend']
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_health_history(request, account_id):
    """API endpoint to get account health history"""
    try:
        account = Account.objects.get(id=account_id)
        days = int(request.GET.get('days', 90))
        
        health_history = get_account_health_history(account, days=days)
        
        # Convert dates to ISO format
        formatted_history = []
        for item in health_history:
            formatted_history.append({
                'date': item['date'].isoformat(),
                'score': item['score'],
                'engagement': item['engagement']
            })
        
        return JsonResponse({
            'account_id': account_id,
            'health_history': formatted_history
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
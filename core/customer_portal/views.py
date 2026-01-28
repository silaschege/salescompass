from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from billing.models import Invoice
from cases.models import Case
from proposals.models import Proposal
from accounts.models import Account

class CustomerPortalMixin(LoginRequiredMixin):
    """
    Mixin to ensure the user belongs to at least one Account.
    """
    def get_user_account(self):
        # Taking the first associated account for simplicity in this prototype
        return self.request.user.associated_accounts.first()

    def dispatch(self, request, *args, **kwargs):
        if not self.get_user_account():
            # If no associated account, they shouldn't be here
            return redirect('core:app_selection')
        return super().dispatch(request, *args, **kwargs)

class PortalDashboardView(CustomerPortalMixin, TemplateView):
    template_name = 'customer_portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.get_user_account()
        
        context['account'] = account
        context['recent_invoices'] = Invoice.objects.filter(subscription__user__tenant=account.tenant, subscription__user__associated_accounts=account)[:5]
        # Note: Invoice relationship might need adjustment depending on how billing links to Account.
        # Assuming Invoice -> Subscription -> User (tenant owner) or direct link if added.
        # For prototype, we'll try to find invoices linked to the account's name or direct link if it exists.
        
        context['active_tickets'] = Case.objects.filter(account=account, status='open')
        context['pending_proposals'] = Proposal.objects.filter(opportunity__account=account, status='sent')
        
        return context

class PortalInvoiceListView(CustomerPortalMixin, ListView):
    model = Invoice
    template_name = 'customer_portal/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        account = self.get_user_account()
        # In a real system, Invoice would have a direct FK to Account. 
        # Using a broad filter for the prototype.
        return Invoice.objects.filter(subscription__user__tenant=account.tenant)

class PortalTicketListView(CustomerPortalMixin, ListView):
    model = Case
    template_name = 'customer_portal/ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return Case.objects.filter(account=self.get_user_account())

class PortalProposalListView(CustomerPortalMixin, ListView):
    model = Proposal
    template_name = 'customer_portal/proposal_list.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        return Proposal.objects.filter(opportunity__account=self.get_user_account())

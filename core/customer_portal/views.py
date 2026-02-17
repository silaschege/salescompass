from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from invoicing.models import Invoice
from cases.models import Case
from proposals.models import Proposal
from accounts.models import Account
from ecommerce.models import Order, EcommerceCustomer
from django.urls import reverse_lazy
from django.views.generic import UpdateView

class CustomerPortalMixin(LoginRequiredMixin):
    """
    Mixin to ensure the user belongs to at least one Account.
    """
    def get_user_account(self):
        # 1. Check if user is linked to a CRM Account (B2B)
        account = self.request.user.associated_accounts.first()
        if account:
            return account
            
        # 2. Check if user is an EcommerceCustomer (B2C)
        if hasattr(self.request.user, 'ecommerce_profile'):
            return self.request.user.ecommerce_profile
            
        # 3. Fallback for staff/admins
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Account.objects.first()
            
        return None

    def dispatch(self, request, *args, **kwargs):
        self.account_or_profile = self.get_user_account()
        if not self.account_or_profile and not request.user.is_superuser:
            # If no associated account/profile and not a superuser, they shouldn't be here
            return redirect('core:app_selection')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if isinstance(self.account_or_profile, Account):
            context['account'] = self.account_or_profile
            context['is_b2b'] = True
        else:
            context['ecommerce_profile'] = self.account_or_profile
            context['is_b2b'] = False
        return context

class PortalDashboardView(CustomerPortalMixin, TemplateView):
    template_name = 'customer_portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Context is already populated by mixin's get_context_data regarding account/profile
        
        if context.get('is_b2b'):
            account = context['account']
            context['recent_invoices'] = Invoice.objects.filter(subscription__user__tenant=account.tenant, subscription__user__associated_accounts=account)[:5]
            context['active_tickets'] = Case.objects.filter(account=account, status='open')
            context['pending_proposals'] = Proposal.objects.filter(opportunity__account=account, status='sent')
        else:
            # Ecommerce Dashboard Context
            profile = context['ecommerce_profile']
            context['recent_orders'] = Order.objects.filter(customer=profile).order_by('-created')[:5]
            # Add abandoned cart if any?
            
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

class EcommerceOrderListView(CustomerPortalMixin, ListView):
    model = Order
    template_name = 'customer_portal/ecommerce_order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Ensure we only show orders for the logged-in ecommerce customer
        if hasattr(self.request.user, 'ecommerce_profile'):
            return Order.objects.filter(customer=self.request.user.ecommerce_profile).order_by('-created')
        return Order.objects.none()

class EcommerceOrderDetailView(CustomerPortalMixin, DetailView):
    model = Order
    template_name = 'customer_portal/ecommerce_order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        if hasattr(self.request.user, 'ecommerce_profile'):
            return Order.objects.filter(customer=self.request.user.ecommerce_profile)
        return Order.objects.none()

class EcommerceProfileView(CustomerPortalMixin, UpdateView):
    model = EcommerceCustomer
    template_name = 'customer_portal/ecommerce_profile.html'
    fields = ['phone', 'address']
    success_url = reverse_lazy('customer_portal:profile')

    def get_object(self, queryset=None):
        return self.request.user.ecommerce_profile

from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .models import Commission
from .utils import get_user_performance

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'commissions/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Determine current period (Monthly default)
        start_of_month = today.replace(day=1)
        # Simple end of month calc
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)
            
        performance = get_user_performance(user, start_of_month, end_of_month)
        
        context['performance'] = performance
        context['recent_commissions'] = Commission.objects.filter(user=user).order_by('-date_earned')[:5]
        context['period_start'] = start_of_month
        context['period_end'] = end_of_month
        
        return context

class CommissionListView(LoginRequiredMixin, ListView):
    model = Commission
    template_name = 'commissions/commission_list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        return Commission.objects.filter(user=self.request.user).order_by('-date_earned')

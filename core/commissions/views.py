from django.views import generic
from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView, DetailView, View
from core.views import (
    SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView,
    SalesCompassUpdateView, SalesCompassDeleteView, TenantAwareViewMixin
)
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Avg
from decimal import Decimal
import json
import random
import csv
from django.http import JsonResponse

from .models import Commission, CommissionPayment, Quota, UserCommissionPlan, CommissionPlan, CommissionRule, CommissionPlanTemplate, CommissionDispute,CommissionPlanVersion
from .utils import get_user_performance, calculate_forecast, get_earnings_trend, calculate_pace
from .forms import CommissionPlanForm, CommissionRuleForm
from core.models import User


class CommissionPlanCreateView(SalesCompassCreateView):

    model = CommissionPlan
    form_class = CommissionPlanForm
    template_name = 'commissions/plan_form.html'
    success_url = reverse_lazy('commissions:plan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'create'
        return context
    
    def form_valid(self, form):
        # Tenant assignment matches base class logic but explicit check is fine.
        # SalesCompassCreateView handles tenant_id assignment automatically.
        return super().form_valid(form)


class CommissionPlanUpdateView(SalesCompassUpdateView):
    model = CommissionPlan
    form_class = CommissionPlanForm
    template_name = 'commissions/plan_form.html'
    success_url = reverse_lazy('commissions:plan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'update'
        context['rules'] = self.object.rules.all()
        context['rule_form'] = CommissionRuleForm(plan=self.object)
        
        # Add products and users for the rule form
        from products.models import Product
        from django.contrib.auth.models import User
        context['products'] = Product.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        
        # Add today's date for versioning
        from django.utils import timezone
        context['today'] = timezone.now()
        
        return context






class CommissionRuleCreateView(SalesCompassCreateView):
    model = CommissionRule
    form_class = CommissionRuleForm
    template_name = 'commissions/rule_form.html'

    def form_valid(self, form):
        # Get the plan from the URL parameter
        plan_id = self.kwargs['plan_id']
        plan = get_object_or_404(CommissionPlan, id=plan_id)
        
        # Set the plan for the rule
        form.instance.commission_rule_plan = plan
        # Base class handles tenant, but here we inherit from plan's tenant which is safer
        form.instance.tenant = plan.tenant if hasattr(plan, 'tenant') and plan.tenant else None
        
        response = super().form_valid(form)
        
        # Return JSON response for AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'rule_id': self.object.id,
                'rule_name': str(self.object)
            })
        
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        plan_id = self.kwargs.get('plan_id')
        if plan_id:
            plan = get_object_or_404(CommissionPlan, id=plan_id)
            kwargs['plan'] = plan
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        if plan_id:
            from products.models import Product
            from django.contrib.auth.models import User
            context['products'] = Product.objects.all()
            context['users'] = User.objects.filter(is_active=True)
        return context

    def get_success_url(self):
        plan_id = self.kwargs['plan_id']
        return reverse_lazy('commissions:plan_update', kwargs={'pk': plan_id})




class CommissionRuleUpdateView(SalesCompassUpdateView):
    model = CommissionRule
    form_class = CommissionRuleForm
    template_name = 'commissions/rule_form.html'

    def get_success_url(self):
        plan_id = self.object.commission_rule_plan.id
        return reverse_lazy('commissions:plan_update', kwargs={'pk': plan_id})

    def get_queryset(self):
        # TenantAwareViewMixin handles tenant filtering
        return super().get_queryset()

class CommissionRuleDeleteView(SalesCompassDeleteView):
    model = CommissionRule

    def get_success_url(self):
        plan_id = self.object.commission_rule_plan.id
        return reverse_lazy('commissions:plan_update', kwargs={'pk': plan_id})

    def get_queryset(self):
        # TenantAwareViewMixin handles tenant filtering
        return super().get_queryset()

    def delete(self, request, *args, **kwargs):
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            self.object.delete()
            return JsonResponse({'success': True})
        
        return super().delete(request, *args, **kwargs)


# Try to import WeasyPrint
try:
    from weasyprint import HTML
except ImportError:
    HTML = None

class DashboardView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
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
        forecast = calculate_forecast(user, start_of_month, end_of_month)
        trend = get_earnings_trend(user)
        
        # Pace
        expected_pace = calculate_pace(user, start_of_month, end_of_month, performance['sales'])
        pace_diff = performance['attainment'] - expected_pace
        
        context['performance'] = performance
        context['forecast'] = forecast
        context['trend'] = trend
        context['pace'] = {
            'expected': expected_pace,
            'diff': pace_diff,
            'status': 'ahead' if pace_diff >= 0 else 'behind'
        }
        context['recent_commissions'] = Commission.objects.filter(user=user).order_by('-date_earned')[:5]
        context['period_start'] = start_of_month
        context['period_end'] = end_of_month
        
        return context



class CommissionListView(SalesCompassListView):
    model = Commission
    template_name = 'commissions/commission_list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        # Base implementation plus user filtering
        queryset = super().get_queryset().filter(user=self.request.user).order_by('-date_earned')
        return queryset




class CommissionStatementView(SalesCompassListView):
    model = Commission
    template_name = 'commissions/commission_statement_pdf.html'
    context_object_name = 'commissions'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Base queryset handled by TenantAwareViewMixin if we called super(), but here we start fresh or need to chain.
        # TenantAwareViewMixin does: return self.model.objects.all().filter(tenant_id=...)
        # We can use that:
        queryset = super().get_queryset().filter(user=user).order_by('-date_earned')
        
        # Add filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        
        if start_date:
            queryset = queryset.filter(date_earned__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_earned__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate totals
        commissions = self.get_queryset()
        total_earned = sum([c.amount for c in commissions], Decimal('0.00'))
        
        context['total_earned'] = total_earned
        context['status_choices'] = getattr(Commission, 'STATUS_CHOICES', [])
        
        return context



class CommissionPaymentListView(SalesCompassListView):
    model = CommissionPayment
    template_name = 'commissions/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).order_by('-period_end')


class CommissionPaymentDetailView(SalesCompassDetailView):
    model = CommissionPayment
    template_name = 'commissions/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        # Ensure user can only see their own payments (or add admin logic later)
        return super().get_queryset().filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        payment = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and payment.status == 'calculated':
            payment.status = 'approved'
            payment.save()
        elif action == 'process' and payment.status == 'approved':
             payment.status = 'processing'
             payment.save()
        elif action == 'pay' and payment.status == 'processing':
            payment.status = 'paid'
            payment.paid_date = timezone.now().date()
            payment.save()
            # Also update related commissions to 'paid'
            payment.commissions.update(status='paid')
            
        return redirect('commissions:payment_detail', pk=payment.pk)



class StatementExportView(LoginRequiredMixin, TenantAwareViewMixin, View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(CommissionPayment, pk=pk)
        
        # Security check: User can only access their own statements
        if payment.user != request.user:
            return HttpResponse("Unauthorized", status=403)
        
        # Additional tenant check if applicable
        if hasattr(request.user, 'tenant') and hasattr(payment, 'tenant') and payment.tenant != request.user.tenant:
            return HttpResponse("Unauthorized", status=403)
            
        # Context for the template
        context = {
            'payment': payment,
            'commissions': payment.commissions.all(),
            'user': request.user,
            'company_name': "SalesCompass", # Replace with dynamic setting if available
            'generated_at': timezone.now()
        }
        
        # Render HTML
        html_string = render_to_string('commissions/statement_pdf.html', context)
        
        # Generate PDF
        if HTML:
            html = HTML(string=html_string)
            result = html.write_pdf()
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="commission_statement_{payment.period_end}.pdf"'
            response['Content-Transfer-Encoding'] = 'binary'
            with response as f:
                f.write(result)
            return response
        else:
            return HttpResponse("PDF generation library not installed (WeasyPrint).", status=500)


class QuotaAttainmentView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'commissions/quota_attainment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Get current period quota
        current_quota = Quota.objects.filter(
            user=user,
            period_start__lte=today,
            period_end__gte=today
        ).first()
        
        if current_quota:
            performance = get_user_performance(user, current_quota.period_start, current_quota.period_end)
            attainment_percentage = performance['attainment']
            pace_indicator = self.calculate_pace_indicator(current_quota, performance['sales'])
            
            # Calculate remaining to quota
            remaining_to_quota = current_quota.target_amount - performance['sales']
            if remaining_to_quota < 0:
                remaining_to_quota = 0  # Don't show negative values
            
            context['quota'] = current_quota
            context['performance'] = performance
            context['attainment_percentage'] = attainment_percentage
            context['pace_indicator'] = pace_indicator
            context['pace_status'] = self.get_pace_status(attainment_percentage, current_quota)
            context['remaining_to_quota'] = remaining_to_quota
        else:
            context['quota'] = None
            
        return context
    def calculate_pace_indicator(self, quota, current_sales):
        """Calculate if user is on track to hit quota based on time elapsed"""
        from datetime import timedelta
        start_date = quota.period_start
        end_date = quota.period_end
        total_days = (end_date - start_date).days + 1
        days_elapsed = (timezone.now().date() - start_date).days + 1
        
        # Calculate expected sales pace
        expected_pace = (days_elapsed / total_days) * quota.target_amount
        pace_percentage = (current_sales / expected_pace * 100) if expected_pace > 0 else 0
        
        return pace_percentage
    
    def get_pace_status(self, attainment_percentage, quota):
        """Return status based on attainment vs pace"""
        # Calculate pace
        start_date = quota.period_start
        end_date = quota.period_end
        total_days = (end_date - start_date).days + 1
        days_elapsed = (timezone.now().date() - start_date).days + 1
        
        expected_pace = (days_elapsed / total_days) * 100
        pace_difference = attainment_percentage - expected_pace
        
        if pace_difference >= 10:
            return "ahead"
        elif pace_difference >= -5:
            return "on_track"
        else:
            return "behind"

class WhatIfCalculatorView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'commissions/what_if_calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's current commission plan
        active_plan = UserCommissionPlan.objects.filter(
            user=user,
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).first()
        
        if not active_plan:
            # Check for open-ended plan
            active_plan = UserCommissionPlan.objects.filter(
                user=user,
                start_date__lte=timezone.now().date(),
                end_date__isnull=True
            ).first()
        
        context['active_plan'] = active_plan
        return context



class CommissionPlanListView(SalesCompassListView):
    model = CommissionPlan
    template_name = 'commissions/plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        # Tenant filtering handled by SalesCompassListView
        return super().get_queryset()




class CommissionPlanUpdateView(SalesCompassUpdateView):
    model = CommissionPlan
    form_class = CommissionPlanForm
    template_name = 'commissions/plan_form.html'
    success_url = reverse_lazy('commissions:plan_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'update'
        context['rules'] = self.object.rules.all()
        context['rule_form'] = CommissionRuleForm(plan=self.object)
        
        # Add products and users for the rule form
        from products.models import Product
        from django.contrib.auth.models import User
        context['products'] = Product.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        
        # Add today's date for versioning
        from django.utils import timezone
        context['today'] = timezone.now()
        
        return context








class CommissionPlanTemplateView(SalesCompassListView):
    model = CommissionPlanTemplate
    template_name = 'commissions/plan_templates.html'
    context_object_name = 'templates'

    def get_queryset(self):
        # Only show active templates by default, but allow all via parameter
        queryset = super().get_queryset()
        
        show_all = self.request.GET.get('show_all', 'false').lower() == 'true'
        
        if not show_all:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-is_active', 'name')




class ForecastingView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'commissions/forecasting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get current period data
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)
        
        # Get historical data for variance analysis
        historical_commissions = self.get_historical_commissions(user)
        
        # Calculate forecast
        forecast = calculate_forecast(user, start_of_month, end_of_month)
        
        # Calculate variance
        actual_earned = Commission.objects.filter(
            user=user,
            date_earned__range=[start_of_month, today]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Monte Carlo simulation
        monte_carlo_forecast = self.monte_carlo_simulation(user, start_of_month, end_of_month)
        
        context.update({
            'forecast': forecast,
            'actual_earned': actual_earned,
            'remaining_days': (end_of_month - today).days,
            'historical_data': historical_commissions,
            'monte_carlo_forecast': monte_carlo_forecast,
        })
        
        return context
    
    def get_historical_commissions(self, user):
        """Get historical commission data for variance analysis"""
        # Get data for last 6 months
        commissions = []
        today = timezone.now().date()
        
        for i in range(6):
            month_start = today.replace(day=1) - timezone.timedelta(days=30*i)
            if month_start.month == 1:
                month_end = month_start.replace(year=month_start.year - 1, month=12, day=31)
            else:
                month_end = month_start.replace(month=month_start.month - 1, day=1) - timezone.timedelta(days=1)
                
            monthly_amount = Commission.objects.filter(
                user=user,
                date_earned__year=month_start.year,
                date_earned__month=month_start.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            commissions.append({
                'month': month_start.strftime('%b %Y'),
                'amount': monthly_amount
            })
        
        return commissions
    
    def monte_carlo_simulation(self, user, start_date, end_date):
        """Run Monte Carlo simulation for commission forecast"""
        # Get historical data to estimate probabilities
        from opportunities.models import Opportunity
        historical_wins = Opportunity.objects.filter(
            owner=user,
            stage__is_won=True,
            close_date__gte=start_date - timezone.timedelta(days=365)  # Last year
        ).count()
        
        historical_total = Opportunity.objects.filter(
            owner=user,
            close_date__gte=start_date - timezone.timedelta(days=365)
        ).count()
        
        win_rate = Decimal(historical_wins) / Decimal(historical_total) if historical_total > 0 else Decimal('0.30')
        
        # Get open opportunities for this period
        open_opportunities = Opportunity.objects.filter(
            owner=user,
            stage__is_won=False,
            stage__is_lost=False,
            close_date__range=[start_date, end_date]
        )
        
        # Run simulation (1000 iterations)
        from .utils import calculate_commission
        simulations = []
        for _ in range(1000):
            total_simulated = Decimal('0.00')
            for opp in open_opportunities:
                # Randomly determine if opportunity wins based on historical win rate
                if random.random() < float(win_rate):
                    # Calculate commission if won
                    commission_obj = calculate_commission(opp)
                    if commission_obj:
                        total_simulated += commission_obj.amount
            simulations.append(total_simulated)
        
        # Calculate statistics
        simulations.sort()
        p10 = simulations[int(0.1 * len(simulations))]
        p50 = simulations[int(0.5 * len(simulations))]
        p90 = simulations[int(0.9 * len(simulations))]
        
        return {
            'p10': p10,  # 10% chance to achieve this or less
            'p50': p50,  # 50% chance (median)
            'p90': p90,  # 90% chance to achieve this or less
            'avg': sum(simulations) / len(simulations)
        }


class TeamDashboardView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'commissions/team_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Base query for users in the same tenant
        tenant_users = User.objects.filter(is_active=True)
        if hasattr(user, 'tenant_id') and user.tenant_id:
             tenant_users = tenant_users.filter(tenant_id=user.tenant_id)
        
        # Get team members (users in the same team/department)
        # This assumes some team relationship - you may need to adjust based on your model
        team_members = tenant_users.exclude(id=user.id)[:10]  # Top 10
        
        # Get current period
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)
        
        # Calculate team performance
        team_performance = []
        for member in team_members:
            member_performance = get_user_performance(member, start_of_month, end_of_month)
            team_performance.append({
                'user': member,
                'performance': member_performance
            })
        
        # Add current user's performance
        current_user_performance = get_user_performance(user, start_of_month, end_of_month)
        
        # Create leaderboard
        leaderboard = []
        for u in tenant_users:
            perf = get_user_performance(u, start_of_month, end_of_month)
            if perf['commissions_earned'] > 0:  # Only include users with earnings
                leaderboard.append({
                    'user': u,
                    'earnings': perf['commissions_earned'],
                    'rank': 0  # Will be set after sorting
                })
        
        # Sort by earnings and assign ranks
        leaderboard.sort(key=lambda x: x['earnings'], reverse=True)
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        context.update({
            'team_performance': team_performance,
            'current_user_performance': current_user_performance,
            'leaderboard': leaderboard[:10],  # Top 10
            'current_user_rank': next((i + 1 for i, x in enumerate(leaderboard) if x['user'] == user), None)
        })
        
        return context
    
class PayrollExportView(LoginRequiredMixin, TenantAwareViewMixin, View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        # Get commissions ready for payment
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            # Default to previous month
            from datetime import date
            today = date.today()
            if today.month == 1:
                start_date = date(today.year - 1, 12, 1)
                end_date = date(today.year - 1, 12, 31)
            else:
                start_date = date(today.year, today.month - 1, 1)
                if today.month == 1:
                    end_date = date(today.year - 1, 12, 31)
                else:
                    end_date = date(today.year, today.month, 1) - timezone.timedelta(days=1)
        else:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get commissions for export
        commissions = Commission.objects.filter(
            status='approved',
            date_earned__range=[start_date, end_date],
            payment_record__isnull=True  # Not already paid
        )
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="commissions_export_{start_date}_to_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Employee Name', 'Amount', 'Date Earned', 
            'Opportunity Name', 'Customer', 'Commission Plan'
        ])
        
        for commission in commissions:
            writer.writerow([
                commission.user.id,
                commission.user.get_full_name() or commission.user.username,
                commission.amount,
                commission.date_earned,
                commission.opportunity.opportunity_name,
                commission.opportunity.account.name if commission.opportunity.account else '',
                commission.user.commission_plans.filter(
                    start_date__lte=commission.date_earned,
                    end_date__gte=commission.date_earned
                ).first().assigned_plan.commission_plan_name if commission.user.commission_plans.filter(
                    start_date__lte=commission.date_earned,
                    end_date__gte=commission.date_earned
                ).first() else ''
            ])
        
        return response

class CommissionAPIExportView(LoginRequiredMixin, TenantAwareViewMixin, View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            # Default to previous month
            from datetime import date
            today = date.today()
            if today.month == 1:
                start_date = date(today.year - 1, 12, 1)
                end_date = date(today.year - 1, 12, 31)
            else:
                start_date = date(today.year, today.month - 1, 1)
                if today.month == 1:
                    end_date = date(today.year - 1, 12, 31)
                else:
                    end_date = date(today.year, today.month, 1) - timezone.timedelta(days=1)
        else:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get commissions for export
        from opportunities.models import Opportunity
        commissions = Commission.objects.filter(
            status__in=['approved', 'paid'],
            date_earned__range=[start_date, end_date]
        ).select_related('user', 'opportunity', 'opportunity__account')
        
        # Format data for export
        export_data = []
        for commission in commissions:
            commission_data = {
                'commission_id': commission.commission_id,
                'employee_id': commission.user.id,
                'employee_name': commission.user.get_full_name() or commission.user.username,
                'employee_email': commission.user.email,
                'amount': float(commission.amount),
                'date_earned': commission.date_earned.isoformat(),
                'status': commission.status,
                'opportunity_name': commission.opportunity.opportunity_name,
                'customer_name': commission.opportunity.account.name if commission.opportunity.account else '',
                'commission_plan': commission.user.commission_plans.filter(
                    start_date__lte=commission.date_earned,
                    end_date__gte=commission.date_earned
                ).first().assigned_plan.commission_plan_name if commission.user.commission_plans.filter(
                    start_date__lte=commission.date_earned,
                    end_date__gte=commission.date_earned
                ).first() else ''
            }
            export_data.append(commission_data)
        
        response = HttpResponse(
            json.dumps(export_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="commissions_api_export_{start_date}_to_{end_date}.json"'
        
        return response



class CommissionDisputeCreateView(LoginRequiredMixin, CreateView):
    model = CommissionDispute
    fields = ['reason', 'description']
    template_name = 'commissions/dispute_form.html'

    def form_valid(self, form):
        commission_id = self.kwargs['commission_id']
        commission = get_object_or_404(Commission, id=commission_id)
        
        # Security check: User can only dispute their own commissions
        if commission.user != self.request.user:
            return HttpResponse("Unauthorized", status=403)
        
        form.instance.commission = commission
        form.instance.raised_by = self.request.user
        form.instance.tenant = commission.tenant if hasattr(commission, 'tenant') and commission.tenant else None
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('commissions:statement')







class CommissionPlanVersionListView(LoginRequiredMixin, ListView):
    model = CommissionPlanVersion
    template_name = 'commissions/plan_version_list.html'
    context_object_name = 'versions'

    def get_queryset(self):
        plan_id = self.kwargs['plan_id']
        queryset = CommissionPlanVersion.objects.filter(plan_id=plan_id).order_by('-effective_date')
        
        # Filter by tenant if applicable
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        return queryset




class CommissionPlanVersionDetailView(LoginRequiredMixin, DetailView):
    model = CommissionPlanVersion
    template_name = 'commissions/plan_version_detail.html'
    context_object_name = 'version'

    def get_queryset(self):
        # Filter by tenant if applicable
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        return queryset





class CommissionPlanCreateVersionView(LoginRequiredMixin, CreateView):
    model = CommissionPlanVersion
    fields = ['version_number', 'effective_date', 'description', 'plan_data']
    template_name = 'commissions/plan_version_form.html'

    def form_valid(self, form):
        plan_id = self.kwargs['plan_id']
        plan = get_object_or_404(CommissionPlan, id=plan_id)
        
        # Save the current plan data as JSON
        import json
        from django.forms.models import model_to_dict
        
        # Get the plan and its related rules
        plan_data = model_to_dict(plan)
        plan_data['rules'] = []
        for rule in plan.rules.all():
            plan_data['rules'].append(model_to_dict(rule))
        
        form.instance.plan = plan
        form.instance.plan_data = json.dumps(plan_data, default=str)
        form.instance.tenant = plan.tenant if hasattr(plan, 'tenant') and plan.tenant else None
        form.instance.created_by = self.request.user
        
        return super().form_valid(form)

    def get_success_url(self):
        plan_id = self.kwargs['plan_id']
        return reverse_lazy('commissions:plan_update', kwargs={'pk': plan_id})




from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DetailView, DeleteView


class CommissionPlanVisualBuilderView(LoginRequiredMixin, TemplateView):
    template_name = 'commissions/plan_builder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from products.models import Product
        from django.contrib.auth.models import User
        
        context['products'] = Product.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        
        return context




class CommissionPlanTemplateCreateView(LoginRequiredMixin, CreateView):
    model = CommissionPlanTemplate
    fields = ['name', 'description', 'template_data', 'is_active']
    template_name = 'commissions/plan_template_form.html'
    success_url = reverse_lazy('commissions:plan_templates')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant if hasattr(self.request.user, 'tenant') else None
        return super().form_valid(form)

class CommissionPlanTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = CommissionPlanTemplate
    fields = ['name', 'description', 'template_data', 'is_active']
    template_name = 'commissions/plan_template_form.html'
    success_url = reverse_lazy('commissions:plan_templates')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant if hasattr(self.request.user, 'tenant') else None
        return super().form_valid(form)

class CommissionPlanTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = CommissionPlanTemplate
    template_name = 'commissions/plan_template_confirm_delete.html'
    success_url = reverse_lazy('commissions:plan_templates')






class CommissionPlanCloneView(LoginRequiredMixin, View):
    def post(self, request, pk):
        original_plan = get_object_or_404(CommissionPlan, pk=pk)
        
        # Create new plan copy
        new_plan = CommissionPlan(
            commission_plan_name=f"{original_plan.commission_plan_name} (Copy)",
            commission_plan_description=f"Copy of {original_plan.commission_plan_description}",
            commission_plan_is_active=True,
            basis=original_plan.basis,
            period=original_plan.period,
        )
        
        # Add tenant if applicable
        if hasattr(original_plan, 'tenant') and original_plan.tenant:
            new_plan.tenant = original_plan.tenant
            
        new_plan.save()
        
        # Copy rules
        for rule in original_plan.rules.all():
            new_rule = CommissionRule(
                commission_rule_plan=new_plan,
                product=rule.product,
                product_category=rule.product_category,
                rate_type=rule.rate_type,
                rate_value=rule.rate_value,
                tier_min_amount=rule.tier_min_amount,
                tier_max_amount=rule.tier_max_amount,
                performance_threshold=rule.performance_threshold,
                split_with=rule.split_with,
                split_percentage=rule.split_percentage,
            )
            
            # Add tenant if applicable 
            if hasattr(rule, 'tenant') and rule.tenant:
                new_rule.tenant = rule.tenant
                
            new_rule.save()
        
        return redirect('commissions:plan_update', pk=new_plan.pk)






class CommissionStatementPDFView(LoginRequiredMixin, View):
    """
    Generate and download commission statement as PDF
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get commissions for the user
        queryset = Commission.objects.filter(user=user).order_by('-date_earned')
        
        # Filter by tenant if applicable
        if hasattr(user, 'tenant'):
            queryset = queryset.filter(tenant=user.tenant)
        
        # Add filters if provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status = request.GET.get('status')
        
        if start_date:
            queryset = queryset.filter(date_earned__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_earned__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        
        commissions = queryset
        
        # Calculate totals
        total_earned = sum([c.amount for c in commissions], Decimal('0.00'))
        
        # Context for the template
        context = {
            'commissions': commissions,
            'user': user,
            'total_earned': total_earned,
            'start_date': start_date,
            'end_date': end_date,
            'status': status,
            'company_name': "SalesCompass",  # Replace with dynamic setting if available
            'generated_at': timezone.now()
        }
        
        # Render HTML
        html_string = render_to_string('commissions/statement_pdf.html', context)
        
        # Generate PDF
        if HTML:
            html = HTML(string=html_string)
            result = html.write_pdf()
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="commission_statement_{timezone.now().date()}.pdf"'
            response['Content-Transfer-Encoding'] = 'binary'
            with response as f:
                f.write(result)
            return response
        else:
            return HttpResponse("PDF generation library not installed (WeasyPrint).", status=500)


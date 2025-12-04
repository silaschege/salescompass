from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from .models import FeatureFlag, FeatureTarget
from .utils import calculate_adoption_rate, get_feature_analytics, get_rollout_breakdown


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class FeatureFlagsDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_flags'] = FeatureFlag.objects.count()
        context['active_flags'] = FeatureFlag.objects.filter(is_active=True).count()
        context['disabled_flags'] = FeatureFlag.objects.filter(is_active=False).count()
        context['recent_flags'] = FeatureFlag.objects.all()[:10]
        return context


class FeatureFlagListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = FeatureFlag
    template_name = 'feature_flags/flag_list.html'
    context_object_name = 'flags'
    paginate_by = 20


class FeatureFlagCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = FeatureFlag
    template_name = 'feature_flags/flag_form.html'
    fields = ['key', 'name', 'description', 'is_active', 'rollout_percentage']
    success_url = reverse_lazy('feature_flags:flag_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user.username
        messages.success(self.request, f"Feature flag '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class FeatureFlagUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = FeatureFlag
    template_name = 'feature_flags/flag_form.html'
    fields = ['name', 'description', 'is_active', 'rollout_percentage']
    success_url = reverse_lazy('feature_flags:flag_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Feature flag '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class FeatureFlagDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = FeatureFlag
    template_name = 'feature_flags/flag_confirm_delete.html'
    success_url = reverse_lazy('feature_flags:flag_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Feature flag deleted successfully.")
        return super().delete(request, *args, **kwargs)


class FeatureFlagDetailView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/flag_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flag = get_object_or_404(FeatureFlag, pk=kwargs['pk'])
        context['flag'] = flag
        context['targets'] = flag.targets.all()
        context['analytics'] = get_feature_analytics(flag)
        return context


class ActiveFlagsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = FeatureFlag
    template_name = 'feature_flags/active_flags.html'
    context_object_name = 'flags'
    
    def get_queryset(self):
        return FeatureFlag.objects.filter(is_active=True)


class DisabledFlagsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = FeatureFlag
    template_name = 'feature_flags/disabled_flags.html'
    context_object_name = 'flags'
    
    def get_queryset(self):
        return FeatureFlag.objects.filter(is_active=False)


class PercentageRolloutView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/percentage_rollout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flags'] = FeatureFlag.objects.filter(is_active=True, rollout_percentage__gt=0, rollout_percentage__lt=100)
        return context


class GradualRolloutView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/gradual_rollout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flags'] = FeatureFlag.objects.filter(is_active=True)
        return context


class CanaryReleasesView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/canary_releases.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Canary releases are typically flags with specific targeting
        context['flags'] = FeatureFlag.objects.filter(
            is_active=True
        ).annotate(
            target_count=Count('targets')
        ).filter(target_count__gt=0)
        return context


class TargetingRulesView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/targeting_rules.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = kwargs.get('pk')
        if pk:
            flag = get_object_or_404(FeatureFlag, pk=pk)
            context['flag'] = flag
            context['targets'] = flag.targets.all()
        else:
            context['flags'] = FeatureFlag.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle adding/removing targeting rules
        flag_id = request.POST.get('flag_id')
        target_type = request.POST.get('target_type')
        target_value = request.POST.get('target_value')
        action = request.POST.get('action')
        
        if action == 'add' and flag_id and target_type and target_value:
            flag = get_object_or_404(FeatureFlag, pk=flag_id)
            FeatureTarget.objects.create(
                feature_flag=flag,
                target_type=target_type,
                target_value=target_value
            )
            messages.success(request, "Targeting rule added successfully.")
        elif action == 'remove':
            target_id = request.POST.get('target_id')
            if target_id:
                FeatureTarget.objects.filter(pk=target_id).delete()
                messages.success(request, "Targeting rule removed successfully.")
        
        return redirect('feature_flags:targeting_rules')


class ABTestingView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/ab_testing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # A/B tests are typically flags with 50% rollout or specific variants
        context['ab_tests'] = FeatureFlag.objects.filter(
            is_active=True,
            rollout_percentage__gte=30,
            rollout_percentage__lte=70
        )
        return context


class FeatureAnalyticsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flags = FeatureFlag.objects.all()
        analytics_data = []
        
        for flag in flags:
            analytics_data.append(get_feature_analytics(flag))
        
        context['analytics_data'] = analytics_data
        return context


class AdoptionRatesView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'feature_flags/adoption_rates.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flags = FeatureFlag.objects.filter(is_active=True)
        adoption_data = []
        
        for flag in flags:
            adoption = calculate_adoption_rate(flag)
            adoption_data.append({
                'flag': flag,
                'metrics': adoption
            })
        
        context['adoption_data'] = adoption_data
        return context

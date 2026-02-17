from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant


class FeatureFlag(models.Model):
    """Model for managing feature flags"""
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True, help_text="Unique identifier for the feature flag")
    name = models.CharField(max_length=255, help_text="Display name for the feature flag")
    description = models.TextField(blank=True, help_text="Description of what the feature flag controls")
    is_active = models.BooleanField(default=False, help_text="Whether the feature flag is currently active")
    rollout_percentage = models.FloatField(default=0.0, help_text="Percentage of users to whom the feature is rolled out (0-100)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feature_flags_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enabled_for_all = models.BooleanField(default=False, help_text="Enable for all users regardless of rollout percentage")
    disabled_for_all = models.BooleanField(default=False, help_text="Disable for all users regardless of other settings")
    scheduled_activation = models.DateTimeField(null=True, blank=True, help_text="Automatically activate at this time")
    scheduled_deactivation = models.DateTimeField(null=True, blank=True, help_text="Automatically deactivate at this time")
    prerequisites = models.JSONField(default=list, blank=True, help_text="Other feature flags that must be enabled for this one")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing feature flags")
    notes = models.TextField(blank=True, help_text="Internal notes about the feature flag")
    
    class Meta:
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.key}) - {'Active' if self.is_active else 'Inactive'}"


class FeatureTarget(models.Model):
    """Model for targeting specific users, tenants, or groups for feature flags"""
    id = models.AutoField(primary_key=True)
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='targets')
    target_type = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('tenant', 'Tenant'),
        ('group', 'Group'),
        ('role', 'Role'),
        ('email_domain', 'Email Domain'),
        ('percentage', 'Percentage Rollout'),
    ])
    target_value = models.CharField(max_length=255, help_text="Value to match (e.g., user ID, tenant ID, group name)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Feature Target"
        verbose_name_plural = "Feature Targets"
        unique_together = ['feature_flag', 'target_type', 'target_value']
    
    def __str__(self):
        return f"{self.feature_flag.name} - {self.target_type}: {self.target_value}"

class FeatureFlagRolloutSchedule(models.Model):
    """Model for managing gradual feature rollouts"""
    id = models.AutoField(primary_key=True)
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='rollout_schedules')
    rollout_phase = models.CharField(max_length=50, choices=[
        ('alpha', 'Alpha Testing'),
        ('beta', 'Beta Testing'),
        ('canary', 'Canary Release'),
        ('gradual', 'Gradual Rollout'),
        ('full_release', 'Full Release'),
    ])
    phase_name = models.CharField(max_length=255, help_text="Descriptive name for this rollout phase")
    target_percentage = models.FloatField(help_text="Target percentage for this rollout phase (0-100)")
    start_date = models.DateTimeField(help_text="When to start this rollout phase")
    end_date = models.DateTimeField(help_text="When to end this rollout phase")
    target_tenants = models.ManyToManyField(Tenant, blank=True, related_name='feature_rollout_schedules')
    target_users = models.ManyToManyField(User, blank=True, related_name='feature_rollout_schedules')
    conditions = models.JSONField(default=dict, blank=True, help_text="Conditions for this rollout phase")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rollout_schedules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Notes about this rollout phase")
    
    class Meta:
        verbose_name = "Feature Flag Rollout Schedule"
        verbose_name_plural = "Feature Flag Rollout Schedules"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.phase_name} for {self.feature_flag.name} - {self.target_percentage}%"


class FeatureFlagImpactAnalysis(models.Model):
    """Model for tracking the impact of feature flags"""
    id = models.AutoField(primary_key=True)
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='impact_analyses')
    analysis_type = models.CharField(max_length=100, choices=[
        ('performance', 'Performance Impact'),
        ('user_experience', 'User Experience Impact'),
        ('conversion_rate', 'Conversion Rate Impact'),
        ('error_rate', 'Error Rate Impact'),
        ('load', 'System Load Impact'),
        ('revenue', 'Revenue Impact'),
        ('engagement', 'User Engagement Impact'),
        ('adoption', 'Feature Adoption Rate'),
    ])
    metric_name = models.CharField(max_length=255, help_text="Name of the metric being analyzed")
    baseline_value = models.FloatField(help_text="Baseline value before feature activation")
    current_value = models.FloatField(help_text="Current value after feature activation")
    unit = models.CharField(max_length=50, help_text="Unit of measurement for the metric")
    impact_percentage = models.FloatField(help_text="Percentage change in the metric")
    statistical_significance = models.FloatField(help_text="Statistical significance of the change (0-1)")
    sample_size = models.IntegerField(help_text="Number of samples in the analysis")
    start_date = models.DateTimeField(help_text="Start date of the analysis period")
    end_date = models.DateTimeField(help_text="End date of the analysis period")
    is_positive_impact = models.BooleanField(null=True, blank=True, help_text="Whether the impact is positive or negative")
    confidence_level = models.FloatField(help_text="Confidence level in the analysis results (0-1)")
    impact_summary = models.TextField(help_text="Summary of the impact findings")
    recommendations = models.TextField(blank=True, help_text="Recommendations based on the analysis")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feature_impact_analyses')
    
    class Meta:
        verbose_name = "Feature Flag Impact Analysis"
        verbose_name_plural = "Feature Flag Impact Analyses"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.analysis_type} for {self.feature_flag.name} - {self.impact_percentage:+.2f}%"


class FeatureFlagDependency(models.Model):
    """Model for managing feature flag dependencies"""
    id = models.AutoField(primary_key=True)
    dependent_feature = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='dependencies')
    required_feature = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='dependents')
    dependency_type = models.CharField(max_length=50, choices=[
        ('requires', 'Requires'),
        ('conflicts_with', 'Conflicts With'),
        ('prerequisite', 'Prerequisite'),
        ('alternative', 'Alternative'),
        ('supersedes', 'Supersedes'),
    ])
    condition = models.JSONField(default=dict, blank=True, help_text="Condition for the dependency")
    is_active = models.BooleanField(default=True, help_text="Whether this dependency is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feature_dependencies_created')
    notes = models.TextField(blank=True, help_text="Notes about this dependency")
    
    class Meta:
        verbose_name = "Feature Flag Dependency"
        verbose_name_plural = "Feature Flag Dependencies"
        unique_together = ['dependent_feature', 'required_feature']
        ordering = ['dependent_feature__name']
    
    def __str__(self):
        return f"{self.dependent_feature.name} {self.dependency_type} {self.required_feature.name}"


class FeatureFlagExperiment(models.Model):
    """Model for A/B testing and experimentation with feature flags"""
    id = models.AutoField(primary_key=True)
    experiment_name = models.CharField(max_length=255, help_text="Name of the experiment")
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='experiments')
    hypothesis = models.TextField(help_text="What you expect to happen with this experiment")
    start_date = models.DateTimeField(help_text="Start date of the experiment")
    end_date = models.DateTimeField(help_text="End date of the experiment")
    status = models.CharField(max_length=20, choices=[
        ('design', 'Design'),
        ('running', 'Running'),
        ('analysis', 'Analysis'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='design')
    target_metric = models.CharField(max_length=255, help_text="Primary metric to measure")
    success_criteria = models.JSONField(default=dict, blank=True, help_text="Criteria for determining success")
    variant_a_percentage = models.FloatField(default=50.0, help_text="Percentage of users in variant A (0-100)")
    variant_b_percentage = models.FloatField(default=50.0, help_text="Percentage of users in variant B (0-100)")
    minimum_sample_size = models.IntegerField(help_text="Minimum sample size for statistical significance")
    statistical_power = models.FloatField(default=0.8, help_text="Statistical power of the experiment (0-1)")
    significance_level = models.FloatField(default=0.05, help_text="Significance level (alpha) for the experiment (0-1)")
    results = models.JSONField(default=dict, blank=True, help_text="Results of the experiment")
    winner = models.CharField(max_length=20, choices=[
        ('variant_a', 'Variant A'),
        ('variant_b', 'Variant B'),
        ('tie', 'Tie'),
        ('inconclusive', 'Inconclusive'),
    ], null=True, blank=True)
    conclusion = models.TextField(blank=True, help_text="Conclusion of the experiment")
    recommendations = models.TextField(blank=True, help_text="Recommendations based on results")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feature_experiments_created')
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes about the experiment")
    
    class Meta:
        verbose_name = "Feature Flag Experiment"
        verbose_name_plural = "Feature Flag Experiments"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.experiment_name} - {self.status}"

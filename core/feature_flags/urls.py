from django.urls import path
from . import views

app_name = 'feature_flags'

urlpatterns = [
    path('', views.FeatureFlagsDashboardView.as_view(), name='dashboard'),
    path('flags/', views.FeatureFlagListView.as_view(), name='flag_list'),
    path('flags/create/', views.FeatureFlagCreateView.as_view(), name='flag_create'),
    path('flags/<int:pk>/', views.FeatureFlagDetailView.as_view(), name='flag_detail'),
    path('flags/<int:pk>/edit/', views.FeatureFlagUpdateView.as_view(), name='flag_update'),
    path('flags/<int:pk>/delete/', views.FeatureFlagDeleteView.as_view(), name='flag_delete'),
    path('active/', views.ActiveFlagsView.as_view(), name='active_flags'),
    path('disabled/', views.DisabledFlagsView.as_view(), name='disabled_flags'),
    path('rollout/percentage/', views.PercentageRolloutView.as_view(), name='percentage_rollout'),
    path('rollout/gradual/', views.GradualRolloutView.as_view(), name='gradual_rollout'),
    path('rollout/canary/', views.CanaryReleasesView.as_view(), name='canary_releases'),
    path('targeting/', views.TargetingRulesView.as_view(), name='targeting_rules'),
    path('targeting/<int:pk>/', views.TargetingRulesView.as_view(), name='targeting_rules_detail'),
    path('testing/ab/', views.ABTestingView.as_view(), name='ab_testing'),
    path('analytics/', views.FeatureAnalyticsView.as_view(), name='analytics'),
    path('analytics/adoption/', views.AdoptionRatesView.as_view(), name='adoption_rates'),
]

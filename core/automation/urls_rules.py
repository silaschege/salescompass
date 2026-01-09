from django.urls import path
from . import rules_views
 
urlpatterns = [
    path('rules/', rules_views.AutomationRuleListView.as_view(), name='rule_list'),
    path('rules/create/', rules_views.AutomationRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/edit/', rules_views.AutomationRuleUpdateView.as_view(), name='rule_update'),
    path('rules/<int:pk>/delete/', rules_views.AutomationRuleDeleteView.as_view(), name='rule_delete'),
]

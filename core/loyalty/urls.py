from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    # Dashboard
    path('', views.LoyaltyDashboardView.as_view(), name='dashboard'),
    
    # Programs
    path('programs/', views.LoyaltyProgramListView.as_view(), name='program_list'),
    path('programs/setup/', views.LoyaltyProgramView.as_view(), name='program_setup'),
    path('programs/<int:pk>/edit/', views.LoyaltyProgramView.as_view(), name='program_edit'),
    
    # Members
    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('members/<int:pk>/adjust/', views.PointsAdjustmentView.as_view(), name='points_adjust'),
    
    # Rules
    path('tier-rules/', views.TierRulesListView.as_view(), name='tier_rules'),
    # Transactions
    path('transactions/', views.LoyaltyTransactionListView.as_view(), name='transaction_list'),
]

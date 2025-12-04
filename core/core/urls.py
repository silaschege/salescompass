from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='product'),
    path('customers/', views.customers, name='customers'),
    path('support/', views.support, name='support'),
    path('company/', views.company, name='company'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('mfa/verify/', views.mfa_verify, name='mfa_verify'),
    path('try/', views.try_free, name='try_free'),
    path('appselection/', views.app_selection, name='app_selection'),
    path('integrations/', views.integrations, name='integrations'),
    path('api/', views.api_docs, name='api_docs'),
    path('pricing/', views.pricing, name='pricing'),
    path('solutions/', views.solutions, name='solutions'),
]

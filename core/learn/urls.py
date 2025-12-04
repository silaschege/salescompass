from django.urls import path
from . import views

app_name = 'learn'
urlpatterns = [
    # CRUD
    path('', views.ArticleListView.as_view(), name='list'),
    path('create/', views.ArticleCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='delete'),
    
    # Search
    path('search/', views.SearchResultsView.as_view(), name='search'),
    
    # Export
    path('<slug:slug>/export-pdf/', views.ArticlePDFExportView.as_view(), name='export_pdf'),
    
    # Rating
    path('<slug:slug>/rate/', views.ArticleRatingView.as_view(), name='rate_article'),
    
    # Analytics
    path('analytics/', views.UsageAnalyticsView.as_view(), name='usage_analytics'),
]
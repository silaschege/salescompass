from django.urls import path
from . import views

app_name = 'learn'
urlpatterns = [
    # Dashboard
    path('dashboard/', views.LearnerDashboardView.as_view(), name='dashboard'),

    # Articles
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('article/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:slug>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Lessons
    path('lessons/<slug:slug>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<slug:slug>/complete/', views.CompleteLessonView.as_view(), name='complete_lesson'),
    path('lessons/<slug:slug>/edit/', views.LessonUpdateView.as_view(), name='lesson_update'),
    path('lessons/<slug:slug>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    path('courses/<slug:course_slug>/lessons/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    
    # Certificates
    path('certificates/<int:pk>/download/', views.CertificateDownloadView.as_view(), name='certificate_download'),
    
    # Search
    path('search/', views.SearchResultsView.as_view(), name='search'),
    
    # Export
    path('article/<slug:slug>/export-pdf/', views.ArticlePDFExportView.as_view(), name='export_pdf'),
    
    # Rating
    path('article/<slug:slug>/rate/', views.ArticleRatingView.as_view(), name='rate_article'),
    
    # Analytics
    path('analytics/', views.UsageAnalyticsView.as_view(), name='usage_analytics'),
]
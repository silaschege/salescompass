import json
import uuid
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponseForbidden
from core.permissions import ObjectPermissionRequiredMixin, PermissionRequiredMixin
from .models import Article, Category, ArticleRating, Course, Lesson, UserProgress, ArticleView, Certificate
from .forms import ArticleForm, ArticleRatingForm, CourseForm, LessonForm
from .utils import generate_article_pdf
from automation.utils import emit_event
import logging

# Import engagement tracking
from engagement.utils import log_engagement_event

logger = logging.getLogger(__name__)

class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'learn/list.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().filter(status='published').select_related('category', 'author')

class ArticleDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Article
    template_name = 'learn/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Log view
        from .utils import log_article_view
        log_article_view(
            self.object.id,
            user=self.request.user if self.request.user.is_authenticated else None,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Emit event
        emit_event('learn.article_viewed', {
            'article_id': self.object.id,
            'user_id': self.request.user.id if self.request.user.is_authenticated else None,
            'tenant_id': getattr(self.request.user, 'tenant_id', None)
        })
        
        # Log engagement event for article viewed
        try:
            if self.request.user.is_authenticated:
                log_engagement_event(
                    tenant_id=self.request.user.tenant_id,
                    event_type='article_viewed',
                    description=f"Article viewed: {self.object.title}",
                    title="Article Viewed",
                    metadata={
                        'article_id': self.object.id,
                        'title': self.object.title,
                        'category': str(self.object.category)
                    },
                    engagement_score=1,
                    created_by=self.request.user
                )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        return context

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class ArticleCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'learn/form.html'
    success_url = reverse_lazy('learn:list')
    permission_action = 'change'

    def form_valid(self, form):
        messages.success(self.request, f"Article '{form.instance.title}' created successfully!")
        return super().form_valid(form)
    
class ArticleUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'learn/form.html'
    permission_action = 'change'

    def get_success_url(self):
        return reverse_lazy('learn:detail', kwargs={'slug': self.object.article_slug})

    def form_valid(self, form):
        messages.success(self.request, f"Article '{form.instance.title}' updated successfully!")
        return super().form_valid(form)

class ArticleDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Article
    template_name = 'learn/delete.html'
    success_url = reverse_lazy('learn:list')
    permission_action = 'delete'


class SearchResultsView(TemplateView):
    template_name = 'learn/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        context['query'] = query
        
        if query:
            from .search import search_articles_elastic
            tenant_id = getattr(self.request.user, 'tenant_id', None)
            response = search_articles_elastic(query, tenant_id, self.request.user)
            
            results = []
            if 'hits' in response:
                for hit in response['hits']['hits']:
                    results.append({
                        'id': hit['_source']['article_id'],
                        'title': hit['_source']['title'],
                        'summary': hit['_source']['summary'],
                        'highlight': hit.get('highlight', {}),
                        'article_type': hit['_source']['article_type'],
                        'category': hit['_source']['category']
                    })
            context['results'] = results
            context['total'] = response['hits']['total']['value'] if 'hits' in response else 0
        
        return context


class ArticlePDFExportView(ObjectPermissionRequiredMixin, ListView):
    permission_action = 'view'

    def get(self, request, slug):
        article = get_object_or_404(Article, article_slug=slug)
        
        # Log engagement event for article PDF downloaded
        try:
            log_engagement_event(
                tenant_id=request.user.tenant_id,
                event_type='article_downloaded',
                description=f"Article PDF downloaded: {article.title}",
                title="Article Downloaded",
                metadata={
                    'article_id': article.id,
                    'title': article.title
                },
                engagement_score=2,
                created_by=request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        return generate_article_pdf(article.id)


class ArticleRatingView(ObjectPermissionRequiredMixin, CreateView):
    model = ArticleRating
    form_class = ArticleRatingForm
    template_name = 'learn/rating_form.html'
    permission_action = 'view'

    def form_valid(self, form):
        form.instance.article = get_object_or_404(Article, article_slug=self.kwargs['slug'])
        form.instance.user = self.request.user if self.request.user.is_authenticated else None
        messages.success(self.request, "Thank you for your feedback!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('learn:detail', kwargs={'slug': self.kwargs['slug']})


class UsageAnalyticsView(PermissionRequiredMixin, TemplateView):
    template_name = 'learn/usage_analytics.html'
    required_permission = 'reports:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Total views
        total_views = ArticleView.objects.filter(tenant_id=tenant_id).count()
        
        # Top articles
        top_articles = ArticleView.objects.filter(
            tenant_id=tenant_id
        ).values('article__title').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:10]
        
        # Views by article type
        type_views = ArticleView.objects.filter(
            tenant_id=tenant_id
        ).values('article__article_type').annotate(
            view_count=Count('id')
        )
        
        # Recent views (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_views = ArticleView.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=thirty_days_ago
        ).extra(select={'date': "date(created_at)"}).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        trend_data = []
        for view in recent_views:
            trend_data.append({
                'date': view['date'].isoformat(),
                'views': view['count']
            })
        
        context.update({
            'total_views': total_views,
            'top_articles': top_articles,
            'type_views': type_views,
            'trend_data_json': trend_data,
        })
        return context


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'learn/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        return super().get_queryset().filter(status='published').select_related('category', 'author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(tenant=getattr(self.request.user, 'tenant', None))
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'learn/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all().order_by('order_in_course')
        # Check if user is enrolled or has progress
        user_progress_qs = UserProgress.objects.filter(
            user=self.request.user,
            course=self.object
        ).select_related('lesson')
        
        # Map progress by lesson ID for quick lookup in template
        progress_dict = {p.lesson_id: p for p in user_progress_qs}
        context['user_progress'] = progress_dict
        
        # Calculate overall progress
        total_lessons = context['lessons'].count()
        completed_lessons = user_progress_qs.filter(completion_status='completed').count()
        context['progress_percentage'] = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # Check if certificate exists
        context['certificate'] = Certificate.objects.filter(user=self.request.user, course=self.object).first()
        
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'learn/lesson_player.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object.course
        context['course'] = course
        context['lessons'] = course.lessons.all().order_by('order_in_course')
        
        # Next and previous lessons
        lessons_list = list(context['lessons'])
        current_index = lessons_list.index(self.object)
        context['previous_lesson'] = lessons_list[current_index - 1] if current_index > 0 else None
        context['next_lesson'] = lessons_list[current_index + 1] if current_index < len(lessons_list) - 1 else None
        
        # Progress tracking
        progress, created = UserProgress.objects.get_or_create(
            user=self.request.user,
            course=course,
            lesson=self.object,
            tenant=self.request.user.tenant,
            defaults={'completion_status': 'in_progress'}
        )
        if not created and progress.completion_status == 'not_started':
            progress.completion_status = 'in_progress'
            progress.save()
            
        # Emit event
        emit_event('learn.lesson_started', {
            'course_id': course.id,
            'lesson_id': self.object.id,
            'user_id': self.request.user.id,
            'tenant_id': self.request.user.tenant_id
        })
            
        context['user_progress'] = progress
        return context


class LearnerDashboardView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'learn/learner_dashboard.html'
    context_object_name = 'enrolled_courses'

    def get_queryset(self):
        # We define "enrolled" as having at least one UserProgress record for the course
        enrolled_course_ids = UserProgress.objects.filter(
            user=self.request.user
        ).values_list('course_id', flat=True).distinct()
        return Course.objects.filter(id__in=enrolled_course_ids).select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add progress data for each course
        enrolled_courses_data = []
        for course in context['enrolled_courses']:
            total_lessons = course.lessons.count()
            completed_lessons = UserProgress.objects.filter(
                user=self.request.user,
                course=course,
                completion_status='completed'
            ).count()
            
            progress_percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            
            enrolled_courses_data.append({
                'course': course,
                'progress_percent': progress_percent,
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons
            })
            
        context['enrolled_courses_data'] = enrolled_courses_data
        
        # Add some stats
        context['total_completed_lessons'] = UserProgress.objects.filter(
            user=self.request.user,
            completion_status='completed'
        ).count()
        context['total_started_courses'] = len(enrolled_courses_data)
        
        return context


class CompleteLessonView(LoginRequiredMixin, DetailView):
    model = Lesson
    
    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        course = lesson.course
        
        # Mark current lesson as completed
        progress, created = UserProgress.objects.get_or_create(
            user=self.request.user,
            course=course,
            lesson=lesson,
            tenant=self.request.user.tenant
        )
        progress.completion_status = 'completed'
        progress.completion_date = timezone.now()
        progress.save()
        
        # Emit event
        emit_event('learn.lesson_completed', {
            'course_id': course.id,
            'lesson_id': lesson.id,
            'user_id': self.request.user.id,
            'tenant_id': self.request.user.tenant_id
        })
        
        # Log engagement event for lesson completed
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='lesson_completed',
                description=f"Lesson completed: {lesson.title} ({course.title})",
                title="Lesson Completed",
                metadata={
                    'lesson_id': lesson.id,
                    'course_id': course.id,
                    'lesson_title': lesson.title,
                    'course_title': course.title
                },
                engagement_score=3,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        # Check if all lessons in the course are completed
        total_lessons = course.lessons.count()
        completed_lessons = UserProgress.objects.filter(
            user=self.request.user,
            course=course,
            completion_status='completed'
        ).count()
        
        if total_lessons == completed_lessons:
            # Issue certificate
            Certificate.objects.get_or_create(
                user=self.request.user,
                course=course,
                tenant=self.request.user.tenant,
                defaults={
                    'certificate_number': str(uuid.uuid4())[:8].upper()
                }
            )
            
            # Emit event
            emit_event('learn.course_completed', {
                'course_id': course.id,
                'user_id': self.request.user.id,
                'tenant_id': self.request.user.tenant_id
            })
            
            # Log engagement event for course completed & certificate earned
            try:
                log_engagement_event(
                    tenant_id=self.request.user.tenant_id,
                    event_type='course_completed',
                    description=f"Course completed: {course.title}",
                    title="Course Completed",
                    metadata={
                        'course_id': course.id,
                        'title': course.title,
                        'total_lessons': total_lessons
                    },
                    engagement_score=10,
                    created_by=self.request.user
                )
                
                log_engagement_event(
                    tenant_id=self.request.user.tenant_id,
                    event_type='certificate_earned',
                    description=f"Certificate earned for {course.title}",
                    title="Certificate Earned",
                    metadata={
                        'course_id': course.id,
                        'certificate_number': str(uuid.uuid4())[:8].upper() # Note: logic duplication from view, harmless for log
                    },
                    engagement_score=5,
                    created_by=self.request.user
                )
            except Exception as e:
                logger.warning(f"Failed to log engagement event: {e}")
            
            messages.success(request, f"Congratulations! You've completed {course.title}!")
            return redirect('learn:course_detail', slug=course.slug)
        
        # Find next lesson
        next_lesson = course.lessons.filter(order_in_course__gt=lesson.order_in_course).order_by('order_in_course').first()
        if next_lesson:
            return redirect('learn:lesson_detail', slug=next_lesson.slug)
        
        return redirect('learn:course_detail', slug=course.slug)


class CertificateDownloadView(LoginRequiredMixin, DetailView):
    model = Certificate
    
    def get(self, request, *args, **kwargs):
        certificate = self.get_object()
        if certificate.user != request.user:
            return HttpResponseForbidden("You are not authorized to view this certificate.")
            
        from .utils import generate_certificate_pdf
        return generate_certificate_pdf(certificate.id)


class CourseCreateView(PermissionRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'learn/course_form.html'
    success_url = reverse_lazy('learn:course_list')
    required_permission = 'learn:change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f"Course '{form.instance.title}' created successfully!")
        return super().form_valid(form)


class CourseUpdateView(PermissionRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'learn/course_form.html'
    required_permission = 'learn:change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('learn:course_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        messages.success(self.request, f"Course '{form.instance.title}' updated successfully!")
        return super().form_valid(form)


class CourseDeleteView(PermissionRequiredMixin, DeleteView):
    model = Course
    template_name = 'learn/course_confirm_delete.html'
    success_url = reverse_lazy('learn:course_list')
    required_permission = 'learn:delete'


class LessonCreateView(PermissionRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'learn/lesson_form.html'
    required_permission = 'learn:change'

    def get_initial(self):
        initial = super().get_initial()
        course_slug = self.kwargs.get('course_slug')
        if course_slug:
            initial['course'] = get_object_or_404(Course, slug=course_slug, tenant=self.request.user.tenant)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        course_slug = self.kwargs.get('course_slug')
        if course_slug:
            kwargs['course'] = get_object_or_404(Course, slug=course_slug, tenant=self.request.user.tenant)
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f"Lesson '{form.instance.title}' created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('learn:course_detail', kwargs={'slug': self.object.course.slug})


class LessonUpdateView(PermissionRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'learn/lesson_form.html'
    required_permission = 'learn:change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['course'] = self.object.course
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Lesson '{form.instance.title}' updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('learn:course_detail', kwargs={'slug': self.object.course.slug})


class LessonDeleteView(PermissionRequiredMixin, DeleteView):
    model = Lesson
    template_name = 'learn/lesson_confirm_delete.html'
    required_permission = 'learn:delete'

    def get_success_url(self):
        return reverse('learn:course_detail', kwargs={'slug': self.object.course.slug})
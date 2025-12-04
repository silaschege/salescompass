import json
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.permissions import ObjectPermissionRequiredMixin,PermissionRequiredMixin
from .models import Article, Category, ArticleRating
from .forms import ArticleForm, ArticleRatingForm
from .utils import generate_article_pdf
from .search import search_articles_elastic

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
        return reverse_lazy('learn:detail', kwargs={'slug': self.object.slug})

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
            context['total'] = response['hits']['total']['value']
        
        return context


class ArticlePDFExportView(ObjectPermissionRequiredMixin,ListView):
    permission_action = 'view'

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        return generate_article_pdf(article.id)


class ArticleRatingView(ObjectPermissionRequiredMixin, CreateView):
    model = ArticleRating
    form_class = ArticleRatingForm
    template_name = 'learn/rating_form.html'
    permission_action = 'view'

    def form_valid(self, form):
        form.instance.article = get_object_or_404(Article, slug=self.kwargs['slug'])
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
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
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
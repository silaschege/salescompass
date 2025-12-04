# apps/learn/
# ├── __init__.py
# ├── admin.py
# ├── apps.py
# ├── forms.py
# ├── models.py
# ├── urls.py
# ├── views.py
# ├── utils.py
# ├── tasks.py
# ├── search.py
# ├── consumers.py
# └── templates/learn/
#     ├── list.html
#     ├── detail.html
#     ├── form.html
#     ├── search_results.html
#     ├── export_pdf.html
#     └── usage_analytics.html

from django.db import models

# Create your models here.
from django.db import models
from core.models import TenantModel, TimeStampedModel
from core.models import User

ARTICLE_TYPES = [
    ('user_guide', 'User Guide'),
    ('api_docs', 'API Documentation'),
    ('release_notes', 'Release Notes'),
    ('esg_manual', 'ESG Compliance Manual'),
    ('admin_guide', 'Admin Guide'),
    ('faq', 'FAQ'),
]

STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('review', 'In Review'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

class Category(TenantModel):
    """
    Documentation categories (e.g., "Sales", "ESG", "API").
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['order']
        unique_together = [('name', 'tenant_id')]

    def __str__(self):
        return self.name


class Article(TenantModel):
    """
    Documentation article.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    summary = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    article_type = models.CharField(max_length=20, choices=ARTICLE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Access control
    is_public = models.BooleanField(default=False)  # Visible to customers
    required_role = models.CharField(max_length=100, blank=True)  # e.g., "admin", "esg_analyst"
    
    # Metadata
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='authored_articles')
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_articles')
    tags = models.CharField(max_length=255, blank=True)  # Comma-separated
    
    # SEO
    meta_description = models.TextField(blank=True)
    
    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class ArticleVersion(TenantModel):
    """
    Versioned snapshot of article content.
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()  # Markdown or HTML
    version_number = models.IntegerField(default=1)
    is_current = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = [('article', 'version_number')]

    def __str__(self):
        return f"{self.article.title} v{self.version_number}"


class ArticleView(TenantModel):
    """
    Track article views for analytics.
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.article.title} viewed by {self.user or 'anonymous'}"


class ArticleRating(TenantModel):
    """
    User ratings for articles (1-5 stars).
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField()  # 1-5
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.article.title} - {self.rating} stars"


class SearchIndex(TimeStampedModel):
    """
    Elasticsearch index status (for monitoring).
    """
    index_name = models.CharField(max_length=100)
    document_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(null=True, blank=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.index_name


class ExportJob(TenantModel):
    """
    PDF export job tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='article_exports/', null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Export {self.article.title} - {self.status}"

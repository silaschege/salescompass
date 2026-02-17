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


# Create your models here.
from datetime import timedelta
from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel
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

LESSON_TYPES = [
    ('article', 'Article'),
    ('video', 'Video'),
    ('quiz', 'Quiz'),
    ('assignment', 'Assignment'),
]

COMPLETION_STATUS = [
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
]

class Category(TenantModel):
    """
    Documentation categories (e.g., "Sales", "ESG", "API").
    """
    category_name = models.CharField(max_length=100)
    category_description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['order']
        unique_together = [('category_name', 'tenant')]

    def __str__(self):
        return self.category_name


class Article(TenantModel):
    """
    Documentation article.
    """
    title = models.CharField(max_length=255)
    article_slug = models.SlugField(max_length=255, unique=True)
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
        unique_together = [('article', 'version_number', 'tenant')]

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


class Course(TenantModel, TimeStampedModel):
    """
    Structured learning path.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='authored_courses')
    order = models.IntegerField(default=0)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    estimated_duration = models.DurationField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = [('title', 'tenant')]

    def __str__(self):
        return self.title


class Lesson(TenantModel, TimeStampedModel):
    """
    Individual units of content within a course.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    content = models.TextField(blank=True)  # Markdown/HTML content
    order_in_course = models.IntegerField(default=0)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='article')
    duration = models.DurationField(null=True, blank=True)
    prerequisite_lesson = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_lessons')
    
    # Integration with Article system
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')

    class Meta:
        ordering = ['order_in_course']
        unique_together = [('course', 'order_in_course', 'tenant')]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class UserProgress(TenantModel, TimeStampedModel):
    """
    Tracks user progress within courses and lessons.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS, default='not_started')
    completion_date = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)  # Used for quiz scores
    time_spent = models.DurationField(default=timedelta(0))

    class Meta:
        unique_together = [('user', 'lesson', 'tenant')]

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title} ({self.completion_status})"


class Certificate(TenantModel, TimeStampedModel):
    """
    Issued to users upon course completion.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issue_date = models.DateTimeField(auto_now_add=True)
    certificate_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)

    class Meta:
        unique_together = [('user', 'course', 'tenant')]

    def __str__(self):
        return f"Certificate: {self.user.email} - {self.course.title}"

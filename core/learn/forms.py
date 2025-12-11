from django import forms
from django.core.exceptions import ValidationError
from .models import Article, ArticleRating, Category

class ArticleForm(forms.ModelForm):
    """
    Form for creating and updating documentation articles.
    """
    class Meta:
        model = Article
        fields = [
            'title', 'article_slug', 'summary', 'category', 'article_type', 
            'status', 'is_public', 'required_role', 'tags', 'meta_description',
            'author'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Getting Started with SalesCompass'
            }),
            'article_slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., getting-started-salescompass'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief summary of the article content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'article_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., sales, onboarding, esg (comma-separated)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'SEO meta description (150-160 characters)'
            }),
            'author': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'required_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., admin, esg_analyst, sales_rep'
            })
        }
        help_texts = {
            'title': 'Descriptive title for your article',
            'article_slug': 'URL-friendly version of the title (letters, numbers, hyphens only)',
            'summary': 'Brief overview that appears in search results and listings',
            'category': 'Organizational category for this article',
            'article_type': 'Type of documentation this represents',
            'status': 'Current publication status',
            'is_public': 'Public articles are visible to customers and external users',
            'required_role': 'Leave blank for public articles, or specify role for internal access',
            'tags': 'Comma-separated keywords for search and filtering',
            'meta_description': 'SEO description that appears in search engine results',
            'author': 'Original author of this article'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter categories to user's tenant
            self.fields['category'].queryset = Category.objects.filter(
                tenant_id=user.tenant_id
            )
            
            # Filter authors to active users in tenant
            from core.models import User
            self.fields['author'].queryset = User.objects.filter(
                tenant_id=user.tenant_id,
                is_active=True
            )
            
            # Set author to current user for new articles
            if not self.instance.pk:
                self.fields['author'].initial = user
        
        # Make slug field readonly for existing articles
        if self.instance.pk:
            self.fields['article_slug'].widget.attrs['readonly'] = True

    def clean_article_slug(self):
        """Validate slug format and uniqueness."""
        slug = self.cleaned_data['article_slug']
        
        # Check for valid slug format (letters, numbers, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
            raise ValidationError('Slug can only contain letters, numbers, hyphens, and underscores.')
        
        # Check uniqueness within tenant
        qs = Article.objects.filter(article_slug=slug, tenant_id=self.instance.tenant_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('An article with this slug already exists.')
        
        return slug

    def clean_tags(self):
        """Clean and validate tags."""
        tags = self.cleaned_data['tags']
        if tags:
            # Split by comma and clean each tag
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            # Remove duplicates and rejoin
            unique_tags = list(dict.fromkeys(tag_list))
            return ', '.join(unique_tags)
        return tags

    def clean_meta_description(self):
        """Validate meta description length."""
        meta_description = self.cleaned_data['meta_description']
        if meta_description and len(meta_description) > 160:
            raise ValidationError('Meta description should be 160 characters or less for optimal SEO.')
        return meta_description

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        is_public = cleaned_data.get('is_public', False)
        required_role = cleaned_data.get('required_role')
        
        # If article is public, required_role should be empty
        if is_public and required_role:
            raise ValidationError({
                'required_role': 'Public articles should not have a required role.'
            })
        
        # If article is not public, required_role should be specified
        if not is_public and not required_role:
            raise ValidationError({
                'required_role': 'Private articles must specify a required role.'
            })
        
        return cleaned_data


class ArticleRatingForm(forms.ModelForm):
    """
    Form for rating documentation articles.
    """
    class Meta:
        model = ArticleRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What did you think of this article? Your feedback helps us improve.'
            })
        }
        help_texts = {
            'rating': 'Rate this article from 1 (Poor) to 5 (Excellent)',
            'comment': 'Optional feedback to help us improve this content'
        }

    def __init__(self, *args, **kwargs):
        article = kwargs.pop('article', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.article = article
        self.user = user

    def clean_rating(self):
        """Validate rating is between 1 and 5."""
        rating = self.cleaned_data['rating']
        if rating < 1 or rating > 5:
            raise ValidationError('Rating must be between 1 and 5.')
        return rating

    def clean(self):
        """Prevent duplicate ratings from the same user."""
        cleaned_data = super().clean()
        
        if self.user and self.article:
            # Check if user already rated this article
            existing_rating = ArticleRating.objects.filter(
                article=self.article,
                user=self.user
            ).exists()
            
            if existing_rating:
                raise ValidationError('You have already rated this article.')
        
        return cleaned_data


class ArticleSearchForm(forms.Form):
    """
    Form for searching documentation articles.
    """
    query = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documentation...',
            'aria-label': 'Search documentation'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All Categories"
    )
    article_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Article._meta.get_field('article_type').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_public = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Public Only'), ('false', 'Internal Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                tenant_id=user.tenant_id
            )


class ArticleVersionForm(forms.Form):
    """
    Form for creating article versions.
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 20,
            'placeholder': 'Enter the article content in Markdown or HTML...'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief description of changes made in this version...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)

    def clean_content(self):
        """Validate content is not empty."""
        content = self.cleaned_data['content']
        if not content or not content.strip():
            raise ValidationError('Article content cannot be empty.')
        return content.strip()
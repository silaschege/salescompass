from django.contrib import admin
from .models import Category, Article, Course, Lesson, UserProgress

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'tenant', 'order', 'parent')
    list_filter = ('tenant', 'parent')
    search_fields = ('category_name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'category', 'article_type', 'status', 'is_public')
    list_filter = ('tenant', 'category', 'article_type', 'status', 'is_public')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'article_slug': ('title',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'tenant', 'category', 'status', 'order', 'author')
    list_filter = ('tenant', 'category', 'status', 'author')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'tenant', 'lesson_type', 'order_in_course')
    list_filter = ('course', 'tenant', 'lesson_type')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'course', 'tenant', 'completion_status', 'completion_date')
    list_filter = ('tenant', 'completion_status', 'course')
    search_fields = ('user__email', 'lesson__title', 'course__title')

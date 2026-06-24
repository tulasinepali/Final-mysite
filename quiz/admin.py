from django.contrib import admin
from .models import Quiz, Question, QuizAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    ordering = ['order']
    fields = ['order', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'time_limit', 'is_published', 'is_featured', 'attempts', 'created_at']
    list_filter = ['is_published', 'is_featured', 'difficulty', 'category', 'created_at']
    search_fields = ['title', 'description', 'meta_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['attempts', 'created_at', 'updated_at']
    list_editable = ['is_published', 'is_featured']
    ordering = ['-created_at']
    inlines = [QuestionInline]
    fieldsets = (
        ('Quiz Info', {
            'fields': ('title', 'slug', 'category', 'description', 'difficulty', 'time_limit')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'attempts')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text', 'correct_answer']
    list_filter = ['quiz', 'correct_answer']
    search_fields = ['question_text', 'explanation']
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'session_key', 'score', 'total_questions', 'percentage', 'completed_at']
    list_filter = ['quiz', 'completed_at']
    search_fields = ['quiz__title', 'session_key']
    readonly_fields = ['quiz', 'session_key', 'score', 'total_questions', 'answers', 'completed_at']
    ordering = ['-completed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

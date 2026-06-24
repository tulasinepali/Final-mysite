from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'is_featured', 'views', 'created_at', 'updated_at']
    list_filter = ['is_published', 'is_featured', 'category', 'tags', 'created_at']
    search_fields = ['title', 'summary', 'content', 'meta_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views', 'created_at', 'updated_at']
    list_editable = ['is_published', 'is_featured']
    ordering = ['-created_at']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'tags', 'content', 'summary', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'views')
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

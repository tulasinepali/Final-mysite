from django.contrib import admin
from .models import Download


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'file_type', 'file_size', 'is_published', 'is_featured', 'download_count', 'created_at']
    list_filter = ['is_published', 'is_featured', 'file_type', 'category', 'tags', 'created_at']
    search_fields = ['title', 'description', 'summary', 'meta_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['download_count', 'created_at', 'updated_at']
    list_editable = ['is_published', 'is_featured']
    ordering = ['-created_at']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'tags', 'description', 'summary', 'thumbnail')
        }),
        ('File', {
            'fields': ('file', 'file_type', 'file_size')
        }),
        ('Publishing', {
            'fields': ('is_published', 'is_featured', 'download_count')
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

from django.contrib import admin
from .models import SiteSettings, Category, Tag, ContactMessage, AdPlacement, Subscriber

admin.site.site_header = "Tulasi Nepali - Admin Console"
admin.site.site_title = "Tulasi Nepali Admin"
admin.site.index_title = "Platform Management & Operations"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for singleton site settings - restrict to one instance only."""
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'site_logo', 'site_favicon')
        }),
        ('Owner Information', {
            'fields': ('owner_name', 'owner_title', 'owner_tagline', 'owner_experience', 'owner_bio', 'owner_image')
        }),
        ('Mission & Vision', {
            'fields': ('mission', 'vision')
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'youtube_url')
        }),
        ('Analytics & Ads', {
            'fields': ('google_analytics_id', 'adsense_client_id')
        }),
        ('Web Push Notifications', {
            'fields': ('enable_web_push', 'onesignal_app_id', 'onesignal_rest_api_key', 'auto_push_on_quiz', 'auto_push_on_blog'),
            'description': 'Configure browser push notifications for visitors when new quizzes or blog posts are published.'
        }),
        ('Email & Subscriber Notifications', {
            'fields': (
                'sender_email', 'email_host', 'email_port', 'email_host_user', 'email_host_password', 'email_use_tls',
                'auto_email_on_quiz', 'auto_email_on_note', 'auto_email_on_blog', 'auto_email_on_download'
            ),
            'description': 'Configure SMTP credentials and auto-notification triggers for email subscribers.'
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding more than one SiteSettings instance."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton SiteSettings instance."""
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'slug', 'icon', 'color', 'order', 'is_active', 'created_at']
    list_filter = ['module', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    ordering = ['module', 'order', 'name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False


@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ['name', 'placement', 'is_active']
    list_filter = ['is_active', 'placement']
    list_editable = ['is_active']
    search_fields = ['name']


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'source', 'created_at']
    list_filter = ['is_active', 'source', 'created_at']
    list_editable = ['is_active']
    search_fields = ['email']
    ordering = ['-created_at']
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscribers.short_description = "Mark selected subscribers as active"

    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_subscribers.short_description = "Mark selected subscribers as inactive"


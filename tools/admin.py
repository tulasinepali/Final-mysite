from django.contrib import admin
from .models import Tool, Widget, WidgetSetting

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order', 'view_count', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'order')


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'order', 'embed_count', 'default_height', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'order')


@admin.register(WidgetSetting)
class WidgetSettingAdmin(admin.ModelAdmin):
    list_display = ('branding_text', 'branding_url', 'allow_embedding', 'show_ads_in_widgets')

    def has_add_permission(self, request):
        return not WidgetSetting.objects.exists()

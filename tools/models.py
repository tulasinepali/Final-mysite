from django.db import models
from django.urls import reverse

class Tool(models.Model):
    CATEGORY_CHOICES = (
        ('converter', 'Date & Units Converter'),
        ('calculator', 'Calculators'),
        ('typing', 'Typing & Font Utilities'),
        ('general', 'General Utilities'),
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    icon = models.CharField(max_length=50, default='bi-tools', help_text='Bootstrap Icon class (e.g., bi-calendar3, bi-calculator)')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='converter')
    short_description = models.TextField(help_text='Brief explanation of what the tool does')
    meta_title = models.CharField(max_length=200, blank=True, help_text='SEO title tag')
    meta_description = models.TextField(blank=True, help_text='SEO meta description')
    is_active = models.BooleanField(default=True, help_text='Show/hide this tool across the platform')
    order = models.PositiveIntegerField(default=0, help_text='Sort display order (lowest first)')
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Tool'
        verbose_name_plural = 'Tools'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tools:tool_detail', kwargs={'slug': self.slug})


class Widget(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    tool = models.ForeignKey(Tool, on_delete=models.SET_NULL, null=True, blank=True, related_name='widgets')
    icon = models.CharField(max_length=50, default='bi-puzzle', help_text='Bootstrap icon')
    badge_text = models.CharField(max_length=50, default='Free Widget', blank=True)
    short_description = models.TextField(help_text='Why external webmasters/bloggers should embed this widget')
    default_width = models.CharField(max_length=20, default='100%')
    default_height = models.CharField(max_length=20, default='480')
    is_active = models.BooleanField(default=True, help_text='Active widgets appear on the /widgets/ showcase page')
    order = models.PositiveIntegerField(default=0)
    embed_count = models.PositiveIntegerField(default=0, help_text='Count of times embed code has been generated')
    custom_html = models.TextField(blank=True, help_text='Optional custom iframe/HTML template code for custom widgets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Embeddable Widget'
        verbose_name_plural = 'Embeddable Widgets'

    def __str__(self):
        return self.title

    def get_embed_url(self):
        return reverse('tools:widget_embed', kwargs={'slug': self.slug})


class WidgetSetting(models.Model):
    allow_embedding = models.BooleanField(default=True, help_text='Global toggle: allow other websites to embed widgets via iframe')
    branding_text = models.CharField(max_length=100, default='Powered by Tulasi Nepali')
    branding_url = models.URLField(default='https://tulasinepali.com.np')
    show_ads_in_widgets = models.BooleanField(default=False, help_text='Render AdSense banner inside embedded widget iframes')

    class Meta:
        verbose_name = 'Widget Global Setting'
        verbose_name_plural = 'Widget Global Settings'

    def __str__(self):
        return 'Widget Settings'

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

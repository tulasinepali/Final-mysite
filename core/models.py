from django.db import models
from django.urls import reverse


class SiteSettings(models.Model):
    """Singleton model for site-wide settings"""
    site_name = models.CharField(max_length=200, default='Learning Platform')
    site_tagline = models.CharField(max_length=300, default='Learn Technology, General Knowledge & Exam Preparation')
    site_description = models.TextField(default='An open educational platform for technology, computing, general knowledge, and competitive exam preparation.')
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True)
    site_favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    owner_name = models.CharField(max_length=200, default='Tulasi Nepali')
    owner_title = models.CharField(
        max_length=200,
        default='Educator & Mentor',
        blank=True,
        help_text='Your professional title or role (e.g. Educator & Mentor, Computer Operator Trainer, Teacher, IT Officer)'
    )
    owner_tagline = models.CharField(
        max_length=300,
        blank=True,
        default='Technology, GK & Competitive Learning Mentor',
        help_text='A short tagline or headline displayed with your profile'
    )
    owner_experience = models.CharField(
        max_length=150,
        blank=True,
        default='IT Specialist & Educator',
        help_text='Highlights such as years of experience or credentials'
    )
    owner_bio = models.TextField(default='')
    owner_image = models.ImageField(upload_to='about/', blank=True, null=True)
    mission = models.TextField(default='')
    vision = models.TextField(default='')
    contact_email = models.EmailField(default='admin@learningplatform.com')
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    adsense_client_id = models.CharField(max_length=100, blank=True)
    
    # Web Push Notification Settings
    enable_web_push = models.BooleanField(
        default=False,
        help_text='Master switch to enable or disable browser push notifications for visitors'
    )
    onesignal_app_id = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='OneSignal App ID (from your free OneSignal dashboard at onesignal.com)'
    )
    onesignal_rest_api_key = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='OneSignal REST API Key for automated backend push broadcasts'
    )
    auto_push_on_quiz = models.BooleanField(
        default=True,
        help_text='Automatically broadcast push notification when a new quiz is published'
    )
    auto_push_on_blog = models.BooleanField(
        default=True,
        help_text='Automatically broadcast push notification when a new blog post is published'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name


class Category(models.Model):
    """Shared category model used across apps"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text='Font Awesome class, e.g. fa-book')
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relation fields - which module this category belongs to
    module = models.CharField(max_length=50, choices=[
        ('notes', 'Notes'),
        ('downloads', 'Downloads'),
        ('blog', 'Blog'),
        ('quiz', 'Quiz'),
    ])

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.module})"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}: {self.subject}"


class AdPlacement(models.Model):
    PLACEMENT_CHOICES = [
        ('home_top', 'Home - Top Banner'),
        ('home_sidebar', 'Home - Sidebar'),
        ('notes_top', 'Notes - Top'),
        ('notes_middle', 'Notes - Middle'),
        ('notes_bottom', 'Notes - Bottom'),
        ('blog_top', 'Blog - Top'),
        ('blog_middle', 'Blog - Middle (after content)'),
        ('blog_sidebar', 'Blog - Sidebar'),
        ('quiz_result', 'Quiz Result Page'),
        ('downloads_top', 'Downloads - Top'),
        ('sidebar', 'Global Sidebar'),
        ('footer', 'Global Footer'),
        ('popup', 'Popup - Full Screen Overlay'),
    ]
    name = models.CharField(max_length=200)
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, unique=True)
    ad_code = models.TextField(help_text='AdSense or HTML ad code', blank=True, default='')
    ad_image = models.ImageField(upload_to='ads/', blank=True, null=True, help_text='Upload an ad image (PNG, JPG). Used for popup or banner ads.')
    link_url = models.URLField(blank=True, default='', help_text='URL to open when the ad image is clicked')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class VisitorCount(models.Model):
    """Track total site visits"""
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Visitor Count'
        verbose_name_plural = 'Visitor Count'

    def __str__(self):
        return str(self.count)

    @classmethod
    def get_count(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj.count

    @classmethod
    def increment(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={'count': 1})
        if not created:
            obj.count += 1
            obj.save(update_fields=['count', 'updated_at'])
        return obj.count

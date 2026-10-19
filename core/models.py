import re
from django.db import models
from django.urls import reverse


class SiteSettings(models.Model):
    """Singleton model for site-wide settings"""
    site_name = models.CharField(max_length=200, default='Tulasi Nepali')
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
    adsense_client_id = models.CharField(
        max_length=100,
        blank=True,
        default='ca-pub-3956705237421931',
        help_text='Google AdSense Publisher ID (e.g. ca-pub-3956705237421931)'
    )
    adsense_verification_method = models.CharField(
        max_length=50,
        default='code',
        choices=[
            ('code', 'AdSense code snippet'),
            ('adstxt', 'Ads.txt snippet'),
            ('meta', 'Meta tag'),
        ],
        help_text='AdSense verification method for your site'
    )
    enable_adsense_code = models.BooleanField(
        default=True,
        help_text='Automatically add AdSense code snippet to <head> on all pages'
    )
    adsense_code_snippet = models.TextField(
        blank=True,
        default='<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3956705237421931" crossorigin="anonymous"></script>',
        help_text='AdSense code snippet inserted between <head> tags'
    )
    enable_adsense_meta = models.BooleanField(
        default=True,
        help_text='Automatically add AdSense meta tag to <head> on all pages'
    )
    adsense_meta_tag = models.TextField(
        blank=True,
        default='<meta name="google-adsense-account" content="ca-pub-3956705237421931">',
        help_text='AdSense verification meta tag inserted between <head> tags'
    )
    enable_ads_txt = models.BooleanField(
        default=True,
        help_text='Enable serving ads.txt file'
    )
    ads_txt_content = models.TextField(
        blank=True,
        default='google.com, pub-3956705237421931, DIRECT, f08c47fec0942fa0',
        help_text='Content for /ads.txt file (Google AdSense and authorized digital sellers)'
    )
    
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

    # Email & Subscriber Notification Settings
    sender_email = models.EmailField(
        blank=True,
        default='',
        help_text='The "From" email address displayed to subscribers (leave blank to use contact email)'
    )
    email_host = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='SMTP Host, e.g. smtp.gmail.com or smtp.zoho.com'
    )
    email_port = models.PositiveIntegerField(
        default=587,
        blank=True,
        help_text='SMTP Port (usually 587 for TLS or 465 for SSL)'
    )
    email_host_user = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='SMTP Username / Email address'
    )
    email_host_password = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='SMTP Password or App Password'
    )
    email_use_tls = models.BooleanField(
        default=True,
        help_text='Use TLS encryption (recommended for port 587)'
    )
    auto_email_on_quiz = models.BooleanField(
        default=False,
        help_text='Automatically email subscribers when a new Quiz is published'
    )
    auto_email_on_note = models.BooleanField(
        default=False,
        help_text='Automatically email subscribers when a new Study Note is published'
    )
    auto_email_on_blog = models.BooleanField(
        default=False,
        help_text='Automatically email subscribers when a new Blog article is published'
    )
    auto_email_on_download = models.BooleanField(
        default=False,
        help_text='Automatically email subscribers when a new Download file is published'
    )

    # AI Auto-Blogger & Auto-Notes Configuration
    ai_provider = models.CharField(
        max_length=20,
        default='gemini',
        choices=[
            ('gemini', 'Google Gemini (Google AI Studio)'),
            ('groq', 'Groq (Llama 3.3 70B - Free, Ultra-Fast, No Rate Limits)'),
        ],
        help_text='AI Engine provider for content generation'
    )
    gemini_api_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Google Gemini API Key from Google AI Studio (aistudio.google.com)'
    )
    groq_api_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Groq API Key (starts with gsk_...) from console.groq.com'
    )
    gemini_model = models.CharField(
        max_length=100,
        default='gemini-3.8-flash',
        choices=[
            ('gemini-3.8-flash', 'Gemini 3.8 Flash (Google)'),
            ('gemini-3.5-flash-lite', 'Gemini 3.5 Flash-Lite (Google)'),
            ('llama-3.3-70b-versatile', 'Llama 3.3 70B Versatile (Groq - Recommended)'),
            ('llama-3.1-8b-instant', 'Llama 3.1 8B Instant (Groq - Super Fast)'),
        ],
        help_text='AI model engine for article generation'
    )
    enable_daily_ai_blog = models.BooleanField(
        default=False,
        help_text='Enable daily automated generation of 1 blog post'
    )
    enable_daily_ai_note = models.BooleanField(
        default=False,
        help_text='Enable daily automated generation of 1 study note'
    )
    ai_blog_publish_mode = models.CharField(
        max_length=20,
        default='published',
        choices=[
            ('published', 'Publish Immediately (Live)'),
            ('draft', 'Save as Draft (Require Review)'),
        ],
        help_text='Publication status for auto-generated blogs'
    )
    ai_note_publish_mode = models.CharField(
        max_length=20,
        default='published',
        choices=[
            ('published', 'Publish Immediately (Live)'),
            ('draft', 'Save as Draft (Require Review)'),
        ],
        help_text='Publication status for auto-generated notes'
    )
    ai_default_language = models.CharField(
        max_length=20,
        default='bilingual',
        choices=[
            ('bilingual', 'Bilingual (नेपाली with English terms - Recommended)'),
            ('ne', 'Pure Nepali (नेपाली - देवनागरी)'),
            ('en', 'English'),
        ],
        help_text='Default language for generated articles'
    )
    ai_default_blog_category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='default_ai_blogs',
        limit_choices_to={'module': 'blog'},
        help_text='Default category for auto-generated blogs if none specified'
    )
    ai_default_note_category = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='default_ai_notes',
        limit_choices_to={'module': 'notes'},
        help_text='Default category for auto-generated notes if none specified'
    )
    last_ai_blog_at = models.DateTimeField(null=True, blank=True)
    last_ai_note_at = models.DateTimeField(null=True, blank=True)

    # Maintenance Mode Suite
    maintenance_mode = models.BooleanField(
        default=False,
        help_text='If checked, full maintenance screen is displayed to regular visitors. Staff and admins can still access the site and admin panel.'
    )
    maintenance_banner_only = models.BooleanField(
        default=False,
        help_text='If checked instead of full lockdown, the site stays accessible with a visible top warning banner.'
    )
    maintenance_message = models.TextField(
        default='We are currently performing scheduled platform maintenance and upgrades. We will be back online shortly!',
        blank=True,
        help_text='Custom message shown on the maintenance page and top banner'
    )
    maintenance_estimated_end = models.CharField(
        max_length=150,
        blank=True,
        default='Under 1 hour',
        help_text='Estimated downtime shown to visitors (e.g., "Under 30 minutes", "10:30 PM NST")'
    )

    # YouTube & Study Break Rewards
    enable_video_break_rewards = models.BooleanField(
        default=True,
        help_text='Master switch to enable or disable floating study break and completion reward video popups across the site'
    )
    video_break_popup_delay = models.PositiveIntegerField(
        default=18,
        help_text='Delay in seconds before the floating break card appears on lesson/blog pages (default: 18 seconds)'
    )
    video_break_scroll_threshold = models.PositiveIntegerField(
        default=65,
        help_text='Scroll percentage (0-100%) down a lesson or note before triggering the study break card (default: 65%)'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name


class Subscriber(models.Model):
    """Email alert and newsletter subscriber"""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, default='homepage_newsletter', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'

    def __str__(self):
        return self.email


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
        """Return current visitor count, creating the record if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'count': 0})
        return obj.count

    @classmethod
    def increment(cls):
        """Legacy method kept for compatibility. Middleware now uses F() directly."""
        from django.db.models import F
        updated = cls.objects.filter(pk=1).update(count=F('count') + 1)
        if updated == 0:
            obj, _ = cls.objects.get_or_create(pk=1, defaults={'count': 1})
            return obj.count
        return cls.objects.get(pk=1).count


class VisitorLog(models.Model):
    """Detailed log of each visitor page view"""
    ip_address = models.CharField(max_length=50, db_index=True)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, default='GET')
    referrer = models.CharField(max_length=500, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=30, default='Desktop')  # Mobile, Tablet, Desktop
    browser = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=60, default='Nepal')
    city = models.CharField(max_length=60, blank=True, null=True)
    isp = models.CharField(max_length=100, blank=True, null=True)
    session_key = models.CharField(max_length=60, blank=True, null=True, db_index=True)
    is_bot = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Visitor Log'
        verbose_name_plural = 'Visitor Logs'

    def __str__(self):
        return f"{self.ip_address} visited {self.path} ({self.device_type}) at {self.timestamp}"


class AITopicQueue(models.Model):
    """Queue of topics for automated or 1-click AI generation"""
    CONTENT_TYPE_CHOICES = [
        ('blog', 'Blog Post (लेख / ब्लग)'),
        ('note', 'Study Note (अध्ययन सामग्री / नोट)'),
    ]
    LANGUAGE_CHOICES = [
        ('bilingual', 'Bilingual (नेपाली + English)'),
        ('ne', 'Nepali (नेपाली - देवनागरी)'),
        ('en', 'English'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Queue'),
        ('generating', 'Generating...'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=350, help_text='Topic title or prompt idea')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='blog')
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_topics',
        help_text='Target category (optional, will fallback to default)'
    )
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='bilingual')
    prompt_hint = models.TextField(
        blank=True,
        help_text='Optional custom instructions, target audience, or specific subtopics to cover'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField(default=10, help_text='Lower number = higher priority')

    # Linked outputs
    generated_blog = models.ForeignKey(
        'blog.BlogPost',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_source_topics'
    )
    generated_note = models.ForeignKey(
        'notes.Note',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_source_topics'
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['priority', 'created_at']
        verbose_name = 'AI Topic Queue'
        verbose_name_plural = 'AI Topic Queue'

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title} ({self.status})"


class AIGenerationLog(models.Model):
    """Audit log of AI content generation events"""
    topic_title = models.CharField(max_length=350)
    content_type = models.CharField(max_length=20)
    language = models.CharField(max_length=20)
    status = models.CharField(max_length=20)  # success, error
    word_count = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    article_url = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Generation Log'
        verbose_name_plural = 'AI Generation Logs'

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.topic_title} ({self.status})"


class YouTubeVideo(models.Model):
    """Promoted YouTube videos and channels for popups, study breaks, and showcases"""
    title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Video title (auto-extracted from YouTube if left blank)"
    )
    youtube_url = models.CharField(
        max_length=350,
        help_text="Paste YouTube URL (e.g., https://www.youtube.com/watch?v=... or https://youtu.be/...) or 11-char Video ID"
    )
    video_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Auto-extracted 11-character YouTube video ID (automatically populated if left blank)"
    )
    category = models.CharField(
        max_length=100,
        default="🎧 Anime ASMR",
        help_text="e.g., 🎧 Anime ASMR, 🌸 Cozy Ambience, 💡 Tech & Learning, 🎮 Entertainment, ☕ Vlogs"
    )
    channel_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text="Channel name (auto-extracted from YouTube if left blank)"
    )
    channel_url = models.URLField(
        blank=True,
        default='',
        help_text="Channel link (auto-extracted with ?sub_confirmation=1 if left blank)"
    )
    custom_thumbnail = models.URLField(
        blank=True,
        help_text="Optional custom thumbnail image URL (auto-uses YouTube thumbnail if left empty)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Check to include this video in active rotating popups"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display priority (lower numbers appear first)"
    )
    # Analytics & Engagement Tracking
    views_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this video popup/card was displayed to visitors"
    )
    clicks_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times visitors clicked to watch/play this video"
    )
    sub_clicks_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times visitors clicked the + Subscribe button"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'YouTube Video'
        verbose_name_plural = 'YouTube Videos'

    def __str__(self):
        return f"{self.title or self.video_id} [{self.category}]"

    @property
    def click_through_rate(self):
        if self.views_count > 0:
            return round(((self.clicks_count + self.sub_clicks_count) / self.views_count) * 100, 1)
        return 0.0

    def clean(self):
        self.fetch_youtube_metadata()

    def save(self, *args, **kwargs):
        self.fetch_youtube_metadata()
        super().save(*args, **kwargs)

    def extract_video_id(self):
        if not self.youtube_url:
            return
        url = self.youtube_url.strip()
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})',
            r'shorts\/([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                self.video_id = match.group(1)
                return
        if len(url) == 11 and re.match(r'^[0-9A-Za-z_-]{11}$', url):
            self.video_id = url

    def fetch_youtube_metadata(self):
        self.extract_video_id()
        if not self.video_id:
            return

        # Auto-fetch title, channel name, channel URL, and thumbnail from YouTube oEmbed if missing
        if not self.title or not self.channel_name or not self.channel_url:
            try:
                import urllib.request
                import json
                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={self.video_id}&format=json"
                req = urllib.request.Request(
                    oembed_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if not self.title and data.get('title'):
                        self.title = str(data.get('title'))[:250]
                    if not self.channel_name and data.get('author_name'):
                        self.channel_name = str(data.get('author_name'))[:145]
                    if not self.channel_url and data.get('author_url'):
                        c_url = data.get('author_url')
                        if '?sub_confirmation=1' not in c_url:
                            c_url = f"{c_url}?sub_confirmation=1"
                        self.channel_url = c_url
                    if not self.custom_thumbnail and data.get('thumbnail_url'):
                        self.custom_thumbnail = data.get('thumbnail_url')
            except Exception:
                pass

        if not self.title:
            self.title = f"YouTube Video ({self.video_id})"
        if not self.channel_name:
            self.channel_name = "Featured Channel"
        if not self.channel_url:
            self.channel_url = f"https://www.youtube.com/watch?v={self.video_id}"




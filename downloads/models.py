import os
import uuid
from django.conf import settings as django_settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.models import Category, Tag


class Download(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('ppt', 'PPT'),
        ('zip', 'ZIP'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'module': 'downloads'},
        related_name='downloads'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='downloads')
    description = models.TextField()
    summary = models.TextField(max_length=500, help_text='Brief summary for SEO')
    file = models.FileField(upload_to='downloads/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, blank=True, default='pdf')
    file_size = models.CharField(max_length=50, blank=True, help_text='e.g. 2.5 MB')
    thumbnail = models.ImageField(upload_to='downloads/thumbnails/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('downloads:detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.summary

    def save(self, *args, **kwargs):
        # 1. Ensure upload destination directory exists
        try:
            upload_dir = os.path.join(django_settings.MEDIA_ROOT, 'downloads')
            os.makedirs(upload_dir, exist_ok=True)
            thumbs_dir = os.path.join(upload_dir, 'thumbnails')
            os.makedirs(thumbs_dir, exist_ok=True)
        except Exception:
            pass

        # 2. Auto-generate unique slug if not set or empty
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = f"download-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            counter = 1
            while Download.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # 3. Auto-detect file type from extension if missing or other
        if self.file and (not self.file_type or self.file_type == 'other'):
            fname = getattr(self.file, 'name', '') or ''
            ext = os.path.splitext(fname)[1].lower().lstrip('.')
            if ext == 'pdf':
                self.file_type = 'pdf'
            elif ext in ['doc', 'docx']:
                self.file_type = 'docx'
            elif ext in ['ppt', 'pptx']:
                self.file_type = 'ppt'
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
                self.file_type = 'zip'
            elif not self.file_type:
                self.file_type = 'other'

        # 4. Auto-compute human-readable file size if blank
        if self.file and not self.file_size:
            try:
                size = self.file.size
                if size < 1024:
                    self.file_size = f"{size} B"
                elif size < 1024 * 1024:
                    self.file_size = f"{size / 1024:.1f} KB"
                else:
                    self.file_size = f"{size / (1024 * 1024):.1f} MB"
            except Exception:
                pass

        # 5. Check publish status transition
        is_new = self.pk is None
        was_published = False
        if not is_new:
            try:
                orig = Download.objects.get(pk=self.pk)
                was_published = orig.is_published
            except Download.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # 6. Trigger notification if freshly published
        if self.is_published and not was_published:
            try:
                from core.models import SiteSettings
                from core.emails import trigger_auto_email_notification
                settings = SiteSettings.objects.first()
                if settings and settings.auto_email_on_download:
                    trigger_auto_email_notification(
                        content_type='download',
                        title=self.title,
                        description=self.summary or self.description,
                        url=self.get_absolute_url()
                    )
            except Exception:
                pass

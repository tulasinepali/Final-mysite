from django.db import models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from core.models import Category, Tag


class Note(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'module': 'notes'},
        related_name='notes'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='notes')
    content = CKEditor5Field('Content', config_name='notes_toolbar')
    summary = models.TextField(max_length=500, help_text='Brief summary for SEO and cards')
    featured_image = models.ImageField(upload_to='notes/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True, help_text='SEO title')
    meta_description = models.CharField(max_length=300, blank=True, help_text='SEO description')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('notes:detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.summary

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_published = False
        if not is_new:
            try:
                orig = Note.objects.get(pk=self.pk)
                was_published = orig.is_published
            except Note.DoesNotExist:
                pass
        super().save(*args, **kwargs)

        if self.is_published and not was_published:
            try:
                from core.models import SiteSettings
                from core.emails import trigger_auto_email_notification
                settings = SiteSettings.objects.first()
                if settings and settings.auto_email_on_note:
                    trigger_auto_email_notification(
                        content_type='note',
                        title=self.title,
                        description=self.summary,
                        url=self.get_absolute_url()
                    )
            except Exception:
                pass

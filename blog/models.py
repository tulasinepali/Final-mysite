from django.db import models
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from core.models import Category, Tag


class BlogPost(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'module': 'blog'},
        related_name='blog_posts'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='blog_posts')
    content = CKEditor5Field('Content', config_name='blog_toolbar')
    summary = models.TextField(max_length=500, help_text='Brief summary for SEO and cards')
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.summary

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_published = False
        if not is_new:
            try:
                orig = BlogPost.objects.get(pk=self.pk)
                was_published = orig.is_published
            except BlogPost.DoesNotExist:
                pass
        super().save(*args, **kwargs)

        if self.is_published and not was_published:
            try:
                from core.models import SiteSettings
                from core.push_notifications import send_web_push_notification
                settings = SiteSettings.objects.first()
                if settings and settings.enable_web_push and settings.auto_push_on_blog:
                    send_web_push_notification(
                        title=f"📝 New Post: {self.title}",
                        message=self.summary[:120] if self.summary else "Read our latest Loksewa preparation guide now.",
                        url=self.get_absolute_url()
                    )
            except Exception:
                pass


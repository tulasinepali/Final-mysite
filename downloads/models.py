from django.db import models
from django.urls import reverse
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
    slug = models.SlugField(unique=True)
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
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
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

from django.contrib.sitemaps import Sitemap
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz


class NotesSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Note.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at


class DownloadsSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Download.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at


class QuizSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Quiz.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at
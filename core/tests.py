from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Category, VisitorCount, VisitorLog
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz
from core.middleware import is_admin_or_staff


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminUntrackedVisitsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_tester',
            email='admin@test.com',
            password='Password123!'
        )
        self.category = Category.objects.create(name='Technology', slug='tech')
        self.note = Note.objects.create(
            title='Python Guide',
            slug='python-guide',
            category=self.category,
            content='Test content',
            is_published=True,
            views=0
        )
        self.blog_post = BlogPost.objects.create(
            title='Django Analytics',
            slug='django-analytics',
            category=self.category,
            content='Blog content',
            is_published=True,
            views=0
        )
        self.download = Download.objects.create(
            title='Cheat Sheet',
            slug='cheat-sheet',
            category=self.category,
            download_count=0,
            is_published=True
        )

    def test_public_visitor_is_tracked(self):
        """Standard public visitor should be counted in VisitorCount, VisitorLog, and page views."""
        initial_count = VisitorCount.objects.first().count if VisitorCount.objects.exists() else 0
        
        # Visit blog detail
        res = self.client.get(reverse('blog:detail', kwargs={'slug': self.blog_post.slug}))
        self.assertEqual(res.status_code, 200)

        # VisitorLog should be recorded
        self.assertTrue(VisitorLog.objects.filter(path=self.blog_post.get_absolute_url()).exists())

        # Blog post views incremented
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.views, 1)

        # Note views incremented
        res_note = self.client.get(reverse('notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(res_note.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.views, 1)

    def test_admin_authenticated_visit_is_untracked(self):
        """Staff/admin visit should NOT increment VisitorCount, VisitorLog, or content views."""
        self.client.login(username='admin_tester', password='Password123!')

        # Clear prior logs
        VisitorLog.objects.all().delete()
        initial_blog_views = self.blog_post.views
        initial_note_views = self.note.views

        # Admin visits note detail
        res = self.client.get(reverse('notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(res.status_code, 200)
        
        # Verify DNT cookie was set for the admin browser
        self.assertEqual(res.cookies.get('admin_do_not_track').value, '1')

        # Note view counter must remain unchanged
        self.note.refresh_from_db()
        self.assertEqual(self.note.views, initial_note_views)

        # Admin visits blog detail
        res_blog = self.client.get(reverse('blog:detail', kwargs={'slug': self.blog_post.slug}))
        self.assertEqual(res_blog.status_code, 200)
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.views, initial_blog_views)

        # No VisitorLog recorded for admin visit
        self.assertFalse(VisitorLog.objects.filter(path=self.note.get_absolute_url()).exists())
        self.assertFalse(VisitorLog.objects.filter(path=self.blog_post.get_absolute_url()).exists())

    def test_browser_with_dnt_cookie_is_untracked_even_when_unauthenticated(self):
        """Even if logged out, a browser with admin_do_not_track=1 cookie must remain untracked."""
        self.client.cookies['admin_do_not_track'] = '1'

        VisitorLog.objects.all().delete()
        initial_note_views = self.note.views

        res = self.client.get(reverse('notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(res.status_code, 200)

        # Must not increment views or create logs
        self.note.refresh_from_db()
        self.assertEqual(self.note.views, initial_note_views)
        self.assertFalse(VisitorLog.objects.filter(path=self.note.get_absolute_url()).exists())

    def test_toggle_admin_tracking_endpoint(self):
        """Test the dashboard toggle action to set and clear the untracked protection cookie."""
        self.client.login(username='admin_tester', password='Password123!')
        toggle_url = reverse('dashboard:visitor_logs_toggle_admin')

        # First call: already has cookie or sets it
        res = self.client.get(toggle_url, follow=True)
        self.assertEqual(res.status_code, 200)

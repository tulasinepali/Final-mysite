from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from blog.models import BlogPost, Comment
from core.models import Category, VisitorLog


class CommentAndVisitorLogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Tech', slug='tech', module='blog')
        self.post = BlogPost.objects.create(
            title='Test Blog Post',
            slug='test-blog-post',
            content='Test content',
            category=self.category,
            is_published=True
        )
        self.staff_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.client = Client()

    def test_post_comment_public(self):
        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        response = self.client.post(url, {
            'name': 'John Doe',
            'email': 'john@example.com',
            'content': 'Great article!',
            'hp_website': '',  # Honeypot empty
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.name, 'John Doe')
        self.assertTrue(comment.is_approved)

    def test_honeypot_spam_trap(self):
        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        response = self.client.post(url, {
            'name': 'Spam Bot',
            'email': 'bot@example.com',
            'content': 'Buy cheap links',
            'hp_website': 'http://spam.com',  # Honeypot filled by bot
        })
        self.assertEqual(response.status_code, 302)
        # Should NOT create comment
        self.assertEqual(Comment.objects.count(), 0)

    def test_dashboard_comments_and_reply(self):
        comment = Comment.objects.create(
            post=self.post,
            name='Reader One',
            email='reader@example.com',
            content='Question on article',
            is_approved=True
        )
        self.client.login(username='admin', password='adminpassword')
        
        # Test dashboard list
        list_url = reverse('dashboard:comments')
        res = self.client.get(list_url)
        self.assertEqual(res.status_code, 200)

        # Test toggle approve
        toggle_url = reverse('dashboard:comment_toggle_approve', kwargs={'pk': comment.pk})
        res = self.client.get(toggle_url)
        self.assertEqual(res.status_code, 302)
        comment.refresh_from_db()
        self.assertFalse(comment.is_approved)

        # Test admin reply
        reply_url = reverse('dashboard:comment_reply', kwargs={'pk': comment.pk})
        res = self.client.post(reply_url, {'content': 'Here is the answer!'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Comment.objects.count(), 2)
        reply = Comment.objects.filter(parent=comment).first()
        self.assertIsNotNone(reply)
        self.assertTrue(reply.is_author_reply)

    def test_visitor_log_middleware_and_dashboard(self):
        # Public page visit creates VisitorLog
        res = self.client.get(reverse('blog:list'))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(VisitorLog.objects.filter(path=reverse('blog:list')).exists())

        # Test dashboard visitor logs view
        self.client.login(username='admin', password='adminpassword')
        v_url = reverse('dashboard:visitor_logs')
        res = self.client.get(v_url)
        self.assertEqual(res.status_code, 200)

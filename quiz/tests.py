from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from quiz.models import Quiz, Question, QuizFeedback
from core.models import Category


class QuizFeedbackTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='GK', slug='gk', module='quiz')
        self.quiz = Quiz.objects.create(
            title='General Knowledge Test',
            slug='general-knowledge-test',
            category=self.category,
            is_published=True
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text='What is the capital of Nepal?',
            option_a='Pokhara',
            option_b='Kathmandu',
            option_c='Lalitpur',
            option_d='Biratnagar',
            correct_answer='B',
            order=1
        )
        self.staff_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.client = Client()

    def test_submit_quiz_rating_ajax(self):
        url = reverse('quiz:feedback_submit', kwargs={'slug': self.quiz.slug})
        response = self.client.post(
            url,
            {
                'name': 'Bikash',
                'rating': '5',
                'feedback_type': 'general',
                'message': 'Very helpful practice questions!',
                'hp_subject': '',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizFeedback.objects.count(), 1)
        fb = QuizFeedback.objects.first()
        self.assertEqual(fb.name, 'Bikash')
        self.assertEqual(fb.rating, 5)
        self.assertEqual(fb.quiz, self.quiz)
        self.assertIsNone(fb.question)

    def test_submit_question_error_report(self):
        url = reverse('quiz:feedback_submit', kwargs={'slug': self.quiz.slug})
        response = self.client.post(
            url,
            {
                'name': 'Student',
                'question_id': str(self.question.id),
                'feedback_type': 'question_error',
                'rating': '3',
                'message': '[Typo] Spelling in option B',
                'hp_subject': '',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizFeedback.objects.count(), 1)
        fb = QuizFeedback.objects.first()
        self.assertEqual(fb.feedback_type, 'question_error')
        self.assertEqual(fb.question, self.question)

    def test_honeypot_trap(self):
        url = reverse('quiz:feedback_submit', kwargs={'slug': self.quiz.slug})
        response = self.client.post(
            url,
            {
                'name': 'Bot',
                'message': 'Spam message',
                'hp_subject': 'I am a spam bot',
            }
        )
        self.assertEqual(response.status_code, 302)
        # Should NOT save feedback
        self.assertEqual(QuizFeedback.objects.count(), 0)

    def test_dashboard_feedbacks_management(self):
        fb = QuizFeedback.objects.create(
            quiz=self.quiz,
            question=self.question,
            name='Student One',
            rating=4,
            message='Great quiz!',
            is_reviewed=False
        )
        self.client.login(username='admin', password='adminpassword')
        
        # Test dashboard list
        list_url = reverse('dashboard:quiz_feedbacks')
        res = self.client.get(list_url)
        self.assertEqual(res.status_code, 200)

        # Test toggle review
        toggle_url = reverse('dashboard:quiz_feedback_toggle_review', kwargs={'pk': fb.pk})
        res = self.client.get(toggle_url)
        self.assertEqual(res.status_code, 302)
        fb.refresh_from_db()
        self.assertTrue(fb.is_reviewed)

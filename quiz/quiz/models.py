from django.db import models
from django.urls import reverse
from core.models import Category


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        limit_choices_to={'module': 'quiz'},
        related_name='quizzes'
    )
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    time_limit = models.PositiveIntegerField(default=0, help_text='Time in minutes. 0 = no time limit')
    negative_marking = models.BooleanField(default=False, help_text='Enable negative marking for wrong answers')
    negative_marking_value = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25,
        help_text='Marks deducted per wrong answer (e.g., 0.25 means 0.25 marks deducted). Only applies if negative marking is enabled.'
    )
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('quiz:detail', kwargs={'slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or f"{self.title} - MCQ Practice"

    def get_meta_description(self):
        return self.meta_description or self.description


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ])
    explanation = models.TextField(blank=True, help_text='Explanation shown after answering')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_attempts')
    session_key = models.CharField(max_length=100, blank=True)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0, help_text='Number of correctly answered questions')
    incorrect_count = models.PositiveIntegerField(default=0, help_text='Number of wrongly answered questions')
    unanswered_count = models.PositiveIntegerField(default=0, help_text='Number of unanswered questions')
    negative_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='Total marks deducted due to negative marking')
    final_score = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='Final score after negative marking (correct - negative_marks)')
    answers = models.JSONField(default=dict, help_text='Store answers as {"question_id": "selected_option"}')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"Attempt on {self.quiz.title} - Score: {self.final_score}/{self.total_questions}"

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((float(self.final_score) / self.total_questions) * 100, 1)

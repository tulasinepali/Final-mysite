import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz, Question, QuizAttempt
from core.models import Category

def quiz_list(request):
    quizzes = Quiz.objects.filter(is_published=True)
    
    category_slug = request.GET.get('category')
    if category_slug:
        quizzes = quizzes.filter(category__slug=category_slug)
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)
    
    categories = Category.objects.filter(module='quiz', is_active=True)
    
    paginator = Paginator(quizzes, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'current_difficulty': difficulty,
        'meta_title': 'MCQ Practice - Learning Platform',
        'meta_description': 'Practice MCQ questions for free! No login required. Test your knowledge in Computer, English, GK, and more.',
    }
    return render(request, 'quiz/list.html', context)

def quiz_detail(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    questions = quiz.questions.all()
    
    # Shuffle questions for variety
    question_list = list(questions)
    random.shuffle(question_list)
    
    context = {
        'quiz': quiz,
        'questions': question_list,
        'total_questions': len(question_list),
        'meta_title': quiz.get_meta_title(),
        'meta_description': quiz.get_meta_description(),
    }
    return render(request, 'quiz/detail.html', context)

def quiz_result(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    
    if request.method == 'POST':
        answers = {}
        score = 0
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        questions = quiz.questions.all()
        total_questions = len(questions)
        
        for question in questions:
            selected = request.POST.get(f'question_{question.id}', '')
            answers[str(question.id)] = selected
            if selected == question.correct_answer:
                score += 1
                correct_count += 1
            elif selected:
                incorrect_count += 1
            else:
                unanswered_count += 1
        
        # Calculate negative marking
        negative_marks = 0
        final_score = score
        if quiz.negative_marking and incorrect_count > 0:
            negative_marks = float(quiz.negative_marking_value) * incorrect_count
            final_score = max(0, score - negative_marks)  # Score cannot go below 0
        
        # Save attempt (NO LOGIN REQUIRED)
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            session_key=request.session.session_key or '',
            score=score,
            total_questions=total_questions,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count,
            negative_marks=negative_marks,
            final_score=final_score,
            answers=answers,
        )
        
        # Increment quiz attempts
        quiz.attempts += 1
        quiz.save(update_fields=['attempts'])
        
        percentage = round((final_score / total_questions) * 100, 1) if total_questions > 0 else 0
        
        context = {
            'quiz': quiz,
            'score': score,
            'total_questions': total_questions,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'unanswered_count': unanswered_count,
            'negative_marks': negative_marks,
            'final_score': final_score,
            'percentage': percentage,
            'questions': questions,
            'user_answers': answers,
            'attempt': attempt,
            'meta_title': f'Quiz Results - {quiz.title}',
            'meta_description': f'You scored {final_score}/{total_questions} on {quiz.title}',
        }
        return render(request, 'quiz/result.html', context)
    
    return redirect('quiz:detail', slug=slug)

def quiz_leaderboard(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    top_attempts = QuizAttempt.objects.filter(quiz=quiz).order_by('-final_score', 'completed_at')[:20]
    
    context = {
        'quiz': quiz,
        'top_attempts': top_attempts,
        'meta_title': f'Leaderboard - {quiz.title}',
    }
    return render(request, 'quiz/leaderboard.html', context)

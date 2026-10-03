import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz, Question, QuizAttempt, QuizFeedback
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
        marks_per_question = 2  # Each question is worth 2 marks
        total_marks = total_questions * marks_per_question
        
        for question in questions:
            selected = request.POST.get(f'question_{question.id}', '')
            answers[str(question.id)] = selected
            if selected == question.correct_answer:
                score += marks_per_question
                correct_count += 1
            elif selected:
                incorrect_count += 1
            else:
                unanswered_count += 1
        
        # Calculate negative marking
        negative_marks = 0
        final_score = score
        penalty_percent = 0
        marks_deducted_per_wrong = 0
        if quiz.negative_marking:
            # Get the penalty value from the quiz
            try:
                penalty_percent = float(quiz.negative_marking_value)
            except (TypeError, ValueError):
                penalty_percent = 20.0
            # If value < 1, it's from the old system (stored as marks, e.g. 0.2 = 20%)
            # Convert to percentage by multiplying by 100
            if 0 < penalty_percent < 1:
                penalty_percent = penalty_percent * 100
            if penalty_percent <= 0:
                penalty_percent = 20.0
            # Calculate deduction: X% of marks_per_question per wrong answer
            if incorrect_count > 0:
                marks_deducted_per_wrong = round((penalty_percent / 100) * marks_per_question, 2)
                negative_marks = round(marks_deducted_per_wrong * incorrect_count, 2)
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
        
        percentage = round((float(final_score) / total_marks) * 100, 1) if total_marks > 0 else 0
        
        context = {
            'quiz': quiz,
            'score': score,
            'total_questions': total_questions,
            'total_marks': total_marks,
            'marks_per_question': marks_per_question,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'unanswered_count': unanswered_count,
            'negative_marks': negative_marks,
            'final_score': final_score,
            'percentage': percentage,
            'penalty_percent': penalty_percent,
            'marks_deducted_per_wrong': marks_deducted_per_wrong,
            'questions': questions,
            'user_answers': answers,
            'attempt': attempt,
            'meta_title': f'Quiz Results - {quiz.title}',
            'meta_description': f'You scored {final_score}/{total_marks} on {quiz.title}',
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


def quiz_feedback_submit(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    if request.method == 'POST':
        # Honeypot spam trap
        honeypot = request.POST.get('hp_subject', '').strip()
        if honeypot:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'message': 'Thank you for your feedback!'})
            return redirect('quiz:detail', slug=slug)

        name = request.POST.get('name', '').strip() or 'Student / Visitor'
        feedback_type = request.POST.get('feedback_type', 'general')
        message = request.POST.get('message', '').strip()
        question_id = request.POST.get('question_id')

        try:
            rating = int(request.POST.get('rating', 5))
            if rating < 1 or rating > 5:
                rating = 5
        except (ValueError, TypeError):
            rating = 5

        question_obj = None
        if question_id:
            try:
                question_obj = Question.objects.get(pk=int(question_id), quiz=quiz)
            except (Question.DoesNotExist, ValueError):
                pass

        if message:
            # Client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', '')

            QuizFeedback.objects.create(
                quiz=quiz,
                question=question_obj,
                name=name[:120],
                rating=rating,
                feedback_type=feedback_type,
                message=message,
                ip_address=ip[:50] if ip else None
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
                return JsonResponse({'status': 'ok', 'message': 'Thank you! Your feedback has been sent to the instructor.'})

            messages.success(request, 'Thank you! Your feedback has been sent to the instructor.')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
                return JsonResponse({'status': 'error', 'message': 'Please provide feedback text before submitting.'}, status=400)
            messages.error(request, 'Please provide feedback text before submitting.')

    return redirect(request.META.get('HTTP_REFERER') or reverse('quiz:detail', kwargs={'slug': slug}))


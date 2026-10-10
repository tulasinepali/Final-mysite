from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.http import HttpResponse
import json
import csv
from django.utils.safestring import mark_safe
import openpyxl
from openpyxl import Workbook

from core.models import SiteSettings, Category, Tag, ContactMessage, AdPlacement, Subscriber, VisitorLog, AITopicQueue, AIGenerationLog
from core.ai_blogger import generate_content_for_topic, suggest_topics_with_gemini
from core.emails import send_broadcast_to_subscribers
from notes.models import Note
from blog.models import BlogPost, Comment
from downloads.models import Download
from quiz.models import Quiz, Question, QuizAttempt, QuizFeedback
import csv
import io
import json
from django.http import HttpResponse
from tools.models import Tool, Widget, WidgetSetting, PatroEvent, WidgetUsage
from .forms import (
    SiteSettingsForm, CategoryForm, TagForm, NoteForm, BlogPostForm,
    DownloadForm, QuizForm, QuestionForm, AdPlacementForm, QuestionImportForm,
    BroadcastEmailForm, ToolForm, WidgetForm, WidgetSettingForm,
    PatroEventForm, PatroEventImportForm,
)


# ========== DASHBOARD HOME ==========

@staff_member_required
def dashboard_home(request):
    total_notes = Note.objects.count()
    total_blogs = BlogPost.objects.count()
    total_downloads = Download.objects.count()
    total_quizzes = Quiz.objects.count()
    total_questions = Question.objects.count()
    total_quiz_attempts = QuizAttempt.objects.count()
    total_subscribers = Subscriber.objects.filter(is_active=True).count()
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    total_views = Note.objects.aggregate(total=Sum('views'))['total'] or 0
    total_blog_views = BlogPost.objects.aggregate(total=Sum('views'))['total'] or 0
    total_download_count = Download.objects.aggregate(total=Sum('download_count'))['total'] or 0

    recent_notes = Note.objects.order_by('-created_at')[:3]
    recent_blogs = BlogPost.objects.order_by('-created_at')[:3]
    recent_attempts = QuizAttempt.objects.select_related('quiz').order_by('-completed_at')[:3]
    recent_messages = ContactMessage.objects.order_by('-created_at')[:5]
    popular_notes = Note.objects.order_by('-views')[:3]
    popular_downloads = Download.objects.order_by('-download_count')[:3]

    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    attempts_by_day = QuizAttempt.objects.filter(
        completed_at__gte=seven_days_ago
    ).annotate(date=TruncDate('completed_at')).values('date').annotate(
        count=Count('id'), avg_score=Avg('final_score')
    ).order_by('date')

    quiz_chart_labels = [item['date'].strftime('%Y-%m-%d') if item['date'] else '' for item in attempts_by_day]
    quiz_chart_data = [item['count'] for item in attempts_by_day]
    quiz_avg_scores = [float(item['avg_score']) if item['avg_score'] else 0 for item in attempts_by_day]

    notes_by_category = Category.objects.filter(module='notes').annotate(count=Count('notes')).order_by('-count')
    blog_by_category = Category.objects.filter(module='blog').annotate(count=Count('blog_posts')).order_by('-count')
    quiz_difficulty = list(Quiz.objects.values('difficulty').annotate(count=Count('id')))

    context = {
        'total_notes': total_notes, 'total_blogs': total_blogs,
        'total_downloads': total_downloads, 'total_quizzes': total_quizzes,
        'total_questions': total_questions, 'total_quiz_attempts': total_quiz_attempts,
        'total_subscribers': total_subscribers,
        'unread_messages': unread_messages, 'total_views': total_views,
        'total_blog_views': total_blog_views, 'total_download_count': total_download_count,
        'recent_notes': recent_notes, 'recent_blogs': recent_blogs,
        'recent_attempts': recent_attempts, 'recent_messages': recent_messages,
        'popular_notes': popular_notes, 'popular_downloads': popular_downloads,
        'quiz_chart_labels': quiz_chart_labels, 'quiz_chart_data': quiz_chart_data,
        'quiz_avg_scores': quiz_avg_scores,
        'notes_by_category': notes_by_category, 'blog_by_category': blog_by_category,
        'quiz_difficulty': quiz_difficulty,
        'active_page': 'home',
    }
    return render(request, 'dashboard/home.html', context)


# ========== NOTES CRUD ==========

@staff_member_required
def dashboard_notes(request):
    notes = Note.objects.select_related('category').all()
    category_filter = request.GET.get('category')
    if category_filter:
        notes = notes.filter(category__slug=category_filter)
    published_filter = request.GET.get('published')
    if published_filter == 'yes':
        notes = notes.filter(is_published=True)
    elif published_filter == 'no':
        notes = notes.filter(is_published=False)
    search = request.GET.get('q')
    if search:
        notes = notes.filter(title__icontains=search)
    paginator = Paginator(notes.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.filter(module='notes')
    context = {
        'page_obj': page_obj, 'categories': categories,
        'active_page': 'notes', 'total': notes.count(),
    }
    return render(request, 'dashboard/notes.html', context)

@staff_member_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note created successfully!')
            return redirect('dashboard:notes')
    else:
        form = NoteForm()
    context = {'form': form, 'active_page': 'notes', 'action': 'Create', 'model_name': 'Note'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note updated successfully!')
            return redirect('dashboard:notes')
    else:
        form = NoteForm(instance=note)
    context = {'form': form, 'active_page': 'notes', 'action': 'Edit', 'model_name': 'Note', 'object': note}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
    return redirect('dashboard:notes')

@staff_member_required
def note_toggle_publish(request, pk):
    note = get_object_or_404(Note, pk=pk)
    note.is_published = not note.is_published
    note.save(update_fields=['is_published'])
    status = 'published' if note.is_published else 'unpublished'
    messages.success(request, f'Note {status} successfully!')
    return redirect('dashboard:notes')

@staff_member_required
def note_toggle_featured(request, pk):
    note = get_object_or_404(Note, pk=pk)
    note.is_featured = not note.is_featured
    note.save(update_fields=['is_featured'])
    status = 'featured' if note.is_featured else 'unfeatured'
    messages.success(request, f'Note {status} successfully!')
    return redirect('dashboard:notes')


# ========== BLOGS CRUD ==========

@staff_member_required
def dashboard_blogs(request):
    blogs = BlogPost.objects.select_related('category').all()
    category_filter = request.GET.get('category')
    if category_filter:
        blogs = blogs.filter(category__slug=category_filter)
    published_filter = request.GET.get('published')
    if published_filter == 'yes':
        blogs = blogs.filter(is_published=True)
    elif published_filter == 'no':
        blogs = blogs.filter(is_published=False)
    search = request.GET.get('q')
    if search:
        blogs = blogs.filter(title__icontains=search)
    paginator = Paginator(blogs.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.filter(module='blog')
    context = {
        'page_obj': page_obj, 'categories': categories,
        'active_page': 'blogs', 'total': blogs.count(),
    }
    return render(request, 'dashboard/blogs.html', context)

@staff_member_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post created successfully!')
            return redirect('dashboard:blogs')
    else:
        form = BlogPostForm()
    context = {'form': form, 'active_page': 'blogs', 'action': 'Create', 'model_name': 'Blog Post'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('dashboard:blogs')
    else:
        form = BlogPostForm(instance=post)
    context = {'form': form, 'active_page': 'blogs', 'action': 'Edit', 'model_name': 'Blog Post', 'object': post}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def blog_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Blog post deleted successfully!')
    return redirect('dashboard:blogs')

@staff_member_required
def blog_toggle_publish(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    post.is_published = not post.is_published
    post.save(update_fields=['is_published'])
    status = 'published' if post.is_published else 'unpublished'
    messages.success(request, f'Blog post {status} successfully!')
    return redirect('dashboard:blogs')

@staff_member_required
def blog_toggle_featured(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    post.is_featured = not post.is_featured
    post.save(update_fields=['is_featured'])
    status = 'featured' if post.is_featured else 'unfeatured'
    messages.success(request, f'Blog post {status} successfully!')
    return redirect('dashboard:blogs')


# ========== DOWNLOADS CRUD ==========

@staff_member_required
def dashboard_downloads(request):
    downloads = Download.objects.select_related('category').all()
    category_filter = request.GET.get('category')
    if category_filter:
        downloads = downloads.filter(category__slug=category_filter)
    published_filter = request.GET.get('published')
    if published_filter == 'yes':
        downloads = downloads.filter(is_published=True)
    elif published_filter == 'no':
        downloads = downloads.filter(is_published=False)
    search = request.GET.get('q')
    if search:
        downloads = downloads.filter(title__icontains=search)
    paginator = Paginator(downloads.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.filter(module='downloads')
    context = {
        'page_obj': page_obj, 'categories': categories,
        'active_page': 'downloads', 'total': downloads.count(),
    }
    return render(request, 'dashboard/downloads.html', context)

@staff_member_required
def download_create(request):
    if request.method == 'POST':
        form = DownloadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Download created successfully!')
                return redirect('dashboard:downloads')
            except Exception as e:
                messages.error(request, f'Failed to create download: {e}')
        else:
            messages.error(request, 'Please check the form for errors below.')
    else:
        form = DownloadForm()
    context = {'form': form, 'active_page': 'downloads', 'action': 'Create', 'model_name': 'Download'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def download_edit(request, pk):
    dl = get_object_or_404(Download, pk=pk)
    if request.method == 'POST':
        form = DownloadForm(request.POST, request.FILES, instance=dl)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Download updated successfully!')
                return redirect('dashboard:downloads')
            except Exception as e:
                messages.error(request, f'Failed to update download: {e}')
        else:
            messages.error(request, 'Please check the form for errors below.')
    else:
        form = DownloadForm(instance=dl)
    context = {'form': form, 'active_page': 'downloads', 'action': 'Edit', 'model_name': 'Download', 'object': dl}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def download_delete(request, pk):
    dl = get_object_or_404(Download, pk=pk)
    if request.method == 'POST':
        dl.delete()
        messages.success(request, 'Download deleted successfully!')
    return redirect('dashboard:downloads')

@staff_member_required
def download_toggle_publish(request, pk):
    dl = get_object_or_404(Download, pk=pk)
    dl.is_published = not dl.is_published
    dl.save(update_fields=['is_published'])
    status = 'published' if dl.is_published else 'unpublished'
    messages.success(request, f'Download {status} successfully!')
    return redirect('dashboard:downloads')

@staff_member_required
def download_toggle_featured(request, pk):
    dl = get_object_or_404(Download, pk=pk)
    dl.is_featured = not dl.is_featured
    dl.save(update_fields=['is_featured'])
    status = 'featured' if dl.is_featured else 'unfeatured'
    messages.success(request, f'Download {status} successfully!')
    return redirect('dashboard:downloads')


# ========== QUIZZES CRUD ==========

@staff_member_required
def dashboard_quizzes(request):
    quizzes = Quiz.objects.select_related('category').annotate(question_count=Count('questions'))
    category_filter = request.GET.get('category')
    if category_filter:
        quizzes = quizzes.filter(category__slug=category_filter)
    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        quizzes = quizzes.filter(difficulty=difficulty_filter)
    published_filter = request.GET.get('published')
    if published_filter == 'yes':
        quizzes = quizzes.filter(is_published=True)
    elif published_filter == 'no':
        quizzes = quizzes.filter(is_published=False)
    search = request.GET.get('q')
    if search:
        quizzes = quizzes.filter(title__icontains=search)
    paginator = Paginator(quizzes.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.filter(module='quiz')
    context = {
        'page_obj': page_obj, 'categories': categories,
        'active_page': 'quizzes', 'total': quizzes.count(),
    }
    return render(request, 'dashboard/quizzes.html', context)

@staff_member_required
def quiz_create(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect('dashboard:quizzes')
    else:
        form = QuizForm()
    context = {'form': form, 'active_page': 'quizzes', 'action': 'Create', 'model_name': 'Quiz'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect('dashboard:quizzes')
    else:
        form = QuizForm(instance=quiz)
    context = {'form': form, 'active_page': 'quizzes', 'action': 'Edit', 'model_name': 'Quiz', 'object': quiz}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
    return redirect('dashboard:quizzes')

@staff_member_required
def quiz_toggle_publish(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.is_published = not quiz.is_published
    quiz.save(update_fields=['is_published'])
    status = 'published' if quiz.is_published else 'unpublished'
    messages.success(request, f'Quiz {status} successfully!')
    return redirect('dashboard:quizzes')

@staff_member_required
def quiz_toggle_featured(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.is_featured = not quiz.is_featured
    quiz.save(update_fields=['is_featured'])
    status = 'featured' if quiz.is_featured else 'unfeatured'
    messages.success(request, f'Quiz {status} successfully!')
    return redirect('dashboard:quizzes')


@staff_member_required
def quiz_toggle_negative_marking(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.negative_marking = not quiz.negative_marking
    quiz.save(update_fields=['negative_marking'])
    status = 'enabled' if quiz.negative_marking else 'disabled'
    messages.success(request, f'Negative marking {status} for "{quiz.title}" successfully!')
    return redirect('dashboard:quizzes')


# ========== QUESTIONS CRUD (within Quiz context) ==========

@staff_member_required
def quiz_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.all().order_by('order')
    context = {
        'quiz': quiz, 'questions': questions,
        'active_page': 'quizzes',
    }
    return render(request, 'dashboard/questions.html', context)

@staff_member_required
def question_create(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    next_order = quiz.questions.count() + 1
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            if not question.order:
                question.order = next_order
            question.save()
            messages.success(request, f'Question #{question.order} added successfully!')
            if '_addanother' in request.POST:
                return redirect('dashboard:question_create', quiz_pk=quiz.pk)
            return redirect('dashboard:quiz_questions', pk=quiz.pk)
    else:
        form = QuestionForm(initial={'order': next_order})
    context = {'form': form, 'quiz': quiz, 'active_page': 'quizzes', 'action': 'Create', 'model_name': 'Question'}
    return render(request, 'dashboard/question_form.html', context)

@staff_member_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('dashboard:quiz_questions', pk=question.quiz.pk)
    else:
        form = QuestionForm(instance=question)
    context = {'form': form, 'quiz': question.quiz, 'active_page': 'quizzes', 'action': 'Edit', 'model_name': 'Question', 'object': question}
    return render(request, 'dashboard/question_form.html', context)

@staff_member_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    quiz_pk = question.quiz.pk
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
    return redirect('dashboard:quiz_questions', pk=quiz_pk)


# ========== QUESTION IMPORT FROM EXCEL ==========

@staff_member_required
def question_import_excel(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)

    if request.method == 'POST':
        form = QuestionImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            try:
                wb = openpyxl.load_workbook(excel_file)
                sheet = wb.active
            except Exception as e:
                messages.error(request, f'Invalid Excel file: {e}')
                return redirect('dashboard:question_import', quiz_pk=quiz.pk)

            # Expected headers
            required_headers = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            optional_headers = ['explanation', 'order']

            # Read header row
            headers = []
            for cell in sheet[1]:
                headers.append(str(cell.value).strip().lower() if cell.value else '')

            # Validate headers
            missing = [h for h in required_headers if h not in headers]
            if missing:
                messages.error(request, f'Missing required columns: {", ".join(missing)}. Please use the sample Excel format.')
                return redirect('dashboard:question_import', quiz_pk=quiz.pk)

            # Build column index map
            col_map = {}
            for i, h in enumerate(headers):
                if h in required_headers + optional_headers:
                    col_map[h] = i

            created_count = 0
            skipped_count = 0
            errors = []
            next_order = quiz.questions.count() + 1

            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                # Skip completely empty rows
                if not any(row):
                    continue

                question_text = row[col_map['question_text']] if 'question_text' in col_map and col_map['question_text'] < len(row) else None
                option_a = row[col_map['option_a']] if 'option_a' in col_map and col_map['option_a'] < len(row) else None
                option_b = row[col_map['option_b']] if 'option_b' in col_map and col_map['option_b'] < len(row) else None
                option_c = row[col_map['option_c']] if 'option_c' in col_map and col_map['option_c'] < len(row) else None
                option_d = row[col_map['option_d']] if 'option_d' in col_map and col_map['option_d'] < len(row) else None
                correct_answer = row[col_map['correct_answer']] if 'correct_answer' in col_map and col_map['correct_answer'] < len(row) else None

                # Convert to string and strip
                question_text = str(question_text).strip() if question_text else ''
                option_a = str(option_a).strip() if option_a else ''
                option_b = str(option_b).strip() if option_b else ''
                option_c = str(option_c).strip() if option_c else ''
                option_d = str(option_d).strip() if option_d else ''
                correct_answer = str(correct_answer).strip().upper() if correct_answer else ''

                # Validate required fields
                if not question_text or not option_a or not option_b or not option_c or not option_d:
                    skipped_count += 1
                    errors.append(f'Row {row_idx}: Missing required fields (question_text or options)')
                    continue

                if correct_answer not in ['A', 'B', 'C', 'D']:
                    skipped_count += 1
                    errors.append(f'Row {row_idx}: Invalid correct_answer "{correct_answer}". Must be A, B, C, or D.')
                    continue

                # Get optional fields
                explanation = ''
                if 'explanation' in col_map and col_map['explanation'] < len(row):
                    val = row[col_map['explanation']]
                    explanation = str(val).strip() if val else ''

                order = next_order
                if 'order' in col_map and col_map['order'] < len(row):
                    val = row[col_map['order']]
                    try:
                        order = int(val) if val else next_order
                    except (TypeError, ValueError):
                        order = next_order

                # Create the question
                Question.objects.create(
                    quiz=quiz,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    order=order,
                )
                created_count += 1
                next_order += 1

            # Build result message
            msg = f'Import complete: {created_count} question(s) imported successfully.'
            if skipped_count > 0:
                msg += f' {skipped_count} row(s) skipped due to errors.'
            messages.success(request, msg)

            if errors:
                for err in errors[:10]:  # Show first 10 errors
                    messages.warning(request, err)
                if len(errors) > 10:
                    messages.warning(request, f'... and {len(errors) - 10} more errors.')

            return redirect('dashboard:quiz_questions', pk=quiz.pk)
    else:
        form = QuestionImportForm()

    context = {
        'form': form,
        'quiz': quiz,
        'active_page': 'quizzes',
    }
    return render(request, 'dashboard/question_import.html', context)


@staff_member_required
def question_download_sample_excel(request, quiz_pk):
    """Download a sample Excel file with the correct format for importing questions."""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Questions'

    # Header row
    headers = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation', 'order']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = openpyxl.styles.Font(bold=True)
        cell.fill = openpyxl.styles.PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        cell.font = openpyxl.styles.Font(bold=True, color='FFFFFF')
        cell.alignment = openpyxl.styles.Alignment(horizontal='center')

    # Sample data rows
    sample_data = [
        ['What is the capital of Nepal?', 'Kathmandu', 'Pokhara', 'Biratnagar', 'Lalitpur', 'A', 'Kathmandu is the capital and largest city of Nepal.', 1],
        ['Which planet is closest to the Sun?', 'Venus', 'Mercury', 'Mars', 'Earth', 'B', 'Mercury is the closest planet to the Sun.', 2],
        ['What is the chemical formula for water?', 'CO2', 'H2O', 'NaCl', 'O2', 'B', 'H2O is the chemical formula for water.', 3],
        ['Who wrote "Ramayan"?', 'Valmiki', 'Vyas', 'Kalidas', 'Tulsidas', 'A', 'Valmiki is considered the author of the Ramayan.', 4],
        ['What does CPU stand for?', 'Central Processing Unit', 'Computer Personal Unit', 'Central Program Utility', 'Central Processor Unique', 'A', 'CPU stands for Central Processing Unit.', 5],
    ]

    for row_idx, row_data in enumerate(sample_data, 2):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Generate response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="sample_questions_{quiz.slug}.xlsx"'
    wb.save(response)
    return response


# ========== CATEGORIES CRUD ==========

@staff_member_required
def dashboard_categories(request):
    categories = Category.objects.all()
    module_filter = request.GET.get('module')
    if module_filter:
        categories = categories.filter(module=module_filter)
    paginator = Paginator(categories.order_by('module', 'order'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'page_obj': page_obj, 'active_page': 'categories', 'module_filter': module_filter}
    return render(request, 'dashboard/categories.html', context)

@staff_member_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('dashboard:categories')
    else:
        form = CategoryForm()
    context = {'form': form, 'active_page': 'categories', 'action': 'Create', 'model_name': 'Category'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('dashboard:categories')
    else:
        form = CategoryForm(instance=cat)
    context = {'form': form, 'active_page': 'categories', 'action': 'Edit', 'model_name': 'Category', 'object': cat}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted successfully!')
    return redirect('dashboard:categories')


# ========== TAGS CRUD ==========

@staff_member_required
def dashboard_tags(request):
    tags = Tag.objects.all()
    paginator = Paginator(tags.order_by('name'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'page_obj': page_obj, 'active_page': 'tags'}
    return render(request, 'dashboard/tags.html', context)

@staff_member_required
def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully!')
            return redirect('dashboard:tags')
    else:
        form = TagForm()
    context = {'form': form, 'active_page': 'tags', 'action': 'Create', 'model_name': 'Tag'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully!')
            return redirect('dashboard:tags')
    else:
        form = TagForm(instance=tag)
    context = {'form': form, 'active_page': 'tags', 'action': 'Edit', 'model_name': 'Tag', 'object': tag}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully!')
    return redirect('dashboard:tags')


# ========== MESSAGES ==========

@staff_member_required
def dashboard_messages(request):
    msgs = ContactMessage.objects.all()
    status_filter = request.GET.get('status')
    if status_filter == 'unread':
        msgs = msgs.filter(is_read=False)
    elif status_filter == 'read':
        msgs = msgs.filter(is_read=True)
    search = request.GET.get('q')
    if search:
        msgs = msgs.filter(subject__icontains=search)
    paginator = Paginator(msgs.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    unread = ContactMessage.objects.filter(is_read=False).count()
    context = {'page_obj': page_obj, 'unread': unread, 'active_page': 'messages'}
    return render(request, 'dashboard/messages.html', context)

@staff_member_required
def message_read(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    context = {'message': msg, 'active_page': 'messages'}
    return render(request, 'dashboard/message_detail.html', context)

@staff_member_required
def message_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, 'Message deleted successfully!')
    return redirect('dashboard:messages')


# ========== SETTINGS ==========

@staff_member_required
def dashboard_settings(request):
    settings = SiteSettings.objects.first()
    if not settings:
        settings = SiteSettings.objects.create()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('dashboard:settings')
    else:
        form = SiteSettingsForm(instance=settings)
    context = {'form': form, 'active_page': 'settings', 'action': 'Edit', 'model_name': 'Site Settings'}
    return render(request, 'dashboard/settings_form.html', context)


# ========== SUBSCRIBERS & BROADCAST ==========

@staff_member_required
def dashboard_subscribers(request):
    subscribers = Subscriber.objects.all()
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        subscribers = subscribers.filter(is_active=True)
    elif status_filter == 'inactive':
        subscribers = subscribers.filter(is_active=False)

    search = request.GET.get('q')
    if search:
        subscribers = subscribers.filter(email__icontains=search.strip())

    total_count = Subscriber.objects.count()
    active_count = Subscriber.objects.filter(is_active=True).count()
    inactive_count = total_count - active_count

    paginator = Paginator(subscribers.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'active_page': 'subscribers',
        'status_filter': status_filter,
        'search_query': search or '',
    }
    return render(request, 'dashboard/subscribers_list.html', context)


@staff_member_required
def subscriber_toggle_active(request, pk):
    sub = get_object_or_404(Subscriber, pk=pk)
    if request.method == 'POST':
        sub.is_active = not sub.is_active
        sub.save(update_fields=['is_active'])
        status_label = "activated" if sub.is_active else "deactivated"
        messages.success(request, f"Subscriber {sub.email} has been {status_label}.")
    return redirect('dashboard:subscribers')


@staff_member_required
def subscriber_delete(request, pk):
    sub = get_object_or_404(Subscriber, pk=pk)
    if request.method == 'POST':
        email = sub.email
        sub.delete()
        messages.success(request, f"Subscriber {email} removed successfully.")
    return redirect('dashboard:subscribers')


@staff_member_required
def subscriber_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Status', 'Date Subscribed', 'Subscription Source'])

    for sub in Subscriber.objects.all().order_by('-created_at'):
        status = 'Active' if sub.is_active else 'Inactive'
        date_str = sub.created_at.strftime('%Y-%m-%d %H:%M:%S') if sub.created_at else ''
        writer.writerow([sub.email, status, date_str, sub.source])

    return response


@staff_member_required
def dashboard_broadcast_email(request):
    site_settings = SiteSettings.objects.first()
    active_count = Subscriber.objects.filter(is_active=True).count()

    prefill_type = request.GET.get('prefill_type')
    prefill_id = request.GET.get('prefill_id')
    initial_data = {}

    if prefill_type and prefill_id:
        try:
            if prefill_type == 'quiz':
                q = Quiz.objects.get(pk=prefill_id)
                initial_data = {
                    'subject': f"[{site_settings.site_name if site_settings else 'Platform'}] 🚀 New Quiz: {q.title}",
                    'headline': f"Practice Test: {q.title}",
                    'body_content': f"<p>Hello Learner,</p><p>A brand new practice quiz is now live! Test your preparation with our timed exam simulator and detailed answer keys.</p><p><strong>Category:</strong> {q.category.name if q.category else 'General'}</p>",
                    'cta_text': "Start Practice Quiz Now",
                    'cta_url': request.build_absolute_uri(q.get_absolute_url()),
                }
            elif prefill_type == 'note':
                n = Note.objects.get(pk=prefill_id)
                initial_data = {
                    'subject': f"[{site_settings.site_name if site_settings else 'Platform'}] 📚 New Study Note: {n.title}",
                    'headline': f"Study Guide: {n.title}",
                    'body_content': f"<p>Hello Learner,</p><p>{n.summary or 'A comprehensive new study note has been published.'}</p><p>Explore key definitions, syllabus highlights, and expert revision notes.</p>",
                    'cta_text': "Read Complete Study Note",
                    'cta_url': request.build_absolute_uri(n.get_absolute_url()),
                }
            elif prefill_type == 'blog':
                b = BlogPost.objects.get(pk=prefill_id)
                initial_data = {
                    'subject': f"[{site_settings.site_name if site_settings else 'Platform'}] 📝 New Article: {b.title}",
                    'headline': f"Article: {b.title}",
                    'body_content': f"<p>Hello Learner,</p><p>{b.summary or 'A fresh article has been published on our platform.'}</p><p>Read the complete guide for valuable tips and insights.</p>",
                    'cta_text': "Read Full Article",
                    'cta_url': request.build_absolute_uri(b.get_absolute_url()),
                }
            elif prefill_type == 'download':
                d = Download.objects.get(pk=prefill_id)
                initial_data = {
                    'subject': f"[{site_settings.site_name if site_settings else 'Platform'}] 📥 New Resource: {d.title}",
                    'headline': f"Download: {d.title}",
                    'body_content': f"<p>Hello Learner,</p><p>A new free resource file ({d.file_type.upper()}) is ready for download: <strong>{d.title}</strong>.</p><p>{d.summary or d.description or 'Download it from our resource library.'}</p>",
                    'cta_text': "Download PDF Resource",
                    'cta_url': request.build_absolute_uri(d.get_absolute_url()),
                }
        except Exception:
            pass

    if request.method == 'POST':
        form = BroadcastEmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            headline = form.cleaned_data.get('headline') or subject
            body_content = form.cleaned_data['body_content']
            cta_text = form.cleaned_data.get('cta_text')
            cta_url = form.cleaned_data.get('cta_url')
            send_test_only = form.cleaned_data.get('send_test_only')
            test_email = form.cleaned_data.get('test_email')

            if send_test_only:
                recipients = [test_email]
                success, sent_count, err_msg = send_broadcast_to_subscribers(
                    subject=f"[PREVIEW TEST] {subject}",
                    headline=headline,
                    body_html=body_content,
                    cta_text=cta_text,
                    cta_url=cta_url,
                    recipient_list=recipients
                )
                if success:
                    messages.success(request, f"Test email successfully sent to {test_email}! Verify your inbox, then uncheck 'Send Test' to blast to all subscribers.")
                else:
                    messages.error(request, f"Failed to send test email: {err_msg}")
            else:
                if active_count == 0:
                    messages.warning(request, "There are currently 0 active subscribers to send to.")
                else:
                    success, sent_count, err_msg = send_broadcast_to_subscribers(
                        subject=subject,
                        headline=headline,
                        body_html=body_content,
                        cta_text=cta_text,
                        cta_url=cta_url,
                    )
                    if success:
                        messages.success(request, f"🎉 Email successfully dispatched to {sent_count} active subscriber(s)!")
                        return redirect('dashboard:subscribers')
                    else:
                        messages.error(request, f"Dispatch encountered an error: {err_msg}")
    else:
        form = BroadcastEmailForm(initial=initial_data)

    recent_notes = Note.objects.filter(is_published=True).order_by('-created_at')[:4]
    recent_quizzes = Quiz.objects.filter(is_published=True).order_by('-created_at')[:4]
    recent_blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:4]
    recent_downloads = Download.objects.filter(is_published=True).order_by('-created_at')[:4]

    context = {
        'form': form,
        'active_count': active_count,
        'site_settings': site_settings,
        'active_page': 'broadcast',
        'recent_notes': recent_notes,
        'recent_quizzes': recent_quizzes,
        'recent_blogs': recent_blogs,
        'recent_downloads': recent_downloads,
    }
    return render(request, 'dashboard/broadcast_email.html', context)


# ========== AD PLACEMENTS CRUD ==========

@staff_member_required
def dashboard_ads(request):
    ads = AdPlacement.objects.all()
    context = {'ads': ads, 'active_page': 'ads'}
    return render(request, 'dashboard/ads.html', context)

@staff_member_required
def ad_create(request):
    if request.method == 'POST':
        form = AdPlacementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ad placement created successfully!')
            return redirect('dashboard:ads')
    else:
        form = AdPlacementForm()
    context = {'form': form, 'active_page': 'ads', 'action': 'Create', 'model_name': 'Ad Placement'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def ad_edit(request, pk):
    ad = get_object_or_404(AdPlacement, pk=pk)
    if request.method == 'POST':
        form = AdPlacementForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ad placement updated successfully!')
            return redirect('dashboard:ads')
    else:
        form = AdPlacementForm(instance=ad)
    context = {'form': form, 'active_page': 'ads', 'action': 'Edit', 'model_name': 'Ad Placement', 'object': ad}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def ad_delete(request, pk):
    ad = get_object_or_404(AdPlacement, pk=pk)
    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Ad placement deleted successfully!')
    return redirect('dashboard:ads')


@staff_member_required
def ad_toggle(request, pk):
    ad = get_object_or_404(AdPlacement, pk=pk)
    ad.is_active = not ad.is_active
    ad.save(update_fields=['is_active'])
    status = 'activated' if ad.is_active else 'deactivated'
    messages.success(request, f'Ad placement {status} successfully!')
    return redirect('dashboard:ads')


# ========== ANALYTICS ==========

@staff_member_required
def dashboard_analytics(request):
    from django.utils import timezone
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)

    attempts_by_day = QuizAttempt.objects.filter(
        completed_at__gte=thirty_days_ago
    ).annotate(date=TruncDate('completed_at')).values('date').annotate(
        count=Count('id'), avg_score=Avg('final_score'), avg_total=Avg('total_questions')
    ).order_by('date')

    chart_labels = [item['date'].strftime('%Y-%m-%d') if item['date'] else '' for item in attempts_by_day]
    chart_counts = [item['count'] for item in attempts_by_day]
    chart_avg = [round(float(item['avg_score']) / float(item['avg_total']) * 100, 1) if item['avg_total'] else 0 for item in attempts_by_day]

    top_quizzes = Quiz.objects.annotate(
        attempt_count=Count('quiz_attempts'), avg_score=Avg('quiz_attempts__final_score')
    ).filter(attempt_count__gt=0).order_by('-attempt_count')[:10]

    # Serialize category data for JS charts
    notes_by_cat = mark_safe(json.dumps(list(Category.objects.filter(module='notes').annotate(count=Count('notes')).order_by('-count').values('name', 'count'))))
    blog_by_cat = mark_safe(json.dumps(list(Category.objects.filter(module='blog').annotate(count=Count('blog_posts')).order_by('-count').values('name', 'count'))))

    # Monthly attempts data
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_attempts = QuizAttempt.objects.filter(
        completed_at__gte=twelve_months_ago
    ).annotate(month=TruncDate('completed_at')).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    monthly_labels = [item['month'].strftime('%b %Y') if item['month'] else '' for item in monthly_attempts]
    monthly_counts = [item['count'] for item in monthly_attempts]

    # Difficulty breakdown
    difficulty_stats = list(Quiz.objects.values('difficulty').annotate(
        count=Count('id'),
        total_attempts=Count('quiz_attempts'),
        avg_score=Avg('quiz_attempts__final_score'),
    ).order_by('difficulty'))

    context = {
        'chart_labels': chart_labels, 'chart_counts': chart_counts,
        'chart_avg': chart_avg, 'top_quizzes': top_quizzes,
        'notes_by_cat': notes_by_cat, 'blog_by_cat': blog_by_cat,
        'monthly_labels': monthly_labels, 'monthly_counts': monthly_counts,
        'difficulty_stats': difficulty_stats,
        'active_page': 'analytics',
        'total_attempts_30d': QuizAttempt.objects.filter(completed_at__gte=thirty_days_ago).count(),
        'avg_score_30d': QuizAttempt.objects.filter(completed_at__gte=thirty_days_ago).aggregate(avg=Avg('final_score'))['avg'] or 0,
    }
    return render(request, 'dashboard/analytics.html', context)


# ========== TOOLS CRUD ==========

@staff_member_required
def dashboard_tools(request):
    tools = Tool.objects.all()
    category_filter = request.GET.get('category')
    if category_filter:
        tools = tools.filter(category=category_filter)
    active_filter = request.GET.get('active')
    if active_filter == 'yes':
        tools = tools.filter(is_active=True)
    elif active_filter == 'no':
        tools = tools.filter(is_active=False)
    search = request.GET.get('q')
    if search:
        tools = tools.filter(name__icontains=search)
    paginator = Paginator(tools.order_by('order', 'name'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page_obj,
        'active_page': 'tools',
        'total': tools.count(),
        'category_choices': Tool.CATEGORY_CHOICES,
    }
    return render(request, 'dashboard/tools.html', context)

@staff_member_required
def tool_create(request):
    if request.method == 'POST':
        form = ToolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tool created successfully!')
            return redirect('dashboard:tools')
    else:
        form = ToolForm()
    context = {'form': form, 'active_page': 'tools', 'action': 'Create', 'model_name': 'Tool'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def tool_edit(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        form = ToolForm(request.POST, instance=tool)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tool updated successfully!')
            return redirect('dashboard:tools')
    else:
        form = ToolForm(instance=tool)
    context = {'form': form, 'active_page': 'tools', 'action': 'Edit', 'model_name': 'Tool', 'object': tool}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def tool_delete(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        tool.delete()
        messages.success(request, 'Tool deleted successfully!')
    return redirect('dashboard:tools')

@staff_member_required
def tool_toggle_active(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    tool.is_active = not tool.is_active
    tool.save(update_fields=['is_active'])
    status = 'activated' if tool.is_active else 'deactivated'
    messages.success(request, f'Tool {status} successfully!')
    return redirect('dashboard:tools')


# ========== WIDGETS CRUD ==========

@staff_member_required
def dashboard_widgets(request):
    widgets = Widget.objects.select_related('tool').all()
    active_filter = request.GET.get('active')
    if active_filter == 'yes':
        widgets = widgets.filter(is_active=True)
    elif active_filter == 'no':
        widgets = widgets.filter(is_active=False)
    search = request.GET.get('q')
    if search:
        widgets = widgets.filter(title__icontains=search)
    paginator = Paginator(widgets.order_by('order', 'title'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    settings = WidgetSetting.get_settings()
    context = {
        'page_obj': page_obj,
        'active_page': 'widgets',
        'total': widgets.count(),
        'widget_settings': settings,
    }
    return render(request, 'dashboard/widgets.html', context)

@staff_member_required
def widget_create(request):
    if request.method == 'POST':
        form = WidgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Widget created successfully!')
            return redirect('dashboard:widgets')
    else:
        form = WidgetForm()
    context = {'form': form, 'active_page': 'widgets', 'action': 'Create', 'model_name': 'Widget'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def widget_edit(request, pk):
    widget = get_object_or_404(Widget, pk=pk)
    if request.method == 'POST':
        form = WidgetForm(request.POST, instance=widget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Widget updated successfully!')
            return redirect('dashboard:widgets')
    else:
        form = WidgetForm(instance=widget)
    context = {'form': form, 'active_page': 'widgets', 'action': 'Edit', 'model_name': 'Widget', 'object': widget}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def widget_delete(request, pk):
    widget = get_object_or_404(Widget, pk=pk)
    if request.method == 'POST':
        widget.delete()
        messages.success(request, 'Widget deleted successfully!')
    return redirect('dashboard:widgets')

@staff_member_required
def widget_toggle_active(request, pk):
    widget = get_object_or_404(Widget, pk=pk)
    widget.is_active = not widget.is_active
    widget.save(update_fields=['is_active'])
    status = 'activated' if widget.is_active else 'deactivated'
    messages.success(request, f'Widget {status} successfully!')
    return redirect('dashboard:widgets')

@staff_member_required
def dashboard_widget_settings(request):
    obj = WidgetSetting.get_settings()
    if request.method == 'POST':
        form = WidgetSettingForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Widget settings updated successfully!')
            return redirect('dashboard:widget_settings')
    else:
        form = WidgetSettingForm(instance=obj)
    context = {
        'form': form,
        'active_page': 'widget_settings',
        'widget_setting': obj,
    }
    return render(request, 'dashboard/widget_settings.html', context)


# ========== PATRO EVENTS & HOLIDAYS CRUD ==========

@staff_member_required
def dashboard_patro_events(request):
    events = PatroEvent.objects.all()
    available_years = list(PatroEvent.objects.values_list('year_bs', flat=True).distinct().order_by('year_bs'))
    if not available_years:
        available_years = [2083]

    selected_year = request.GET.get('year')
    if selected_year and selected_year != 'all':
        try:
            events = events.filter(year_bs=int(selected_year))
        except ValueError:
            pass
    elif not selected_year:
        # Default to 2083 or latest
        selected_year = '2083' if 2083 in available_years else str(available_years[-1])
        events = events.filter(year_bs=int(selected_year))

    selected_month = request.GET.get('month')
    if selected_month:
        try:
            events = events.filter(month_bs=int(selected_month))
        except ValueError:
            pass

    holiday_filter = request.GET.get('holiday')
    if holiday_filter == 'yes':
        events = events.filter(is_public_holiday=True)
    elif holiday_filter == 'no':
        events = events.filter(is_public_holiday=False)

    search = request.GET.get('q')
    if search:
        events = events.filter(title__icontains=search)

    paginator = Paginator(events.order_by('year_bs', 'month_bs', 'day_bs'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'active_page': 'patro_events',
        'total': events.count(),
        'available_years': available_years,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'holiday_filter': holiday_filter,
        'month_choices': PatroEvent.MONTH_CHOICES,
    }
    return render(request, 'dashboard/patro_events.html', context)

@staff_member_required
def patro_event_create(request):
    if request.method == 'POST':
        form = PatroEventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday / Event added successfully!')
            return redirect('dashboard:patro_events')
    else:
        initial_year = request.GET.get('year', 2083)
        form = PatroEventForm(initial={'year_bs': initial_year})
    context = {'form': form, 'active_page': 'patro_events', 'action': 'Add', 'model_name': 'Patro Holiday / Event'}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def patro_event_edit(request, pk):
    event = get_object_or_404(PatroEvent, pk=pk)
    if request.method == 'POST':
        form = PatroEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday / Event updated successfully!')
            return redirect('dashboard:patro_events')
    else:
        form = PatroEventForm(instance=event)
    context = {'form': form, 'active_page': 'patro_events', 'action': 'Edit', 'model_name': 'Patro Holiday / Event', 'object': event}
    return render(request, 'dashboard/form.html', context)

@staff_member_required
def patro_event_delete(request, pk):
    event = get_object_or_404(PatroEvent, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Holiday / Event deleted successfully!')
    return redirect('dashboard:patro_events')

@staff_member_required
def patro_event_toggle_holiday(request, pk):
    event = get_object_or_404(PatroEvent, pk=pk)
    event.is_public_holiday = not event.is_public_holiday
    event.save(update_fields=['is_public_holiday'])
    status = 'marked as Public Holiday' if event.is_public_holiday else 'marked as Normal Event (Not a Holiday)'
    messages.success(request, f'"{event.title}" {status}!')
    return redirect('dashboard:patro_events')

@staff_member_required
def patro_event_import(request):
    if request.method == 'POST':
        form = PatroEventImportForm(request.POST, request.FILES)
        if form.is_valid():
            target_year = form.cleaned_data['target_year']
            replace_existing = form.cleaned_data['replace_existing']
            uploaded_file = request.FILES['file']
            file_name = uploaded_file.name.lower()

            if replace_existing:
                deleted_count, _ = PatroEvent.objects.filter(year_bs=target_year).delete()
                messages.info(request, f'Removed {deleted_count} existing events for year {target_year}.')

            imported_count = 0
            errors = []

            try:
                if file_name.endswith('.json'):
                    content = uploaded_file.read().decode('utf-8')
                    items = json.loads(content)
                    if isinstance(items, dict):
                        # Format {"2084-01-01": {"title": "...", "is_holiday": true}}
                        for key, val in items.items():
                            parts = key.split('-')
                            if len(parts) >= 3:
                                y = int(parts[0])
                                m = int(parts[1])
                                d = int(parts[2])
                                title = val.get('title', '').strip()
                                is_h = bool(val.get('is_holiday', True))
                                e_type = val.get('event_type', 'holiday')
                                if title:
                                    PatroEvent.objects.update_or_create(
                                        year_bs=y, month_bs=m, day_bs=d, title=title,
                                        defaults={'is_public_holiday': is_h, 'event_type': e_type}
                                    )
                                    imported_count += 1
                    elif isinstance(items, list):
                        # Format [{"month": 1, "day": 1, "title": "...", "is_holiday": true}]
                        for item in items:
                            m = int(item.get('month', 1))
                            d = int(item.get('day', 1))
                            title = item.get('title', '').strip()
                            is_h = bool(item.get('is_holiday', True))
                            e_type = item.get('event_type', 'holiday')
                            if title:
                                PatroEvent.objects.update_or_create(
                                    year_bs=target_year, month_bs=m, day_bs=d, title=title,
                                    defaults={'is_public_holiday': is_h, 'event_type': e_type}
                                )
                                imported_count += 1
                else:
                    # CSV processing
                    csv_text = uploaded_file.read().decode('utf-8-sig')
                    reader = csv.reader(io.StringIO(csv_text))
                    for row_num, row in enumerate(reader, start=1):
                        if not row or len(row) < 3:
                            continue
                        # Skip header row if found
                        first_col = row[0].strip().lower()
                        if 'month' in first_col or 'महिना' in first_col:
                            continue
                        try:
                            m = int(row[0].strip())
                            d = int(row[1].strip())
                            title = row[2].strip()
                            is_h = True
                            if len(row) > 3:
                                is_h_str = row[3].strip().lower()
                                is_h = is_h_str in ['1', 'true', 'yes', 'y', 'हो', 'बिदा']
                            e_type = row[4].strip() if len(row) > 4 and row[4].strip() else 'holiday'
                            desc = row[5].strip() if len(row) > 5 else ''

                            if title:
                                PatroEvent.objects.update_or_create(
                                    year_bs=target_year, month_bs=m, day_bs=d, title=title,
                                    defaults={
                                        'is_public_holiday': is_h,
                                        'event_type': e_type,
                                        'description': desc,
                                    }
                                )
                                imported_count += 1
                        except Exception as row_err:
                            errors.append(f"Row {row_num}: {str(row_err)}")

                messages.success(request, f'Successfully imported {imported_count} holidays/events for year {target_year}!')
                if errors:
                    messages.warning(request, f'{len(errors)} rows had issues and were skipped.')
                return redirect(f"/dashboard/patro/events/?year={target_year}")

            except Exception as e:
                messages.error(request, f'Error parsing import file: {str(e)}')

    else:
        form = PatroEventImportForm()

    context = {
        'form': form,
        'active_page': 'patro_events',
    }
    return render(request, 'dashboard/patro_event_import.html', context)

@staff_member_required
def patro_event_sample_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="nepali_patro_holidays_sample.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel compatibility

    writer = csv.writer(response)
    writer.writerow(['Month (1-12)', 'Day (1-32)', 'Title (Nepali)', 'Is Public Holiday (1/0)', 'Event Type', 'Description'])
    writer.writerow([1, 1, 'नयाँ वर्ष / मेष संक्रान्ति', 1, 'holiday', 'Official Gazette Holiday'])
    writer.writerow([1, 18, 'अन्तर्राष्ट्रिय श्रमिक दिवस', 1, 'international', 'May Day'])
    writer.writerow([2, 15, 'गणतन्त्र दिवस', 1, 'national', 'Republic Day'])
    writer.writerow([6, 3, 'संविधान दिवस', 1, 'national', 'National Day'])
    writer.writerow([6, 25, 'घटस्थापना', 1, 'holiday', 'Dashain Festival Start'])
    writer.writerow([7, 3, 'विजया दशमी', 1, 'holiday', 'Main Tika'])
    writer.writerow([7, 27, 'भाइटीका', 1, 'holiday', 'Tihar Festival'])
    return response


# ========== WIDGET ANALYTICS & DOMAIN TRACKER ==========

@staff_member_required
def dashboard_widget_analytics(request):
    usages = WidgetUsage.objects.select_related('widget').all()

    # Filter by widget
    widget_slug = request.GET.get('widget')
    if widget_slug:
        usages = usages.filter(widget__slug=widget_slug)

    # Filter by type (external vs all vs internal)
    type_filter = request.GET.get('type', 'external')
    if type_filter == 'external':
        usages = usages.filter(is_internal=False)
    elif type_filter == 'internal':
        usages = usages.filter(is_internal=True)

    # Search query (domain)
    q = request.GET.get('q')
    if q:
        usages = usages.filter(domain__icontains=q)

    # KPIs
    total_external_domains = WidgetUsage.objects.filter(is_internal=False).values('domain').distinct().count()
    total_external_views = WidgetUsage.objects.filter(is_internal=False).aggregate(total=Sum('total_views'))['total'] or 0
    total_all_views = WidgetUsage.objects.aggregate(total=Sum('total_views'))['total'] or 0
    total_widgets = Widget.objects.filter(is_active=True).count()

    # Top 5 external domains
    top_domains = (
        WidgetUsage.objects.filter(is_internal=False)
        .values('domain')
        .annotate(domain_views=Sum('total_views'))
        .order_by('-domain_views')[:5]
    )

    # Widgets list
    widgets_list = Widget.objects.filter(is_active=True).annotate(usage_views=Sum('usages__total_views')).order_by('-usage_views')

    paginator = Paginator(usages.order_by('-total_views', '-last_seen'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'active_page': 'widget_analytics',
        'total_external_domains': total_external_domains,
        'total_external_views': total_external_views,
        'total_all_views': total_all_views,
        'total_widgets': total_widgets,
        'top_domains': top_domains,
        'widgets_list': widgets_list,
        'selected_widget': widget_slug,
        'selected_type': type_filter,
    }
    return render(request, 'dashboard/widget_analytics.html', context)


# ========== BLOG COMMENTS ==========

@staff_member_required
def dashboard_comments(request):
    status_filter = request.GET.get('status', 'all')
    q = request.GET.get('q', '').strip()

    comments = Comment.objects.select_related('post', 'parent').order_by('-created_at')

    if status_filter == 'pending':
        comments = comments.filter(is_approved=False)
    elif status_filter == 'approved':
        comments = comments.filter(is_approved=True)

    if q:
        from django.db.models import Q
        comments = comments.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(content__icontains=q) |
            Q(post__title__icontains=q)
        )

    # KPIs
    from django.utils import timezone
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_count = Comment.objects.count()
    pending_count = Comment.objects.filter(is_approved=False).count()
    approved_count = Comment.objects.filter(is_approved=True).count()
    today_count = Comment.objects.filter(created_at__gte=today_start).count()

    paginator = Paginator(comments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'q': q,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'today_count': today_count,
        'active_page': 'comments',
    }
    return render(request, 'dashboard/comments/list.html', context)


@staff_member_required
def comment_toggle_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.is_approved = not comment.is_approved
    comment.save(update_fields=['is_approved', 'updated_at'])
    if comment.is_approved:
        messages.success(request, f'Comment by "{comment.name}" approved!')
    else:
        messages.info(request, f'Comment by "{comment.name}" set to pending.')
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard:comments')


@staff_member_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
    return redirect('dashboard:comments')


@staff_member_required
def comment_reply(request, pk):
    parent = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            admin_name = request.user.get_full_name() or request.user.username or "Admin"
            admin_email = request.user.email or "admin@example.com"
            Comment.objects.create(
                post=parent.post,
                parent=parent,
                name=admin_name,
                email=admin_email,
                content=content,
                is_approved=True,
                is_author_reply=True,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, f'Reply to "{parent.name}" published successfully!')
        else:
            messages.error(request, 'Reply content cannot be empty.')
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard:comments')


# ========== VISITOR LOGS ==========

@staff_member_required
def dashboard_visitor_logs(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q

    range_filter = request.GET.get('range', '7d')
    device_filter = request.GET.get('device', 'all')
    bot_filter = request.GET.get('bot', 'real')
    q = request.GET.get('q', '').strip()

    now = timezone.now()
    if range_filter == 'today':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_filter == '24h':
        start_time = now - timedelta(hours=24)
    elif range_filter == '7d':
        start_time = now - timedelta(days=7)
    elif range_filter == '30d':
        start_time = now - timedelta(days=30)
    else:
        start_time = None

    logs = VisitorLog.objects.all()

    if start_time:
        logs = logs.filter(timestamp__gte=start_time)

    if device_filter in ['Mobile', 'Desktop', 'Tablet']:
        logs = logs.filter(device_type=device_filter)

    if bot_filter == 'real':
        logs = logs.filter(is_bot=False)
    elif bot_filter == 'bot':
        logs = logs.filter(is_bot=True)

    if q:
        logs = logs.filter(
            Q(ip_address__icontains=q) |
            Q(path__icontains=q) |
            Q(browser__icontains=q) |
            Q(os__icontains=q) |
            Q(country__icontains=q) |
            Q(referrer__icontains=q)
        )

    # KPIs in this selection / today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    total_views = logs.count()
    unique_visitors = logs.values('ip_address').distinct().count()
    today_views = VisitorLog.objects.filter(timestamp__gte=today_start, is_bot=False).count()
    today_uniques = VisitorLog.objects.filter(timestamp__gte=today_start, is_bot=False).values('ip_address').distinct().count()

    # Device breakdown
    mobile_count = logs.filter(device_type='Mobile').count()
    desktop_count = logs.filter(device_type='Desktop').count()
    tablet_count = logs.filter(device_type='Tablet').count()
    mobile_pct = round((mobile_count / total_views * 100), 1) if total_views > 0 else 0

    # Top 5 visited paths
    top_paths = (
        logs.values('path')
        .annotate(view_count=Count('id'))
        .order_by('-view_count')[:5]
    )

    # Top 5 referrers
    top_referrers = (
        logs.exclude(referrer__isnull=True).exclude(referrer='')
        .values('referrer')
        .annotate(ref_count=Count('id'))
        .order_by('-ref_count')[:5]
    )

    # Top browsers
    top_browsers = (
        logs.values('browser')
        .annotate(b_count=Count('id'))
        .order_by('-b_count')[:5]
    )

    # Pagination
    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'range_filter': range_filter,
        'device_filter': device_filter,
        'bot_filter': bot_filter,
        'q': q,
        'total_views': total_views,
        'unique_visitors': unique_visitors,
        'today_views': today_views,
        'today_uniques': today_uniques,
        'mobile_pct': mobile_pct,
        'mobile_count': mobile_count,
        'desktop_count': desktop_count,
        'tablet_count': tablet_count,
        'top_paths': top_paths,
        'top_referrers': top_referrers,
        'top_browsers': top_browsers,
        'active_page': 'visitor_logs',
    }
    return render(request, 'dashboard/visitor_logs/list.html', context)


@staff_member_required
def visitor_logs_clear_old(request):
    from django.utils import timezone
    from datetime import timedelta
    if request.method == 'POST':
        try:
            days = int(request.POST.get('days', 30))
        except (ValueError, TypeError):
            days = 30
        cutoff = timezone.now() - timedelta(days=days)
        deleted_count, _ = VisitorLog.objects.filter(timestamp__lt=cutoff).delete()
        messages.success(request, f'Cleaned {deleted_count} visitor logs older than {days} days.')
    return redirect('dashboard:visitor_logs')


# ========== QUIZ FEEDBACKS & ISSUE REPORTS ==========

@staff_member_required
def dashboard_quiz_feedbacks(request):
    type_filter = request.GET.get('type', 'all')
    status_filter = request.GET.get('status', 'all')
    quiz_id = request.GET.get('quiz')
    q = request.GET.get('q', '').strip()

    feedbacks = QuizFeedback.objects.select_related('quiz', 'question').order_by('-created_at')

    if type_filter == 'issues':
        feedbacks = feedbacks.filter(feedback_type='question_error')
    elif type_filter == 'reviews':
        feedbacks = feedbacks.exclude(feedback_type='question_error')

    if status_filter == 'pending':
        feedbacks = feedbacks.filter(is_reviewed=False)
    elif status_filter == 'reviewed':
        feedbacks = feedbacks.filter(is_reviewed=True)

    if quiz_id:
        feedbacks = feedbacks.filter(quiz_id=quiz_id)

    if q:
        from django.db.models import Q
        feedbacks = feedbacks.filter(
            Q(name__icontains=q) |
            Q(message__icontains=q) |
            Q(quiz__title__icontains=q) |
            Q(question__question_text__icontains=q)
        )

    # KPIs
    total_feedbacks = QuizFeedback.objects.count()
    pending_count = QuizFeedback.objects.filter(is_reviewed=False).count()
    issue_reports = QuizFeedback.objects.filter(feedback_type='question_error').count()
    avg_rating = QuizFeedback.objects.exclude(feedback_type='question_error').aggregate(avg=Avg('rating'))['avg'] or 5.0
    avg_rating = round(avg_rating, 1)

    quizzes_list = Quiz.objects.filter(is_published=True).order_by('title')

    paginator = Paginator(feedbacks, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'selected_quiz': quiz_id,
        'q': q,
        'total_feedbacks': total_feedbacks,
        'pending_count': pending_count,
        'issue_reports': issue_reports,
        'avg_rating': avg_rating,
        'quizzes_list': quizzes_list,
        'active_page': 'quiz_feedbacks',
    }
    return render(request, 'dashboard/quiz_feedback.html', context)


@staff_member_required
def quiz_feedback_toggle_review(request, pk):
    fb = get_object_or_404(QuizFeedback, pk=pk)
    fb.is_reviewed = not fb.is_reviewed
    fb.save(update_fields=['is_reviewed'])
    status_str = "marked as Reviewed" if fb.is_reviewed else "marked as Pending"
    messages.success(request, f'Feedback item {status_str}.')
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard:quiz_feedbacks')


@staff_member_required
def quiz_feedback_delete(request, pk):
    fb = get_object_or_404(QuizFeedback, pk=pk)
    if request.method == 'POST':
        fb.delete()
        messages.success(request, 'Feedback item deleted successfully!')
    return redirect('dashboard:quiz_feedbacks')


# ========== AI AUTO-BLOGGER & NOTE GENERATOR ==========

@staff_member_required
def dashboard_ai_blogger(request):
    """Main AI Content Generator Dashboard"""
    settings = SiteSettings.objects.first()
    if not settings:
        settings = SiteSettings.objects.create()

    # Filters
    content_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    search_q = request.GET.get('q', '').strip()

    queue_qs = AITopicQueue.objects.all()
    if content_filter:
        queue_qs = queue_qs.filter(content_type=content_filter)
    if status_filter:
        queue_qs = queue_qs.filter(status=status_filter)
    if search_q:
        queue_qs = queue_qs.filter(title__icontains=search_q)

    # Metrics
    total_topics = AITopicQueue.objects.count()
    pending_topics = AITopicQueue.objects.filter(status='pending').count()
    completed_topics = AITopicQueue.objects.filter(status='completed').count()
    total_ai_blogs = AITopicQueue.objects.filter(content_type='blog', status='completed', generated_blog__isnull=False).count()
    total_ai_notes = AITopicQueue.objects.filter(content_type='note', status='completed', generated_note__isnull=False).count()

    paginator = Paginator(queue_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    recent_logs = AIGenerationLog.objects.order_by('-created_at')[:10]
    all_categories = Category.objects.all().order_by('name')

    context = {
        'settings': settings,
        'page_obj': page_obj,
        'recent_logs': recent_logs,
        'all_categories': all_categories,
        'total_topics': total_topics,
        'pending_topics': pending_topics,
        'completed_topics': completed_topics,
        'total_ai_blogs': total_ai_blogs,
        'total_ai_notes': total_ai_notes,
        'content_filter': content_filter,
        'status_filter': status_filter,
        'search_q': search_q,
        'active_page': 'ai_blogger',
    }
    return render(request, 'dashboard/ai_blogger.html', context)


@staff_member_required
def ai_topic_create(request):
    """Add a new topic (single or bulk paste) to the AI queue"""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'single')
        content_type = request.POST.get('content_type', 'blog')
        language = request.POST.get('language', 'bilingual')
        category_id = request.POST.get('category')
        priority = int(request.POST.get('priority', 5) or 5)
        prompt_hint = request.POST.get('prompt_hint', '').strip()

        category = None
        if category_id:
            category = Category.objects.filter(pk=category_id).first()

        if mode == 'bulk':
            bulk_text = request.POST.get('bulk_topics', '').strip()
            lines = [l.strip() for l in bulk_text.splitlines() if l.strip()]
            added_count = 0
            for line in lines:
                clean_title = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if clean_title:
                    AITopicQueue.objects.create(
                        title=clean_title,
                        content_type=content_type,
                        language=language,
                        category=category,
                        priority=priority,
                        prompt_hint=prompt_hint,
                        status='pending'
                    )
                    added_count += 1
            messages.success(request, f'Successfully queued {added_count} topics for automatic AI generation!')
        else:
            title = request.POST.get('title', '').strip()
            if title:
                AITopicQueue.objects.create(
                    title=title,
                    content_type=content_type,
                    language=language,
                    category=category,
                    priority=priority,
                    prompt_hint=prompt_hint,
                    status='pending'
                )
                messages.success(request, f'Topic "{title}" queued successfully!')
            else:
                messages.error(request, 'Topic title cannot be empty.')

    return redirect('dashboard:ai_blogger')


@staff_member_required
def ai_topic_run_now(request, pk):
    """Trigger immediate generation for a specific queued topic"""
    topic = get_object_or_404(AITopicQueue, pk=pk)
    success, res, log = generate_content_for_topic(topic)
    if success:
        messages.success(request, f'Successfully generated content for: "{topic.title}"!')
    else:
        messages.error(request, f'Failed to generate: {res}')
    return redirect('dashboard:ai_blogger')


@staff_member_required
def ai_topic_delete(request, pk):
    """Delete a topic from the AI queue"""
    topic = get_object_or_404(AITopicQueue, pk=pk)
    if request.method == 'POST':
        title = topic.title
        topic.delete()
        messages.success(request, f'Topic "{title}" removed from queue.')
    return redirect('dashboard:ai_blogger')


@staff_member_required
def ai_generate_instant(request):
    """Instant 1-Click generation button for next pending blog or note"""
    target_type = request.POST.get('target_type', 'blog')
    topic = AITopicQueue.objects.filter(content_type=target_type, status='pending').first()

    if not topic:
        messages.warning(request, f'No pending topics found in queue for {target_type.upper()}. Please add topics first or use AI Topic Suggestions.')
        return redirect('dashboard:ai_blogger')

    success, res, log = generate_content_for_topic(topic)
    if success:
        target_name = "Blog article" if target_type == 'blog' else "Study note"
        messages.success(request, f'⚡ {target_name} generated and created successfully: "{topic.title}"!')
    else:
        messages.error(request, f'Generation failed: {res}')
    return redirect('dashboard:ai_blogger')


@staff_member_required
def ai_save_settings(request):
    """Save AI Auto-Blogger Configuration & Automation toggles"""
    if request.method == 'POST':
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create()

        settings.gemini_api_key = request.POST.get('gemini_api_key', '').strip()
        settings.gemini_model = request.POST.get('gemini_model', 'gemini-2.0-flash').strip()
        settings.enable_daily_ai_blog = 'enable_daily_ai_blog' in request.POST
        settings.enable_daily_ai_note = 'enable_daily_ai_note' in request.POST
        settings.ai_blog_publish_mode = request.POST.get('ai_blog_publish_mode', 'published')
        settings.ai_note_publish_mode = request.POST.get('ai_note_publish_mode', 'published')
        settings.ai_default_language = request.POST.get('ai_default_language', 'bilingual')

        cat_blog_id = request.POST.get('ai_default_blog_category')
        cat_note_id = request.POST.get('ai_default_note_category')
        settings.ai_default_blog_category = Category.objects.filter(pk=cat_blog_id).first() if cat_blog_id else None
        settings.ai_default_note_category = Category.objects.filter(pk=cat_note_id).first() if cat_note_id else None

        settings.save()
        messages.success(request, 'AI Auto-Blogger settings saved successfully!')
    return redirect('dashboard:ai_blogger')


@staff_member_required
def ai_suggest_topics_ajax(request):
    """Ajax endpoint: Uses Gemini to suggest exciting topics across domains"""
    from django.http import JsonResponse
    domain = request.GET.get('domain', 'Technology, Computer Operator, Grammar & Education')
    content_type = request.GET.get('content_type', 'blog')
    language = request.GET.get('language', 'bilingual')
    count = int(request.GET.get('count', 6))

    try:
        suggestions = suggest_topics_with_gemini(domain=domain, content_type=content_type, language=language, count=count)
        return JsonResponse({'status': 'success', 'topics': suggestions})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
def ai_test_api_key(request):
    """Test connection with Google Gemini API"""
    from django.http import JsonResponse
    from core.ai_blogger import get_gemini_config, _call_gemini_api, GEMINI_API_URL

    api_key, model, _ = get_gemini_config()
    test_key = request.GET.get('key', '').strip() or api_key

    if not test_key:
        return JsonResponse({
            'status': 'error',
            'message': 'No API key provided. Please paste your Gemini API key first.'
        }, status=400)

    url = GEMINI_API_URL.format(model=model) + f"?key={test_key}"
    payload = {
        "contents": [{"parts": [{"text": "Reply with only: OK"}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }

    try:
        data = _call_gemini_api(url, payload, timeout=15)
        reply = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return JsonResponse({
            'status': 'success',
            'model': model,
            'message': f'API Connection Verified! Gemini responded successfully ({model}).'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)






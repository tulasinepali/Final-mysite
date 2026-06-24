from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
import json
from django.utils.safestring import mark_safe

from core.models import SiteSettings, Category, Tag, ContactMessage, AdPlacement
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz, Question, QuizAttempt
from .forms import (
    SiteSettingsForm, CategoryForm, TagForm, NoteForm, BlogPostForm,
    DownloadForm, QuizForm, QuestionForm, AdPlacementForm,
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
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    total_views = Note.objects.aggregate(total=Sum('views'))['total'] or 0
    total_blog_views = BlogPost.objects.aggregate(total=Sum('views'))['total'] or 0
    total_download_count = Download.objects.aggregate(total=Sum('download_count'))['total'] or 0

    recent_notes = Note.objects.order_by('-created_at')[:5]
    recent_blogs = BlogPost.objects.order_by('-created_at')[:5]
    recent_attempts = QuizAttempt.objects.select_related('quiz').order_by('-completed_at')[:8]
    recent_messages = ContactMessage.objects.order_by('-created_at')[:5]
    popular_notes = Note.objects.order_by('-views')[:5]
    popular_downloads = Download.objects.order_by('-download_count')[:5]

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
            form.save()
            messages.success(request, 'Download created successfully!')
            return redirect('dashboard:downloads')
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
            form.save()
            messages.success(request, 'Download updated successfully!')
            return redirect('dashboard:downloads')
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


# ========== AD PLACEMENTS CRUD ==========

@staff_member_required
def dashboard_ads(request):
    ads = AdPlacement.objects.all()
    context = {'ads': ads, 'active_page': 'ads'}
    return render(request, 'dashboard/ads.html', context)

@staff_member_required
def ad_create(request):
    if request.method == 'POST':
        form = AdPlacementForm(request.POST)
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
        form = AdPlacementForm(request.POST, instance=ad)
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

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from core.models import SiteSettings, ContactMessage
from core.forms import ContactForm
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz, QuizAttempt

def home(request):
    """Home page with hero, quick nav, featured content, stats, about section"""
    # Featured content
    featured_notes = Note.objects.filter(is_published=True, is_featured=True)[:4]
    latest_notes = Note.objects.filter(is_published=True).order_by('-created_at')[:6]
    trending_blogs = BlogPost.objects.filter(is_published=True).order_by('-views')[:6]
    popular_downloads = Download.objects.filter(is_published=True).order_by('-download_count')[:6]
    recent_quizzes = Quiz.objects.filter(is_published=True).order_by('-created_at')[:4]
    
    # Statistics
    total_notes = Note.objects.filter(is_published=True).count()
    total_blogs = BlogPost.objects.filter(is_published=True).count()
    total_downloads = Download.objects.filter(is_published=True).count()
    total_mcqs = Quiz.objects.filter(is_published=True).aggregate(
        total=Count('questions')
    )['total'] or 0
    
    # About section
    site_settings = SiteSettings.objects.first()
    
    context = {
        'featured_notes': featured_notes,
        'latest_notes': latest_notes,
        'trending_blogs': trending_blogs,
        'popular_downloads': popular_downloads,
        'recent_quizzes': recent_quizzes,
        'total_notes': total_notes,
        'total_blogs': total_blogs,
        'total_downloads': total_downloads,
        'total_mcqs': total_mcqs,
        'site_settings': site_settings,
        'meta_title': 'Learning Platform - Your Gateway to Knowledge',
        'meta_description': 'Access free notes, practice MCQs, download study materials, and read educational blogs. No login required for MCQ practice!',
    }
    return render(request, 'core/home.html', context)

def about(request):
    site_settings = SiteSettings.objects.first()
    context = {
        'site_settings': site_settings,
        'meta_title': 'About Us - Learning Platform',
        'meta_description': f'Learn about {site_settings.site_name if site_settings else "Learning Platform"}. Our mission is to help students learn and prepare for exams.',
    }
    return render(request, 'core/about.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
            )
            return render(request, 'core/contact.html', {
                'form': ContactForm(),
                'form_success': True,
                'meta_title': 'Contact Us - Learning Platform',
                'meta_description': 'Get in touch with us. We would love to hear from you.',
            })
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'meta_title': 'Contact Us - Learning Platform',
        'meta_description': 'Get in touch with us. We would love to hear from you.',
    }
    return render(request, 'core/contact.html', context)

def privacy_policy(request):
    context = {
        'meta_title': 'Privacy Policy - Learning Platform',
        'meta_description': 'Read our privacy policy to understand how we handle your data.',
    }
    return render(request, 'core/privacy.html', context)

def terms_conditions(request):
    context = {
        'meta_title': 'Terms & Conditions - Learning Platform',
        'meta_description': 'Read our terms and conditions for using Learning Platform.',
    }
    return render(request, 'core/terms.html', context)

def sitemap_view(request):
    """Generate a basic HTML sitemap"""
    notes = Note.objects.filter(is_published=True)
    blogs = BlogPost.objects.filter(is_published=True)
    downloads = Download.objects.filter(is_published=True)
    quizzes = Quiz.objects.filter(is_published=True)
    context = {
        'notes': notes,
        'blogs': blogs,
        'downloads': downloads,
        'quizzes': quizzes,
    }
    return render(request, 'core/sitemap.html', context)

def robots_txt(request):
    from django.http import HttpResponse
    content = """User-agent: *
Allow: /
Disallow: /dashboard/
Disallow: /admin/

Sitemap: https://tulasinepali.com.np/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')

def custom_404(request, exception):
    return render(request, 'core/404.html', {'meta_title': 'Page Not Found'}, status=404)

def custom_500(request):
    return render(request, 'core/500.html', {'meta_title': 'Server Error'}, status=500)

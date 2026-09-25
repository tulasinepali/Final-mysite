from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from core.models import SiteSettings, ContactMessage, Subscriber
from core.forms import ContactForm
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz, QuizAttempt
from django.contrib.auth.models import User


def home(request):
    featured_notes = Note.objects.filter(is_published=True, is_featured=True)[:4]
    latest_notes = Note.objects.filter(is_published=True).order_by('-created_at')[:6]
    trending_blogs = BlogPost.objects.filter(is_published=True).order_by('-views')[:6]
    popular_downloads = Download.objects.filter(is_published=True).order_by('-download_count')[:6]
    recent_quizzes = Quiz.objects.filter(is_published=True).order_by('-created_at')[:4]
    total_notes = Note.objects.filter(is_published=True).count()
    total_blogs = BlogPost.objects.filter(is_published=True).count()
    total_downloads = Download.objects.filter(is_published=True).count()
    total_mcqs = Quiz.objects.filter(is_published=True).aggregate(total=Count('questions'))['total'] or 0
    total_users = User.objects.count()
    site_settings = SiteSettings.objects.first()
    context = {
        'featured_notes': featured_notes, 'latest_notes': latest_notes,
        'trending_blogs': trending_blogs, 'popular_downloads': popular_downloads,
        'recent_quizzes': recent_quizzes,
        'stats': {
            'total_notes': total_notes,
            'total_blogs': total_blogs,
            'total_downloads': total_downloads,
            'total_mcqs': total_mcqs,
            'total_users': total_users,
        },
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

def disclaimer(request):
    context = {
        'meta_title': 'Disclaimer - Tulasi Nepali',
        'meta_description': 'Read the disclaimer for tulasinepali.com.np. Educational content provided for informational purposes only, not affiliated with any government body.',
    }
    return render(request, 'core/disclaimer.html', context)


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

def sitemap_xml(request):
    """Generate XML sitemap for search engines"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string

    xml_content = render_to_string(
        'core/sitemap.xml',
        {
            'all_notes': Note.objects.filter(is_published=True),
            'all_blogs': BlogPost.objects.filter(is_published=True),
            'all_downloads': Download.objects.filter(is_published=True),
            'all_quizzes': Quiz.objects.filter(is_published=True),
        },
        request=request,
    )

    return HttpResponse(xml_content, content_type='application/xml')

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


def subscribe_newsletter(request):
    """
    Handle visitor newsletter and updates subscription.
    Supports both standard form submission and AJAX JSON requests.
    """
    if request.method != 'POST':
        return redirect('core:home')

    email = request.POST.get('email', '').strip().lower()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')

    if not email:
        msg = "Please provide a valid email address."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))

    try:
        validate_email(email)
    except ValidationError:
        msg = "Please enter a valid email address format (e.g. name@example.com)."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))

    subscriber, created = Subscriber.objects.get_or_create(
        email=email,
        defaults={'source': request.POST.get('source', 'homepage_newsletter'), 'is_active': True}
    )

    if created:
        msg = "🎉 Thank you for subscribing! You'll now receive updates about new quizzes, notes, blogs, and downloads."
        status_type = 'success'
    elif not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=['is_active'])
        msg = "Welcome back! Your subscription has been reactivated."
        status_type = 'success'
    else:
        msg = "You are already subscribed to our updates! Stay tuned."
        status_type = 'info'

    if is_ajax:
        return JsonResponse({'status': status_type, 'message': msg})

    if status_type == 'success':
        messages.success(request, msg)
    else:
        messages.info(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


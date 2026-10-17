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

    # Question of the Day: Fetch up to 10 published questions with related quiz/category
    from quiz.models import Question
    import json
    daily_questions_qs = Question.objects.filter(
        quiz__is_published=True
    ).select_related('quiz', 'quiz__category').order_by('?')[:8]

    daily_questions_data = []
    choice_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    for q in daily_questions_qs:
        daily_questions_data.append({
            'category': q.quiz.category.name if q.quiz.category else 'General Knowledge',
            'categoryIcon': 'bi-laptop' if 'computer' in (q.quiz.category.name.lower() if q.quiz.category else '') else 'bi-question-circle',
            'level': q.quiz.title,
            'question': q.question_text,
            'options': [q.option_a, q.option_b, q.option_c, q.option_d],
            'correctIndex': choice_map.get(q.correct_answer.upper().strip(), 0),
            'explanation': q.explanation or f"Option {q.correct_answer.upper()} is the correct answer.",
            'quizUrl': q.quiz.get_absolute_url() if hasattr(q.quiz, 'get_absolute_url') else '/quizzes/'
        })

    context = {
        'featured_notes': featured_notes, 'latest_notes': latest_notes,
        'trending_blogs': trending_blogs, 'popular_downloads': popular_downloads,
        'recent_quizzes': recent_quizzes,
        'daily_questions_json': json.dumps(daily_questions_data) if daily_questions_data else '',
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
Allow: /notes/
Allow: /quiz/
Allow: /blog/
Allow: /downloads/
Allow: /tools/
Allow: /about/
Allow: /contact/
Allow: /privacy-policy/
Allow: /terms-conditions/
Allow: /disclaimer/
Allow: /sitemap.html
Allow: /ads.txt

# Block internal, server scripts, embed widgets, and search queries from index
Disallow: /search/
Disallow: /admin/
Disallow: /rishav/
Disallow: /cgi-bin/
Disallow: /login/
Disallow: /logout/
Disallow: /dashboard/
Disallow: /ckeditor5/
Disallow: /widgets/embed/
Disallow: /media/site/

# Sitemaps
Sitemap: https://tulasinepali.com.np/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')


def ads_txt(request):
    """Serve /ads.txt dynamically from SiteSettings or fallback to default publisher snippet."""
    from django.http import HttpResponse
    default_snippet = "google.com, pub-3956705237421931, DIRECT, f08c47fec0942fa0"
    content = default_snippet
    try:
        s = SiteSettings.objects.first()
        if s and s.ads_txt_content and s.ads_txt_content.strip():
            content = s.ads_txt_content.strip()
    except Exception:
        pass
    return HttpResponse(content.strip() + "\n", content_type='text/plain; charset=utf-8')


def favicon_view(request):
    """Serve favicon or redirect to site icon so /favicon.ico always returns 200/302"""
    from django.shortcuts import redirect
    from django.http import HttpResponse
    try:
        s = SiteSettings.objects.first()
        if s and s.site_favicon:
            return redirect(s.site_favicon.url, permanent=False)
    except Exception:
        pass
    # Minimal 1x1 ICO byte sequence so crawlers receive 200 OK
    ico_bytes = b'\x00\x00\x01\x00\x01\x00\x01\x01\x00\x00\x01\x00\x18\x000\x00\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    return HttpResponse(ico_bytes, content_type='image/x-icon', status=200)


def health_check(request):
    """Lightweight 200 OK endpoint for uptime monitors and load balancers"""
    from django.http import JsonResponse
    from django.db import connection
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse({
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "unavailable",
    }, status=status_code)


def custom_404(request, exception=None):
    from django.http import HttpResponse
    try:
        return render(request, 'core/404.html', {'meta_title': 'Page Not Found'}, status=404)
    except Exception:
        return HttpResponse("<!DOCTYPE html><html><head><title>Page Not Found</title></head><body><h1>404 - Page Not Found</h1><p>The requested page could not be found.</p><a href='/'>Go Home</a></body></html>", content_type="text/html", status=404)


def custom_500(request):
    from django.http import HttpResponse
    try:
        return render(request, 'core/500.html', {'meta_title': 'Server Error'}, status=500)
    except Exception:
        return HttpResponse("<!DOCTYPE html><html><head><title>Server Error</title></head><body><h1>500 - Server Error</h1><p>Something went wrong on our end. We are working to fix it.</p><a href='/'>Go Home</a></body></html>", content_type="text/html", status=500)


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


def manifest_json(request):
    """Serve Web App Manifest with dynamic branding fallback"""
    import os
    import json
    from django.conf import settings
    from django.http import HttpResponse

    manifest_file = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if os.path.exists(manifest_file):
        with open(manifest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "name": "Tulasi Nepali - Admin & Learning Platform",
            "short_name": "Tulasi Nepali",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#0559b7"
        }

    try:
        s = SiteSettings.objects.first()
        if s and s.site_name:
            data["name"] = f"{s.site_name} - Admin & Learning Platform"
            data["short_name"] = s.site_name
    except Exception:
        pass

    return HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/manifest+json; charset=utf-8'
    )


def service_worker(request):
    """Serve Service Worker from /sw.js with root scope authority"""
    import os
    from django.conf import settings
    from django.http import HttpResponse

    sw_file = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    if os.path.exists(sw_file):
        with open(sw_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "self.addEventListener('fetch', () => {});"

    response = HttpResponse(content, content_type='application/javascript; charset=utf-8')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def offline_view(request):
    """Serve offline fallback page"""
    from django.shortcuts import render
    return render(request, 'core/offline.html')


from django.views.decorators.csrf import csrf_exempt
from django.db.models import F

@csrf_exempt
def track_video_engagement(request, video_id, action_type):
    """Asynchronously track impressions, watch clicks, and subscribe clicks without affecting UX."""
    if request.method in ('POST', 'GET'):
        try:
            from core.models import YouTubeVideo
            if action_type == 'view':
                YouTubeVideo.objects.filter(pk=video_id).update(views_count=F('views_count') + 1)
            elif action_type == 'click':
                YouTubeVideo.objects.filter(pk=video_id).update(clicks_count=F('clicks_count') + 1)
            elif action_type == 'sub':
                YouTubeVideo.objects.filter(pk=video_id).update(sub_clicks_count=F('sub_clicks_count') + 1)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'method_not_allowed'}, status=405)




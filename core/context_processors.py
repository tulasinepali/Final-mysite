import json
from django.apps import apps
from django.core.cache import cache
from .models import SiteSettings, Category, AdPlacement, VisitorCount, Subscriber


def site_settings(request):
    """Make site settings available in all templates (Cached for 10 minutes)."""
    cached_base = cache.get('cp_site_settings_base_v2')
    if cached_base is None:
        settings, _ = SiteSettings.objects.get_or_create(pk=1)
        total_videos_count = 0
        try:
            YouTubeVideo = apps.get_model('core', 'YouTubeVideo', require_ready=False)
            if YouTubeVideo:
                promoted_videos = list(YouTubeVideo.objects.filter(is_active=True).values(
                    'id', 'video_id', 'title', 'category', 'channel_name', 'channel_url', 'custom_thumbnail'
                ))
                total_videos_count = YouTubeVideo.objects.count()
            else:
                promoted_videos = []
        except Exception:
            promoted_videos = []

        cached_base = {
            'site_settings': settings,
            'promoted_youtube_videos': promoted_videos,
            'promoted_youtube_videos_json': json.dumps(promoted_videos),
            'total_youtube_videos_count': total_videos_count,
        }
        cache.set('cp_site_settings_base_v2', cached_base, 600)

    sub_count = 0
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
        try:
            sub_count = Subscriber.objects.filter(is_active=True).count()
        except Exception:
            sub_count = 0

    return {
        'site_settings': cached_base['site_settings'],
        'total_subscribers': sub_count,
        'promoted_youtube_videos': cached_base['promoted_youtube_videos'],
        'promoted_youtube_videos_json': cached_base['promoted_youtube_videos_json'],
        'total_youtube_videos_count': cached_base['total_youtube_videos_count'],
    }


def global_categories(request):
    """Make categorized navigation and downloads counts available in all templates (Cached for 10 minutes)."""
    cached = cache.get('cp_global_categories_v2')
    if cached is not None:
        return cached

    notes_categories = list(Category.objects.filter(module='notes', is_active=True))
    downloads_categories = list(Category.objects.filter(module='downloads', is_active=True))
    blog_categories = list(Category.objects.filter(module='blog', is_active=True))
    quiz_categories = list(Category.objects.filter(module='quiz', is_active=True))

    downloads_counts = {}
    downloads_sub_counts = {}
    try:
        Download = apps.get_model('downloads', 'Download', require_ready=False)
        if Download:
            from django.db.models import Count
            qs = list(Download.objects.filter(is_published=True).values('resource_type').annotate(c=Count('id')))
            for row in qs:
                downloads_counts[row['resource_type']] = row['c']
            downloads_counts['questions'] = (
                downloads_counts.get('past_question', 0) + 
                downloads_counts.get('model_question', 0)
            )
            downloads_counts['total'] = sum(row['c'] for row in qs)

            # Sub-counts grouped by resource_type and target_sector
            qs_sub = list(Download.objects.filter(is_published=True).values('resource_type', 'target_sector').annotate(c=Count('id')))
            for row in qs_sub:
                key = f"{row['resource_type']}_{row['target_sector']}"
                downloads_sub_counts[key] = row['c']
    except Exception:
        downloads_counts = {}
        downloads_sub_counts = {}

    res = {
        'notes_categories': notes_categories,
        'downloads_categories': downloads_categories,
        'blog_categories': blog_categories,
        'quiz_categories': quiz_categories,
        'downloads_counts': downloads_counts,
        'downloads_sub_counts': downloads_sub_counts,
    }
    cache.set('cp_global_categories_v2', res, 600)
    return res


def ad_placements(request):
    """Make ad placements available in all templates (Cached for 5 minutes)."""
    cached = cache.get('cp_ad_placements_v2')
    if cached is not None:
        return cached

    ads = {}
    popup_ad = None
    for ad in AdPlacement.objects.filter(is_active=True):
        if ad.placement == 'popup':
            popup_ad = ad
        else:
            ads[ad.placement] = ad.ad_code
    visitor_count = VisitorCount.get_count()
    res = {'ads': ads, 'popup_ad': popup_ad, 'visitor_count': visitor_count}
    cache.set('cp_ad_placements_v2', res, 300)
    return res


def dashboard_signals(request):
    """Make live notification signals and actionable alerts available across all dashboard templates."""
    if not (hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff):
        return {}

    try:
        from django.utils import timezone
        from django.urls import reverse
        from core.models import ContactMessage, VisitorLog, Subscriber
        from blog.models import Comment
        from quiz.models import QuizFeedback, QuizAttempt

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        unread_messages = ContactMessage.objects.filter(is_read=False).count()
        pending_comments = Comment.objects.filter(is_approved=False).count()
        pending_feedbacks = QuizFeedback.objects.filter(is_reviewed=False).count()
        question_issues = QuizFeedback.objects.filter(is_reviewed=False, feedback_type='question_error').count()
        today_attempts = QuizAttempt.objects.filter(completed_at__gte=today_start).count()
        today_subscribers = Subscriber.objects.filter(created_at__gte=today_start).count()
        today_visitors = VisitorLog.objects.filter(timestamp__gte=today_start, is_bot=False).values('ip_address').distinct().count()

        total_signals = unread_messages + pending_comments + pending_feedbacks

        recent_signals = []

        # 1. Pending Comments
        for c in Comment.objects.filter(is_approved=False).select_related('post').order_by('-created_at')[:4]:
            recent_signals.append({
                'title': f'Comment: {c.name}',
                'desc': f'On "{c.post.title[:32]}..."',
                'url': reverse('dashboard:comments') + '?status=pending',
                'time': c.created_at,
                'icon': 'bi-chat-left-text-fill',
                'color': 'warning',
                'badge': 'Comment',
            })

        # 2. Pending Quiz Feedbacks & Question Error Reports
        for fb in QuizFeedback.objects.filter(is_reviewed=False).select_related('quiz', 'question').order_by('-created_at')[:4]:
            is_issue = fb.feedback_type == 'question_error'
            recent_signals.append({
                'title': 'Question Error Report' if is_issue else f'Quiz Review ({fb.rating}★)',
                'desc': f'"{fb.quiz.title[:32]}..." by {fb.name}',
                'url': reverse('dashboard:quiz_feedbacks') + '?status=pending',
                'time': fb.created_at,
                'icon': 'bi-flag-fill' if is_issue else 'bi-star-fill',
                'color': 'danger' if is_issue else 'info',
                'badge': 'Error Report' if is_issue else 'Feedback',
            })

        # 3. Unread Messages
        for msg in ContactMessage.objects.filter(is_read=False).order_by('-created_at')[:4]:
            recent_signals.append({
                'title': f'Inquiry: {msg.name}',
                'desc': msg.subject[:36],
                'url': reverse('dashboard:message_read', kwargs={'pk': msg.pk}),
                'time': msg.created_at,
                'icon': 'bi-envelope-fill',
                'color': 'primary',
                'badge': 'Inquiry',
            })

        # 4. Recent Quiz Attempts
        for qa in QuizAttempt.objects.select_related('quiz').order_by('-completed_at')[:3]:
            recent_signals.append({
                'title': 'Candidate Attempt',
                'desc': f'{qa.quiz.title[:28]} — Score: {qa.final_score}/{qa.total_questions * 2}',
                'url': reverse('dashboard:quizzes'),
                'time': qa.completed_at,
                'icon': 'bi-patch-check-fill',
                'color': 'success',
                'badge': 'Quiz Attempt',
            })

        recent_signals.sort(key=lambda x: x['time'], reverse=True)
        recent_signals = recent_signals[:7]

        return {
            'unread_messages': unread_messages,
            'pending_comments_count': pending_comments,
            'pending_feedbacks_count': pending_feedbacks,
            'question_issues_count': question_issues,
            'today_attempts_count': today_attempts,
            'today_subscribers_count': today_subscribers,
            'today_visitors_count': today_visitors,
            'total_signals_count': total_signals,
            'recent_signals': recent_signals,
        }
    except Exception:
        return {}

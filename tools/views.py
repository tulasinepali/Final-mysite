from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
import json
from urllib.parse import urlparse
from django.utils import timezone
from .models import Tool, Widget, WidgetSetting, PatroEvent, WidgetUsage
from core.middleware import is_admin_or_staff

def tools_index(request):
    tools = Tool.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'tools/index.html', {
        'tools': tools,
        'meta_title': 'Student Tools & Utilities | Nepali Date Converter, Age Calculator & Font Tools',
        'meta_description': 'Free online tools curated by Tulasi Nepali. Accurate Nepali Date Converter (B.S. to A.D.), Age Calculator, and Preeti to Unicode font converter.',
    })

def date_converter(request):
    tool = Tool.objects.filter(slug='date-converter', is_active=True).first()
    if tool and not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/date_converter.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Nepali Date Converter (B.S. ↔ A.D.) | Tulasi Nepali',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Convert Bikram Sambat (B.S.) to English (A.D.) dates accurately. Includes today\'s date and full calendar support.',
    })

def age_calculator(request):
    tool = Tool.objects.filter(slug='age-calculator', is_active=True).first()
    if tool and not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/age_calculator.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Age Calculator Online | Exact Years, Months & Days in B.S. & A.D.',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Calculate your exact age in years, months, and days. Enter your birth date in B.S. or A.D. with next birthday countdown.',
    })

def unicode_converter(request):
    tool = Tool.objects.filter(slug='unicode-converter', is_active=True).first()
    if tool and not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/unicode_converter.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Preeti to Unicode Converter | Unicode to Preeti Nepali Font Tool',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Fast, accurate Preeti to Unicode Converter and Unicode to Preeti font converter with 1-click copy.',
    })

def nepali_patro(request):
    tool = Tool.objects.filter(slug='nepali-patro', is_active=True).first()
    if tool and not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    
    events_qs = PatroEvent.objects.all()
    events_dict = {
        e.date_key: {
            'title': e.title,
            'is_holiday': e.is_public_holiday,
            'event_type': e.event_type,
            'description': e.description,
        }
        for e in events_qs
    }

    return render(request, 'tools/nepali_patro.html', {
        'tool': tool,
        'events_json': json.dumps(events_dict),
        'meta_title': tool.meta_title if tool and tool.meta_title else 'नेपाली पात्रो २०८३ | Nepali Patro (Calendar) with Tithi, Holidays & Festivals',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Interactive Nepali Patro (Calendar) 2083 Bikram Sambat with Tithi, official public holidays, Dashain & Tihar dates, and English calendar sync.',
    })

def tool_detail(request, slug):
    if slug == 'date-converter':
        return date_converter(request)
    elif slug == 'age-calculator':
        return age_calculator(request)
    elif slug == 'unicode-converter':
        return unicode_converter(request)
    elif slug == 'nepali-patro':
        return nepali_patro(request)
    elif slug == 'nepali-tts':
        return nepali_tts(request)
    tool = get_object_or_404(Tool, slug=slug, is_active=True)
    if not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/tool_detail.html', {'tool': tool})

def widgets_index(request):
    widgets = Widget.objects.filter(is_active=True).order_by('order', 'title')
    settings = WidgetSetting.get_settings()
    return render(request, 'widgets/index.html', {
        'widgets': widgets,
        'widget_settings': settings,
        'meta_title': 'Free Embeddable Web Widgets | Tulasi Nepali',
        'meta_description': 'Free embeddable widgets for blogs, news portals, and school websites. Embed Nepali Date Converter, Age Calculator, Preeti to Unicode, and Live Nepali Clock easily.',
    })

@xframe_options_exempt
def widget_embed(request, slug):
    settings = WidgetSetting.get_settings()
    if not settings.allow_embedding:
        return render(request, 'widgets/embed_disabled.html')

    widget = get_object_or_404(Widget, slug=slug, is_active=True)
    theme = request.GET.get('theme', 'light')
    template_name = f'widgets/embed_{slug.replace("-", "_")}.html'

    context = {
        'widget': widget,
        'widget_settings': settings,
        'theme': theme,
    }

    if slug == 'nepali-patro':
        events_qs = PatroEvent.objects.all()
        events_dict = {
            e.date_key: {
                'title': e.title,
                'is_holiday': e.is_public_holiday,
                'event_type': e.event_type,
                'description': e.description,
            }
            for e in events_qs
        }
        context['events_json'] = json.dumps(events_dict)

    response = render(request, template_name, context)
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@require_POST
def api_track_embed(request, slug):
    widget = get_object_or_404(Widget, slug=slug, is_active=True)
    Widget.objects.filter(pk=widget.pk).update(embed_count=F('embed_count') + 1)

    referrer = ""
    try:
        if request.content_type == 'application/json' and request.body:
            body_data = json.loads(request.body)
            referrer = body_data.get('referrer', '').strip()
    except Exception:
        pass

    if not referrer:
        referrer = request.POST.get('referrer', '').strip()
    if not referrer:
        referrer = request.META.get('HTTP_REFERER', '').strip()

    if referrer:
        try:
            parsed = urlparse(referrer)
            domain = parsed.netloc.lower()
            if domain:
                if ':' in domain:
                    host, port = domain.split(':', 1)
                    if port in ['80', '443']:
                        domain = host

                current_host = request.get_host().lower().split(':')[0]
                is_internal = (
                    domain in [current_host, 'localhost', '127.0.0.1', 'tulasinepali.com.np', 'www.tulasinepali.com.np']
                    or 'tulasinepali.com' in domain
                )

                usage, created = WidgetUsage.objects.get_or_create(
                    widget=widget,
                    domain=domain,
                    defaults={
                        'full_url': referrer[:500],
                        'is_internal': is_internal,
                        'total_views': 1,
                    }
                )
                if not created:
                    WidgetUsage.objects.filter(pk=usage.pk).update(
                        total_views=F('total_views') + 1,
                        last_seen=timezone.now(),
                        full_url=referrer[:500]
                    )
        except Exception:
            pass

    return JsonResponse({'status': 'ok'})

def api_patro_events(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    qs = PatroEvent.objects.all()
    if year:
        try:
            qs = qs.filter(year_bs=int(year))
        except ValueError:
            pass
    if month:
        try:
            qs = qs.filter(month_bs=int(month))
        except ValueError:
            pass
    data = {
        e.date_key: {
            'title': e.title,
            'is_holiday': e.is_public_holiday,
            'event_type': e.event_type,
            'description': e.description,
        }
        for e in qs
    }
    return JsonResponse(data)



def nepali_tts(request):
    tool = Tool.objects.filter(slug='nepali-tts', is_active=True).first()
    if tool and not is_admin_or_staff(request):
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)

    is_unlocked = bool(is_admin_or_staff(request) or request.session.get('tts_unlocked', False))

    from core.models import YouTubeVideo
    promo_video = YouTubeVideo.objects.filter(is_active=True).order_by('?').first()
    if not promo_video:
        promo_video = {
            'video_id': 'jfKfPfyJRdk',
            'title': 'SkillUp with Tulasi Nepali',
            'channel_name': 'Tulasi Nepali',
            'channel_url': 'https://www.youtube.com/@SkillUpwithTulasiNepali?sub_confirmation=1'
        }

    return render(request, 'tools/nepali_tts.html', {
        'tool': tool,
        'is_unlocked': is_unlocked,
        'promo_video': promo_video,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Nepali Text to Speech (TTS) Online | Natural Human MP3 Voice Generator',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Free online Nepali Text to Speech (TTS) tool. Convert Devanagari text into natural female and male voices (Hemkala & Sagar) and download MP3 audio.',
    })


@require_POST
def nepali_tts_unlock(request):
    """
    Unlock the Nepali TTS tool for this visitor session after watching the promoted video.
    """
    request.session['tts_unlocked'] = True
    request.session.modified = True
    return JsonResponse({
        'status': 'ok',
        'message': 'Tool unlocked successfully! You can now generate speech and download MP3.'
    })


@require_POST
def nepali_tts_generate(request):
    """
    Public frontend endpoint for generating Nepali speech.
    Requires the video to have been watched (or staff access).
    """
    from core.middleware import is_admin_or_staff
    if not is_admin_or_staff(request) and not request.session.get('tts_unlocked', False):
        return JsonResponse({
            'status': 'locked',
            'message': 'Please watch the featured video to unlock free audio generation.'
        }, status=403)

    import json
    import base64
    import uuid
    import os
    from django.conf import settings
    from django.core.cache import cache
    from django.utils.html import strip_tags
    from dashboard.views import _generate_nepali_tts_bytes

    data = {}
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    else:
        data = request.POST

    raw_text = str(data.get('text', '')).strip()
    clean_text = strip_tags(raw_text).strip()
    voice = str(data.get('voice', 'female')).strip().lower()
    tone = str(data.get('tone', 'broadcast')).strip().lower()
    speed = str(data.get('speed', '1.0')).strip()

    if not clean_text:
        return JsonResponse({
            'status': 'error',
            'message': 'Please enter or paste some Nepali text to convert.'
        }, status=400)

    # Max length: 10,000 characters for public visitors
    clean_text = clean_text[:10000]

    audio_bytes, engine_used = _generate_nepali_tts_bytes(clean_text, voice=voice, tone=tone, speed=speed)

    if not audio_bytes:
        return JsonResponse({
            'status': 'error',
            'message': 'Unable to synthesize audio. Please try again.'
        }, status=500)

    cache_id = uuid.uuid4().hex[:16]
    try:
        cache.set(f"tts_audio_{cache_id}", audio_bytes, timeout=7200)
    except Exception:
        pass

    try:
        cache_dir = os.path.join(settings.MEDIA_ROOT, 'tts_cache')
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, f"{cache_id}.mp3")
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
    except Exception:
        pass

    audio_url = f"/rishav/tts/stream/{cache_id}/"
    audio_base64 = "data:audio/mpeg;base64," + base64.b64encode(audio_bytes).decode('utf-8')
    filename = f"nepali-speech-{voice}.mp3"
    voice_label = "Hemkala (Female - Natural Neural)" if voice == 'female' else "Sagar (Male - Natural Neural)"

    return JsonResponse({
        'status': 'ok',
        'audio_url': audio_url,
        'cache_id': cache_id,
        'audio_data': audio_base64,
        'filename': filename,
        'voice_label': voice_label,
        'engine_used': engine_used,
        'char_count': len(clean_text),
        'word_count': len(clean_text.split()),
        'size_kb': round(len(audio_bytes) / 1024, 1),
    })

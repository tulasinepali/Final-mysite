from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
from .models import Tool, Widget, WidgetSetting

def tools_index(request):
    tools = Tool.objects.filter(is_active=True).order_by('order', 'name')
    return render(request, 'tools/index.html', {
        'tools': tools,
        'meta_title': 'Student Tools & Utilities | Nepali Date Converter, Age Calculator & Font Tools',
        'meta_description': 'Free online tools curated by Tulasi Nepali. Accurate Nepali Date Converter (B.S. to A.D.), Age Calculator, and Preeti to Unicode font converter.',
    })

def date_converter(request):
    tool = Tool.objects.filter(slug='date-converter', is_active=True).first()
    if tool:
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/date_converter.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Nepali Date Converter (B.S. ↔ A.D.) | Tulasi Nepali',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Convert Bikram Sambat (B.S.) to English (A.D.) dates accurately. Includes today\'s date and full calendar support.',
    })

def age_calculator(request):
    tool = Tool.objects.filter(slug='age-calculator', is_active=True).first()
    if tool:
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/age_calculator.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Age Calculator Online | Exact Years, Months & Days in B.S. & A.D.',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Calculate your exact age in years, months, and days. Enter your birth date in B.S. or A.D. with next birthday countdown.',
    })

def unicode_converter(request):
    tool = Tool.objects.filter(slug='unicode-converter', is_active=True).first()
    if tool:
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/unicode_converter.html', {
        'tool': tool,
        'meta_title': tool.meta_title if tool and tool.meta_title else 'Preeti to Unicode Converter | Unicode to Preeti Nepali Font Tool',
        'meta_description': tool.meta_description if tool and tool.meta_description else 'Fast, accurate Preeti to Unicode Converter and Unicode to Preeti font converter with 1-click copy.',
    })

def nepali_patro(request):
    tool = Tool.objects.filter(slug='nepali-patro', is_active=True).first()
    if tool:
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)
    return render(request, 'tools/nepali_patro.html', {
        'tool': tool,
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
    tool = get_object_or_404(Tool, slug=slug, is_active=True)
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
    return render(request, template_name, context)

@require_POST
def api_track_embed(request, slug):
    Widget.objects.filter(slug=slug).update(embed_count=F('embed_count') + 1)
    return JsonResponse({'status': 'ok'})

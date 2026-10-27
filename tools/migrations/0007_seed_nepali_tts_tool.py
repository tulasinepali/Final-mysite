from django.db import migrations

def create_nepali_tts_tool(apps, schema_editor):
    Tool = apps.get_model('tools', 'Tool')
    Widget = apps.get_model('tools', 'Widget')

    t_tts, _ = Tool.objects.get_or_create(
        slug='nepali-tts',
        defaults={
            'name': 'Nepali Text to Speech (TTS)',
            'icon': 'bi-soundwave',
            'category': 'typing',
            'short_description': 'Convert Nepali text to natural, lifelike human speech using neural AI voices and download high-quality MP3 audio files.',
            'meta_title': 'Nepali Text to Speech (TTS) Online | Natural Human MP3 Voice Generator',
            'meta_description': 'Free online Nepali Text to Speech (TTS) tool. Convert Devanagari text into natural female and male voices (Hemkala & Sagar) and download MP3 audio.',
            'is_active': True,
            'order': 4,
        }
    )

    Widget.objects.get_or_create(
        slug='nepali-tts',
        defaults={
            'title': 'Nepali Text to Speech Widget',
            'tool': t_tts,
            'icon': 'bi-soundwave',
            'badge_text': 'Free Widget',
            'short_description': 'Embed an interactive Nepali Text to Speech audio converter with natural neural voices and MP3 export onto your website or blog.',
            'default_width': '100%',
            'default_height': '560',
            'is_active': True,
            'order': 4,
        }
    )

def remove_nepali_tts_tool(apps, schema_editor):
    Tool = apps.get_model('tools', 'Tool')
    Widget = apps.get_model('tools', 'Widget')
    Widget.objects.filter(slug='nepali-tts').delete()
    Tool.objects.filter(slug='nepali-tts').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0006_widgetusage'),
    ]

    operations = [
        migrations.RunPython(create_nepali_tts_tool, remove_nepali_tts_tool),
    ]

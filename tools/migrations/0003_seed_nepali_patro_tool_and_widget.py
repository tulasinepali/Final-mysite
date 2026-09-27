from django.db import migrations

def create_nepali_patro_tool_and_widget(apps, schema_editor):
    Tool = apps.get_model('tools', 'Tool')
    Widget = apps.get_model('tools', 'Widget')

    t_patro, _ = Tool.objects.get_or_create(
        slug='nepali-patro',
        defaults={
            'name': 'नेपाली पात्रो २०८३ (Nepali Patro)',
            'icon': 'bi-calendar3',
            'category': 'converter',
            'short_description': 'इन्टर्याक्टिभ नेपाली पात्रो २०८३: दैनिक तिथि, सार्वजनिक बिदा, दशैँ-तिहार, चाडपर्वहरू र अंग्रेजी मिति समन्वय।',
            'meta_title': 'नेपाली पात्रो २०८३ | Nepali Patro (Calendar) with Tithi, Holidays & Festivals',
            'meta_description': 'Interactive Nepali Patro (Calendar) 2083 Bikram Sambat with Tithi, official public holidays, Dashain & Tihar dates, and English calendar sync.',
            'is_active': True,
            'order': 1,
        }
    )

    Widget.objects.get_or_create(
        slug='nepali-patro',
        defaults={
            'title': 'Nepali Patro (Calendar) Widget',
            'tool': t_patro,
            'icon': 'bi-calendar-date',
            'badge_text': 'Free Widget',
            'short_description': 'Embed a responsive, lightweight Nepali Bikram Sambat Calendar with official holidays, festivals, and English dates onto your school portal, personal blog, or website.',
            'default_width': '100%',
            'default_height': '540',
            'is_active': True,
            'order': 1,
        }
    )

def remove_nepali_patro_tool_and_widget(apps, schema_editor):
    Tool = apps.get_model('tools', 'Tool')
    Widget = apps.get_model('tools', 'Widget')
    Widget.objects.filter(slug='nepali-patro').delete()
    Tool.objects.filter(slug='nepali-patro').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0002_seed_initial_tools_and_widgets'),
    ]

    operations = [
        migrations.RunPython(create_nepali_patro_tool_and_widget, remove_nepali_patro_tool_and_widget),
    ]

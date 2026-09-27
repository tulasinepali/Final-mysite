from django.db import migrations

def create_initial_tools_and_widgets(apps, schema_editor):
    Tool = apps.get_model('tools', 'Tool')
    Widget = apps.get_model('tools', 'Widget')
    WidgetSetting = apps.get_model('tools', 'WidgetSetting')

    WidgetSetting.objects.get_or_create(
        pk=1,
        defaults={
            'allow_embedding': True,
            'branding_text': 'Powered by Tulasi Nepali',
            'branding_url': 'https://tulasinepali.com.np',
            'show_ads_in_widgets': False,
        }
    )

    t_date, _ = Tool.objects.get_or_create(
        slug='date-converter',
        defaults={
            'name': 'Nepali Date Converter (B.S. ↔ A.D.)',
            'icon': 'bi-calendar3',
            'category': 'converter',
            'short_description': 'Accurate two-way Bikram Sambat (B.S.) to Gregorian (A.D.) calendar converter with day of the week and Nepali formatting.',
            'meta_title': 'Nepali Date Converter | Convert B.S. to A.D. & A.D. to B.S. Online',
            'meta_description': 'Free online Nepali Date Converter. Convert Bikram Sambat (B.S.) to English (A.D.) dates accurately. Includes today\'s Nepali date (आजको मिति).',
            'is_active': True,
            'order': 1,
        }
    )

    t_age, _ = Tool.objects.get_or_create(
        slug='age-calculator',
        defaults={
            'name': 'Universal Age Calculator',
            'icon': 'bi-calculator',
            'category': 'calculator',
            'short_description': 'Calculate your exact age in years, months, and days from your Date of Birth in B.S. or A.D.',
            'meta_title': 'Age Calculator Online | Exact Years, Months & Days in B.S. and A.D.',
            'meta_description': 'Free online Age Calculator. Calculate your exact age in years, months, days, total days, and next birthday countdown accurately.',
            'is_active': True,
            'order': 2,
        }
    )

    t_unicode, _ = Tool.objects.get_or_create(
        slug='unicode-converter',
        defaults={
            'name': 'Preeti ↔ Unicode Converter',
            'icon': 'bi-keyboard',
            'category': 'typing',
            'short_description': 'Instant two-way converter for legacy Preeti font text to universal Nepali Unicode and vice-versa.',
            'meta_title': 'Preeti to Unicode Converter | Unicode to Preeti Nepali Font Converter',
            'meta_description': 'Fast and accurate Preeti to Nepali Unicode Converter and Unicode to Preeti converter. Clean text formatting with 1-click copy.',
            'is_active': True,
            'order': 3,
        }
    )

    Widget.objects.get_or_create(
        slug='date-converter',
        defaults={
            'title': 'Nepali Date Converter Widget',
            'tool': t_date,
            'icon': 'bi-calendar3',
            'badge_text': 'Popular',
            'short_description': 'Free embeddable Nepali Date Converter for blogs, schools, and portals. Supports B.S. ↔ A.D. conversion.',
            'default_width': '100%',
            'default_height': '490',
            'is_active': True,
            'order': 1,
        }
    )

    Widget.objects.get_or_create(
        slug='age-calculator',
        defaults={
            'title': 'Age Calculator Widget',
            'tool': t_age,
            'icon': 'bi-calculator',
            'badge_text': 'Essential',
            'short_description': 'Embeddable universal age calculator widget. Calculates exact years, months, and days.',
            'default_width': '100%',
            'default_height': '460',
            'is_active': True,
            'order': 2,
        }
    )

    Widget.objects.get_or_create(
        slug='unicode-converter',
        defaults={
            'title': 'Preeti ↔ Unicode Converter Widget',
            'tool': t_unicode,
            'icon': 'bi-keyboard',
            'badge_text': 'Typing Tool',
            'short_description': 'Allows your website visitors to convert between Preeti font and Nepali Unicode directly on your site.',
            'default_width': '100%',
            'default_height': '480',
            'is_active': True,
            'order': 3,
        }
    )

    Widget.objects.get_or_create(
        slug='nepali-clock',
        defaults={
            'title': "Today's Nepali Miti & Time Widget",
            'tool': None,
            'icon': 'bi-clock-history',
            'badge_text': 'Live Miti',
            'short_description': 'Lightweight live badge showing today\'s Bikram Sambat date (आजको मिति) and Nepal Standard Time (NST).',
            'default_width': '100%',
            'default_height': '220',
            'is_active': True,
            'order': 4,
        }
    )

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_tools_and_widgets, reverse_func),
    ]

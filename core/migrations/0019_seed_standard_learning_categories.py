from django.db import migrations


def create_standard_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    standard_cats = [
        ('Computer Operator', 'computer-operator-notes', 'notes'),
        ('नेपाली व्याकरण (Nepali Grammar)', 'nepali-grammar-notes', 'notes'),
        ('सामान्य ज्ञान (General Knowledge)', 'general-knowledge-notes', 'notes'),
        ('शिक्षक सेवा आयोग (TSC Prep)', 'tsc-prep-notes', 'notes'),
        ('लोक सेवा आयोग (Loksewa PSC)', 'loksewa-psc-notes', 'notes'),
        ('Information Technology & Programming', 'it-programming-notes', 'notes'),
        ('विज्ञान तथा गणित (Science & Math)', 'science-math-notes', 'notes'),
        ('शिक्षा तथा शिक्षण विधि (Pedagogy)', 'pedagogy-education-notes', 'notes'),
        ('Information Technology', 'information-technology-blog', 'blog'),
        ('General Knowledge & Current Affairs', 'gk-current-affairs-blog', 'blog'),
        ('Career & Exam Tips', 'career-exam-tips-blog', 'blog'),
    ]
    for name, slug, module in standard_cats:
        Category.objects.get_or_create(slug=slug, defaults={'name': name, 'module': module})


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_sitesettings_ai_provider_sitesettings_groq_api_key_and_more'),
    ]

    operations = [
        migrations.RunPython(create_standard_categories, migrations.RunPython.noop),
    ]

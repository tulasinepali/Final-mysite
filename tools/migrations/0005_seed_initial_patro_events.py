from django.db import migrations

INITIAL_EVENTS_2083 = [
    # 2083 Baisakh
    (2083, 1, 1, "नयाँ वर्ष २०८३ / मेष संक्रान्ति", True, "holiday"),
    (2083, 1, 11, "लोकतन्त्र दिवस", False, "national"),
    (2083, 1, 18, "अन्तर्राष्ट्रिय श्रमिक दिवस", True, "international"),
    (2083, 1, 19, "बुद्ध जयन्ती / चण्डी पूर्णिमा / उभौली", True, "holiday"),

    # 2083 Jestha
    (2083, 2, 1, "वृष संक्रान्ति", False, "festival"),
    (2083, 2, 15, "गणतन्त्र दिवस", True, "national"),

    # 2083 Ashadh
    (2083, 3, 1, "मिथुन संक्रान्ति", False, "festival"),
    (2083, 3, 15, "राष्ट्रिय धान दिवस", False, "festival"),

    # 2083 Shrawan
    (2083, 4, 1, "साउने संक्रान्ति", False, "festival"),
    (2083, 4, 13, "गाईजात्रा", False, "festival"),
    (2083, 4, 14, "जनै पूर्णिमा / रक्षाबन्धन", True, "holiday"),
    (2083, 4, 20, "श्रीकृष्ण जन्माष्टमी", True, "holiday"),

    # 2083 Bhadra
    (2083, 5, 1, "सिंह संक्रान्ति", False, "festival"),
    (2083, 5, 8, "गौरा पर्व", True, "holiday"),
    (2083, 5, 19, "हरितालिका तीज", True, "holiday"),
    (2083, 5, 21, "ऋषि पञ्चमी", False, "festival"),
    (2083, 5, 30, "इन्द्रजात्रा", False, "festival"),
    (2083, 5, 31, "ओजोन तह संरक्षण दिवस", False, "international"),

    # 2083 Ashwin (दशैं)
    (2083, 6, 1, "कन्या संक्रान्ति", False, "festival"),
    (2083, 6, 3, "संविधान दिवस (राष्ट्रिय दिवस)", True, "national"),
    (2083, 6, 25, "घटस्थापना (दशैं प्रारम्भ)", True, "holiday"),
    (2083, 6, 31, "फूलपाती", True, "holiday"),

    # 2083 Kartik (दशैं र तिहार)
    (2083, 7, 1, "महाअष्टमी / कालरात्रि", True, "holiday"),
    (2083, 7, 2, "महानवमी", True, "holiday"),
    (2083, 7, 3, "विजया दशमी (दशैं टीका)", True, "holiday"),
    (2083, 7, 4, "एकादशी", True, "holiday"),
    (2083, 7, 5, "द्वादशी", True, "holiday"),
    (2083, 7, 8, "कोजाग्रत पूर्णिमा", False, "festival"),
    (2083, 7, 23, "काग तिहार / धनतेरस", False, "festival"),
    (2083, 7, 24, "कुकुर तिहार", False, "festival"),
    (2083, 7, 25, "लक्ष्मी पूजा / दिपावली", True, "holiday"),
    (2083, 7, 26, "गोवर्धन पूजा / म्ह पूजा", True, "holiday"),
    (2083, 7, 27, "भाइटीका", True, "holiday"),
    (2083, 7, 30, "छठ पर्व", True, "holiday"),

    # 2083 Mangsir
    (2083, 8, 1, "वृश्चिक संक्रान्ति", False, "festival"),
    (2083, 8, 8, "बाला चतुर्दशी", False, "festival"),
    (2083, 8, 23, "उधौली पर्व / योमरी पुन्ही", False, "festival"),

    # 2083 Poush
    (2083, 9, 1, "धनु संक्रान्ति", False, "festival"),
    (2083, 9, 10, "क्रिसमस डे", True, "holiday"),
    (2083, 9, 15, "तमु ल्होसार", True, "holiday"),
    (2083, 9, 27, "पृथ्वी जयन्ती / राष्ट्रिय एकता दिवस", True, "national"),

    # 2083 Magh
    (2083, 10, 1, "माघे संक्रान्ति / माघी", True, "holiday"),
    (2083, 10, 16, "शहीद दिवस", False, "national"),
    (2083, 10, 24, "सोनाम ल्होसार", True, "holiday"),
    (2083, 10, 28, "सरस्वती पूजा / श्रीपञ्चमी", False, "festival"),

    # 2083 Falgun
    (2083, 11, 1, "कुम्भ संक्रान्ति", False, "festival"),
    (2083, 11, 7, "राष्ट्रिय प्रजातन्त्र दिवस", True, "national"),
    (2083, 11, 21, "महाशिवरात्रि", True, "holiday"),
    (2083, 11, 24, "अन्तर्राष्ट्रिय नारी दिवस", True, "international"),
    (2083, 11, 26, "ग्याल्पो ल्होसार", True, "holiday"),

    # 2083 Chaitra
    (2083, 12, 1, "मीन संक्रान्ति", False, "festival"),
    (2083, 12, 8, "फागु पूर्णिमा (होली - पहाड)", True, "holiday"),
    (2083, 12, 9, "होली पर्व (तराई)", True, "holiday"),
    (2083, 12, 24, "घोडेजात्रा", False, "festival"),
    (2083, 12, 31, "चैते दशैं / चैत्र मसान्त", False, "festival"),
]

def seed_patro_events(apps, schema_editor):
    PatroEvent = apps.get_model('tools', 'PatroEvent')
    for y, m, d, title, is_h, e_type in INITIAL_EVENTS_2083:
        PatroEvent.objects.get_or_create(
            year_bs=y,
            month_bs=m,
            day_bs=d,
            title=title,
            defaults={
                'is_public_holiday': is_h,
                'event_type': e_type,
            }
        )

def unseed_patro_events(apps, schema_editor):
    PatroEvent = apps.get_model('tools', 'PatroEvent')
    PatroEvent.objects.filter(year_bs=2083).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0004_patroevent'),
    ]

    operations = [
        migrations.RunPython(seed_patro_events, unseed_patro_events),
    ]

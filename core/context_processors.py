from .models import SiteSettings, Category, AdPlacement, VisitorCount


def site_settings(request):
    """Make site settings available in all templates."""
    settings, _ = SiteSettings.objects.get_or_create(pk=1)
    return {'site_settings': settings}


def global_categories(request):
    """Make categorized navigation available in all templates."""
    notes_categories = Category.objects.filter(module='notes', is_active=True)
    downloads_categories = Category.objects.filter(module='downloads', is_active=True)
    blog_categories = Category.objects.filter(module='blog', is_active=True)
    quiz_categories = Category.objects.filter(module='quiz', is_active=True)
    return {
        'notes_categories': notes_categories,
        'downloads_categories': downloads_categories,
        'blog_categories': blog_categories,
        'quiz_categories': quiz_categories,
    }


def ad_placements(request):
    """Make ad placements available in all templates."""
    ads = {}
    popup_ad = None
    for ad in AdPlacement.objects.filter(is_active=True):
        if ad.placement == 'popup':
            popup_ad = ad
        else:
            ads[ad.placement] = ad.ad_code
    visitor_count = VisitorCount.get_count()
    return {'ads': ads, 'popup_ad': popup_ad, 'visitor_count': visitor_count}

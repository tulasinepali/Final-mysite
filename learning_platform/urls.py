from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from core import views as core_views
from core.views import custom_404, custom_500
from django.views.generic import TemplateView
from tools import views as tools_views


urlpatterns = [
    # Private Admin, Login, and Dashboard Suite
    path('rishav/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('rishav/logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('rishav/admin/', admin.site.urls),
    path('rishav/', include('dashboard.urls')),

    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('core.urls')),
    path('notes/', include('notes.urls')),
    path('downloads/', include('downloads.urls')),
    path('blog/', include('blog.urls')),
    path('quiz/', include('quiz.urls')),
    path('search/', include('search.urls')),
    path('tools/', include('tools.urls')),
    path('widgets/', RedirectView.as_view(pattern_name='tools:widgets_index', permanent=False)),
    path('widget/', RedirectView.as_view(pattern_name='tools:widgets_index', permanent=False)),
    path('widgets/embed/<slug:slug>/', tools_views.widget_embed),
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
    path('favicon.ico', core_views.favicon_view, name='favicon'),
    path('health/', core_views.health_check, name='health_check'),
    path('up/', core_views.health_check, name='up'),
    path('ads.txt', core_views.ads_txt, name='ads_txt'),
    # PWA (Progressive Web App) suite
    path('manifest.json', core_views.manifest_json, name='manifest_json'),
    path('manifest.webmanifest', core_views.manifest_json, name='manifest_webmanifest'),
    path('sw.js', core_views.service_worker, name='service_worker'),
    path('offline/', core_views.offline_view, name='offline_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404
handler500 = custom_500

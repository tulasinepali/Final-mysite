from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from core.views import custom_404, custom_500
from django.views.generic import TemplateView


urlpatterns = [
    # Redirect admin login to our custom login page (preserves ?next= parameter)
    path('admin/login/', RedirectView.as_view(url='/login/', query_string=True, permanent=False)),
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    # Login / Logout
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('', include('core.urls')),
    path('notes/', include('notes.urls')),
    path('downloads/', include('downloads.urls')),
    path('blog/', include('blog.urls')),
    path('quiz/', include('quiz.urls')),
    path('search/', include('search.urls')),
    path('dashboard/', include('dashboard.urls')),
    path(
        "ads.txt",
        TemplateView.as_view(
            template_name="ads.txt",
            content_type="text/plain"
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404
handler500 = custom_500

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy'),
    path('terms-conditions/', views.terms_conditions, name='terms'),
    path('sitemap.html', views.sitemap_view, name='sitemap'),
    # path('robots.txt', views.robots_txt, name='robots'),
]
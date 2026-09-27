from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    # Tools URLs
    path('', views.tools_index, name='tools_index'),
    path('index/', views.tools_index, name='index'),
    path('date-converter/', views.date_converter, name='date_converter'),
    path('age-calculator/', views.age_calculator, name='age_calculator'),
    path('unicode-converter/', views.unicode_converter, name='unicode_converter'),
    path('nepali-patro/', views.nepali_patro, name='nepali_patro'),

    # Widgets URLs
    path('widgets/', views.widgets_index, name='widgets_index'),
    path('widgets/embed/<slug:slug>/', views.widget_embed, name='widget_embed'),
    path('widgets/api/track/<slug:slug>/', views.api_track_embed, name='api_track_embed'),

    # Generic Tool Detail (keep at end to prevent slug conflicts)
    path('<slug:slug>/', views.tool_detail, name='tool_detail'),
]

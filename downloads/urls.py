from django.urls import path
from . import views

app_name = 'downloads'

urlpatterns = [
    path('', views.download_list, name='list'),
    path('<slug:slug>/', views.download_detail, name='detail'),
    path('<slug:slug>/download/', views.download_file, name='download_file'),
]

from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.note_list, name='list'),
    path('<slug:slug>/', views.note_detail, name='detail'),
    path('<slug:slug>/print/', views.note_print, name='print'),
]

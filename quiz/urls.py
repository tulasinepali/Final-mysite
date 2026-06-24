from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.quiz_list, name='list'),
    path('<slug:slug>/', views.quiz_detail, name='detail'),
    path('<slug:slug>/result/', views.quiz_result, name='result'),
    path('<slug:slug>/leaderboard/', views.quiz_leaderboard, name='leaderboard'),
]

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),

    # Notes
    path('notes/', views.dashboard_notes, name='notes'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('notes/<int:pk>/toggle-publish/', views.note_toggle_publish, name='note_toggle_publish'),
    path('notes/<int:pk>/toggle-featured/', views.note_toggle_featured, name='note_toggle_featured'),

    # Blogs
    path('blogs/', views.dashboard_blogs, name='blogs'),
    path('blogs/create/', views.blog_create, name='blog_create'),
    path('blogs/<int:pk>/edit/', views.blog_edit, name='blog_edit'),
    path('blogs/<int:pk>/delete/', views.blog_delete, name='blog_delete'),
    path('blogs/<int:pk>/toggle-publish/', views.blog_toggle_publish, name='blog_toggle_publish'),
    path('blogs/<int:pk>/toggle-featured/', views.blog_toggle_featured, name='blog_toggle_featured'),

    # Downloads
    path('downloads/', views.dashboard_downloads, name='downloads'),
    path('downloads/create/', views.download_create, name='download_create'),
    path('downloads/<int:pk>/edit/', views.download_edit, name='download_edit'),
    path('downloads/<int:pk>/delete/', views.download_delete, name='download_delete'),
    path('downloads/<int:pk>/toggle-publish/', views.download_toggle_publish, name='download_toggle_publish'),
    path('downloads/<int:pk>/toggle-featured/', views.download_toggle_featured, name='download_toggle_featured'),

    # Quizzes
    path('quizzes/', views.dashboard_quizzes, name='quizzes'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quizzes/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('quizzes/<int:pk>/toggle-publish/', views.quiz_toggle_publish, name='quiz_toggle_publish'),
    path('quizzes/<int:pk>/toggle-featured/', views.quiz_toggle_featured, name='quiz_toggle_featured'),
    path('quizzes/<int:pk>/toggle-negative-marking/', views.quiz_toggle_negative_marking, name='quiz_toggle_negative_marking'),
    path('quizzes/<int:pk>/questions/', views.quiz_questions, name='quiz_questions'),

    # Questions (within quiz context)
    path('quizzes/<int:quiz_pk>/questions/create/', views.question_create, name='question_create'),
    path('quizzes/<int:quiz_pk>/questions/import/', views.question_import_excel, name='question_import'),
    path('quizzes/<int:quiz_pk>/questions/sample-excel/', views.question_download_sample_excel, name='question_sample_excel'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),

    # Categories
    path('categories/', views.dashboard_categories, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Tags
    path('tags/', views.dashboard_tags, name='tags'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),

    # Messages
    path('messages/', views.dashboard_messages, name='messages'),
    path('messages/<int:pk>/', views.message_read, name='message_read'),
    path('messages/<int:pk>/mark-read/', views.message_read, name='message_mark_read'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    # Settings
    path('settings/', views.dashboard_settings, name='settings'),

    # Subscribers & Broadcast
    path('subscribers/', views.dashboard_subscribers, name='subscribers'),
    path('subscribers/<int:pk>/toggle/', views.subscriber_toggle_active, name='subscriber_toggle_active'),
    path('subscribers/<int:pk>/delete/', views.subscriber_delete, name='subscriber_delete'),
    path('subscribers/export/', views.subscriber_export_csv, name='subscriber_export_csv'),
    path('subscribers/broadcast/', views.dashboard_broadcast_email, name='broadcast_email'),

    # Ad Placements
    path('ads/', views.dashboard_ads, name='ads'),
    path('ads/create/', views.ad_create, name='ad_create'),
    path('ads/<int:pk>/edit/', views.ad_edit, name='ad_edit'),
    path('ads/<int:pk>/delete/', views.ad_delete, name='ad_delete'),
    path('ads/<int:pk>/toggle/', views.ad_toggle, name='ad_toggle'),

    # Analytics
    path('analytics/', views.dashboard_analytics, name='analytics'),
]

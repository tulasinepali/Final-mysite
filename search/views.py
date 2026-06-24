from django.shortcuts import render
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz

def search(request):
    query = request.GET.get('q', '').strip()
    notes = Note.objects.filter(is_published=True, title__icontains=query) if query else []
    blogs = BlogPost.objects.filter(is_published=True, title__icontains=query) if query else []
    downloads = Download.objects.filter(is_published=True, title__icontains=query) if query else []
    quizzes = Quiz.objects.filter(is_published=True, title__icontains=query) if query else []
    
    total_results = len(notes) + len(blogs) + len(downloads) + len(quizzes)
    
    context = {
        'query': query,
        'notes': notes[:10],
        'blogs': blogs[:10],
        'downloads': downloads[:10],
        'quizzes': quizzes[:10],
        'total_results': total_results,
        'meta_title': f'Search results for "{query}" - Learning Platform' if query else 'Search - Learning Platform',
        'meta_description': 'Search across notes, blogs, downloads, and MCQ quizzes on Learning Platform.',
    }
    return render(request, 'search/results.html', context)

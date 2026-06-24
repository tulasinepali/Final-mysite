from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Note
from core.models import Category

def note_list(request):
    notes = Note.objects.filter(is_published=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        notes = notes.filter(category__slug=category_slug)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        notes = notes.filter(title__icontains=search_query)
    
    # Pagination
    paginator = Paginator(notes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(module='notes', is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query or '',
        'meta_title': 'Study Notes - Learning Platform',
        'meta_description': 'Browse our collection of study notes covering Computer Science, English, Mathematics, Science, GK and more.',
    }
    return render(request, 'notes/list.html', context)

def note_detail(request, slug):
    note = get_object_or_404(Note, slug=slug, is_published=True)
    
    # Increment view count
    note.views += 1
    note.save(update_fields=['views'])
    
    # Related notes
    related_notes = Note.objects.filter(
        category=note.category, is_published=True
    ).exclude(pk=note.pk)[:4]
    
    context = {
        'note': note,
        'related_notes': related_notes,
        'meta_title': note.get_meta_title(),
        'meta_description': note.get_meta_description(),
        'og_image': note.featured_image.url if note.featured_image else None,
    }
    return render(request, 'notes/detail.html', context)

def note_print(request, slug):
    note = get_object_or_404(Note, slug=slug, is_published=True)
    context = {'note': note}
    return render(request, 'notes/print.html', context)

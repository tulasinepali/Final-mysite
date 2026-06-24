from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Download
from core.models import Category

def download_list(request):
    downloads = Download.objects.filter(is_published=True)
    
    category_slug = request.GET.get('category')
    if category_slug:
        downloads = downloads.filter(category__slug=category_slug)
    
    search_query = request.GET.get('q')
    if search_query:
        downloads = downloads.filter(title__icontains=search_query)
    
    paginator = Paginator(downloads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(module='downloads', is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query or '',
        'meta_title': 'Downloads - Learning Platform',
        'meta_description': 'Download study materials, syllabus, question papers, notes PDFs and guides for free.',
    }
    return render(request, 'downloads/list.html', context)

def download_detail(request, slug):
    download = get_object_or_404(Download, slug=slug, is_published=True)
    
    related_downloads = Download.objects.filter(
        category=download.category, is_published=True
    ).exclude(pk=download.pk)[:4]
    
    context = {
        'download': download,
        'related_downloads': related_downloads,
        'meta_title': download.get_meta_title(),
        'meta_description': download.get_meta_description(),
    }
    return render(request, 'downloads/detail.html', context)

def download_file(request, slug):
    download = get_object_or_404(Download, slug=slug, is_published=True)
    download.download_count += 1
    download.save(update_fields=['download_count'])
    return redirect(download.file.url)

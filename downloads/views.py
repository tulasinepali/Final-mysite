import os
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from .models import Download
from core.models import Category
from core.middleware import is_admin_or_staff

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
    if not is_admin_or_staff(request):
        download.download_count += 1
        download.save(update_fields=['download_count'])
    
    if download.file:
        try:
            file_path = download.file.path
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                content_type, _ = mimetypes.guess_type(file_path)
                response = FileResponse(
                    open(file_path, 'rb'),
                    as_attachment=True,
                    filename=filename,
                    content_type=content_type or 'application/octet-stream'
                )
                return response
        except (AttributeError, ValueError, NotImplementedError):
            pass
        return redirect(download.file.url)
    raise Http404("File not found")

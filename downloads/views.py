import os
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from .models import Download
from core.models import Category
from core.middleware import is_admin_or_staff

def download_list(request):
    downloads = Download.objects.filter(is_published=True).select_related('category')
    
    # Filter by resource type (e.g., syllabus, past_question, model_question, solution, notes, software, law)
    resource_type = request.GET.get('type') or request.GET.get('resource_type')
    if resource_type:
        if resource_type in ['question', 'questions']:
            downloads = downloads.filter(resource_type__in=['past_question', 'model_question'])
        elif resource_type in ['law', 'laws', 'legislation', 'legislations']:
            downloads = downloads.filter(resource_type='law')
        elif resource_type in ['other', 'others']:
            downloads = downloads.filter(resource_type='other')
        else:
            downloads = downloads.filter(resource_type=resource_type)
    
    # Filter by exam/education sector (e.g., psc, tsc, banking, school, pradesh, sansthan, security, university, ctevt, entrance)
    target_sector = request.GET.get('sector') or request.GET.get('target_sector')
    if target_sector:
        downloads = downloads.filter(target_sector=target_sector)

    # Filter by specific sub-sector / level keyword
    sub_sector = request.GET.get('sub_sector')
    if sub_sector:
        downloads = downloads.filter(sub_sector__icontains=sub_sector)
    
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

    # Human readable active filter names for SEO / breadcrumb
    type_name_map = dict(Download.RESOURCE_TYPE_CHOICES)
    type_name_map['questions'] = 'Questions'
    type_name_map['question'] = 'Questions'
    type_name_map['laws'] = 'Legislations & Laws'
    type_name_map['legislation'] = 'Legislations & Laws'
    type_name_map['legislations'] = 'Legislations & Laws'
    type_name_map['others'] = 'Others'
    sector_name_map = dict(Download.TARGET_SECTOR_CHOICES)
    active_type_name = type_name_map.get(resource_type, '')
    active_sector_name = sector_name_map.get(target_sector, '')

    page_title = 'Downloads Hub'
    if active_type_name and active_sector_name:
        page_title = f"{active_type_name} - {active_sector_name}"
    elif active_type_name:
        page_title = f"{active_type_name} Downloads"
    elif active_sector_name:
        page_title = f"{active_sector_name} Resources"

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'resource_type': resource_type or '',
        'target_sector': target_sector or '',
        'sub_sector': sub_sector or '',
        'active_type_name': active_type_name,
        'active_sector_name': active_sector_name,
        'resource_type_choices': Download.RESOURCE_TYPE_CHOICES,
        'target_sector_choices': Download.TARGET_SECTOR_CHOICES,
        'search_query': search_query or '',
        'total_count': downloads.count(),
        'meta_title': f"{page_title} - Tulasi Nepali",
        'meta_description': 'Download official syllabi, past and model questions, textbook solutions, notes PDFs, and educational softwares for free.',
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

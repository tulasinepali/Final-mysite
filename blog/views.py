from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost
from core.models import Category, Tag

def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    tag_slug = request.GET.get('tag')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)
    
    search_query = request.GET.get('q')
    if search_query:
        posts = posts.filter(title__icontains=search_query)
    
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(module='blog', is_active=True)
    tags = Tag.objects.filter(blog_posts__isnull=False).distinct()
    featured_posts = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'featured_posts': featured_posts,
        'current_category': category_slug,
        'current_tag': tag_slug,
        'search_query': search_query or '',
        'meta_title': 'Educational Blog - Learning Platform',
        'meta_description': 'Read our latest educational articles, study tips, exam preparation guides, and tutorials.',
    }
    return render(request, 'blog/list.html', context)

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    
    post.views += 1
    post.save(update_fields=['views'])
    
    related_posts = BlogPost.objects.filter(
        category=post.category, is_published=True
    ).exclude(pk=post.pk)[:4]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'meta_title': post.get_meta_title(),
        'meta_description': post.get_meta_description(),
        'og_image': post.featured_image.url if post.featured_image else None,
    }
    return render(request, 'blog/detail.html', context)

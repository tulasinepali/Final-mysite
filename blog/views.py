from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from .models import BlogPost, Comment
from .forms import CommentForm
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
    
    # Increment view count
    post.views += 1
    post.save(update_fields=['views'])
    
    # Related posts
    related_posts = BlogPost.objects.filter(
        category=post.category, is_published=True
    ).exclude(pk=post.pk)[:4]

    # Handle Comment Form Submission
    if request.method == 'POST':
        # Antispam check: honeypot field must be empty
        honeypot = request.POST.get('hp_website', '').strip()
        if honeypot:
            # Bot filled out honeypot - silently redirect
            return redirect(f"{post.get_absolute_url()}#comments")

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            
            # Client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                new_comment.ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                new_comment.ip_address = request.META.get('REMOTE_ADDR')

            # Handle reply to an existing comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_obj = Comment.objects.get(id=int(parent_id), post=post)
                    new_comment.parent = parent_obj
                except (Comment.DoesNotExist, ValueError):
                    pass

            new_comment.save()
            messages.success(request, "🎉 Thank you! Your comment has been posted successfully.")
            return redirect(f"{post.get_absolute_url()}#comment-{new_comment.id}")
        else:
            messages.error(request, "Please check the form fields and try submitting your comment again.")
    else:
        comment_form = CommentForm()

    # Fetch top-level approved comments with their replies pre-fetched
    approved_comments = post.comments.filter(
        is_approved=True, parent__isnull=True
    ).prefetch_related('replies').order_by('created_at')
    
    total_comments_count = post.comments.filter(is_approved=True).count()
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'approved_comments': approved_comments,
        'total_comments_count': total_comments_count,
        'comment_form': comment_form,
        'meta_title': post.get_meta_title(),
        'meta_description': post.get_meta_description(),
        'og_image': post.featured_image.url if post.featured_image else None,
    }
    return render(request, 'blog/detail.html', context)


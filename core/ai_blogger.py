"""
AI Content Generation Engine for Tulasi Nepali Learning Platform
Supports automatic and on-demand generation of Blog Posts and Study Notes
using Google Gemini API (Free tier compatible).
"""

import os
import json
import re
import requests
from django.utils import timezone
from django.utils.text import slugify
from core.models import SiteSettings, Category, Tag, AITopicQueue, AIGenerationLog
from blog.models import BlogPost
from notes.models import Note


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def get_gemini_config():
    """Retrieve API key and model choice from SiteSettings or environment"""
    settings = SiteSettings.objects.first()
    api_key = ''
    model = 'gemini-2.0-flash'

    if settings and settings.gemini_api_key:
        api_key = settings.gemini_api_key.strip()
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if settings and settings.gemini_model:
        model = settings.gemini_model

    return api_key, model, settings


def sanitize_slug(text, max_len=180):
    """Generate a clean URL slug supporting Latin or transliterated text"""
    clean = re.sub(r'[^\w\s-]', '', text).strip()
    clean = re.sub(r'[-\s]+', '-', clean)
    s = slugify(clean, allow_unicode=True)
    if not s:
        s = f"post-{int(timezone.now().timestamp())}"
    return s[:max_len]


def ensure_unique_slug(model_cls, base_slug):
    """Ensure slug does not collide with existing records"""
    slug = base_slug
    counter = 1
    while model_cls.objects.filter(slug=slug).exists():
        slug = f"{base_slug[:170]}-{counter}"
        counter += 1
    return slug


def generate_content_for_topic(topic: AITopicQueue):
    """
    Generate and save a full Blog Post or Study Note from a queued topic.
    Returns: (success: bool, result_obj_or_error_msg, log_obj)
    """
    api_key, model, settings = get_gemini_config()
    if not api_key:
        err = "Google Gemini API Key is missing. Please enter your free Gemini API Key in AI Settings."
        topic.status = 'failed'
        topic.error_message = err
        topic.save(update_fields=['status', 'error_message'])
        log = AIGenerationLog.objects.create(
            topic_title=topic.title,
            content_type=topic.content_type,
            language=topic.language,
            status='error',
            message=err
        )
        return False, err, log

    topic.status = 'generating'
    topic.save(update_fields=['status'])

    # Determine language guidance
    if topic.language == 'ne':
        lang_instruction = "Write strictly in high-quality, authentic Nepali (नेपाली - देवनागरी लिपि). Use proper grammar and natural Devanagari numerals where appropriate."
    elif topic.language == 'en':
        lang_instruction = "Write in professional, clear, fluent English."
    else:  # bilingual
        lang_instruction = (
            "Write in modern bilingual style popular in Nepali education: primarily written in clear, fluent Nepali (देवनागरी), "
            "but keeping all key technical terms, computer concepts, abbreviations (e.g. CPU, RAM, HTML, IP Address), "
            "and subject-matter terminology clearly in English alongside Nepali explanations."
        )

    # Determine content-type guidance
    if topic.content_type == 'note':
        structure_instruction = (
            "Format this as a comprehensive, curriculum-grade Study Note / Educational Chapter:\n"
            "1. Clear Overview & Definition (परिचय तथा परिभाषा)\n"
            "2. Core Concepts with Detailed Sub-sections (मुख्य अवधारणाहरू)\n"
            "3. Key Points / Rules / Functions with bullet points\n"
            "4. Comparison / Summary Table (if applicable, use clean HTML <table>)\n"
            "5. Practical Application / Real-world relevance\n"
            "6. Quick Review Questions & Answers / Practice MCQs at the end (अभ्यासका लागि प्रश्नोत्तर)"
        )
        target_audience = "Students, competitive exam candidates, computer operator trainees, and educators in Nepal."
    else:
        structure_instruction = (
            "Format this as an engaging, informative, and authoritative Blog Guide / Article:\n"
            "1. Engaging hook and Introduction explaining why this topic matters\n"
            "2. Detailed breakdowns organized under multiple <h2> and <h3> subheadings\n"
            "3. Actionable tips, facts, step-by-step guidance or analysis\n"
            "4. Bullet points and highlight boxes (<div class='alert alert-info'>) for key takeaways\n"
            "5. Thoughtful Conclusion with actionable recommendations"
        )
        target_audience = "General learners, technology enthusiasts, students, and readers in Nepal."

    category_name = topic.category.name if topic.category else "Education & Technology"
    hint_text = f"Special Focus Areas / User Instructions: {topic.prompt_hint}" if topic.prompt_hint else ""

    system_prompt = (
        "You are an expert curriculum educator, academic author, and master content creator for 'Tulasi Nepali' (tulasinepali.com.np), "
        "a premier educational and technology knowledge platform in Nepal.\n"
        "Your task is to generate a comprehensive, highly informative, factually accurate article.\n"
        "You MUST return your response as a valid, pure JSON object with NO surrounding markdown backticks."
    )

    user_prompt = f"""
Topic Title / Subject: "{topic.title}"
Content Type: {topic.get_content_type_display()}
Subject Domain / Category: {category_name}
Target Audience: {target_audience}
Language Requirement: {lang_instruction}
Structure Instructions:
{structure_instruction}
{hint_text}

JSON Output Schema required:
{{
  "title": "A compelling, accurate, and SEO-friendly title",
  "slug": "url-friendly-slug-in-english-or-transliteration",
  "summary": "Concise 120-180 character meta summary / excerpt for Google and cards",
  "meta_title": "SEO title under 70 characters",
  "meta_description": "SEO description under 160 characters",
  "content": "Rich HTML content (at least 900-1400 words) using <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>, <blockquote>. Do NOT wrap with <html> or <body> tags. Do NOT use markdown code blocks inside the HTML.",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"]
}}
"""

    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt + "\n\n" + user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 6000,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=90)
        if response.status_code != 200:
            err = f"Gemini API Error ({response.status_code}): {response.text[:300]}"
            raise Exception(err)

        resp_data = response.json()
        raw_text = resp_data['candidates'][0]['content']['parts'][0]['text']

        # Parse JSON
        cleaned_json = raw_text.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()

        data = json.loads(cleaned_json)

        article_title = data.get('title') or topic.title
        article_slug = sanitize_slug(data.get('slug') or article_title)
        article_summary = data.get('summary') or article_title[:150]
        article_content = data.get('content') or ""
        article_meta_title = data.get('meta_title') or article_title[:180]
        article_meta_desc = data.get('meta_description') or article_summary[:280]
        tags_list = data.get('tags') or []

        # Find or assign Category
        target_module = 'notes' if topic.content_type == 'note' else 'blog'
        category = topic.category
        if not category or category.module != target_module:
            if topic.content_type == 'note' and settings and settings.ai_default_note_category:
                category = settings.ai_default_note_category
            elif topic.content_type == 'blog' and settings and settings.ai_default_blog_category:
                category = settings.ai_default_blog_category
            else:
                category = Category.objects.filter(module=target_module).first()
                if not category:
                    category = Category.objects.create(
                        name="General Study" if topic.content_type == 'note' else "General Blog",
                        slug=f"general-{target_module}",
                        module=target_module
                    )

        # Determine publication status
        if topic.content_type == 'note':
            publish_mode = settings.ai_note_publish_mode if settings else 'published'
        else:
            publish_mode = settings.ai_blog_publish_mode if settings else 'published'
        is_pub = (publish_mode == 'published')

        # Create Record
        if topic.content_type == 'note':
            unique_slug = ensure_unique_slug(Note, article_slug)
            obj = Note.objects.create(
                title=article_title,
                slug=unique_slug,
                category=category,
                summary=article_summary,
                content=article_content,
                meta_title=article_meta_title,
                meta_description=article_meta_desc,
                is_published=is_pub
            )
            topic.generated_note = obj
            if settings:
                settings.last_ai_note_at = timezone.now()
                settings.save(update_fields=['last_ai_note_at'])
        else:
            unique_slug = ensure_unique_slug(BlogPost, article_slug)
            obj = BlogPost.objects.create(
                title=article_title,
                slug=unique_slug,
                category=category,
                summary=article_summary,
                content=article_content,
                meta_title=article_meta_title,
                meta_description=article_meta_desc,
                is_published=is_pub
            )
            topic.generated_blog = obj
            if settings:
                settings.last_ai_blog_at = timezone.now()
                settings.save(update_fields=['last_ai_blog_at'])

        # Attach Tags
        for t_name in tags_list[:5]:
            t_name = t_name.strip()
            if t_name:
                tag, _ = Tag.objects.get_or_create(name=t_name, defaults={'slug': slugify(t_name, allow_unicode=True) or f"tag-{int(timezone.now().timestamp())}"})
                obj.tags.add(tag)

        # Mark Topic Completed
        topic.status = 'completed'
        topic.completed_at = timezone.now()
        topic.error_message = ''
        topic.save()

        # Word count calculation
        words = len(re.findall(r'\w+', article_content))

        # Log
        log = AIGenerationLog.objects.create(
            topic_title=topic.title,
            content_type=topic.content_type,
            language=topic.language,
            status='success',
            word_count=words,
            article_url=obj.get_absolute_url(),
            message=f"Successfully generated {words} words. Published status: {is_pub}."
        )

        return True, obj, log

    except Exception as exc:
        err_msg = str(exc)
        topic.status = 'failed'
        topic.error_message = err_msg
        topic.save(update_fields=['status', 'error_message'])

        log = AIGenerationLog.objects.create(
            topic_title=topic.title,
            content_type=topic.content_type,
            language=topic.language,
            status='error',
            message=err_msg
        )
        return False, err_msg, log


def suggest_topics_with_gemini(domain="diverse", content_type="blog", language="bilingual", count=15):
    """
    Ask Gemini to brainstorm high-value, educational topics.
    Returns: list of dicts [{'title': '...', 'content_type': '...', 'category_name': '...', 'hint': '...'}]
    """
    api_key, model, _ = get_gemini_config()
    if not api_key:
        raise ValueError("Google Gemini API Key is missing. Please add it in AI Settings.")

    if language == 'ne':
        lang_note = "Topics should be phrased in clean Nepali (नेपाली - देवनागरी)."
    elif language == 'en':
        lang_note = "Topics should be phrased in English."
    else:
        lang_note = "Topics can be bilingual or Nepali with English technical terms."

    prompt = f"""
Generate {count} engaging, educational, and high-interest article/study topics for 'Tulasi Nepali' (tulasinepali.com.np).
Domain Focus: {domain} (Include topics across Information Technology & Computer Skills, School/College Curriculum & Grammar, General Knowledge & World Affairs, Teacher Training & Productivity).
Target Content Type: {content_type}
Language Requirement: {lang_note}

Return a valid JSON array of {count} objects matching this exact schema:
[
  {{
    "title": "Clear, engaging topic title",
    "content_type": "{content_type}",
    "language": "{language}",
    "category_name": "Technology / Notes / GK / Education",
    "hint": "Brief 1-sentence note on key aspects to cover"
  }}
]
Do NOT include markdown fences, just pure JSON.
"""

    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
    }

    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
    if response.status_code != 200:
        raise Exception(f"Gemini API Error ({response.status_code}): {response.text[:200]}")

    raw = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())


def run_daily_ai_generation_job():
    """
    Scheduled job function: called by cPanel cron or management command.
    Checks if daily blog and/or daily note are enabled, selects the next pending topic for each, and generates.
    """
    settings = SiteSettings.objects.first()
    if not settings:
        return {"status": "skipped", "message": "No SiteSettings found"}

    results = []

    # 1. Process Daily Blog
    if settings.enable_daily_ai_blog:
        blog_topic = AITopicQueue.objects.filter(content_type='blog', status='pending').first()
        if blog_topic:
            ok, res, log = generate_content_for_topic(blog_topic)
            results.append({"type": "blog", "topic": blog_topic.title, "success": ok, "detail": str(res)})
        else:
            results.append({"type": "blog", "status": "no_pending_topics", "message": "Blog queue is empty"})

    # 2. Process Daily Note
    if settings.enable_daily_ai_note:
        note_topic = AITopicQueue.objects.filter(content_type='note', status='pending').first()
        if note_topic:
            ok, res, log = generate_content_for_topic(note_topic)
            results.append({"type": "note", "topic": note_topic.title, "success": ok, "detail": str(res)})
        else:
            results.append({"type": "note", "status": "no_pending_topics", "message": "Note queue is empty"})

    return results

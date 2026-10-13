"""
AI Content Generation Engine for Tulasi Nepali Learning Platform
Supports automatic and on-demand generation of Blog Posts and Study Notes
using Google Gemini API (Free tier compatible).
"""

import os
import json
import re
import urllib.request
import urllib.error
from django.utils import timezone
from django.utils.text import slugify
from core.models import SiteSettings, Category, Tag, AITopicQueue, AIGenerationLog
from blog.models import BlogPost
from notes.models import Note


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_ai_config():
    """Retrieve Provider, API key, and model choice from SiteSettings or environment"""
    settings = SiteSettings.objects.first()
    provider = 'gemini'
    api_key = ''
    model = 'gemini-3.8-flash'

    if settings:
        provider = getattr(settings, 'ai_provider', 'gemini') or 'gemini'
        if provider == 'groq':
            api_key = (getattr(settings, 'groq_api_key', '') or '').strip()
            model = getattr(settings, 'gemini_model', '') or 'llama-3.3-70b-versatile'
            if not model or 'gemini' in model:
                model = 'llama-3.3-70b-versatile'
        else:
            api_key = (settings.gemini_api_key or '').strip()
            model = (settings.gemini_model or '').strip() or 'gemini-3.8-flash'
            if model in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.0-flash-exp', 'gemini-2.5-flash']:
                model = 'gemini-3.8-flash'
            elif 'llama' in model:
                model = 'gemini-3.8-flash'

    # Auto-detect Groq if key starts with gsk_
    if api_key.startswith('gsk_'):
        provider = 'groq'
        if 'gemini' in model:
            model = 'llama-3.3-70b-versatile'

    return provider, api_key, model, settings


def get_gemini_config():
    """Backward compatibility wrapper"""
    provider, api_key, model, settings = get_ai_config()
    return api_key, model, settings


def _call_groq_api(api_key, model, system_prompt, user_prompt, timeout=90):
    """Call Groq OpenAI-compatible chat completion endpoint using standard library urllib"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GROQ_API_URL,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            choices = res_json.get('choices') or []
            if not choices:
                raise Exception(f"No choices returned by Groq: {res_body[:200]}")
            return choices[0].get('message', {}).get('content', '')
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')[:300]
        raise Exception(f"Groq API Error ({e.code}): {err_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Groq Connection Error: {e.reason}")


def _call_gemini_api(url, payload, timeout=90, max_retries=3):
    """
    Call Gemini REST endpoint using Python standard library urllib.
    Includes automated exponential backoff retry for transient 503 (high demand) and 429 (rate limit) errors.
    """
    import time
    data_bytes = json.dumps(payload).encode('utf-8')

    for attempt in range(max_retries):
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')[:300]
            # If server is overloaded (503) or rate-limited (429), retry with backoff
            if e.code in (503, 429) and attempt < max_retries - 1:
                sleep_sec = 2 ** attempt * 2  # 2s, 4s, 8s
                time.sleep(sleep_sec)
                continue
            raise Exception(f"Gemini API Error ({e.code}): {err_body}")
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise Exception(f"Gemini Connection Error: {e.reason}")


def extract_gemini_text(resp_data):
    """Safely extract generated text across various Gemini response structures"""
    if not isinstance(resp_data, dict):
        raise Exception(f"Unexpected response format: {type(resp_data)}")

    # Check for direct prompt feedback or block
    if resp_data.get('promptFeedback', {}).get('blockReason'):
        reason = resp_data['promptFeedback']['blockReason']
        raise Exception(f"Prompt was blocked by Gemini safety filter: {reason}")

    candidates = resp_data.get('candidates') or []
    if not candidates:
        if 'error' in resp_data:
            err = resp_data['error']
            raise Exception(f"Gemini Error ({err.get('code')}): {err.get('message')}")
        raise Exception(f"No candidates returned by Gemini: {json.dumps(resp_data)[:200]}")

    cand = candidates[0]
    content = cand.get('content') or {}
    parts = content.get('parts') or []
    if not parts:
        finish = cand.get('finishReason', 'UNKNOWN')
        if finish in ['MAX_TOKENS', 'STOP']:
            return "OK"
        raise Exception(f"Empty candidate parts (finishReason: {finish})")

    # Combine all parts texts
    texts = [p.get('text', '') for p in parts if isinstance(p, dict) and 'text' in p]
    return ''.join(texts).strip()


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


def fetch_and_attach_featured_image(blog_post: BlogPost, topic_title: str, category_name: str = ""):
    """
    Automatically attach a clean, high-resolution, relevant featured image to the blog post.
    Uses high-quality open educational/tech image sources based on topic keywords.
    """
    from django.core.files.base import ContentFile
    import urllib.parse

    # Extract keywords
    clean_kw = re.sub(r'[^\w\s]', '', topic_title.lower())
    words = [w for w in clean_kw.split() if len(w) > 3 and not re.search(r'[\u0900-\u097F]', w)]
    search_term = words[0] if words else "technology"
    if category_name and not re.search(r'[\u0900-\u097F]', category_name):
        search_term = f"{search_term},{category_name.lower().split()[0]}"

    # Unsplash Source with educational/tech fallback
    encoded_query = urllib.parse.quote(search_term)
    img_urls = [
        f"https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&auto=format&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&auto=format&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&auto=format&fit=crop&q=80",
        f"https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1200&auto=format&fit=crop&q=80"
    ]

    # Select thematic image
    title_lower = topic_title.lower()
    if any(k in title_lower for k in ['code', 'python', 'program', 'html', 'css', 'software', 'developer']):
        chosen_url = "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&auto=format&fit=crop&q=80"
    elif any(k in title_lower for k in ['network', 'cloud', 'cyber', 'security', 'internet', 'server', 'data']):
        chosen_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&auto=format&fit=crop&q=80"
    elif any(k in title_lower for k in ['book', 'grammar', 'nepali', 'literature', 'study', 'exam', 'tsc', 'teacher']):
        chosen_url = "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1200&auto=format&fit=crop&q=80"
    else:
        chosen_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&auto=format&fit=crop&q=80"

    try:
        req = urllib.request.Request(
            chosen_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                img_data = resp.read()
                filename = f"ai_blog_{blog_post.slug[:50]}.jpg"
                blog_post.featured_image.save(filename, ContentFile(img_data), save=True)
                return True
    except Exception as e:
        # Silently log without failing article generation
        pass
    return False


def generate_content_for_topic(topic: AITopicQueue):
    """
    Generate and save a full Blog Post or Study Note from a queued topic.
    Supports both Groq (Llama 3.3 70B) and Google Gemini engines.
    Returns: (success: bool, result_obj_or_error_msg, log_obj)
    """
    provider, api_key, model, settings = get_ai_config()
    if not api_key:
        engine_name = "Groq" if provider == 'groq' else "Google Gemini"
        err = f"{engine_name} API Key is missing. Please enter your API Key in AI Settings."
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

    try:
        if provider == 'groq':
            raw_text = _call_groq_api(api_key, model, system_prompt, user_prompt, timeout=90)
        else:
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
                resp_data = _call_gemini_api(url, payload, timeout=90)
            except Exception as primary_err:
                # If primary model is unavailable (503 / 429), try gemini-3.8-flash as fallback
                if "503" in str(primary_err) or "UNAVAILABLE" in str(primary_err) or "429" in str(primary_err):
                    fallback_model = "gemini-3.8-flash"
                    if model != fallback_model:
                        fallback_url = GEMINI_API_URL.format(model=fallback_model) + f"?key={api_key}"
                        resp_data = _call_gemini_api(fallback_url, payload, timeout=90)
                    else:
                        raise primary_err
                else:
                    raise primary_err

            raw_text = extract_gemini_text(resp_data)

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
            # Automatically fetch & attach high-res featured image
            fetch_and_attach_featured_image(obj, article_title, category.name if category else "")

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
    provider, api_key, model, _ = get_ai_config()
    if not api_key:
        raise ValueError("AI API Key is missing. Please add your Groq or Gemini API Key in AI Settings.")

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

    if provider == 'groq':
        raw = _call_groq_api(api_key, model, "You are a helpful educational topic brainstormer.", prompt, timeout=45)
    else:
        url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
        }
        resp_data = _call_gemini_api(url, payload, timeout=45)
        raw = extract_gemini_text(resp_data)

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

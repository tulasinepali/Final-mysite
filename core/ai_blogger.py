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
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"


def get_ai_config():
    """Retrieve Provider, API key, and model choice from SiteSettings or environment"""
    settings = SiteSettings.objects.first()
    provider = 'gemini'
    api_key = ''
    model = ''

    if settings:
        provider = getattr(settings, 'ai_provider', 'gemini') or 'gemini'
        if provider == 'groq':
            api_key = (getattr(settings, 'groq_api_key', '') or '').strip()
            model = (getattr(settings, 'gemini_model', '') or '').strip()
            if 'gemini' in model:
                model = ''
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
            model = ''

    return provider, api_key, model, settings


def get_gemini_config():
    """Backward compatibility wrapper"""
    provider, api_key, model, settings = get_ai_config()
    return api_key, model, settings


def get_groq_available_models(api_key):
    """
    Fetch all active chat models available on this Groq account from the official Groq models endpoint.
    Filters out audio, whisper, embedding, and moderation models.
    """
    api_key = (api_key or '').strip()
    if not api_key:
        return []

    req = urllib.request.Request(
        GROQ_MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            raw_list = body.get('data', [])

            chat_models = []
            for item in raw_list:
                model_id = item.get('id', '')
                if not model_id:
                    continue
                if item.get('active') is False:
                    continue
                mid_lower = model_id.lower()
                # Skip non-chat models
                if any(skip in mid_lower for skip in ['whisper', 'safeguard', 'guard', 'embedding', 'embed', 'tts', 'moderation']):
                    continue
                chat_models.append(model_id)

            return chat_models
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')[:300]
        raise Exception(f"Groq API Error ({e.code}): {err_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Groq Connection Error: {e.reason}")


def pick_best_groq_model(available_models, preferred=None, exclude=None):
    """
    Pick the optimal chat completion model from available models for this Groq account.
    Prioritizes models with massive token limits (e.g. OpenAI GPT-OSS, Llama 3.3/3.1, Mixtral)
    and avoids models with strict 1000 OTPM limits on free tiers.
    """
    if not available_models:
        return 'llama-3.3-70b-versatile'

    exclude = exclude or []
    candidates = [m for m in available_models if m not in exclude]
    if not candidates:
        candidates = available_models

    if preferred and preferred in candidates:
        return preferred

    # Ranking patterns: High-capacity models first (250k / 12k TPM)
    priority_patterns = [
        'openai/gpt-oss-120b',
        'openai/gpt-oss-20b',
        'gpt-oss-120b',
        'gpt-oss-20b',
        'llama-3.3-70b-versatile',
        'llama-3.1-8b-instant',
        'llama-3.3-70b',
        'llama-3.1-70b',
        'llama-3.1-8b',
        'mixtral-8x7b-32768',
        'gemma2-9b-it',
        'llama3-70b',
        'llama3-8b',
        'llama',
        'gemma',
        'mistral',
        'qwen',
    ]

    for pat in priority_patterns:
        for m in candidates:
            if pat in m.lower():
                return m

    return candidates[0]


def _call_groq_api(api_key, model='', system_prompt="", user_prompt="", timeout=90):
    """Call Groq OpenAI-compatible chat completion endpoint using standard library urllib"""
    api_key = (api_key or '').strip()
    if not api_key:
        raise Exception("Groq API key is missing.")

    # Auto-discover available models if no valid model specified
    if not model or 'gemini' in model:
        try:
            available = get_groq_available_models(api_key)
            model = pick_best_groq_model(available)
        except Exception:
            model = 'llama-3.3-70b-versatile'

    def _execute(target_model, use_json_format=True, max_tokens=None):
        if max_tokens is None:
            # On qwen, Groq enforces a strict 1000 Output Tokens Per Minute (OTPM) limit
            if 'qwen' in target_model.lower():
                max_tokens = 850
            else:
                max_tokens = 2048

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }
        if use_json_format:
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GROQ_API_URL,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            choices = res_json.get('choices') or []
            if not choices:
                raise Exception(f"No choices returned by Groq: {res_body[:200]}")
            return choices[0].get('message', {}).get('content', '')

    try:
        return _execute(model, use_json_format=True)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')[:350]

        # 1. Retry without json_object if model does not support response_format
        if e.code == 400 and 'response_format' in err_body.lower():
            try:
                return _execute(model, use_json_format=False)
            except Exception:
                pass

        # 2. If rate limited (429) - e.g. OTPM 1000 limit on qwen or TPM spike:
        if e.code == 429:
            # Automatically fail over to a higher-capacity model (e.g. gpt-oss or llama)
            try:
                available = get_groq_available_models(api_key)
                alt_model = pick_best_groq_model(available, exclude=[model, 'qwen/qwen3.8-27b'])
                if alt_model and alt_model != model:
                    return _execute(alt_model, use_json_format=True, max_tokens=2048)
            except Exception:
                pass
            # Or retry current model with minimal tokens (700 tokens)
            try:
                return _execute(model, use_json_format=True, max_tokens=700)
            except Exception:
                pass

        # 3. If model is not found or not accessible (404/400), dynamically discover available models and retry
        if e.code in (400, 404) and ('model_not_found' in err_body.lower() or 'does not exist' in err_body.lower()):
            try:
                available = get_groq_available_models(api_key)
                alt_model = pick_best_groq_model(available, exclude=[model])
                if alt_model and alt_model != model:
                    return _execute(alt_model, use_json_format=True)
            except Exception:
                pass

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


def fetch_and_attach_featured_image(content_obj, topic_title: str, category_name: str = "", content_type: str = "blog"):
    """
    Automatically attach a clean, high-resolution, relevant featured image to the Note or Blog post.
    Uses high-quality open educational and technical image sources based on topic keywords and category.
    """
    from django.core.files.base import ContentFile
    import urllib.parse

    title_lower = topic_title.lower()
    cat_lower = (category_name or '').lower()
    combined = f"{title_lower} {cat_lower}"

    # Curated, fast-loading, high-resolution educational and technical imagery
    THEMED_IMAGES = {
        'code': "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&auto=format&fit=crop&q=80",
        'network': "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&auto=format&fit=crop&q=80",
        'computer_operator': "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=1200&auto=format&fit=crop&q=80",
        'study_books': "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=1200&auto=format&fit=crop&q=80",
        'writing_notes': "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1200&auto=format&fit=crop&q=80",
        'general_knowledge': "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=1200&auto=format&fit=crop&q=80",
        'data_analytics': "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&auto=format&fit=crop&q=80",
        'science': "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=1200&auto=format&fit=crop&q=80",
        'education_classroom': "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=1200&auto=format&fit=crop&q=80",
        'default': "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1200&auto=format&fit=crop&q=80"
    }

    if any(k in combined for k in ['code', 'python', 'program', 'html', 'css', 'software', 'developer', 'javascript', 'django', 'react', 'sql']):
        chosen_url = THEMED_IMAGES['code']
    elif any(k in combined for k in ['network', 'cloud', 'cyber', 'security', 'internet', 'server', 'protocol', 'ip address', 'router', 'wifi']):
        chosen_url = THEMED_IMAGES['network']
    elif any(k in combined for k in ['operator', 'computer operator', 'excel', 'word', 'office', 'powerpoint', 'typing', 'hardware', 'ms ']):
        chosen_url = THEMED_IMAGES['computer_operator']
    elif any(k in combined for k in ['grammar', 'nepali', 'literature', 'व्याकरण', 'भाषा', 'साहित्य', 'निबन्ध']):
        chosen_url = THEMED_IMAGES['study_books']
    elif any(k in combined for k in ['teacher', 'tsc', 'pedagogy', 'शिक्षा', 'शिक्षक', 'curriculum', 'teaching']):
        chosen_url = THEMED_IMAGES['education_classroom']
    elif any(k in combined for k in ['data', 'database', 'analysis', 'chart', 'statistics', 'तथ्यांक']):
        chosen_url = THEMED_IMAGES['data_analytics']
    elif any(k in combined for k in ['science', 'physics', 'chemistry', 'biology', 'math', 'गणित', 'विज्ञान']):
        chosen_url = THEMED_IMAGES['science']
    elif any(k in combined for k in ['gk', 'general knowledge', 'samanya gyan', 'world', 'geography', 'history', 'सामान्य ज्ञान']):
        chosen_url = THEMED_IMAGES['general_knowledge']
    elif content_type == 'note':
        chosen_url = THEMED_IMAGES['writing_notes']
    else:
        chosen_url = THEMED_IMAGES['default']

    try:
        req = urllib.request.Request(
            chosen_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                img_data = resp.read()
                prefix = "ai_note" if content_type == 'note' else "ai_blog"
                filename = f"{prefix}_{content_obj.slug[:45]}.jpg"
                content_obj.featured_image.save(filename, ContentFile(img_data), save=True)
                return True
    except Exception:
        # Silently log without failing content generation
        pass
    return False


def resolve_category_for_content(topic: AITopicQueue, data: dict = None, settings: SiteSettings = None) -> Category:
    """
    Intelligently determine and assign the best Category for this topic.
    Fixes the issue where all notes were forced into 'Computer Operator'.
    
    1. If user explicitly chose a Category in the queue:
       - Uses it if module matches ('notes' or 'blog').
       - If module doesn't match, finds or creates a sibling Category in the target module.
    2. If no category was assigned (or auto-detect):
       - Uses keywords from topic title and AI-detected category to route to:
         * नेपाली व्याकरण (Nepali Grammar)
         * सामान्य ज्ञान (General Knowledge)
         * शिक्षक सेवा आयोग (TSC Prep)
         * लोक सेवा आयोग (Loksewa PSC)
         * Information Technology & Programming
         * Computer Operator
         * विज्ञान तथा गणित (Science & Math)
         * शिक्षा तथा शिक्षण विधि (Pedagogy)
    3. Auto-creates the category under the target module if it doesn't already exist.
    """
    target_module = 'notes' if topic.content_type == 'note' else 'blog'
    title = (topic.title or '').strip()
    data = data or {}
    ai_cat = (data.get('category_name') or data.get('category') or '').strip()
    combined_text = f"{title} {ai_cat}".lower()

    # 1. Topic has explicit category assigned
    if topic.category:
        if topic.category.module == target_module:
            return topic.category
        sibling = Category.objects.filter(module=target_module, name__iexact=topic.category.name).first()
        if sibling:
            return sibling
        new_cat, _ = Category.objects.get_or_create(
            name=topic.category.name,
            module=target_module,
            defaults={'slug': f"{slugify(topic.category.name, allow_unicode=True) or 'cat'}-{target_module}"}
        )
        return new_cat

    # 2. Intelligent Keyword & Domain Mapping
    cat_mappings = [
        (
            ['व्याकरण', 'grammar', 'पदवर्ग', 'काल', 'वर्णविन्यास', 'कारक', 'विभक्ति', 'वाच्य', 'निबन्ध', 'शब्दवर्ग', 'नेपाली भाषा'],
            "नेपाली व्याकरण (Nepali Grammar)",
            f"nepali-grammar-{target_module}"
        ),
        (
            ['सामान्य ज्ञान', 'gk', 'samanya gyan', 'भूगोल', 'इतिहास', 'संविधान', 'समसामयिक', 'विश्वको', 'नेपालको भूगोल', 'सार्क'],
            "सामान्य ज्ञान (General Knowledge)",
            f"general-knowledge-{target_module}"
        ),
        (
            ['शिक्षक', 'tsc', 'शिक्षक सेवा', 'प्रावि', 'निमावि', 'मावि', 'शिक्षण सिकाइ', 'शिक्षा ऐन', 'शिक्षक तयारी'],
            "शिक्षक सेवा आयोग (TSC Prep)",
            f"tsc-prep-{target_module}"
        ),
        (
            ['लोक सेवा', 'psc', 'loksewa', 'नायब सुब्बा', 'खरिदार', 'शाखा अधिकृत', 'प्रशासन', 'सेवा आयोग'],
            "लोक सेवा आयोग (Loksewa PSC)",
            f"loksewa-psc-{target_module}"
        ),
        (
            ['python', 'programming', 'code', 'html', 'css', 'javascript', 'django', 'react', 'sql', 'database', 'web development', 'सफ्टवेयर', 'नेटवर्किङ', 'network'],
            "Information Technology & Programming",
            f"it-programming-{target_module}"
        ),
        (
            ['कम्प्युटर अपरेटर', 'computer operator', 'excel', 'word', 'powerpoint', 'typing', 'operator', 'hardware', 'ms office', 'अफिस अटोमेसन', 'कम्प्युटर'],
            "Computer Operator",
            f"computer-operator-{target_module}"
        ),
        (
            ['विज्ञान', 'science', 'physics', 'chemistry', 'biology', 'गणित', 'math', 'प्रविधि'],
            "विज्ञान तथा गणित (Science & Math)",
            f"science-math-{target_module}"
        ),
        (
            ['शिक्षा', 'pedagogy', 'curriculum', 'पाठ्यक्रम', 'बालमनोविज्ञान', 'शैक्षिक', 'शिक्षण विधि'],
            "शिक्षा तथा शिक्षण विधि (Pedagogy)",
            f"pedagogy-education-{target_module}"
        ),
    ]

    for keywords, cat_name, cat_slug in cat_mappings:
        if any(kw in combined_text for kw in keywords):
            cat_obj = Category.objects.filter(module=target_module, name=cat_name).first()
            if not cat_obj:
                cat_obj = Category.objects.filter(module=target_module, slug=cat_slug).first()
            if not cat_obj:
                cat_obj, _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={'name': cat_name, 'module': target_module}
                )
            return cat_obj

    # 3. AI-suggested category name if present
    if ai_cat and len(ai_cat) > 2 and 'default' not in ai_cat.lower() and 'general' not in ai_cat.lower() and 'education & technology' not in ai_cat.lower():
        clean_ai_name = ai_cat.split('/')[0].strip()[:50]
        cat_obj = Category.objects.filter(module=target_module, name__iexact=clean_ai_name).first()
        if not cat_obj:
            cat_obj, _ = Category.objects.get_or_create(
                name=clean_ai_name,
                module=target_module,
                defaults={'slug': f"{slugify(clean_ai_name, allow_unicode=True) or 'cat'}-{target_module}"}
            )
        return cat_obj

    # 4. Settings Default if set and module matches
    if settings:
        if target_module == 'notes' and settings.ai_default_note_category and settings.ai_default_note_category.module == 'notes':
            return settings.ai_default_note_category
        elif target_module == 'blog' and settings.ai_default_blog_category and settings.ai_default_blog_category.module == 'blog':
            return settings.ai_default_blog_category

    # 5. Fallback to General Study Notes / General Blog
    default_name = "General Study Notes" if target_module == 'notes' else "General Blog"
    default_slug = f"general-{target_module}"
    cat_obj, _ = Category.objects.get_or_create(
        module=target_module,
        slug=default_slug,
        defaults={'name': default_name}
    )
    return cat_obj


def generate_content_for_topic(topic: AITopicQueue):
    """
    Generate and save a full Blog Post or Study Note from a queued topic.
    Supports both Groq (Llama 3.3 70B / GPT-OSS) and Google Gemini engines.
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
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
  "category_name": "Suggested accurate category (e.g. Nepali Grammar, General Knowledge, Information Technology, TSC Prep, Computer Operator, Science, Pedagogy)"
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

        # Intelligently assign the accurate Category (Grammar, GK, TSC, IT, Science, Computer Operator, etc.)
        category = resolve_category_for_content(topic, data=data, settings=settings)

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
            # Automatically fetch & attach high-res featured image for Note
            fetch_and_attach_featured_image(obj, article_title, category.name if category else "", content_type="note")

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
            # Automatically fetch & attach high-res featured image for Blog
            fetch_and_attach_featured_image(obj, article_title, category.name if category else "", content_type="blog")

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

Return a valid JSON object with a single key "topics" containing a list of {count} items matching this schema:
{{
  "topics": [
    {{
      "title": "Clear, engaging topic title",
      "content_type": "{content_type}",
      "language": "{language}",
      "category_name": "Technology / Notes / GK / Education",
      "hint": "Brief 1-sentence note on key aspects to cover"
    }}
  ]
}}
Do NOT include markdown fences, just pure JSON.
"""

    if provider == 'groq':
        raw = _call_groq_api(api_key, model, "You are a helpful educational topic brainstormer. Respond strictly in valid JSON.", prompt, timeout=45)
    else:
        url = GEMINI_API_URL.format(model=model or 'gemini-3.8-flash') + f"?key={api_key}"
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
    parsed = json.loads(raw.strip())
    if isinstance(parsed, dict) and 'topics' in parsed:
        return parsed['topics']
    if isinstance(parsed, list):
        return parsed
    return []


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

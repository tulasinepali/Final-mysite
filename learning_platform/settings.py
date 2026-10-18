"""
Django settings for learning_platform project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-&k%7q=c&w%isyo&9_r2+=oasik=b-9v*z+$7962nju3)$d39y3'

import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'tulasinepali.com.np',
    'www.tulasinepali.com.np',
]

CSRF_TRUSTED_ORIGINS = [
    'https://tulasinepali.com.np',
    'https://www.tulasinepali.com.np',
    'http://localhost',
    'http://127.0.0.1',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'django_ckeditor_5',
    'widget_tweaks',
    # Local apps
    'core',
    'notes',
    'downloads',
    'blog',
    'quiz',
    'search',
    'dashboard',
    'tools',
    'csp',
]

MIDDLEWARE = [
    'core.middleware.SecurityHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.MaintenanceModeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.VisitorCountMiddleware',
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = 'learning_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
                'core.context_processors.global_categories',
                'core.context_processors.ad_placements',
                'core.context_processors.dashboard_signals',
            ],
        },
    },
]

WSGI_APPLICATION = 'learning_platform.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

# Ensure SQLite performance and concurrency on cPanel
from django.db.backends.signals import connection_created

def configure_sqlite_performance(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=WAL;')
            cursor.execute('PRAGMA busy_timeout=20000;')
            cursor.execute('PRAGMA synchronous=NORMAL;')

connection_created.connect(configure_sqlite_performance)

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kathmandu'

USE_I18N = True

USE_TZ = True

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = '/rishav/login/'
LOGIN_REDIRECT_URL = '/rishav/'
LOGOUT_REDIRECT_URL = '/rishav/login/'

# Site ID
SITE_ID = 1

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CKEditor 5 Configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'bulletedList', 'numberedList', '|',
            'outdent', 'indent', '|',
            'blockQuote', 'insertTable', 'horizontalLine', '|',
            'link', 'imageUpload', '|',
            'undo', 'redo', '|',
            'sourceEditing',
        ],
        'language': 'en',
        'image': {
            'toolbar': [
                'imageTextAlternative',
                '|', 'imageStyle:alignLeft',
                'imageStyle:alignCenter',
                'imageStyle:alignRight',
            ],
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
            ],
        },
    },
    'notes_toolbar': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', '|',
            'bulletedList', 'numberedList', '|',
            'outdent', 'indent', 'blockQuote', '|',
            'alignment', '|',
            'link', 'imageUpload', 'insertTable', 'horizontalLine', 'specialCharacters', '|',
            'undo', 'redo', '|',
            'sourceEditing',
        ],
        'language': 'en',
        'image': {
            'toolbar': [
                'imageTextAlternative',
                '|', 'imageStyle:alignLeft',
                'imageStyle:alignCenter',
                'imageStyle:alignRight',
            ],
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
            ],
        },
    },
    'blog_toolbar': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', 'code', 'subscript', 'superscript', '|',
            'bulletedList', 'numberedList', '|',
            'outdent', 'indent', 'blockQuote', '|',
            'alignment', '|',
            'link', 'imageUpload', 'insertTable', 'horizontalLine', 'specialCharacters', 'mediaEmbed', '|',
            'codeBlock', '|',
            'undo', 'redo', '|',
            'sourceEditing',
        ],
        'language': 'en',
        'image': {
            'toolbar': [
                'imageTextAlternative',
                '|', 'imageStyle:alignLeft',
                'imageStyle:alignCenter',
                'imageStyle:alignRight',
            ],
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
            ],
        },
    },
}

# CKEditor 5 file upload config
CKEDITOR_5_FILE_UPLOAD_PERMISSION = 'staff'
CKEDITOR_5_CUSTOM_CSS = None



SESSION_COOKIE_AGE = 1800  

# 2. Expire session when the user closes the browser (True/False)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  

# 3. Renew expiration time on every user action/request (Sliding Expiration)
SESSION_SAVE_EVERY_REQUEST = True


SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
REFERRER_POLICY = 'strict-origin-when-cross-origin'

X_FRAME_OPTIONS = "SAMEORIGIN"

# Trust reverse proxy header from cPanel / LiteSpeed / Nginx / Cloudflare
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS — tells browsers to only use HTTPS for 1 year (fixes "No HSTS" flag)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redirect HTTP → HTTPS (handled by server, but Django enforces it too)
SECURE_SSL_REDIRECT = not DEBUG  # Only redirect in production

# CSP Settings (django-csp middleware)
# Allow AdSense, GTM, Google Analytics, Fonts, Bootstrap CDN, Google Translate
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'", "'unsafe-inline'", "'unsafe-eval'",
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            'https://pagead2.googlesyndication.com',
            'https://adservice.google.com',
            'https://www.googletagmanager.com',
            'https://www.googletagservices.com',
            'https://www.google-analytics.com',
            'https://googleads.g.doubleclick.net',
            'https://tpc.googlesyndication.com',
            'https://ep1.adtrafficquality.google',
            'https://ep2.adtrafficquality.google',
            'https://cdn.ampproject.org',
            'https://cdn.onesignal.com',
            'https://www.google.com',
            'https://translate.google.com',
            'https://translate.googleapis.com',
        ),
        'style-src': (
            "'self'", "'unsafe-inline'",
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
            'https://translate.googleapis.com',
            'https://translate.google.com',
            'https://www.gstatic.com',
        ),
        'font-src': (
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            'https://fonts.gstatic.com',
            'data:',
        ),
        'img-src': (
            "'self'", 'data:', 'blob:',
            'https://www.google.com',
            'https://www.gstatic.com',
            'https://pagead2.googlesyndication.com',
            'https://googleads.g.doubleclick.net',
            'https://www.google-analytics.com',
            'https://translate.google.com',
            'https://translate.googleapis.com',
            'https://img.youtube.com',
            'https://i.ytimg.com',
        ),
        'frame-src': (
            "'self'",
            'https://googleads.g.doubleclick.net',
            'https://tpc.googlesyndication.com',
            'https://www.google.com',
            'https://ep2.adtrafficquality.google',
            'https://translate.google.com',
            'https://translate.googleapis.com',
            'https://www.youtube.com',
            'https://www.youtube-nocookie.com',
            'https://youtube.com',
        ),
        'connect-src': (
            "'self'",
            'https://www.google-analytics.com',
            'https://www.googletagmanager.com',
            'https://pagead2.googlesyndication.com',
            'https://ep1.adtrafficquality.google',
            'https://ep2.adtrafficquality.google',
            'https://translate.googleapis.com',
            'https://translate.google.com',
            'https://translate-pa.googleapis.com',
            'https://www.gstatic.com',
        ),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
    }
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'Tulasi Nepali <info@tulasinepali.com.np>'
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
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'tulasinepali.com.np',
        'www.tulasinepali.com.np',
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
    'csp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
    }
}

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
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

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
REFERRER_POLICY = 'strict-origin-when-cross-origin'

X_FRAME_OPTIONS = "DENY"
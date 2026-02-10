"""
Django 基础配置
所有环境共享的配置项
"""

import os
from pathlib import Path

# 项目根目录 (judicial_system/)
BASE_DIR = Path(__file__).resolve().parents[2]


# =============================================================================
# 应用配置
# =============================================================================

INSTALLED_APPS = [
    # SimpleUI 必须在 admin 之前
    "simpleui",
    # Django 核心应用
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方应用
    "rest_framework",
    "django_filters",
    "corsheaders",
    "ckeditor",
    "ckeditor_uploader",
    "import_export",
    # 项目应用
    "apps.common.apps.CommonConfig",
    "apps.users.apps.UsersConfig",
    "apps.grids.apps.GridsConfig",
    "apps.cases.apps.CasesConfig",
    "apps.content.apps.ContentConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 静态文件服务 (必须在 SecurityMiddleware 之后)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.DynamicSimpleUIMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# =============================================================================
# 密码验证
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =============================================================================
# 国际化配置
# =============================================================================

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]


# =============================================================================
# 静态文件和媒体文件
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 导入模板文件目录
IMPORT_TEMPLATES_DIR = BASE_DIR / "static" / "import_templates"


# =============================================================================
# 文件上传配置 (20MB)
# =============================================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024


# =============================================================================
# 其他 Django 配置
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 自定义用户模型
AUTH_USER_MODEL = "users.User"


# =============================================================================
# Django REST Framework 配置
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "utils.authentication.SimpleTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "utils.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "utils.exceptions.custom_exception_handler",
}


# =============================================================================
# Token 配置
# =============================================================================

TOKEN_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": 2 * 60 * 60,  # 2小时（秒）
    "REFRESH_TOKEN_LIFETIME": 7 * 24 * 60 * 60,  # 7天（秒）
}


# =============================================================================
# 缓存配置 (文件缓存，支持多进程共享，用于存储 Token)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "cache",
    }
}


# =============================================================================
# CKEditor 配置
# =============================================================================

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline", "Strike"],
            ["NumberedList", "BulletedList", "-", "Outdent", "Indent"],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink"],
            ["Image", "Table", "HorizontalRule"],
            ["TextColor", "BGColor"],
            ["Smiley", "SpecialChar"],
            ["Source"],
            ["RemoveFormat"],
        ],
        "height": 300,
        "width": "100%",
        "filebrowserUploadUrl": "/ckeditor/upload/",
        "filebrowserImageUploadUrl": "/ckeditor/upload/",
        "filebrowserBrowseUrl": "/ckeditor/browse/",
        "filebrowserImageBrowseUrl": "/ckeditor/browse/",
        "image_previewText": " ",
        "tabSpaces": 4,
        "removePlugins": "elementspath",
    },
}

# 忽略 CKEditor 安全警告
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]


# =============================================================================
# SimpleUI 配置
# =============================================================================

SIMPLEUI_HOME_INFO = False
SIMPLEUI_LOGO = "/static/images/logo.jpg"

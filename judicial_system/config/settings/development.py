import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = "django-insecure-5gzvjhuxw^2!x!zo6ux+skvm**%3cxn2m73^*z#ds_g=l_z)6p"

DEBUG = True

ALLOWED_HOSTS: list[str] = ["*"]

INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "ckeditor",
    "ckeditor_uploader",
    "apps.common.apps.CommonConfig",
    "apps.users.apps.UsersConfig",
    "apps.grids.apps.GridsConfig",
    "apps.cases.apps.CasesConfig",
    "apps.content.apps.ContentConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic 收集目录
STATICFILES_DIRS = [
    BASE_DIR.parent / "admin-html",  # 添加 admin-html 目录到静态文件搜索路径
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 腾讯地图配置（可通过环境变量覆盖）
TENCENT_MAP_KEY = "4H4BZ-OJACL-DKBPM-E7Y5H-5VSK5-KFFKK"

# 文件上传配置（20MB）
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True

# CSRF 信任的源（用于反向代理和 FRP 等场景）
CSRF_TRUSTED_ORIGINS = [
    "https://8001.frp.chatgqt.top",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8000",
]

# 自定义用户模型
AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CKEditor 配置
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",  # 使用自定义工具栏
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline", "Strike"],
            ["NumberedList", "BulletedList", "-", "Outdent", "Indent"],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink"],
            ["Image", "Table", "HorizontalRule"],  # 图片上传按钮
            ["TextColor", "BGColor"],
            ["Smiley", "SpecialChar"],
            ["Source"],
            ["RemoveFormat"],
        ],
        "height": 300,
        "width": "100%",
        # 图片上传配置
        "filebrowserUploadUrl": "/ckeditor/upload/",  # 文件上传 URL
        "filebrowserImageUploadUrl": "/ckeditor/upload/",  # 图片上传 URL
        "filebrowserBrowseUrl": "/ckeditor/browse/",  # 浏览已上传文件
        "filebrowserImageBrowseUrl": "/ckeditor/browse/",  # 浏览已上传图片
        # 允许的图片格式
        "image_previewText": " ",
        "tabSpaces": 4,
        "removePlugins": "elementspath",  # 移除底部元素路径显示
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
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

# 忽略 CKEditor 安全警告
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

# 后端基础 URL（用于生成文件绝对路径，适配反向代理场景）
BACKEND_BASE_URL = "https://8001.frp.chatgqt.top"

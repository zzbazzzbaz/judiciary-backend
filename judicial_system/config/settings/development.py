import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = "django-insecure-5gzvjhuxw^2!x!zo6ux+skvm**%3cxn2m73^*z#ds_g=l_z)6p"

DEBUG = True

ALLOWED_HOSTS: list[str] = []

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
    "apps.common.apps.CommonConfig",
    "apps.users.apps.UsersConfig",
    "apps.grids.apps.GridsConfig",
    "apps.cases.apps.CasesConfig",
    "apps.content.apps.ContentConfig",
    "apps.mytests.apps.MytestsConfig",
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

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 腾讯地图配置（可通过环境变量覆盖）
TENCENT_MAP_KEY = "4H4BZ-OJACL-DKBPM-E7Y5H-5VSK5-KFFKK"

# 文件上传配置（20MB）
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True

# 自定义用户模型
AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
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

# SimpleUI 菜单配置
SIMPLEUI_CONFIG = {
    # 保留系统默认菜单，并追加自定义菜单
    "system_keep": True,
    "menus": [
        {
            "name": "网格管理",
            "icon": "fas fa-th-large",
            "models": [
                {"name": "统计", "icon": "fas fa-chart-bar", "url": "grids/statistics/"},
                {"name": "网格", "icon": "fas fa-border-all", "url": "grids/grid/"},
                {"name": "任务", "icon": "fas fa-tasks", "url": "cases/task/"},
            ],
        }, {
            "name": "成员管理",
            "icon": "fas fa-th-large",
            "models": [
                {"name": "成员", "icon": "fas fa-chart-bar", "url": "users/user"},
                {"name": "培训记录", "icon": "fas fa-chart-bar", "url": "users/trainingrecord/"},
                {"name": "绩效", "icon": "fas fa-chart-bar", "url": "users/performancescore/"},
            ]
        }, {
            "name": "法治宣传教育",
            "icon": "fas fa-th-large",
            "models": [
                {"name": "文章分类", "icon": "fas fa-chart-bar", "url": "content/category/"},
                {"name": "文章列表", "icon": "fas fa-chart-bar", "url": "content/article/"},
                {"name": "活动列表", "icon": "fas fa-chart-bar", "url": "content/activity/"},
            ]
        }, {
            "name": "文档管理",
            "icon": "fas fa-th-large",
            "models": [
                {"name": "文档", "icon": "fas fa-chart-bar", "url": "content/document/"},
            ]
        }, {
            "name": "机构管理",
            "icon": "fas fa-th-large",
            "models": [
                {"name": "机构", "icon": "fas fa-chart-bar", "url": "users/organization/"},
            ]
        }
    ],
}

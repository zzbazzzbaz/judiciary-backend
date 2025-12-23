import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key")

DEBUG = False

ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host]

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
    "import_export",
    "apps.common.apps.CommonConfig",
    "apps.users.apps.UsersConfig",
    "apps.grids.apps.GridsConfig",
    "apps.cases.apps.CasesConfig",
    "apps.content.apps.ContentConfig",
]

try:
    import ckeditor  # noqa: F401
except ModuleNotFoundError:
    pass
else:
    INSTALLED_APPS.append("ckeditor")
    INSTALLED_APPS.append("ckeditor_uploader")

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
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 导入模板文件目录
IMPORT_TEMPLATES_DIR = BASE_DIR / "static" / "import_templates"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    origin for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin
]

# 腾讯地图配置
TENCENT_MAP_KEY = os.getenv("TENCENT_MAP_KEY", "")

# 文件上传配置（20MB）
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

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

# 忽略 CKEditor 安全警告
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

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

# SimpleUI 配置：隐藏主页版本信息卡片
SIMPLEUI_HOME_INFO = False

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
        }
    ],
}

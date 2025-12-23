"""
Django 生产环境配置
所有敏感配置通过环境变量获取
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# 安全配置 (生产环境 - 从环境变量读取)
# =============================================================================

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-secret-key-please-change")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# 从环境变量解析允许的主机列表
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]


# =============================================================================
# 数据库配置 (支持 SQLite 和 PostgreSQL/MySQL)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}


# =============================================================================
# CORS 配置 (生产环境 - 指定允许的来源)
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# 如果没有配置 CORS_ALLOWED_ORIGINS，则禁用 CORS
CORS_ALLOW_ALL_ORIGINS = False


# =============================================================================
# CSRF 信任的源 (生产环境)
# =============================================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]


# =============================================================================
# JWT 配置 (生产环境)
# =============================================================================

SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY


# =============================================================================
# 腾讯地图配置
# =============================================================================

TENCENT_MAP_KEY = os.environ.get("TENCENT_MAP_KEY", "")


# =============================================================================
# 后端基础 URL
# =============================================================================

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")


# =============================================================================
# 静态文件配置 (WhiteNoise)
# =============================================================================

# WhiteNoise 压缩和缓存配置
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# =============================================================================
# 安全相关配置 (生产环境强化)
# =============================================================================

# HTTPS 相关
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() == "true"

# Cookie 安全
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 日志配置
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

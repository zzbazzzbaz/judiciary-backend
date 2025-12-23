# =============================================================================
# Django 生产环境 Dockerfile
# 包含 Django Admin 和 API 服务
# =============================================================================

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (快速的 Python 包管理器)
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖
RUN uv pip install --system -r pyproject.toml

# 复制项目代码
COPY judicial_system ./judicial_system

# 设置工作目录为 Django 项目目录
WORKDIR /app/judicial_system

# 收集静态文件 (Django Admin + SimpleUI 等)
# 设置临时环境变量以通过配置检查
RUN DJANGO_SECRET_KEY=build-time-secret \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# 创建 media 目录
RUN mkdir -p /app/judicial_system/media

# 创建非 root 用户运行应用
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# 启动命令 - 使用 gunicorn 作为生产服务器
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

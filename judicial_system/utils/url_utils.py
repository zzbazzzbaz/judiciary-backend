"""
URL 工具函数

用于生成文件的绝对路径，适配反向代理场景。
"""

from django.conf import settings


def get_absolute_url(relative_url: str) -> str:
    """
    将相对路径转换为绝对路径。

    使用 settings.BACKEND_BASE_URL 配置的域名，而不是从 request 自动获取，
    以适配反向代理场景。

    Args:
        relative_url: 相对路径，如 /media/attachments/2024/12/file.pdf

    Returns:
        绝对路径，如 https://example.com/media/attachments/2024/12/file.pdf
    """
    if not relative_url:
        return ""

    # 已经是绝对路径则直接返回
    if relative_url.startswith(("http://", "https://")):
        return relative_url

    base_url = getattr(settings, "BACKEND_BASE_URL", "").rstrip("/")
    if not base_url:
        return relative_url

    # 确保相对路径以 / 开头
    if not relative_url.startswith("/"):
        relative_url = "/" + relative_url

    return base_url + relative_url

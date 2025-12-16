"""Content 子应用工具函数。"""

from __future__ import annotations

from utils.attachment_utils import get_attachments_by_ids


def get_article_attachments(article):
    """获取文章附件列表（解析 file_ids）。"""

    return get_attachments_by_ids(getattr(article, "file_ids", "") or "")


def format_article_for_list(article):
    """格式化文章列表（不包含完整 content）。"""

    return {
        "id": article.id,
        "title": article.title,
        "category_name": article.category.name if getattr(article, "category", None) else None,
        "cover_image": article.cover_image,
        "published_at": article.published_at,
    }


def format_article_for_detail(article):
    """格式化文章详情（包含 content 和附件）。"""

    return {
        "id": article.id,
        "title": article.title,
        "category_name": article.category.name if getattr(article, "category", None) else None,
        "content": article.content,
        "cover_image": article.cover_image,
        "video": article.video,
        "files": get_article_attachments(article),
        "published_at": article.published_at,
    }

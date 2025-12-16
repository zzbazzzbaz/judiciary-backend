"""
文件处理工具

用于 common/upload 接口的文件校验与路径生成。
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Iterable


# 允许上传的文件格式（白名单）
ALLOWED_EXTENSIONS: dict[str, list[str]] = {
    "document": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"],
    "image": ["jpg", "jpeg", "png", "gif", "webp"],
}

# 文件大小限制（字节）
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写，不含点），如：'a.JPG' -> 'jpg'。"""

    _, ext = os.path.splitext(filename or "")
    return ext.lstrip(".").lower()


def get_file_type(extension: str) -> str:
    """根据扩展名判断文件类型（image/document）。"""

    extension = (extension or "").lower()
    if extension in ALLOWED_EXTENSIONS["image"]:
        return "image"
    return "document"


def validate_file_extension(extension: str, allowed_types: Iterable[str] | None = None) -> bool:
    """验证文件扩展名是否允许。"""

    extension = (extension or "").lower()
    if not extension:
        return False

    types = list(allowed_types) if allowed_types else list(ALLOWED_EXTENSIONS.keys())
    allowed: set[str] = set()
    for t in types:
        allowed.update(ALLOWED_EXTENSIONS.get(t, []))

    return extension in allowed


def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE) -> bool:
    """验证文件大小是否在限制内。"""

    if file_size is None:
        return False
    return 0 <= int(file_size) <= int(max_size)


def generate_upload_path(filename: str) -> str:
    """
    生成上传路径: attachments/年/月/随机文件名.扩展名

    说明：
    - 返回相对 MEDIA_ROOT 的路径，适用于 Django 默认存储 `default_storage.save()`。
    """

    extension = get_file_extension(filename)
    now = datetime.now()
    random_name = uuid.uuid4().hex
    # 若没有扩展名仍允许保存（但一般会被白名单校验拦截）
    suffix = f".{extension}" if extension else ""
    return f"attachments/{now:%Y}/{now:%m}/{random_name}{suffix}"


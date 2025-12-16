"""
附件关联工具

项目采用「逗号分隔 ID 列表」的方式在业务表中关联附件表（common_attachment）。
"""

from __future__ import annotations

from apps.common.models import Attachment


def parse_attachment_ids(ids_str: str) -> list[int]:
    """
    解析附件ID字符串为列表。

    输入: "1,2,3"
    输出: [1, 2, 3]
    """

    if not ids_str:
        return []
    return [int(_id) for _id in ids_str.split(",") if _id.strip().isdigit()]


def format_attachment_ids(ids_list: list[int]) -> str:
    """
    格式化附件ID列表为字符串。

    输入: [1, 2, 3]
    输出: "1,2,3"
    """

    return ",".join(str(_id) for _id in ids_list)


def get_attachments_by_ids(ids_str: str) -> list[dict]:
    """根据ID字符串获取附件详情列表。"""

    ids = parse_attachment_ids(ids_str)
    if not ids:
        return []

    attachments = Attachment.objects.filter(id__in=ids)
    return [
        {
            "id": att.id,
            "file": att.file.url if att.file else "",
            "file_type": att.file_type,
            "file_size": att.file_size,
            "original_name": att.original_name,
        }
        for att in attachments
    ]


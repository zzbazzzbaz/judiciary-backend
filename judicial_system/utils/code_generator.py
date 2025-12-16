"""
编号生成工具

用于 cases.Task 的任务编号生成：
- 纠纷: JFYYYYMMDD0001
- 援助: YZYYYYMMDD0001
"""

from __future__ import annotations

from django.db.models import Max
from django.utils import timezone


def generate_task_code(task_type: str) -> str:
    """
    生成任务编号：类型前缀 + 年月日 + 4位序号。

    注意：
    - prefix: dispute -> JF，legal_aid -> YZ
    - 并发场景下仍建议由调用方配合事务/重试，最终以唯一约束为准。
    """

    from apps.cases.models import Task

    if task_type == Task.Type.DISPUTE:
        prefix = "JF"
    elif task_type == Task.Type.LEGAL_AID:
        prefix = "YZ"
    else:
        raise ValueError("task_type 不正确")

    today = timezone.now().strftime("%Y%m%d")
    today_prefix = f"{prefix}{today}"

    result = Task.objects.filter(code__startswith=today_prefix).aggregate(max_code=Max("code"))
    max_code = result.get("max_code")

    if max_code:
        last_seq = int(max_code[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{today_prefix}{new_seq:04d}"


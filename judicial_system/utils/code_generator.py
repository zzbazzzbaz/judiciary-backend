"""
编号生成工具

用于 cases.Task 的任务编号生成：
- 纠纷: JFYYYYMMDD0001
- 援助: YZYYYYMMDD0001
"""

from __future__ import annotations

from django.db.models import Max
from django.utils import timezone


# 任务类型名称关键字 -> 编号前缀
_NAME_PREFIX_MAP = {
    "纠纷": "JF",
    "法律援助": "YZ",
}

_DEFAULT_PREFIX = "RW"  # 默认前缀（任务）


def generate_task_code(task_type_id: int) -> str:
    """
    生成任务编号：类型前缀 + 年月日 + 4位序号。

    参数：
        task_type_id: TaskType 的主键 ID。

    注意：
    - 并发场景下仍建议由调用方配合事务/重试，最终以唯一约束为准。
    """

    from apps.cases.models import Task, TaskType

    # 根据任务类型名称确定编号前缀
    prefix = _DEFAULT_PREFIX
    task_type = TaskType.objects.filter(id=task_type_id).first()
    if task_type:
        for keyword, p in _NAME_PREFIX_MAP.items():
            if keyword in task_type.name:
                prefix = p
                break

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


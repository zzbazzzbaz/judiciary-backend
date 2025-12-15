"""
Cases 模块模型

模块说明：
- 案件管理：纠纷上报 / 法律援助申请、任务分派、调解结果等。
"""

from django.db import models


class Task(models.Model):
    """任务表（cases_task）。"""

    class Type(models.TextChoices):
        """任务类型（dispute/legal_aid）。"""

        DISPUTE = "dispute", "Dispute"
        LEGAL_AID = "legal_aid", "Legal Aid"

    class Status(models.TextChoices):
        """状态（reported/assigned/processing/completed）。"""

        REPORTED = "reported", "Reported"
        ASSIGNED = "assigned", "Assigned"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"

    class HandleMethod(models.TextChoices):
        """处理方式（onsite/online）。"""

        ONSITE = "onsite", "Onsite"
        ONLINE = "online", "Online"

    class Result(models.TextChoices):
        """调解结果（success/failure/partial）。"""

        SUCCESS = "success", "Success"
        FAILURE = "failure", "Failure"
        PARTIAL = "partial", "Partial"

    # 基本信息
    code = models.CharField(max_length=30, unique=True)  # 任务编号（唯一，自动生成）
    type = models.CharField(max_length=20, choices=Type.choices)  # 任务类型
    status = models.CharField(  # 状态
        max_length=20,
        choices=Status.choices,
        default=Status.REPORTED,
    )

    description = models.TextField()  # 任务描述
    amount = models.DecimalField(  # 涉及金额
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    grid = models.ForeignKey(
        "grids.Grid",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )  # 所属网格

    # 当事人信息
    party_name = models.CharField(max_length=50)  # 当事人姓名
    party_phone = models.CharField(max_length=20, null=True, blank=True)  # 当事人电话
    party_address = models.CharField(max_length=255, null=True, blank=True)  # 当事人住址

    # 上报阶段
    reporter = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="reported_tasks",
    )  # 上报人
    reported_at = models.DateTimeField(auto_now_add=True)  # 上报时间
    report_lng = models.DecimalField(  # 上报经度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    report_lat = models.DecimalField(  # 上报纬度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    report_address = models.CharField(max_length=255, null=True, blank=True)  # 上报地址
    report_image_ids = models.CharField(  # 上报图片ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )
    report_file_ids = models.CharField(  # 上报文件ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )

    # 分配阶段
    assigner = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )  # 分配人
    assigned_mediator = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks_to_handle",
    )  # 被分配调解员
    assigned_at = models.DateTimeField(null=True, blank=True)  # 分配时间

    # 进行中阶段
    process_submitted_at = models.DateTimeField(null=True, blank=True)
    participants = models.CharField(max_length=500, null=True, blank=True)  # 参与人员列表
    handle_method = models.CharField(
        max_length=20,
        choices=HandleMethod.choices,
        null=True,
        blank=True,
    )
    expected_plan = models.TextField(null=True, blank=True)  # 预计调解方案

    # 已完成阶段
    result = models.CharField(max_length=20, choices=Result.choices, null=True, blank=True)
    result_detail = models.TextField(null=True, blank=True)  # 调解结果详情
    process_description = models.TextField(null=True, blank=True)  # 调解过程描述
    completed_at = models.DateTimeField(null=True, blank=True)  # 完成时间
    complete_lng = models.DecimalField(  # 完成经度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    complete_lat = models.DecimalField(  # 完成纬度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    complete_address = models.CharField(max_length=255, null=True, blank=True)  # 完成地址
    complete_image_ids = models.CharField(  # 完成图片ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )
    complete_file_ids = models.CharField(  # 完成文件ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cases_task"

    def __str__(self) -> str:  # pragma: no cover
        return self.code

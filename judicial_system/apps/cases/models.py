"""
Cases 模块模型

模块说明：
- 案件管理：纠纷上报 / 法律援助申请、任务分派、调解结果等。
"""

from django.db import models


class TaskType(models.Model):
    """任务类型表（cases_task_type）。"""

    name = models.CharField("类型名称", max_length=50, unique=True)
    description = models.TextField("描述", blank=True, default="")
    is_active = models.BooleanField("是否启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "cases_task_type"
        verbose_name = "任务类型"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class Town(models.Model):
    """所属镇表（cases_town）。"""

    name = models.CharField("镇名称", max_length=100, unique=True)
    description = models.TextField("描述", blank=True, default="")
    is_active = models.BooleanField("是否启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "cases_town"
        verbose_name = "所属镇"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    """任务表（cases_task）。"""

    class Status(models.TextChoices):
        """状态（reported/assigned/processing/completed/archived）。"""

        REPORTED = "reported", "已上报"
        ASSIGNED = "assigned", "已分配"
        PROCESSING = "processing", "进行中"
        COMPLETED = "completed", "已完成"
        ARCHIVED = "archived", "已归档"

    class HandleMethod(models.TextChoices):
        """处理方式（onsite/online）。"""

        ONSITE = "onsite", "到达现场"
        ONLINE = "online", "线上沟通"

    class Result(models.TextChoices):
        """调解结果（success/failure/partial）。"""

        SUCCESS = "success", "成功"
        FAILURE = "failure", "失败"
        PARTIAL = "partial", "部分成功"

    # 基本信息
    code = models.CharField("任务编号", max_length=30, unique=True)
    task_type = models.ForeignKey(
        TaskType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
        verbose_name="任务类型",
    )
    town = models.ForeignKey(
        Town,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
        verbose_name="所属镇",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.REPORTED,
    )

    description = models.TextField("任务描述")
    amount = models.DecimalField(
        "涉及金额",
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
        verbose_name="所属网格",
    )

    # 当事人信息
    party_name = models.CharField("当事人姓名", max_length=50)
    party_phone = models.CharField("当事人电话", max_length=20, null=True, blank=True)
    party_address = models.CharField("当事人住址", max_length=255, null=True, blank=True)

    # 上报阶段
    reporter = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="reported_tasks",
        verbose_name="上报人",
    )
    reported_at = models.DateTimeField("上报时间", auto_now_add=True)
    report_lng = models.DecimalField(
        "上报经度",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    report_lat = models.DecimalField(
        "上报纬度",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    report_address = models.CharField("上报地址", max_length=255, null=True, blank=True)
    report_image_ids = models.CharField(
        "上报图片ID",
        max_length=500,
        blank=True,
        default="",
    )
    report_file_ids = models.CharField(
        "上报文件ID",
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
        verbose_name="分配人",
    )
    assigned_mediator = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks_to_handle",
        verbose_name="被分配调解员",
    )
    assigned_at = models.DateTimeField("分配时间", null=True, blank=True)

    # 进行中阶段
    process_submitted_at = models.DateTimeField("进行中提交时间", null=True, blank=True)
    participants = models.CharField("参与人员", max_length=500, null=True, blank=True)
    handle_method = models.CharField(
        "处理方式",
        max_length=20,
        choices=HandleMethod.choices,
        null=True,
        blank=True,
    )
    expected_plan = models.TextField("预计调解方案", null=True, blank=True)

    # 已完成阶段
    result = models.CharField("调解结果", max_length=20, choices=Result.choices, null=True, blank=True)
    result_detail = models.TextField("结果详情", null=True, blank=True)
    process_description = models.TextField("调解过程描述", null=True, blank=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    complete_lng = models.DecimalField(
        "完成经度",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    complete_lat = models.DecimalField(
        "完成纬度",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    complete_address = models.CharField("完成地址", max_length=255, null=True, blank=True)
    complete_image_ids = models.CharField(
        "完成图片ID",
        max_length=500,
        blank=True,
        default="",
    )
    complete_file_ids = models.CharField(
        "完成文件ID",
        max_length=500,
        blank=True,
        default="",
    )

    # 时间戳
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "cases_task"
        verbose_name = "任务"
        verbose_name_plural = verbose_name
        ordering = ["-reported_at", "-id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class UnassignedTask(Task):
    """未分配任务代理模型（用于网格管理员端未分配任务列表）。"""

    class Meta:
        proxy = True
        verbose_name = "待分配任务"
        verbose_name_plural = verbose_name


class ArchivedTask(Task):
    """已归档任务代理模型（用于归档管理）。"""

    class Meta:
        proxy = True
        verbose_name = "任务归档"
        verbose_name_plural = verbose_name


class TaskStatReport(Task):
    """统计报表代理模型（用于管理员端按月统计报表）。"""

    class Meta:
        proxy = True
        verbose_name = "统计报表"
        verbose_name_plural = verbose_name


class CaseArchive(models.Model):
    """案件归档表（cases_case_archive）。"""

    serial_number = models.CharField("序号", max_length=50, blank=True, default="")
    applicant = models.CharField("申请人", max_length=100)
    respondent = models.CharField("被申请人", max_length=100)
    case_reason = models.TextField("案由")
    acceptance_time = models.DateField("受理时间")
    handler = models.CharField("承办人员", max_length=100)
    applicable_procedure = models.TextField("适用程序")
    closure_time = models.DateField("结案时间")
    closure_method = models.TextField("结案方式")
    case_number = models.TextField("案号")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "cases_case_archive"
        verbose_name = "案件归档"
        verbose_name_plural = verbose_name
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.case_number} - {self.applicant}"


class CaseArchiveFile(models.Model):
    """案件归档附件表（cases_case_archive_file）。"""

    archive = models.ForeignKey(
        CaseArchive,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="所属归档案件",
    )
    file = models.FileField("文件", upload_to="case_archive/%Y/%m/")
    original_name = models.CharField("原始文件名", max_length=255, blank=True, default="")
    file_size = models.BigIntegerField("文件大小(字节)", default=0)
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        db_table = "cases_case_archive_file"
        verbose_name = "归档附件"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self) -> str:
        return ""

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = self.file.name
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, AttributeError):
                pass
        super().save(*args, **kwargs)

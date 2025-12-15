"""
Users 模块模型

模块说明：
- 用户与人员模块：用户认证、人员管理、机构管理、绩效管理。
"""

from django.db import models


class Organization(models.Model):
    """机构表（users_organization）。"""

    name = models.CharField(max_length=100)  # 机构名称
    type = models.CharField(max_length=50, null=True, blank=True)  # 机构类型
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )  # 上级机构（自关联）
    description = models.TextField(null=True, blank=True)  # 职能介绍
    contact = models.CharField(max_length=50, null=True, blank=True)  # 联系方式
    address = models.CharField(max_length=255, null=True, blank=True)  # 地址
    sort_order = models.IntegerField(default=0)  # 排序
    is_active = models.BooleanField(default=True)  # 是否启用
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    class Meta:
        db_table = "users_organization"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class User(models.Model):
    """用户/人员表（users_user）。

注意：
- 当前为业务用户表，未接入 Django 内置认证体系（AUTH_USER_MODEL 未替换）。
"""

    class Gender(models.TextChoices):
        """性别（male/female）。"""

        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class Role(models.TextChoices):
        """身份角色（admin/grid_manager/mediator）。"""

        ADMIN = "admin", "Admin"
        GRID_MANAGER = "grid_manager", "Grid Manager"
        MEDIATOR = "mediator", "Mediator"

    username = models.CharField(max_length=50, unique=True)  # 用户名（登录账号，唯一）
    password = models.CharField(max_length=128)  # 密码（加密存储）
    name = models.CharField(max_length=50)  # 姓名
    gender = models.CharField(  # 性别
        max_length=10,
        choices=Gender.choices,
        null=True,
        blank=True,
    )
    id_card = models.CharField(max_length=18, null=True, blank=True)  # 身份证号
    phone = models.CharField(max_length=20, null=True, blank=True)  # 联系电话
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )  # 所属机构
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEDIATOR)  # 身份角色
    is_active = models.BooleanField(default=True)  # 是否启用
    last_login = models.DateTimeField(null=True, blank=True)  # 最后登录时间
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    class Meta:
        db_table = "users_user"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.username}({self.name})"


class TrainingRecord(models.Model):
    """培训记录表（users_training_record）。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="training_records")  # 用户ID
    name = models.CharField(max_length=100)  # 培训名称
    content = models.TextField(null=True, blank=True)  # 培训内容
    training_time = models.DateField(null=True, blank=True)  # 培训时间
    file_ids = models.CharField(  # 证书附件ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    class Meta:
        db_table = "users_training_record"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:{self.name}"


class PerformanceScore(models.Model):
    """绩效打分表（users_performance_score）。"""

    mediator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="performance_scores_received",
    )  # 调解员
    scorer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="performance_scores_given",
    )  # 打分人
    score = models.IntegerField()  # 分数（0-100）
    period = models.CharField(max_length=20)  # 考核周期（如：2024-01）
    comment = models.TextField(null=True, blank=True)  # 评语
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间

    class Meta:
        db_table = "users_performance_score"
        constraints = [
            models.UniqueConstraint(
                fields=["mediator", "period"], name="uniq_users_score_mediator_period"
            )
        ]

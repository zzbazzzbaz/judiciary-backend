"""
Users 模块模型

模块说明：
- 用户与人员模块：用户认证、人员管理、机构管理、绩效管理。
"""

from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models



class Organization(models.Model):
    """机构表（users_organization）。"""

    name = models.CharField("机构名称", max_length=100)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name="上级机构",
    )  # 上级机构（自关联）
    description = models.TextField("职能介绍", null=True, blank=True)
    contact = models.CharField("联系方式", max_length=50, null=True, blank=True)
    address = models.CharField("地址", max_length=255, null=True, blank=True)
    tag = models.TextField("标签", null=True, blank=True)
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "users_organization"
        verbose_name = "机构"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class UserManager(BaseUserManager):
    """用户管理器。

    说明：
    - 该项目使用自定义用户模型（AUTH_USER_MODEL = 'users.User'）。
    - 通过 `set_password()` 统一加密存储密码。
    """

    def create_user(self, username: str, password: str | None = None, **extra_fields):
        if not username:
            raise ValueError("username 不能为空")

        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, password: str | None = None, **extra_fields):
        """
        创建超级用户（用于 Django 管理后台）。

        说明：本系统以 role=admin 作为管理员身份标识。
        """

        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_active", True)
        return self.create_user(username=username, password=password, **extra_fields)


class User(AbstractBaseUser):
    """用户/人员表（users_user）。

注意：
    - 继承 AbstractBaseUser 以接入 Django/DRF 认证体系（JWT）。
    - 本项目使用 `role` 字段做业务权限控制（admin/grid_manager/mediator）。
"""

    class Gender(models.TextChoices):
        """性别（male/female）。"""

        MALE = "male", "男"
        FEMALE = "female", "女"

    class Role(models.TextChoices):
        """身份角色（admin/grid_manager/mediator）。"""

        ADMIN = "admin", "管理员"
        GRID_MANAGER = "grid_manager", "网格负责人"
        MEDIATOR = "mediator", "调解员"

    username = models.CharField("用户名", max_length=50, unique=True)
    name = models.CharField("姓名", max_length=50)
    gender = models.CharField(  # 性别
        "性别",
        max_length=10,
        choices=Gender.choices,
        null=True,
        blank=True,
    )
    id_card = models.CharField("身份证号", max_length=18, null=True, blank=True)
    phone = models.CharField("联系电话", max_length=20, null=True, blank=True)
    avatar = models.ImageField("头像", upload_to="users/avatars/%Y/%m/", null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        verbose_name="所属机构",
    )  # 所属机构
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.MEDIATOR)
    grid = models.ForeignKey(
        "grids.Grid",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
        verbose_name="所属网格",
    )
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users_user"
        verbose_name = "人员"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.username} - {self.get_role_display()})"

    @property
    def is_staff(self) -> bool:
        """Django admin 需要的 is_staff 属性"""
        return True

    @property
    def is_superuser(self) -> bool:
        """Django admin 需要的 is_superuser 属性"""
        return True

    def has_perm(self, perm, obj=None) -> bool:
        """Django admin 需要的权限接口"""
        return True

    def has_module_perms(self, app_label) -> bool:
        """Django admin 需要的模块权限接口"""
        return True

class TrainingRecord(models.Model):
    """培训记录表（users_training_record）。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="training_records",
        verbose_name="人员",
    )
    name = models.CharField("培训名称", max_length=100)
    content = models.TextField("培训内容", null=True, blank=True)
    training_time = models.DateField("培训时间", null=True, blank=True)
    files = models.ManyToManyField(
        "UserAttachment",
        blank=True,
        related_name="training_records",
        verbose_name="证书附件",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "users_training_record"
        verbose_name = "培训记录"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user_id}:{self.name}"


class PerformanceScore(models.Model):
    """绩效打分表（users_performance_score）。"""

    mediator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="performance_scores_received",
        verbose_name="调解员",
    )  # 调解员
    scorer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="performance_scores_given",
        verbose_name="打分人",
    )  # 打分人
    score = models.IntegerField("分数")  # 0-100
    period = models.CharField("考核周期", max_length=20, help_text="格式：YYYY-MM")  # 如：2024-01
    comment = models.TextField("评语", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "users_performance_score"
        verbose_name = "绩效打分"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["mediator", "period"], name="uniq_users_score_mediator_period"
            )
        ]


class UserAttachment(models.Model):
    """附件表（users_attachment）。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attachments", verbose_name="用户")
    file = models.FileField("文件", max_length=255, upload_to="users/%Y/%m/")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "users_attachment"
        verbose_name = "附件"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file.name.split("/")[-1]


class PerformanceHistory(PerformanceScore):
    """历史绩效代理模型（用于网格管理员端只读展示）。"""

    class Meta:
        proxy = True
        verbose_name = "历史绩效"
        verbose_name_plural = verbose_name

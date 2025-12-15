"""
Grids 模块模型

模块说明：
- 网格管理：网格信息、边界管理、调解员分配。
"""

from django.db import models


class Grid(models.Model):
    """网格表（grids_grid）。"""

    name = models.CharField(max_length=100)  # 网格名称
    region = models.CharField(max_length=100, null=True, blank=True)  # 所属区域
    boundary = models.JSONField(null=True, blank=True)  # 边界坐标（[[lng, lat], ...]）
    center_lng = models.DecimalField(  # 中心点经度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    center_lat = models.DecimalField(  # 中心点纬度
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    current_manager = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_grids",
    )  # 当前负责人（网格负责人）
    description = models.TextField(null=True, blank=True)  # 网格描述
    is_active = models.BooleanField(default=True)  # 是否启用
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    class Meta:
        db_table = "grids_grid"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class MediatorAssignment(models.Model):
    """网格调解员分配表（grids_mediator_assignment）。"""

    grid = models.ForeignKey(  # 网格ID
        Grid,
        on_delete=models.CASCADE,
        related_name="mediator_assignments",
    )
    mediator = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="grid_assignments",
    )  # 调解员ID
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间

    class Meta:
        db_table = "grids_mediator_assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["grid", "mediator"], name="uniq_grids_assignment_grid_mediator"
            )
        ]

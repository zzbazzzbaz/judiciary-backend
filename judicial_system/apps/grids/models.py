"""
Grids 模块模型

模块说明：
- 网格管理：网格信息、边界管理、调解员分配。
"""

from django.db import models


class Grid(models.Model):
    """网格表（grids_grid）。"""

    name = models.CharField("网格名称", max_length=100)
    region = models.CharField("所属区域", max_length=100, null=True, blank=True)
    boundary = models.JSONField("边界坐标", null=True, blank=True, help_text="[[lng, lat], ...]")
    center_lng = models.DecimalField(
        "中心点经度",
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )
    center_lat = models.DecimalField(
        "中心点纬度",
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
        verbose_name="当前负责人",
    )
    description = models.TextField("网格描述", null=True, blank=True)
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "grids_grid"
        verbose_name = "网格"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:  # pragma: no cover
        return self.name



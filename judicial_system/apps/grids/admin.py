"""Grids 子应用 Admin 配置。"""

from __future__ import annotations

from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.forms import Textarea

from config.admin_sites import admin_site, grid_manager_site

from .models import Grid


class GridAdmin(admin.ModelAdmin):
    """网格管理（网格信息、边界、负责人、调解员分配）。"""

    list_display = ("id", "name", "region", "current_manager", "mediator_count", "is_active", "created_at")
    search_fields = ("name", "region")
    list_filter = ("is_active", "region")
    ordering = ("-id",)

    readonly_fields = ("current_manager", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("name", "region", "description", "is_active")}),
        ("边界与中心点", {"fields": ("boundary", ("center_lng", "center_lat"))}),
        ("负责人", {"fields": ("current_manager",)}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    formfield_overrides = {
        models.JSONField: {
            "widget": Textarea(attrs={"rows": 6, "style": "font-family: ui-monospace, SFMono-Regular, Menlo;"}),
        }
    }

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_mediator_count=Count("members", distinct=True))

    @admin.display(description="调解员数量", ordering="_mediator_count")
    def mediator_count(self, obj: Grid) -> int:
        return getattr(obj, "_mediator_count", 0)

# 注册到管理员后台
admin_site.register(Grid, GridAdmin)

# 注册到网格负责人后台
grid_manager_site.register(Grid, GridAdmin)

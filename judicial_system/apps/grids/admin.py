"""Grids 子应用 Admin 配置。"""

from __future__ import annotations

from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.forms import Textarea

from apps.users.models import User

from .models import Grid, MediatorAssignment


class MediatorAssignmentInline(admin.TabularInline):
    """在网格详情页内进行调解员分配。"""

    model = MediatorAssignment
    extra = 0
    autocomplete_fields = ("mediator",)
    fields = ("mediator", "created_at")
    readonly_fields = ("created_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mediator":
            kwargs["queryset"] = User.objects.filter(role=User.Role.MEDIATOR, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Grid)
class GridAdmin(admin.ModelAdmin):
    """网格管理（网格信息、边界、负责人、调解员分配）。"""

    list_display = ("id", "name", "region", "current_manager", "mediator_count", "is_active", "created_at")
    search_fields = ("name", "region")
    list_filter = ("is_active", "region")
    ordering = ("-id",)

    autocomplete_fields = ("current_manager",)
    inlines = (MediatorAssignmentInline,)

    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("name", "region", "description", "is_active")}),
        ("边界与中心点", {"fields": ("boundary", ("center_lng", "center_lat"))}),
        ("负责人指派", {"fields": ("current_manager",)}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    formfield_overrides = {
        models.JSONField: {
            "widget": Textarea(attrs={"rows": 6, "style": "font-family: ui-monospace, SFMono-Regular, Menlo;"}),
        }
    }

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_mediator_count=Count("mediator_assignments", distinct=True))

    @admin.display(description="调解员数量", ordering="_mediator_count")
    def mediator_count(self, obj: Grid) -> int:
        return getattr(obj, "_mediator_count", 0)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "current_manager":
            kwargs["queryset"] = User.objects.filter(role=User.Role.GRID_MANAGER, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

"""Grids 子应用 Admin 配置。"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count
from django.db.utils import OperationalError, ProgrammingError
from django.forms import Textarea
from django.template.response import TemplateResponse
from django.urls import path

from apps.users.models import User
from config.admin_sites import admin_site, grid_manager_site

from .models import Grid, MediatorAssignment


from django import forms


class MediatorAssignmentForm(forms.ModelForm):
    """调解员分配表单，验证一个调解员只能属于一个网格。"""

    class Meta:
        model = MediatorAssignment
        fields = "__all__"

    def clean_mediator(self):
        mediator = self.cleaned_data.get("mediator")
        if not mediator:
            return mediator
        # 检查该调解员是否已分配到其他网格（排除当前记录）
        qs = MediatorAssignment.objects.filter(mediator=mediator).select_related("grid")
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existing = qs.first()
        if existing:
            raise forms.ValidationError(f"该调解员已分配到网格「{existing.grid.name}」，一个调解员只能属于一个网格")
        return mediator


class MediatorAssignmentInline(admin.TabularInline):
    """在网格详情页内进行调解员分配。"""

    model = MediatorAssignment
    form = MediatorAssignmentForm
    extra = 0
    autocomplete_fields = ("mediator",)
    fields = ("mediator", "created_at")
    readonly_fields = ("created_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mediator":
            kwargs["queryset"] = User.objects.filter(role=User.Role.MEDIATOR, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "draw-boundary/",
                self.admin_site.admin_view(self.draw_boundary_view),
                name="grids_grid_draw_boundary",
            )
        ]
        return custom_urls + urls

    def draw_boundary_view(self, request):
        """网格边界绘制（腾讯地图 JS SDK）。"""

        if not (self.has_add_permission(request) or self.has_view_or_change_permission(request)):
            raise PermissionDenied

        tencent_map_js_key = getattr(settings, "TENCENT_MAP_JS_KEY", "") or getattr(
            settings, "TENCENT_MAP_KEY", ""
        )
        zoom_level: int = 14
        center_lng: str = "116.3974"
        center_lat: str = "39.9087"

        try:
            from apps.common.models import MapConfig

            cfg = MapConfig.objects.filter(is_active=True).order_by("-updated_at", "-id").first()
        except (OperationalError, ProgrammingError):  # 未迁移/未建表时避免后台报错
            cfg = None

        if cfg:
            if getattr(cfg, "api_key", ""):
                tencent_map_js_key = cfg.api_key
            if getattr(cfg, "zoom_level", None):
                zoom_level = int(cfg.zoom_level)
            if getattr(cfg, "center_longitude", None) is not None:
                center_lng = str(cfg.center_longitude)
            if getattr(cfg, "center_latitude", None) is not None:
                center_lat = str(cfg.center_latitude)

        zoom_level = max(14, int(zoom_level))

        context = {
            **self.admin_site.each_context(request),
            "title": "绘制网格边界坐标",
            "tencent_map_key": tencent_map_js_key,
            "zoom_level": zoom_level,
            "min_zoom_level": 14,
            "center_lng": center_lng,
            "center_lat": center_lat,
            "current_host": request.get_host(),
        }
        return TemplateResponse(request, "admin/grids/grid/draw_boundary.html", context)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_mediator_count=Count("mediator_assignments", distinct=True))

    @admin.display(description="调解员数量", ordering="_mediator_count")
    def mediator_count(self, obj: Grid) -> int:
        return getattr(obj, "_mediator_count", 0)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "current_manager":
            kwargs["queryset"] = User.objects.filter(role=User.Role.GRID_MANAGER, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# 注册到管理员后台
admin_site.register(Grid, GridAdmin)

# 注册到网格负责人后台
grid_manager_site.register(Grid, GridAdmin)

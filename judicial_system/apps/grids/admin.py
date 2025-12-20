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
        return super().get_queryset(request).annotate(_mediator_count=Count("members", distinct=True))

    @admin.display(description="调解员数量", ordering="_mediator_count")
    def mediator_count(self, obj: Grid) -> int:
        return getattr(obj, "_mediator_count", 0)

# 注册到管理员后台
admin_site.register(Grid, GridAdmin)

# 注册到网格负责人后台
grid_manager_site.register(Grid, GridAdmin)

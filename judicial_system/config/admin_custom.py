"""
Admin 扩展配置

说明：
- 增加“网格管理/统计”页面（腾讯地图渲染 Grid 区域）
- 适配自定义 AdminSite（admin_site / grid_manager_site）
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.db.models import Count
from django.db.utils import OperationalError, ProgrammingError
from django.template.response import TemplateResponse
from django.urls import path

from .admin_sites import admin_site, grid_manager_site

MIN_TENCENT_MAP_ZOOM_LEVEL = 14


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_boundary(boundary) -> list[list[float]]:
    if not isinstance(boundary, list):
        return []
    cleaned: list[list[float]] = []
    for point in boundary:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        lng = _safe_float(point[0])
        lat = _safe_float(point[1])
        if lng is None or lat is None:
            continue
        cleaned.append([lng, lat])
    return cleaned


def _compute_center_from_boundary(boundary: list[list[float]]) -> tuple[float | None, float | None]:
    if not boundary:
        return None, None
    lngs = [p[0] for p in boundary]
    lats = [p[1] for p in boundary]
    if not lngs or not lats:
        return None, None
    return (min(lngs) + max(lngs)) / 2, (min(lats) + max(lats)) / 2


def _get_tencent_map_context() -> dict:
    tencent_map_js_key = getattr(settings, "TENCENT_MAP_JS_KEY", "") or getattr(
        settings, "TENCENT_MAP_KEY", ""
    )
    zoom_level: int = MIN_TENCENT_MAP_ZOOM_LEVEL
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

    zoom_level = max(MIN_TENCENT_MAP_ZOOM_LEVEL, int(zoom_level))

    return {
        "tencent_map_key": tencent_map_js_key,
        "zoom_level": zoom_level,
        "min_zoom_level": MIN_TENCENT_MAP_ZOOM_LEVEL,
        "center_lng": center_lng,
        "center_lat": center_lat,
    }


def _make_grids_statistics_view(site):
    def grids_statistics_view(request):
        """网格管理/统计。"""

        try:
            from apps.grids.models import Grid

            qs = (
                Grid.objects.select_related("current_manager")
                .annotate(_mediator_count=Count("mediator_assignments", distinct=True))
                .order_by("id")
            )
            grids = list(qs)
        except (OperationalError, ProgrammingError):
            grids = []

        grids_data: list[dict] = []
        grids_with_boundary = 0
        grids_active = 0
        mediators_total = 0
        regions: set[str] = set()

        for grid in grids:
            if grid.is_active:
                grids_active += 1

            if grid.region:
                regions.add(str(grid.region))

            mediator_count = int(getattr(grid, "_mediator_count", 0) or 0)
            mediators_total += mediator_count

            boundary = _clean_boundary(grid.boundary or [])
            if len(boundary) >= 3:
                grids_with_boundary += 1
            else:
                boundary = []

            center_lng = _safe_float(getattr(grid, "center_lng", None))
            center_lat = _safe_float(getattr(grid, "center_lat", None))
            if (center_lng is None or center_lat is None) and boundary:
                center_lng, center_lat = _compute_center_from_boundary(boundary)

            grids_data.append(
                {
                    "id": grid.id,
                    "name": grid.name,
                    "region": grid.region or "",
                    "is_active": bool(grid.is_active),
                    "manager": str(grid.current_manager) if grid.current_manager else "",
                    "mediator_count": mediator_count,
                    "boundary": boundary,
                    "center_lng": center_lng,
                    "center_lat": center_lat,
                }
            )

        map_ctx = _get_tencent_map_context()
        context = {
            **site.each_context(request),
            "title": "网格统计",
            "current_host": request.get_host(),
            "grids_total": len(grids),
            "grids_active": grids_active,
            "grids_with_boundary": grids_with_boundary,
            "regions_total": len(regions),
            "mediators_total": mediators_total,
            "grids": grids_data,
            **map_ctx,
        }
        return TemplateResponse(request, "admin/grids/statistics.html", context)

    return grids_statistics_view


def _patch_adminsite_urls(site):
    if getattr(site, "_grids_statistics_patched", False):
        return

    original_get_urls = site.get_urls

    def get_urls():
        return [
            path(
                "grids/statistics/",
                site.admin_view(_make_grids_statistics_view(site)),
                name="grids_statistics",
            ),
        ] + original_get_urls()

    site.get_urls = get_urls
    site._grids_statistics_patched = True


_patch_adminsite_urls(admin_site)
_patch_adminsite_urls(grid_manager_site)

# 兼容默认 admin.site（项目现已使用自定义 admin_site / grid_manager_site 路由）
admin.site.site_header = "司法监管系统"
admin.site.site_title = "司法监管系统后台"
admin.site.index_title = "后台管理"

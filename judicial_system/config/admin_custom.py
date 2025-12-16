"""
Admin 扩展配置

说明：
- 增加“网格管理/统计”占位页面
- 配置站点标题信息
"""

from __future__ import annotations

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path


def grids_statistics_view(request):
    """网格统计（占位）。"""

    context = {**admin.site.each_context(request), "title": "网格统计"}
    return TemplateResponse(request, "admin/grids/statistics.html", context)


def _patch_admin_urls():
    original_get_urls = admin.site.get_urls

    def get_urls():
        return [
            path(
                "grids/statistics/",
                admin.site.admin_view(grids_statistics_view),
                name="grids_statistics",
            ),
        ] + original_get_urls()

    admin.site.get_urls = get_urls


_patch_admin_urls()

admin.site.site_header = "司法监管系统"
admin.site.site_title = "司法监管系统后台"
admin.site.index_title = "后台管理"


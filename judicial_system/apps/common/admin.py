"""Common 子应用 Admin 配置。"""

from django.contrib import admin

from config.admin_sites import admin_site
from .models import Attachment, MapConfig


class AttachmentAdmin(admin.ModelAdmin):
    """附件管理。"""

    list_display = ("id", "file_type", "file_size", "original_name")
    search_fields = ("original_name",)


class MapConfigAdmin(admin.ModelAdmin):
    """地图配置管理。"""

    list_display = ("id", "zoom_level", "center_longitude", "center_latitude", "is_active", "created_at")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("zoom_level", "center_longitude", "center_latitude", "api_key", "is_active", "created_at", "updated_at")


# 注册到管理员后台
admin_site.register(Attachment, AttachmentAdmin)
admin_site.register(MapConfig, MapConfigAdmin)


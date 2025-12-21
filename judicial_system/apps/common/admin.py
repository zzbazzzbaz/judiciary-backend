"""Common 子应用 Admin 配置。"""

from django.contrib import admin

from apps.users.models import User
from config.admin_sites import admin_site, grid_manager_site
from .models import Attachment, MapConfig


class AttachmentAdmin(admin.ModelAdmin):
    """附件管理（管理员后台，可删除和修改）。"""

    list_display = ("id", "file", "file_type", "file_size", "original_name")
    list_filter = ("file_type",)
    search_fields = ("original_name",)


class AttachmentReadOnlyAdmin(admin.ModelAdmin):
    """附件管理（网格管理员后台，管理员可修改删除，网格管理员只能新增）。"""

    list_display = ("id", "file", "file_type", "file_size", "original_name")
    list_filter = ("file_type",)
    search_fields = ("original_name",)

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MapConfigAdmin(admin.ModelAdmin):
    """地图配置管理。"""

    list_display = ("id", "zoom_level", "center_longitude", "center_latitude", "is_active", "created_at")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("zoom_level", "center_longitude", "center_latitude", "api_key", "is_active", "created_at", "updated_at")


# 注册到管理员后台
admin_site.register(Attachment, AttachmentAdmin)
admin_site.register(MapConfig, MapConfigAdmin)

# 注册到网格管理员后台（只读）
grid_manager_site.register(Attachment, AttachmentReadOnlyAdmin)


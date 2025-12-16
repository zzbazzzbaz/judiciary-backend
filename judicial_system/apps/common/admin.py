"""Common 子应用 Admin 配置。"""

from django.contrib import admin

from config.admin_sites import admin_site
from .models import Attachment


class AttachmentAdmin(admin.ModelAdmin):
    """附件管理。"""

    list_display = ("id", "file_type", "file_size", "original_name")
    search_fields = ("original_name",)


# 注册到管理员后台
admin_site.register(Attachment, AttachmentAdmin)


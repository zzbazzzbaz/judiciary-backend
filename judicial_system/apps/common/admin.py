"""Common 子应用 Admin 配置。"""

from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """附件管理。"""

    list_display = ("id", "file_type", "file_size", "original_name")
    search_fields = ("original_name",)


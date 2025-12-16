"""Cases 子应用 Admin 配置。"""

from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "type", "status", "party_name", "grid", "reported_at")
    search_fields = ("code", "party_name")
    list_filter = ("type", "status")


"""Grids 子应用 Admin 配置。"""

from django.contrib import admin

from .models import Grid, MediatorAssignment


@admin.register(Grid)
class GridAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "region", "is_active", "created_at")
    search_fields = ("name", "region")
    list_filter = ("is_active",)


@admin.register(MediatorAssignment)
class MediatorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "grid", "mediator", "created_at")
    search_fields = ("grid__name", "mediator__name", "mediator__phone")


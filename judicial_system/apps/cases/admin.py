"""Cases 子应用 Admin 配置。"""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.grids.models import Grid, MediatorAssignment
from apps.users.models import User
from utils.code_generator import generate_task_code

from .models import Task


class TaskAdminForm(forms.ModelForm):
    """任务管理表单（管理员）。"""

    class Meta:
        model = Task
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        reporter: User | None = cleaned_data.get("reporter")
        if reporter and reporter.role != User.Role.MEDIATOR:
            raise forms.ValidationError("上报人必须为调解员")

        grid: Grid | None = cleaned_data.get("grid")
        assigned_mediator: User | None = cleaned_data.get("assigned_mediator")
        if assigned_mediator:
            if assigned_mediator.role != User.Role.MEDIATOR or not assigned_mediator.is_active:
                raise forms.ValidationError("被分配人员必须为启用状态的调解员")
            if not grid:
                raise forms.ValidationError("分派调解员前必须先选择所属网格")
            if not MediatorAssignment.objects.filter(grid=grid, mediator=assigned_mediator).exists():
                raise forms.ValidationError("该调解员不在此网格内，请先在网格中分配调解员")

        return cleaned_data


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """任务管理（纠纷/法律援助、分派与调解结果）。"""

    form = TaskAdminForm

    list_display = (
        "id",
        "code",
        "type",
        "status",
        "party_name",
        "grid",
        "reporter",
        "assigned_mediator",
        "reported_at",
        "assigned_at",
        "completed_at",
    )
    list_select_related = ("grid", "reporter", "assigned_mediator")
    search_fields = ("code", "party_name", "party_phone", "reporter__name", "assigned_mediator__name")
    list_filter = ("type", "status", "grid", "reported_at")
    date_hierarchy = "reported_at"
    ordering = ("-reported_at", "-id")

    readonly_fields = ("code", "reported_at", "created_at", "updated_at")
    fieldsets = (
        ("任务信息", {"fields": ("code", "type", "status", "grid", "description", "amount")}),
        ("当事人信息", {"fields": ("party_name", "party_phone", "party_address")}),
        (
            "上报信息",
            {
                "fields": (
                    "reporter",
                    "reported_at",
                    ("report_lng", "report_lat"),
                    "report_address",
                    "report_image_ids",
                    "report_file_ids",
                )
            },
        ),
        ("分派信息", {"fields": ("assigner", "assigned_mediator", "assigned_at")}),
        (
            "进行中",
            {"fields": ("process_submitted_at", "participants", "handle_method", "expected_plan")},
        ),
        (
            "调解结果",
            {
                "fields": (
                    "result",
                    "result_detail",
                    "process_description",
                    "completed_at",
                    ("complete_lng", "complete_lat"),
                    "complete_address",
                    "complete_image_ids",
                    "complete_file_ids",
                )
            },
        ),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "grid":
            kwargs["queryset"] = Grid.objects.filter(is_active=True)
        if db_field.name in {"reporter", "assigned_mediator"}:
            kwargs["queryset"] = User.objects.filter(role=User.Role.MEDIATOR, is_active=True)
        if db_field.name == "assigner":
            kwargs["queryset"] = User.objects.filter(
                role__in=[User.Role.ADMIN, User.Role.GRID_MANAGER],
                is_active=True,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj: Task, form, change):
        """
        管理端便捷逻辑：
        - 新增任务时自动生成 code（并发冲突简单重试）
        - 选择调解员后自动写入 assigner/assigned_at，并在已上报状态下切到已分配
        """

        if obj.assigned_mediator_id and (not obj.assigner_id):
            obj.assigner = request.user
        if obj.assigned_mediator_id and (not obj.assigned_at):
            obj.assigned_at = timezone.now()
        if obj.assigned_mediator_id and obj.status == Task.Status.REPORTED:
            obj.status = Task.Status.ASSIGNED
        if obj.process_submitted_at and obj.status == Task.Status.ASSIGNED:
            obj.status = Task.Status.PROCESSING
        if obj.completed_at and obj.status != Task.Status.COMPLETED:
            obj.status = Task.Status.COMPLETED

        if obj.code:
            return super().save_model(request, obj, form, change)

        last_error: IntegrityError | None = None
        for _ in range(3):
            obj.code = generate_task_code(task_type=obj.type)
            try:
                with transaction.atomic():
                    return super().save_model(request, obj, form, change)
            except IntegrityError as e:
                last_error = e
                obj.code = ""
                continue

        if last_error:
            raise last_error

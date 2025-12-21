"""Cases 子应用 Admin 配置。"""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.models import Attachment
from apps.grids.models import Grid
from apps.users.models import User
from config.admin_sites import admin_site, grid_manager_site


def get_attachments_from_ids(ids_str: str) -> list:
    """根据逗号分隔的ID字符串获取附件列表。"""
    if not ids_str:
        return []
    try:
        ids = [int(i.strip()) for i in ids_str.split(",") if i.strip()]
        return list(Attachment.objects.filter(id__in=ids))
    except (ValueError, TypeError):
        return []


from utils.code_generator import generate_task_code

from .models import Task, UnassignedTask


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
            if assigned_mediator.grid_id != grid.id:
                raise forms.ValidationError("该调解员不在此网格内，请先将调解员分配到该网格")

        return cleaned_data


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
        "view_detail_action",
    )
    list_select_related = ("grid", "reporter", "assigned_mediator")
    search_fields = ("code", "party_name", "party_phone", "reporter__name", "assigned_mediator__name")
    list_filter = ("type", "status", "grid", "reported_at")
    date_hierarchy = "reported_at"
    ordering = ("-reported_at", "-id")

    readonly_fields = ("code", "type", "status", "reported_at", "created_at", "updated_at")
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

    def view_detail_action(self, obj):
        """查看详情按钮。"""
        from django.utils.html import format_html
        return format_html(
            '<a style="display:inline-block;padding:4px 12px;background:#e3f2fd;color:#333;'
            'border-radius:4px;text-decoration:none;font-size:12px;" '
            'href="{}">详情</a>',
            f"/admin/cases/task/{obj.pk}/detail/"
        )
    view_detail_action.short_description = "操作"
    view_detail_action.allow_tags = True

    def get_urls(self):
        """添加自定义详情页 URL。"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:task_id>/detail/",
                self.admin_site.admin_view(self.detail_view),
                name="cases_task_detail",
            ),
        ]
        return custom_urls + urls

    def detail_view(self, request, task_id):
        """任务详情视图（管理员端）。"""
        from django.shortcuts import get_object_or_404, render

        task = get_object_or_404(
            Task.objects.select_related("grid", "reporter", "assigned_mediator", "assigner"),
            pk=task_id
        )

        # 获取附件
        report_images = get_attachments_from_ids(task.report_image_ids)
        report_files = get_attachments_from_ids(task.report_file_ids)
        complete_images = get_attachments_from_ids(task.complete_image_ids)
        complete_files = get_attachments_from_ids(task.complete_file_ids)

        context = {
            "title": f"任务详情: {task.code}",
            "task": task,
            "opts": self.model._meta,
            "has_view_permission": True,
            "back_url": "/admin/cases/task/",
            "back_text": "返回任务列表",
            "report_images": report_images,
            "report_files": report_files,
            "complete_images": complete_images,
            "complete_files": complete_files,
        }
        return render(request, "admin/cases/task/detail.html", context)


# 注册到管理员后台
admin_site.register(Task, TaskAdmin)

# ==================== 网格管理员专用 Admin ====================

class GridManagerTaskAdmin(admin.ModelAdmin):
    """
    网格管理员端 - 所有任务列表。

    功能：
    - 查看本网格所有任务
    - 点击查看任务详情（自定义页面）
    """

    list_display = (
        "id",
        "code",
        "type",
        "status",
        "party_name",
        "reporter",
        "assigned_mediator",
        "reported_at",
        "view_detail_action",
    )
    list_display_links = None  # 禁用ID点击进入详情
    list_select_related = ("grid", "reporter", "assigned_mediator")
    search_fields = ("code", "party_name", "party_phone", "reporter__name", "assigned_mediator__name")
    list_filter = ("type", "status", "reported_at")
    date_hierarchy = "reported_at"
    ordering = ("-reported_at", "-id")

    def get_queryset(self, request):
        """只显示本网格的任务。"""
        queryset = super().get_queryset(request)
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        return queryset.filter(grid__in=managed_grids)

    def view_detail_action(self, obj):
        """查看详情按钮。"""
        from django.utils.html import format_html
        return format_html(
            '<a style="display:inline-block;padding:4px 12px;background:#e3f2fd;color:#333;'
            'border-radius:4px;text-decoration:none;font-size:12px;" '
            'href="{}">详情</a>',
            f"/grid-admin/cases/task/{obj.pk}/detail/"
        )
    view_detail_action.short_description = "操作"
    view_detail_action.allow_tags = True

    def has_add_permission(self, request):
        """网格管理员不能新增任务（任务由调解员上报）。"""
        return False

    def has_change_permission(self, request, obj=None):
        """网格管理员不能编辑任务（只能查看）。"""
        return False

    def has_delete_permission(self, request, obj=None):
        """网格管理员不能删除任务。"""
        return False

    def get_urls(self):
        """添加自定义详情页 URL。"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:task_id>/detail/",
                self.admin_site.admin_view(self.detail_view),
                name="task_detail",
            ),
        ]
        return custom_urls + urls

    def detail_view(self, request, task_id):
        """任务详情视图。"""
        from django.shortcuts import get_object_or_404, render
        from django.contrib import messages

        task = get_object_or_404(
            Task.objects.select_related("grid", "reporter", "assigned_mediator", "assigner"),
            pk=task_id
        )

        # 检查权限：任务必须属于当前管理员管理的网格
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        if task.grid not in managed_grids:
            messages.error(request, "您没有权限查看此任务")
            from django.shortcuts import redirect
            return redirect("grid_admin:cases_task_changelist")

        # 根据来源确定返回链接
        from_page = request.GET.get("from", "")
        if from_page == "unassigned":
            back_url = "/grid-admin/cases/unassignedtask/"
            back_text = "返回待分配任务"
        else:
            back_url = "/grid-admin/cases/task/"
            back_text = "返回任务列表"

        # 获取附件
        report_images = get_attachments_from_ids(task.report_image_ids)
        report_files = get_attachments_from_ids(task.report_file_ids)
        complete_images = get_attachments_from_ids(task.complete_image_ids)
        complete_files = get_attachments_from_ids(task.complete_file_ids)

        context = {
            "title": f"任务详情: {task.code}",
            "task": task,
            "opts": self.model._meta,
            "has_view_permission": True,
            "back_url": back_url,
            "back_text": back_text,
            "report_images": report_images,
            "report_files": report_files,
            "complete_images": complete_images,
            "complete_files": complete_files,
        }
        return render(request, "admin/cases/task/detail.html", context)


class AssignMediatorForm(forms.Form):
    """分配调解员表单。"""
    mediator = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="选择调解员",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, grid=None, **kwargs):
        super().__init__(*args, **kwargs)
        if grid:
            self.fields["mediator"].queryset = User.objects.filter(
                role=User.Role.MEDIATOR, is_active=True, grid=grid
            )


class GridManagerUnassignedTaskAdmin(admin.ModelAdmin):
    """
    网格管理员端 - 未分配任务列表。

    功能：
    - 查看本网格未分配的任务（状态为 reported）
    - 点击分配按钮分配给本网格调解员
    """

    list_display = (
        "id",
        "code",
        "type",
        "party_name",
        "reporter",
        "reported_at",
        "action_buttons",
    )
    list_display_links = None  # 禁用ID点击进入详情
    list_select_related = ("grid", "reporter")
    search_fields = ("code", "party_name", "party_phone", "reporter__name")
    list_filter = ("type", "reported_at")
    date_hierarchy = "reported_at"
    ordering = ("-reported_at", "-id")

    def get_queryset(self, request):
        """只显示本网格未分配的任务。"""
        queryset = super().get_queryset(request)
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        return queryset.filter(grid__in=managed_grids, status=Task.Status.REPORTED)

    def action_buttons(self, obj):
        """操作按钮：详情 + 分配。"""
        from django.utils.html import format_html
        btn_style = (
            'display:inline-block;padding:4px 12px;background:#e3f2fd;color:#333;'
            'border-radius:4px;text-decoration:none;font-size:12px;margin-right:8px;'
        )
        return format_html(
            '<a style="{}" href="{}">详情</a>'
            '<a style="{}" href="{}">分配</a>',
            btn_style,
            f"/grid-admin/cases/task/{obj.pk}/detail/?from=unassigned",
            btn_style,
            f"/grid-admin/cases/unassignedtask/{obj.pk}/assign/"
        )
    action_buttons.short_description = "操作"
    action_buttons.allow_tags = True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        """添加自定义分配页面 URL。"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:task_id>/assign/",
                self.admin_site.admin_view(self.assign_view),
                name="unassignedtask_assign",
            ),
        ]
        return custom_urls + urls

    def assign_view(self, request, task_id):
        """分配任务视图。"""
        from django.shortcuts import get_object_or_404, redirect, render
        from django.contrib import messages

        task = get_object_or_404(Task, pk=task_id)

        # 检查权限：任务必须属于当前管理员管理的网格
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        if task.grid not in managed_grids:
            messages.error(request, "您没有权限分配此任务")
            return redirect("grid_admin:cases_unassignedtask_changelist")

        if task.status != Task.Status.REPORTED:
            messages.error(request, "此任务已被分配")
            return redirect("grid_admin:cases_unassignedtask_changelist")

        if request.method == "POST":
            form = AssignMediatorForm(request.POST, grid=task.grid)
            if form.is_valid():
                mediator = form.cleaned_data["mediator"]
                task.assigned_mediator = mediator
                task.assigner = request.user
                task.assigned_at = timezone.now()
                task.status = Task.Status.ASSIGNED
                task.save(update_fields=["assigned_mediator", "assigner", "assigned_at", "status", "updated_at"])
                messages.success(request, f"任务 {task.code} 已分配给 {mediator.name}")
                return redirect("grid_admin:cases_unassignedtask_changelist")
        else:
            form = AssignMediatorForm(grid=task.grid)

        # 获取上报附件
        report_images = get_attachments_from_ids(task.report_image_ids)
        report_files = get_attachments_from_ids(task.report_file_ids)

        context = {
            "title": f"分配任务: {task.code}",
            "task": task,
            "form": form,
            "opts": self.model._meta,
            "has_view_permission": True,
            "report_images": report_images,
            "report_files": report_files,
        }
        return render(request, "admin/cases/unassignedtask/assign.html", context)


# 注册到网格负责人后台
grid_manager_site.register(Task, GridManagerTaskAdmin)
grid_manager_site.register(UnassignedTask, GridManagerUnassignedTaskAdmin)

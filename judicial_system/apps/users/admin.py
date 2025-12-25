"""
Users 子应用 Django Admin

完成：
- 人员管理（users_user）增删改查
- 人员培训记录管理（users_training_record）增删改查
- 绩效管理（users_performance_score）增删改查
- 机构管理（users_organization）增删改查
"""

from __future__ import annotations

import os

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ImportMixin
from import_export.formats.base_formats import XLSX
from import_export.results import RowResult

from apps.grids.models import Grid
from config.admin_sites import admin_site, grid_manager_site
from .models import Organization, PerformanceHistory, PerformanceScore, TrainingRecord, User, UserAttachment
from .resources import MediatorResource, TrainingRecordResource


class UserCreationForm(forms.ModelForm):
    """
    Admin 新增用户表单。

    说明：
    - 通过两次输入密码并校验一致性
    - 使用 `set_password()` 保存哈希后的密码
    """

    password1 = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "name", "role", "grid", "organization", "is_active", "gender", "id_card", "phone")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("两次输入的密码不一致")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        grid = cleaned_data.get("grid")

        # 调解员必须有所属网格
        if role == User.Role.MEDIATOR and not grid:
            raise forms.ValidationError("调解员必须选择所属网格")

        # 网格管理员必须有所属网格且该网格未分配其他管理员
        if role == User.Role.GRID_MANAGER:
            if not grid:
                raise forms.ValidationError("网格管理员必须选择所属网格")
            # 检查该网格是否已有网格管理员
            if grid.current_manager_id is not None:
                raise forms.ValidationError(f"网格「{grid.name}」已有网格管理员，请选择其他网格")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # 如果是网格管理员，同步更新网格的 current_manager
            if user.role == User.Role.GRID_MANAGER and user.grid:
                user.grid.current_manager = user
                user.grid.save(update_fields=["current_manager"])
        return user


class UserChangeForm(forms.ModelForm):
    """
    Admin 编辑用户表单。

    说明：
    - 密码字段使用只读哈希展示，避免直接编辑明文
    - 需要重置密码时可在用户详情页使用「修改密码」功能
    """

    password = ReadOnlyPasswordHashField(label="密码", help_text="密码已加密存储，无法查看明文。")

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "name",
            "gender",
            "id_card",
            "phone",
            "organization",
            "role",
            "grid",
            "is_active",
        )

    def clean_password(self):
        return self.initial.get("password")

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        grid = cleaned_data.get("grid")

        # 调解员必须有所属网格
        if role == User.Role.MEDIATOR and not grid:
            raise forms.ValidationError("调解员必须选择所属网格")

        # 网格管理员必须有所属网格且该网格未分配其他管理员
        if role == User.Role.GRID_MANAGER:
            if not grid:
                raise forms.ValidationError("网格管理员必须选择所属网格")
            # 检查该网格是否已有其他网格管理员（排除当前用户）
            if grid.current_manager_id is not None and grid.current_manager_id != self.instance.pk:
                raise forms.ValidationError(f"网格「{grid.name}」已有网格管理员，请选择其他网格")

        return cleaned_data


class ExcelImportMixin:
    """Excel导入功能Mixin，提供模板下载和友好错误提示。"""

    excel_template_file = ""  # 子类需要设置模板文件名

    def get_urls(self):
        """添加模板下载 URL。"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "download-template/",
                self.admin_site.admin_view(self.download_template_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_download_template",
            ),
        ]
        return custom_urls + urls

    def download_template_view(self, request):
        """下载导入模板文件。"""
        if not self.excel_template_file:
            messages.error(request, "模板文件未配置")
            return redirect("../")

        template_path = getattr(settings, "IMPORT_TEMPLATES_DIR", None)
        if not template_path:
            messages.error(request, "模板目录未配置")
            return redirect("../")

        file_path = os.path.join(template_path, self.excel_template_file)
        if not os.path.exists(file_path):
            messages.error(request, f"模板文件不存在: {self.excel_template_file}")
            return redirect("../")

        response = FileResponse(
            open(file_path, "rb"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        from urllib.parse import quote
        encoded_filename = quote(self.excel_template_file)
        response["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return response

    def get_import_formats(self):
        """只支持 Excel 格式。"""
        return [XLSX]

    def generate_log_entries(self, result, request):
        """生成导入日志并显示详细错误信息。"""
        if result.has_errors():
            # 收集所有错误信息
            error_messages = []
            for row_errors in result.row_errors():
                row_number, errors = row_errors
                for error in errors:
                    error_msg = str(error.error)
                    error_messages.append(f"第 {row_number + 1} 行: {error_msg}")

            # 显示错误摘要
            if error_messages:
                error_summary = "<br>".join(error_messages[:10])  # 最多显示10条
                if len(error_messages) > 10:
                    error_summary += f"<br>...还有 {len(error_messages) - 10} 条错误"
                messages.error(
                    request,
                    format_html(
                        "导入失败，共 {} 条错误：<br>{}",
                        len(error_messages),
                        format_html(error_summary),
                    ),
                )
        else:
            # 统计导入结果
            new_count = sum(1 for row in result.rows if row.import_type == RowResult.IMPORT_TYPE_NEW)
            update_count = sum(1 for row in result.rows if row.import_type == RowResult.IMPORT_TYPE_UPDATE)
            skip_count = sum(1 for row in result.rows if row.import_type == RowResult.IMPORT_TYPE_SKIP)

            if new_count > 0 or update_count > 0:
                messages.success(
                    request,
                    f"导入成功！新增 {new_count} 条，更新 {update_count} 条，跳过 {skip_count} 条。",
                )

        return super().generate_log_entries(result, request)


class UserAdmin(ImportMixin, ExcelImportMixin, BaseUserAdmin):
    """人员管理（用户/人员），支持Excel导入。"""

    actions = ["reset_password"]

    resource_class = MediatorResource
    excel_template_file = "调解员导入模板.xlsx"
    change_list_template = "admin/users/user/change_list.html"

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("id", "username", "name", "role", "grid", "organization", "phone", "is_active", "last_login")
    list_filter = ("role", "is_active", "organization", "grid")
    search_fields = ("username", "name", "phone", "id_card")
    ordering = ("-id",)
    autocomplete_fields = ("grid",)

    readonly_fields = ("last_login", "created_at", "updated_at")

    fieldsets = (
        ("账号信息", {"fields": ("username", "password")}),
        ("基本信息", {"fields": ("name", "gender", "id_card", "phone", "organization", "role", "grid", "avatar")}),
        ("状态", {"fields": ("is_active",)}),
        ("时间", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            "新增用户",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "name",
                    "role",
                    "avatar",
                    "grid",
                    "organization",
                    "is_active",
                    "gender",
                    "id_card",
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # 项目暂不使用 Django 权限/分组体系，这里置空避免 admin 尝试渲染相关字段
    filter_horizontal = ()

    def get_queryset(self, request):
        """
        根据当前用户角色过滤用户列表。

        说明：
        - admin 角色：返回所有用户
        - grid_manager 角色：返回其管理的网格中分配的调解员
        """
        queryset = super().get_queryset(request)

        # admin 角色返回所有记录
        if hasattr(request.user, 'role') and request.user.role == User.Role.ADMIN:
            return queryset

        # grid_manager 角色返回其管理网格中的调解员
        if hasattr(request.user, 'role') and request.user.role == User.Role.GRID_MANAGER:
            # 获取该 grid_manager 管理的网格
            managed_grids = Grid.objects.filter(current_manager=request.user)
            # 返回这些网格中的调解员
            return queryset.filter(grid__in=managed_grids).distinct()

        # 其他角色返回空查询集
        return queryset.none()

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """
        限制 role 字段的可选项：只有 admin 角色的用户可以选择 admin 和 grid_manager。

        说明：
        - admin 角色：可以选择所有角色
        - grid_manager 角色：只能选择 mediator
        - 其他角色：只能选择 mediator
        """
        if db_field.name == "role":
            # grid_manager 角色只能选择 mediator
            if hasattr(request.user, 'role') and request.user.role == User.Role.GRID_MANAGER:
                kwargs["choices"] = [(User.Role.MEDIATOR, "调解员")]

        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        限制网格下拉列表的可选项。

        说明：
        - 显示所有启用的网格
        - 网格管理员的唯一性检查在表单验证中进行
        """
        if db_field.name == "grid":
            kwargs["queryset"] = Grid.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        保存用户时同步更新网格的 current_manager。
        """
        super().save_model(request, obj, form, change)

        # 如果是网格管理员，同步更新网格的 current_manager
        if obj.role == User.Role.GRID_MANAGER and obj.grid:
            # 先清除该用户在其他网格的管理员身份
            Grid.objects.filter(current_manager=obj).exclude(id=obj.grid_id).update(current_manager=None)
            # 设置当前网格的管理员
            if obj.grid.current_manager_id != obj.pk:
                obj.grid.current_manager = obj
                obj.grid.save(update_fields=["current_manager"])
        elif obj.role != User.Role.GRID_MANAGER:
            # 如果角色不是网格管理员，清除其管理的网格
            Grid.objects.filter(current_manager=obj).update(current_manager=None)

    def get_search_results(self, request, queryset, search_term):
        """
        为 Admin autocomplete 提供按字段名的角色过滤。

        说明：
        - Django 的 autocomplete 视图会携带 `field_name` 参数（源模型的字段名）
        - 用于限制负责人/调解员等字段只搜索到对应角色，提升后台可用性
        """

        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        field_name = request.GET.get("field_name")
        if field_name == "current_manager":
            queryset = queryset.filter(role=User.Role.GRID_MANAGER)
        elif field_name in {"mediator", "reporter", "assigned_mediator"}:
            queryset = queryset.filter(role=User.Role.MEDIATOR)
        elif field_name == "assigner":
            queryset = queryset.filter(role__in=[User.Role.ADMIN, User.Role.GRID_MANAGER])

        return queryset, use_distinct

    @admin.action(description="重置密码")
    def reset_password(self, request, queryset):
        """批量重置选中用户的密码为 123456。"""
        count = queryset.count()
        for user in queryset:
            user.set_password("123456")
            user.save(update_fields=["password"])
        self.message_user(request, f"已成功重置 {count} 个用户的密码为 123456", messages.SUCCESS)


class UserAttachmentAdmin(admin.ModelAdmin):
    """用户附件管理。"""

    list_display = ("id", "user", "created_at")
    search_fields = ("user__username", "user__name")
    readonly_fields = ("user", "created_at")

    def get_fields(self, request, obj=None):
        if obj is None:  # 新增时不显示 user
            return ("file",)
        return ("user", "file", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:  # 新增时自动设置为当前用户
            obj.user = request.user
        super().save_model(request, obj, form, change)


class OrganizationAdmin(admin.ModelAdmin):
    """机构管理。"""

    list_display = ("id", "name", "parent", "sort_order", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    list_editable = ("sort_order",)
    ordering = ("sort_order", "id")


class TrainingRecordAdmin(ImportMixin, ExcelImportMixin, admin.ModelAdmin):
    """培训记录管理，支持Excel导入。"""

    resource_class = TrainingRecordResource
    excel_template_file = "培训记录导入模板.xlsx"
    change_list_template = "admin/users/trainingrecord/change_list.html"

    list_display = ("id", "user", "name", "training_time", "created_at")
    search_fields = ("name", "user__name", "user__username", "user__phone")
    list_filter = ("training_time",)
    raw_id_fields = ("user",)
    autocomplete_fields = ("files", "user")
    ordering = ("-training_time", "-created_at")


class PerformanceScoreAdmin(admin.ModelAdmin):
    """绩效管理（网格负责人对调解员打分）。"""

    list_display = ("id", "mediator", "score", "period", "scorer", "created_at")
    search_fields = ("mediator__name", "mediator__username", "scorer__name", "period")
    list_filter = ("period", "score")
    # 搜索 + 下拉框（Select2 自动完成）
    autocomplete_fields = ("mediator",)
    ordering = ("-created_at",)

    readonly_fields = ("period", "scorer", "created_at")
    fields = ("mediator", "score", "period", "scorer", "comment", "created_at")

    def get_fields(self, request, obj=None):
        """
        新增页面不展示：考核周期、打分人、创建时间。

        说明：period/scorer/created_at 均由系统自动生成/记录，仅在编辑页展示为只读信息。
        """

        if obj is None:
            return ("mediator", "score", "comment")
        return super().get_fields(request, obj=obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制可选择的调解员范围，避免误选其他角色。"""

        if db_field.name == "mediator":
            kwargs["queryset"] = User.objects.filter(role=User.Role.MEDIATOR, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        业务约束：
        - 新增绩效仅允许本月：period 由系统自动生成，不允许手动填写
        - 打分人=当前登录用户：scorer 由系统自动赋值，不允许手动选择
        """

        # scorer 始终记录为当前操作用户
        obj.scorer = request.user

        # 仅在新增时写入本月周期，避免编辑历史记录时误改周期
        if not change or not obj.period:
            obj.period = timezone.now().strftime("%Y-%m")

        super().save_model(request, obj, form, change)


# 注册到管理员后台（完整功能）
admin_site.register(User, UserAdmin)
admin_site.register(UserAttachment, UserAttachmentAdmin)
admin_site.register(Organization, OrganizationAdmin)
admin_site.register(TrainingRecord, TrainingRecordAdmin)
admin_site.register(PerformanceScore, PerformanceScoreAdmin)


# ==================== 网格管理员专用 Admin ====================

class GridManagerMediatorCreationForm(forms.ModelForm):
    """
    网格管理员新增调解员表单。

    说明：
    - 网格字段由系统自动设置为当前登录网格管理员管理的网格
    - 角色固定为调解员
    """

    password1 = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "name", "organization", "is_active", "gender", "id_card", "phone")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("两次输入的密码不一致")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = User.Role.MEDIATOR  # 强制设置为调解员
        if commit:
            user.save()
        return user


class GridManagerMediatorChangeForm(forms.ModelForm):
    """
    网格管理员编辑调解员表单。

    说明：
    - 密码字段使用只读哈希展示
    - 网格和角色字段只读
    """

    password = ReadOnlyPasswordHashField(label="密码", help_text="密码已加密存储，无法查看明文。")

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "name",
            "gender",
            "id_card",
            "phone",
            "organization",
            "is_active",
        )

    def clean_password(self):
        return self.initial.get("password")


class GridManagerUserAdmin(BaseUserAdmin):
    """
    网格管理员端 - 调解员管理。

    功能：
    - 查看本网格调解员列表
    - 新增调解员（自动设置为当前管理员管理的网格）
    - 编辑调解员信息
    """

    form = GridManagerMediatorChangeForm
    add_form = GridManagerMediatorCreationForm

    list_display = ("id", "username", "name", "phone", "organization", "is_active", "last_login")
    list_filter = ("is_active", "organization")
    search_fields = ("username", "name", "phone", "id_card")
    ordering = ("-id",)

    readonly_fields = ("last_login", "created_at", "updated_at", "role", "grid")

    fieldsets = (
        ("账号信息", {"fields": ("username", "password")}),
        ("基本信息", {"fields": ("name", "gender", "id_card", "phone", "organization")}),
        ("网格信息", {"fields": ("role", "grid")}),
        ("状态", {"fields": ("is_active",)}),
        ("时间", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            "新增调解员",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "name",
                    "organization",
                    "is_active",
                    "gender",
                    "id_card",
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    filter_horizontal = ()

    def get_queryset(self, request):
        """只显示当前网格管理员管理的网格下的调解员。"""
        queryset = super().get_queryset(request)
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        return queryset.filter(grid__in=managed_grids, role=User.Role.MEDIATOR)

    def save_model(self, request, obj, form, change):
        """
        保存时自动设置网格和角色。

        说明：
        - 新增调解员时自动设置为当前管理员管理的网格
        - 角色固定为调解员
        """
        if not change:  # 新增
            obj.role = User.Role.MEDIATOR
            # 获取当前管理员管理的网格
            managed_grid = Grid.objects.filter(current_manager=request.user, is_active=True).first()
            if managed_grid:
                obj.grid = managed_grid
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        """网格管理员不能删除调解员，只能禁用。"""
        return False


class GridManagerPerformanceScoreForm(forms.ModelForm):
    """网格管理员绩效打分表单，添加唯一性校验。"""

    class Meta:
        model = PerformanceScore
        fields = ("mediator", "score", "comment")

    def clean(self):
        cleaned_data = super().clean()
        mediator = cleaned_data.get("mediator")
        if mediator:
            current_period = timezone.now().strftime("%Y-%m")
            # 检查本月是否已有该调解员的绩效记录
            exists = PerformanceScore.objects.filter(
                mediator=mediator, period=current_period
            ).exists()
            if exists:
                raise forms.ValidationError(
                    f"调解员「{mediator.name}」本月（{current_period}）已有绩效记录，请勿重复打分。"
                )
        return cleaned_data


class GridManagerPerformanceScoreAdmin(admin.ModelAdmin):
    """
    网格管理员端 - 绩效打分。

    功能：
    - 对本月网格下调解员进行打分
    - 只能打分本网格的调解员
    - 考核周期由系统自动设置为本月
    """

    form = GridManagerPerformanceScoreForm
    list_display = ("id", "mediator", "score", "period", "created_at")
    search_fields = ("mediator__name", "mediator__username", "period")
    list_filter = ("period",)
    autocomplete_fields = ("mediator",)
    ordering = ("-created_at",)

    readonly_fields = ("period", "scorer", "created_at")
    fields = ("mediator", "score", "period", "scorer", "comment", "created_at")

    def get_fields(self, request, obj=None):
        """新增页面不展示：考核周期、打分人、创建时间。"""
        if obj is None:
            return ("mediator", "score", "comment")
        return super().get_fields(request, obj=obj)

    def get_queryset(self, request):
        """只显示本网格调解员的绩效记录。"""
        queryset = super().get_queryset(request)
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        return queryset.filter(mediator__grid__in=managed_grids)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制可选择的调解员为本网格的调解员。"""
        if db_field.name == "mediator":
            managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
            kwargs["queryset"] = User.objects.filter(
                role=User.Role.MEDIATOR, is_active=True, grid__in=managed_grids
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        业务约束：
        - 新增绩效仅允许本月
        - 打分人=当前登录用户
        """
        obj.scorer = request.user
        if not change or not obj.period:
            obj.period = timezone.now().strftime("%Y-%m")
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """只能修改本月的绩效记录。"""
        if obj is not None:
            current_period = timezone.now().strftime("%Y-%m")
            if obj.period != current_period:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """只能删除本月的绩效记录。"""
        if obj is not None:
            current_period = timezone.now().strftime("%Y-%m")
            if obj.period != current_period:
                return False
        return super().has_delete_permission(request, obj)


class GridManagerPerformanceHistoryAdmin(admin.ModelAdmin):
    """
    网格管理员端 - 历史绩效列表（只读）。

    功能：
    - 查看本网格调解员的历史绩效记录
    - 完全只读，不能增删改
    """

    list_display = ("id", "mediator", "score", "period", "scorer", "comment", "created_at")
    search_fields = ("mediator__name", "mediator__username", "period")
    list_filter = ("period", "mediator")
    ordering = ("-period", "-created_at")

    def get_queryset(self, request):
        """只显示本网格调解员的历史绩效记录（非本月）。"""
        queryset = super().get_queryset(request)
        managed_grids = Grid.objects.filter(current_manager=request.user, is_active=True)
        current_period = timezone.now().strftime("%Y-%m")
        return queryset.filter(mediator__grid__in=managed_grids).exclude(period=current_period)

    def has_add_permission(self, request):
        """历史记录不能新增。"""
        return False

    def has_change_permission(self, request, obj=None):
        """历史记录不能修改。"""
        return False

    def has_delete_permission(self, request, obj=None):
        """历史记录不能删除。"""
        return False


# 注册到网格负责人后台（仅相关功能）
grid_manager_site.register(User, GridManagerUserAdmin)
grid_manager_site.register(PerformanceScore, GridManagerPerformanceScoreAdmin)
grid_manager_site.register(PerformanceHistory, GridManagerPerformanceHistoryAdmin)

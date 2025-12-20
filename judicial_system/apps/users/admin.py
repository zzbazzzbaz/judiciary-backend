"""
Users 子应用 Django Admin

完成：
- 人员管理（users_user）增删改查
- 人员培训记录管理（users_training_record）增删改查
- 绩效管理（users_performance_score）增删改查
- 机构管理（users_organization）增删改查
"""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils import timezone

from apps.grids.models import Grid
from config.admin_sites import admin_site, grid_manager_site
from .models import Organization, PerformanceScore, TrainingRecord, User, UserAttachment


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


class UserAdmin(BaseUserAdmin):
    """人员管理（用户/人员）。"""

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("id", "username", "name", "role", "organization", "phone", "is_active", "last_login")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("username", "name", "phone", "id_card")
    ordering = ("-id",)

    readonly_fields = ("last_login", "created_at", "updated_at")

    fieldsets = (
        ("账号信息", {"fields": ("username", "password")}),
        ("基本信息", {"fields": ("name", "gender", "id_card", "phone", "organization", "role", "grid")}),
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
        - 网格管理员：只显示未分配网格管理员的网格（或当前用户已分配的网格）
        - 调解员：显示所有启用的网格
        """
        if db_field.name == "grid":
            # 获取当前编辑的用户对象
            obj_id = request.resolver_match.kwargs.get("object_id")
            current_user_grid_id = None
            if obj_id:
                try:
                    current_user = User.objects.get(pk=obj_id)
                    current_user_grid_id = current_user.grid_id
                except User.DoesNotExist:
                    pass
            # 显示未分配网格管理员的网格，或当前用户已分配的网格
            from django.db.models import Q
            kwargs["queryset"] = Grid.objects.filter(
                Q(current_manager__isnull=True) | Q(id=current_user_grid_id),
                is_active=True
            )
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


class TrainingRecordAdmin(admin.ModelAdmin):
    """培训记录管理。"""

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

# 注册到网格负责人后台（仅相关功能）
grid_manager_site.register(User, UserAdmin)
grid_manager_site.register(PerformanceScore, PerformanceScoreAdmin)

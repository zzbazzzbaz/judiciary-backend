"""DRF 权限类封装（基于 users.User.role）。"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """管理员权限（role=admin）。"""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )


class IsGridManager(BasePermission):
    """网格负责人权限（role in admin/grid_manager）。"""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in {"admin", "grid_manager"}
        )


class IsMediator(BasePermission):
    """调解员权限（role=mediator）。"""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "mediator"
        )


class IsStaff(BasePermission):
    """工作人员权限（role in admin/grid_manager/mediator）。"""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in {"admin", "grid_manager", "mediator"}
        )


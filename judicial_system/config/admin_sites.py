"""
自定义 Django Admin 站点

说明：
- AdminSite: 管理员后台（使用完整的 SIMPLEUI_CONFIG）
- GridManagerSite: 网格负责人后台（简化菜单）
"""

from django.contrib.admin import AdminSite


class AdminSite(AdminSite):
    """管理员后台"""

    site_header = "司法监管系统 - 管理员后台"
    site_title = "管理员后台"
    index_title = "系统管理"

    def has_permission(self, request):
        """只允许管理员登录"""
        return (
            request.user.is_authenticated
            and request.user.is_active
            and hasattr(request.user, 'role')
            and request.user.role == 'admin'
        )


class GridManagerSite(AdminSite):
    """网格负责人后台"""

    site_header = "司法监管系统 - 网格管理后台"
    site_title = "网格管理后台"
    index_title = "网格管理"

    def has_permission(self, request):
        """允许网格负责人（必须有管理的网格）和管理员登录"""
        if not request.user.is_authenticated or not request.user.is_active:
            return False

        if not hasattr(request.user, 'role'):
            return False

        # 管理员可以直接登录
        if request.user.role == 'admin':
            return True

        # 网格管理员必须有管理的网格才能登录
        if request.user.role == 'grid_manager':
            from apps.grids.models import Grid
            return Grid.objects.filter(current_manager=request.user, is_active=True).exists()

        return False


# 创建站点实例
admin_site = AdminSite(name='admin')
grid_manager_site = GridManagerSite(name='grid_admin')

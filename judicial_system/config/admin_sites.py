"""
自定义 Django Admin 站点

说明：
- AdminSite: 管理员后台（使用完整的 SIMPLEUI_CONFIG）
- GridManagerSite: 网格负责人后台（简化菜单）
"""

from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.cache import never_cache


class AdminSite(admin.AdminSite):
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

    @never_cache
    def logout(self, request, extra_context=None):
        """
        自定义 logout 视图，支持 GET 请求。
        
        说明：Django 4.0+ 的 LogoutView 默认需要 POST 请求，
        但 admin 模板的退出链接使用 GET，导致 CSRF 错误。
        """
        auth_logout(request)
        return HttpResponseRedirect(reverse(f'{self.name}:login'))


class GridManagerSite(AdminSite):
    """网格负责人后台"""

    site_header = "司法监管系统 - 网格管理后台"
    site_title = "网格管理后台"
    index_title = "网格管理"

    def has_permission(self, request):
        """只允许网格负责人登录（必须有管理的网格）"""
        if not request.user.is_authenticated or not request.user.is_active:
            return False

        if not hasattr(request.user, 'role'):
            return False

        # 只允许网格管理员登录，且必须有管理的网格
        if request.user.role == 'grid_manager':
            from apps.grids.models import Grid
            return Grid.objects.filter(current_manager=request.user, is_active=True).exists()

        return False


# 创建站点实例
admin_site = AdminSite(name='admin')
grid_manager_site = GridManagerSite(name='grid_admin')

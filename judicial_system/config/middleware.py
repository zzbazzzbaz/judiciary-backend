"""自定义中间件"""

from django.conf import settings


class DynamicSimpleUIMiddleware:
    """根据不同的 admin 站点动态设置 SimpleUI 配置"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 网格负责人后台使用简化菜单
        if request.path.startswith('/grid-admin/'):
            settings.SIMPLEUI_CONFIG = {
                "system_keep": False,
                "menus": [
                    {
                        "name": "网格管理",
                        "icon": "fas fa-map-marked-alt",
                        "models": [
                            {"name": "待分配任务", "icon": "fas fa-clipboard-list",
                             "url": "/grid-admin/cases/unassignedtask/"},
                            {"name": "所有任务", "icon": "fas fa-tasks", "url": "/grid-admin/cases/task/"},
                            {"name": "任务附件", "icon": "fas fa-file", "url": "/grid-admin/common/attachment/"},
                        ],
                    },
                    {
                        "name": "成员管理",
                        "icon": "fas fa-users",
                        "models": [
                            {"name": "调解员", "icon": "fas fa-user-tie", "url": "/grid-admin/users/user/"},
                            {"name": "绩效打分", "icon": "fas fa-chart-line",
                             "url": "/grid-admin/users/performancescore/"},
                            {"name": "历史绩效", "icon": "fas fa-history",
                             "url": "/grid-admin/users/performancehistory/"},
                        ],
                    },
                ],
            }
        # 管理员后台使用完整菜单（恢复默认配置）
        elif request.path.startswith('/admin/'):
            settings.SIMPLEUI_CONFIG = {
                "system_keep": False,
                "menus": [
                    {
                        "name": "网格管理",
                        "icon": "fas fa-map-marked-alt",
                        "models": [
                            {"name": "地图", "icon": "fas fa-map", "url": "/admin-html/map-dashboard.html"},
                            {"name": "网格", "icon": "fas fa-border-all", "url": "/admin/grids/grid/"},
                            {"name": "任务", "icon": "fas fa-tasks", "url": "/admin/cases/task/"},
                            {"name": "任务附件", "icon": "fas fa-file", "url": "/admin/common/attachment/"},
                        ],
                    },
                    {
                        "name": "成员管理",
                        "icon": "fas fa-users",
                        "models": [
                            {"name": "成员", "icon": "fas fa-user", "url": "/admin/users/user/"},
                            {"name": "培训记录", "icon": "fas fa-graduation-cap",
                             "url": "/admin/users/trainingrecord/"},
                            {"name": "绩效", "icon": "fas fa-chart-line", "url": "/admin/users/performancescore/"},
                        ],
                    },
                    {
                        "name": "法治宣传教育",
                        "icon": "fas fa-book-open",
                        "models": [
                            {"name": "文章分类", "icon": "fas fa-folder", "url": "/admin/content/category/"},
                            {"name": "文章列表", "icon": "fas fa-file-alt", "url": "/admin/content/article/"},
                            {"name": "活动列表", "icon": "fas fa-calendar-alt", "url": "/admin/content/activity/"},
                        ],
                    },
                    {
                        "name": "文档管理",
                        "icon": "fas fa-folder-open",
                        "models": [
                            {"name": "文档分类", "icon": "fas fa-folder", "url": "/admin/content/documentcategory/"},
                            {"name": "文书模板", "icon": "fas fa-file-pdf", "url": "/admin/content/document/"},
                        ],
                    },
                    {
                        "name": "机构管理",
                        "icon": "fas fa-building",
                        "models": [
                            {"name": "机构", "icon": "fas fa-sitemap", "url": "/admin/users/organization/"},
                        ],
                    },
                    {
                        "name": "系统配置",
                        "icon": "fas fa-cog",
                        "models": [
                            {"name": "地图配置", "icon": "fas fa-map-marker-alt", "url": "/admin/common/mapconfig/"},
                        ],
                    },
                ],
            }

        response = self.get_response(request)
        return response

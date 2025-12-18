from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# 自定义 Admin 站点
from .admin_sites import admin_site, grid_manager_site

# Admin 扩展（自定义菜单页面等）
from . import admin_custom  # noqa: F401

urlpatterns = [
    path("admin/", admin_site.urls),  # 管理员后台
    path("grid-admin/", grid_manager_site.urls),  # 网格负责人后台
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.cases.urls")),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.grids.urls")),  # 网格接口
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.views.static import serve
from pathlib import Path

admin_html_root = Path(settings.BASE_DIR).parent / "admin-html"
urlpatterns += [
    path("admin-html/<path:path>", serve, {"document_root": admin_html_root}),
]

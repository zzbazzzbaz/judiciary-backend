from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Admin 扩展（自定义菜单页面等）
from . import admin_custom  # noqa: F401

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.grids.urls")),
    path("api/v1/", include("apps.cases.urls")),
    path("api/v1/", include("apps.content.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

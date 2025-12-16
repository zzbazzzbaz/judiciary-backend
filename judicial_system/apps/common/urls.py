"""Common 子应用路由。"""

from django.urls import path

from .views import UploadView

urlpatterns = [
    path("common/upload/", UploadView.as_view(), name="common-upload"),
]

"""Common 子应用路由。"""

from django.urls import path

from .views import MapConfigAPIView, UploadView

urlpatterns = [
    path("common/upload/", UploadView.as_view(), name="common-upload"),
    path("common/map-config/", MapConfigAPIView.as_view(), name="common-map-config"),
]

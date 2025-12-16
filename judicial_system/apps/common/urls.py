"""Common 子应用路由。"""

from django.urls import path

from .views import ReverseGeocodeView, UploadView

urlpatterns = [
    path("common/upload/", UploadView.as_view(), name="common-upload"),
    path("common/reverse-geocode/", ReverseGeocodeView.as_view(), name="common-reverse-geocode"),
]


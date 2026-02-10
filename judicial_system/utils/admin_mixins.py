"""
Admin 通用 Mixin

说明：
- DetailButtonMixin: 在列表页第一列添加「详情」按钮，禁用默认字段点击进入详情。
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


class DetailButtonMixin:
    """
    在列表页第一列添加「详情」按钮，禁用默认的字段链接。

    用法：将此 Mixin 放在 ModelAdmin 之前继承即可。
    如果子类已定义 view_detail_action，则不会覆盖。
    """

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        list_display = tuple(list_display)
        if "view_detail_action" not in list_display:
            list_display = ("view_detail_action",) + list_display
        return list_display

    def get_list_display_links(self, request, list_display):
        return None

    @admin.display(description="操作")
    def view_detail_action(self, obj):
        meta = obj._meta
        # 代理模型使用自身的 model_name
        url_name = f"{self.admin_site.name}:{meta.app_label}_{meta.model_name}_change"
        try:
            url = reverse(url_name, args=[obj.pk])
        except Exception:
            return "-"
        return format_html(
            '<a style="display:inline-block;padding:4px 12px;background:#e3f2fd;color:#333;'
            'border-radius:4px;text-decoration:none;font-size:12px;" '
            'href="{}">详情</a>',
            url,
        )

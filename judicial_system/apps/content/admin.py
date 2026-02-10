"""Content 子应用 Admin 配置。"""

from django.contrib import admin

from config.admin_sites import admin_site
from utils.admin_mixins import DetailButtonMixin
from .models import Activity, Article, ArticleViewLog, Category, ContentAttachment, Document, DocumentCategory


class CategoryAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "name", "sort_order", "created_at")
    search_fields = ("name",)
    ordering = ("sort_order", "id")
    list_editable = ("sort_order",)


class ArticleAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "status",
        "sort_order",
        "publisher",
        "published_at",
        "created_at",
    )
    search_fields = ("title",)
    list_filter = ("status", "category")
    autocomplete_fields = ('files', 'category')
    list_editable = ("status","sort_order")
    ordering = ("sort_order","-created_at",)
    readonly_fields = ("publisher",)

    def save_model(self, request, obj, form, change):
        """新增文章时自动设置发布人为当前用户"""
        if not change:  # 新增时
            obj.publisher = request.user
        super().save_model(request, obj, form, change)


class ContentAttachmentAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "file", "created_at")
    search_fields = ("file",)


class ActivityAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "name", "start_time", "registration_start", "registration_end", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("participants",)
    autocomplete_fields = ('files',)


class DocumentCategoryAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "name", "sort_order", "created_at")
    search_fields = ("name",)
    ordering = ("sort_order", "id")
    list_editable = ("sort_order",)


class DocumentAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "name", "category", "file", "created_at")
    search_fields = ("name",)
    list_filter = ("category",)
    autocomplete_fields = ("category",)


class ArticleViewLogAdmin(DetailButtonMixin, admin.ModelAdmin):
    list_display = ("id", "article", "user", "viewed_at")
    search_fields = ("article__title", "user__username", "user__name")
    list_filter = ("viewed_at",)
    autocomplete_fields = ("article", "user")
    ordering = ("-viewed_at", "-id")


# 注册到管理员后台
admin_site.register(Category, CategoryAdmin)
admin_site.register(Article, ArticleAdmin)
admin_site.register(ArticleViewLog, ArticleViewLogAdmin)
admin_site.register(ContentAttachment, ContentAttachmentAdmin)
admin_site.register(Activity, ActivityAdmin)
admin_site.register(Document, DocumentAdmin)
admin_site.register(DocumentCategory, DocumentCategoryAdmin)

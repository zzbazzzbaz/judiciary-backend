"""Content 子应用 Admin 配置。"""

from django.contrib import admin

from config.admin_sites import admin_site
from .models import Activity, Article, Category, ContentAttachment, Document, DocumentCategory


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sort_order", "created_at")
    ordering = ("sort_order", "id")
    list_editable = ("sort_order",)


class ArticleAdmin(admin.ModelAdmin):
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
    autocomplete_fields = ('files',)
    list_editable = ("status","sort_order")
    ordering = ("sort_order","-created_at",)
    readonly_fields = ("publisher",)

    def save_model(self, request, obj, form, change):
        """新增文章时自动设置发布人为当前用户"""
        if not change:  # 新增时
            obj.publisher = request.user
        super().save_model(request, obj, form, change)


class ContentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "created_at")
    search_fields = ("file",)


class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_time", "registration_start", "registration_end", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("participants",)
    autocomplete_fields = ('files',)


class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sort_order", "created_at")
    ordering = ("sort_order", "id")
    list_editable = ("sort_order",)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "file", "created_at")
    search_fields = ("name",)
    list_filter = ("category",)


# 注册到管理员后台
admin_site.register(Category, CategoryAdmin)
admin_site.register(Article, ArticleAdmin)
admin_site.register(ContentAttachment, ContentAttachmentAdmin)
admin_site.register(Activity, ActivityAdmin)
admin_site.register(Document, DocumentAdmin)
admin_site.register(DocumentCategory, DocumentCategoryAdmin)

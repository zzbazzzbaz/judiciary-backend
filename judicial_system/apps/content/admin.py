"""Content 子应用 Admin 配置。"""

from django.contrib import admin

from config.admin_sites import admin_site
from .models import Activity, Article, Category, ContentAttachment, Document


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
    autocomplete_fields = ("publisher",'files')
    ordering = ("-created_at",)


class ContentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "created_at")
    search_fields = ("file",)


class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_time", "registration_start", "registration_end", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("participants",)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "file", "created_at")
    search_fields = ("name",)


# 注册到管理员后台
admin_site.register(Category, CategoryAdmin)
admin_site.register(Article, ArticleAdmin)
admin_site.register(ContentAttachment, ContentAttachmentAdmin)
admin_site.register(Activity, ActivityAdmin)
admin_site.register(Document, DocumentAdmin)

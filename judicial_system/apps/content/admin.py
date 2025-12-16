"""Content 子应用 Admin 配置。"""

from django.contrib import admin

from .models import Activity, Article, Category, ContentAttachment, Document


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sort_order", "created_at")
    ordering = ("sort_order", "id")


@admin.register(Article)
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
    raw_id_fields = ("publisher",)
    ordering = ("-created_at",)


@admin.register(ContentAttachment)
class ContentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "created_at")
    search_fields = ("file",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_time", "registration_start", "registration_end", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("participants",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "file", "created_at")
    search_fields = ("name",)

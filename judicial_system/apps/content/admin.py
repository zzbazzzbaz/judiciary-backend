"""Content 子应用 Admin 配置。"""

from django.contrib import admin

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "is_template", "sort_order", "created_at")
    search_fields = ("code", "name")
    list_filter = ("is_template",)
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

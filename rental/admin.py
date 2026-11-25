from django.contrib import admin

from .models import Category, Rental, Tag, Tool


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "created_by",
        "is_active",
        "daily_rate",
    )
    list_filter = ("category", "is_active", "tags")
    search_fields = (
        "name",
        "description",
        "category__name",
        "created_by__username",
    )
    filter_horizontal = ("tags",)
    list_select_related = ("category", "created_by")


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = (
        "tool",
        "renter",
        "start_date",
        "end_date",
        "actual_return_date",
        "status",
    )
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("tool__name", "renter__username")
    list_select_related = ("tool", "renter")
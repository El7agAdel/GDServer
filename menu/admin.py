from django.contrib import admin
from .models import MenuCategory, MenuItem

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    ordering = ("sort_order", "name")

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price_egp", "is_available", "sort_order")
    list_filter = ("category", "is_available")
    search_fields = ("name",)
    ordering = ("category__sort_order", "sort_order", "name")

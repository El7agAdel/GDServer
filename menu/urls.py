from django.urls import path
from .api import MenuView, MenuItemDetailView

urlpatterns = [
    path("menu/", MenuView.as_view(), name="api_menu"),
    path("menu/items/<int:pk>/", MenuItemDetailView.as_view(), name="api_menu_item_detail"),
]

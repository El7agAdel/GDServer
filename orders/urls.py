from django.urls import path

from .views import OrderListView, OrderStatusUpdateView, PromoCodeDetailView, PromoCodeListView

urlpatterns = [
    path("promo-codes/", PromoCodeListView.as_view(), name="api_promo_codes"),
    path("promo-codes/<int:pk>/", PromoCodeDetailView.as_view(), name="api_promo_code_detail"),
    path("orders/", OrderListView.as_view(), name="api_orders"),
    path("orders/<int:pk>/status/", OrderStatusUpdateView.as_view(), name="api_order_status"),
]

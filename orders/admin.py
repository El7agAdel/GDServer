from decimal import Decimal

from django.contrib import admin

from .models import (
    CustomerProfile,
    Order,
    OrderItem,
    OrderStatusEvent,
    PromoCode,
)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percentage", "is_valid", "times_redeemed", "expires_at")
    list_filter = ("is_valid",)
    search_fields = ("code", "description")
    ordering = ("code",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu_item_name", "unit_price_cents", "quantity")


class OrderStatusEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "changed_at", "note")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "status", "total_display", "created_at", "promo_code")
    list_filter = ("status", "promo_code")
    search_fields = ("id", "customer_name", "customer_phone", "customer_email")
    readonly_fields = (
        "total_display",
        "subtotal_display",
        "tax_display",
        "discount_display",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline, OrderStatusEventInline]
    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "status",
                    "promo_code",
                    "payment_method",
                    "notes",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "Customer",
            {
                "fields": (
                    "customer_name",
                    "customer_phone",
                    "customer_email",
                    "customer_address",
                    "customer_city",
                )
            },
        ),
        (
            "Totals",
            {"fields": ("subtotal_display", "tax_display", "discount_display", "total_display")},
        ),
    )

    def _format_currency(self, amount, is_cents=True):
        if amount in (None, ""):
            value = Decimal("0")
        else:
            value = Decimal(amount)
        if is_cents:
            value = (value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            value = value.quantize(Decimal("0.01"))
        return f"EGP {value:.2f}"

    def total_display(self, obj):
        return self._format_currency(obj.total_cents)

    total_display.short_description = "Total"

    def subtotal_display(self, obj):
        return self._format_currency(obj.subtotal_cents)

    subtotal_display.short_description = "Subtotal"

    def tax_display(self, obj):
        return self._format_currency(obj.tax_cents)

    tax_display.short_description = "Tax"

    def discount_display(self, obj):
        return self._format_currency(obj.discount_egp, is_cents=False)

    discount_display.short_description = "Discount"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "current_order", "current_order_status")
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("order_history",)

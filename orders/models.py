from django.conf import settings
from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=150, blank=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    is_valid = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    times_redeemed = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code


class Order(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # snapshot totals (so history doesn’t change if menu prices change)
    subtotal_cents = models.PositiveIntegerField(default=0)
    tax_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    discount_egp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    promo_code = models.ForeignKey(PromoCode, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    # Optional: pickup name/notes
    customer_name = models.CharField(max_length=80, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_address = models.CharField(max_length=200, blank=True)
    customer_city = models.CharField(max_length=80, blank=True)
    payment_method = models.CharField(max_length=40, blank=True)
    notes = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item_name = models.CharField(max_length=120)   # snapshot
    unit_price_cents = models.PositiveIntegerField()    # snapshot
    quantity = models.PositiveIntegerField(default=1)


class OrderStatusEvent(models.Model):
    """Audit trail for history + debugging + staff accountability."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=300, blank=True)


class CustomerProfile(models.Model):
    class CurrentOrderStatus(models.TextChoices):
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    order_history = models.ManyToManyField(Order, related_name="history_customers", blank=True)
    current_order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="current_customers")
    current_order_status = models.CharField(max_length=20, choices=CurrentOrderStatus.choices, blank=True)

    def __str__(self):
        return f"Profile for {self.user}"

from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusEvent, PromoCode


def to_cents(amount):
    return int((Decimal(amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def cents_to_egp(amount):
    if amount in (None, ""):
        return 0.0
    egp_value = (Decimal(amount) / Decimal("100")).quantize(Decimal("0.01"))
    return float(egp_value)


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            "id",
            "code",
            "description",
            "discount_percentage",
            "is_valid",
            "max_uses",
            "times_redeemed",
            "expires_at",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    price_egp = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item_name", "unit_price_cents", "price_egp", "quantity"]

    def get_price_egp(self, obj):
        return cents_to_egp(obj.unit_price_cents)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    promo_code = PromoCodeSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    subtotal_egp = serializers.SerializerMethodField()
    tax_egp = serializers.SerializerMethodField()
    total_egp = serializers.SerializerMethodField()
    discount_egp = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "status_display",
            "created_at",
            "updated_at",
            "subtotal_cents",
            "tax_cents",
            "total_cents",
            "subtotal_egp",
            "tax_egp",
            "total_egp",
            "discount_egp",
            "customer_name",
            "customer_phone",
            "customer_email",
            "customer_address",
            "customer_city",
            "payment_method",
            "notes",
            "promo_code",
            "items",
        ]

    def get_user(self, obj):
        return str(obj.user) if obj.user else None

    def get_subtotal_egp(self, obj):
        return cents_to_egp(obj.subtotal_cents)

    def get_tax_egp(self, obj):
        return cents_to_egp(obj.tax_cents)

    def get_total_egp(self, obj):
        return cents_to_egp(obj.total_cents)

    def get_discount_egp(self, obj):
        amount = obj.discount_egp or Decimal("0")
        return float(amount.quantize(Decimal("0.01")))


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        if value not in Order.Status.values:
            raise serializers.ValidationError("Invalid order status.")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data["status"]
        old_status = instance.status
        if old_status != new_status:
            instance.status = new_status
            instance.save(update_fields=["status", "updated_at"])
            request = self.context.get("request")
            changed_by = None
            if request is not None and request.user.is_authenticated:
                changed_by = request.user
            OrderStatusEvent.objects.create(
                order=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=changed_by,
            )
        return instance


class OrderItemCreateSerializer(serializers.Serializer):
    item_id = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=120)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Item price must be zero or positive.")
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=4)
    tax = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=0)
    discount = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=0)
    total = serializers.DecimalField(max_digits=12, decimal_places=4)
    status = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = [
            "customer_name",
            "customer_phone",
            "customer_email",
            "customer_address",
            "customer_city",
            "payment_method",
            "notes",
            "promo_code",
            "items",
            "subtotal",
            "tax",
            "discount",
            "total",
            "status",
        ]

    def validate_status(self, value):
        if not value:
            return Order.Status.REQUESTED
        normalized = value.upper()
        if normalized not in Order.Status.values:
            raise serializers.ValidationError("Invalid order status.")
        return normalized

    def validate(self, attrs):
        # ensure totals at least zero
        for field in ["subtotal", "tax", "discount", "total"]:
            amount = attrs.get(field, Decimal("0"))
            if amount < 0:
                raise serializers.ValidationError({field: "Amount must be zero or positive."})
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        promo_code_code = validated_data.pop("promo_code", None)
        subtotal = validated_data.pop("subtotal")
        tax = validated_data.pop("tax", Decimal("0"))
        discount = validated_data.pop("discount", Decimal("0"))
        total = validated_data.pop("total")
        status_value = validated_data.pop("status", Order.Status.REQUESTED)

        promo = None
        if promo_code_code:
            promo = PromoCode.objects.filter(code__iexact=promo_code_code).first()

        order = Order.objects.create(
            subtotal_cents=to_cents(subtotal),
            tax_cents=to_cents(tax),
            discount_egp=Decimal(discount).quantize(Decimal("0.01")),
            total_cents=to_cents(total),
            promo_code=promo,
            status=status_value,
            **validated_data,
        )

        order_items = [
            OrderItem(
                order=order,
                menu_item_name=item["name"],
                unit_price_cents=to_cents(item["price"]),
                quantity=item.get("quantity", 1),
            )
            for item in items_data
        ]
        OrderItem.objects.bulk_create(order_items)
        return order

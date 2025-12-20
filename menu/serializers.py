from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from rest_framework import serializers
from .models import MenuCategory, MenuItem


class MoneyField(serializers.Field):
    """
    Serializes stored integer cents into whole EGP for the API and converts back.
    """

    def to_representation(self, value):
        if value is None:
            return value
        # amount = (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"))
        amount = (Decimal(value)).quantize(Decimal("0.01"))
        if amount == amount.to_integral():
            return int(amount)
        return float(amount)

    def to_internal_value(self, data):
        try:
            decimal_value = Decimal(str(data))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Price must be a numeric value.")
        if decimal_value < 0:
            raise serializers.ValidationError("Price must be zero or positive.")
        # cents = int((decimal_value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        cents = int((decimal_value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return cents

class MenuItemSerializer(serializers.ModelSerializer):
    price_egp = MoneyField()

    class Meta:
        model = MenuItem
        fields = ["id", "name", "description", "price_egp", "is_available", "sort_order"]
        extra_kwargs = {"price_egp": {"required": False}}

class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)  # uses related_name="items"

    class Meta:
        model = MenuCategory
        fields = ["id", "name", "sort_order", "items"]

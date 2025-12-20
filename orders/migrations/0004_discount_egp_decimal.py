from decimal import Decimal

from django.db import migrations, models


def convert_cents_to_egp(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.exclude(discount_egp=None):
        amount = order.discount_egp or 0
        order.discount_egp = (Decimal(amount) / Decimal("100")).quantize(Decimal("0.01"))
        order.save(update_fields=["discount_egp"])


def convert_egp_to_cents(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.exclude(discount_egp=None):
        amount = order.discount_egp or Decimal("0")
        order.discount_egp = (Decimal(amount) * Decimal("100")).quantize(Decimal("1"))
        order.save(update_fields=["discount_egp"])


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_status_requested"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="discount_cents",
            new_name="discount_egp",
        ),
        migrations.AlterField(
            model_name="order",
            name="discount_egp",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(convert_cents_to_egp, convert_egp_to_cents),
    ]


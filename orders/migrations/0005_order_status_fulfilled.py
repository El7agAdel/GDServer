from django.db import migrations, models


def forwards(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    OrderStatusEvent = apps.get_model("orders", "OrderStatusEvent")
    Order.objects.filter(status="OUT").update(status="FULFILLED")
    OrderStatusEvent.objects.filter(from_status="OUT").update(from_status="FULFILLED")
    OrderStatusEvent.objects.filter(to_status="OUT").update(to_status="FULFILLED")


def backwards(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    OrderStatusEvent = apps.get_model("orders", "OrderStatusEvent")
    Order.objects.filter(status="FULFILLED").update(status="OUT")
    OrderStatusEvent.objects.filter(from_status="FULFILLED").update(from_status="OUT")
    OrderStatusEvent.objects.filter(to_status="FULFILLED").update(to_status="OUT")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_discount_egp_decimal"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("REQUESTED", "Requested"),
                    ("PREPARING", "Preparing"),
                    ("READY", "Ready"),
                    ("FULFILLED", "Fulfilled"),
                ],
                default="REQUESTED",
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_order_status_fulfilled"),
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
                    ("CANCELLED", "Cancelled"),
                ],
                default="REQUESTED",
                max_length=20,
            ),
        ),
    ]


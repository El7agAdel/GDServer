from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_extend_order_fields"),
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
                    ("OUT", "Out"),
                ],
                default="REQUESTED",
                max_length=20,
            ),
        ),
    ]


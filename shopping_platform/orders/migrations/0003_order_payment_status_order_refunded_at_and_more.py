# Generated by Django 5.1.6 on 2025-03-06 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("Pending Payment", "Pending Payment"), ("Paid", "Paid")],
                default="Pending Payment",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="refunded_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="return_requested",
            field=models.BooleanField(default=False),
        ),
    ]

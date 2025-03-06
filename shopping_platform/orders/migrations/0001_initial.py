# Generated by Django 5.1.6 on 2025-03-05 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "Pending"),
                            ("Shipped", "Shipped"),
                            ("Delivered", "Delivered"),
                            ("Returned", "Returned"),
                            ("Refunded", "Refunded"),
                        ],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                ("delivery_address", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]

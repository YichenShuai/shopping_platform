# Generated by Django 4.2.16 on 2025-03-17 11:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_address"),
    ]

    operations = [
        migrations.AlterField(
            model_name="address",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="addresses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_buyer",
            field=models.BooleanField(default=False),
        ),
    ]

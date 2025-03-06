from django.db import models
from products.models import Product
from users.models import User

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)  # is the product listed?
    updated_at = models.DateTimeField(auto_now=True) # inventory update time

    def __str__(self):
        return f"Inventory for {self.product.name}"

from django.db import models
from products.models import Product

class SalesStatistic(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='statistics')
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sales stats for {self.product.name}"

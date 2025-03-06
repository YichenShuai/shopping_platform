from django.db import models
from users.models import User
from products.models import Product

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
        ('Refunded', 'Refunded'),
    ], default='Pending')
    payment_status = models.CharField(max_length=20, choices=[
        ('Pending Payment', 'Pending Payment'),
        ('Paid', 'Paid'),
    ], default='Pending Payment')
    delivery_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    return_requested = models.BooleanField(default=False)  # If request a return
    refunded_at = models.DateTimeField(null=True, blank=True)  # return time

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} in Order #{self.order.id}"
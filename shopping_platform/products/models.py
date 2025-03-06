from django.db import models
from users.models import User
from categories.models import Category

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)  # stock
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')  # seller
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)  # category
    rating = models.FloatField(default=0.0)  # average rating
    sales = models.IntegerField(default=0)  # sales volume (used to count hot-selling products)
    created_at = models.DateTimeField(auto_now_add=True) # product creation time

    def __str__(self):
        return self.name

#review (comments/rating)
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField(blank=True)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1-5 star rating
    created_at = models.DateTimeField(auto_now_add=True) # product creation time

    def __str__(self):
        return f"Review for {self.product.name} by {self.buyer.username}"

from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    is_buyer = models.BooleanField(default=True)  # buyer/default
    is_seller = models.BooleanField(default=False)  # seller
    is_admin = models.BooleanField(default=False)  # administration
    email = models.EmailField(unique=True)  # email address (unique)
    phone_number = models.CharField(max_length=15, blank=True)  # phone number (optional)
    date_of_birth = models.DateField(null=True, blank=True)  # date of birth (optional)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # balance

    def __str__(self):
        return self.username

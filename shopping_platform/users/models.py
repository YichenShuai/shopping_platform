from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    is_buyer = models.BooleanField(default=False)  # buyer
    is_seller = models.BooleanField(default=False)  # seller
    is_admin = models.BooleanField(default=False)  # administration
    email = models.EmailField(unique=True)  # email address (unique)
    phone_number = models.CharField(max_length=15, blank=True)  # phone number (optional)
    date_of_birth = models.DateField(null=True, blank=True)  # date of birth (optional)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # balance

    def __str__(self):
        return self.username

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255, verbose_name='Address1')
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name='Address2')
    city = models.CharField(max_length=100, verbose_name='City')
    state = models.CharField(max_length=100, verbose_name='State/Province')
    postal_code = models.CharField(max_length=20, verbose_name='postal code')
    country = models.CharField(max_length=100, verbose_name='Country')
    is_default = models.BooleanField(default=False, verbose_name='Default address')

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.country}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # If set as the default address, cancel the default status of other addresses
            Address.objects.filter(user=self.user).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
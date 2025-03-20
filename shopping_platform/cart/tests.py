# shopping_platform/cart/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Cart
from products.models import Product
from categories.models import Category
from users.models import User
from django.contrib.messages import get_messages

User = get_user_model()

class CartModelTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123',
            is_buyer=True
        )
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="A test product",
            price=10.00,
            stock=100,
            seller=self.seller,
            category=self.category
        )
        self.cart = Cart.objects.create(
            buyer=self.buyer,
            product=self.product,
            quantity=1
        )

    def test_cart_creation(self):
        self.assertEqual(self.cart.buyer, self.buyer)
        self.assertEqual(self.cart.product, self.product)
        self.assertEqual(self.cart.quantity, 1)

    def test_cart_str(self):
        self.assertEqual(str(self.cart), f"{self.buyer.username}'s cart - {self.product.name}")

class CartViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123',
            is_buyer=True
        )
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="A test product",
            price=10.00,
            stock=100,
            seller=self.seller,
            category=self.category
        )

    def test_add_to_cart(self):
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cart.objects.filter(buyer=self.buyer, product=self.product).exists())
        cart_item = Cart.objects.get(buyer=self.buyer, product=self.product)
        self.assertEqual(cart_item.quantity, 1)

    def test_add_to_cart_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(buyer=self.buyer, product=self.product).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Out of stock!")

    def test_add_to_cart_existing_item(self):
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        cart_item = Cart.objects.get(buyer=self.buyer, product=self.product)
        self.assertEqual(cart_item.quantity, 2)

    def test_view_cart(self):
        Cart.objects.create(buyer=self.buyer, product=self.product, quantity=2)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/view_cart.html')
        self.assertContains(response, "Test Product")
        self.assertContains(response, "20.00")

    def test_remove_from_cart(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('remove_from_cart', args=[cart_item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(id=cart_item.id).exists())

    def test_update_cart_valid_quantity(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('update_cart', args=[cart_item.id]), {
            'quantity': '3'
        })
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)

    def test_update_cart_insufficient_stock(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.product.stock = 2
        self.product.save()
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('update_cart', args=[cart_item.id]), {
            'quantity': '5'
        })
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f"Insufficient stock for {self.product.name}! Only {self.product.stock} left.")

    def test_update_cart_invalid_quantity(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('update_cart', args=[cart_item.id]), {
            'quantity': '0'
        })
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Quantity must be greater than 0!")

    def test_update_cart_non_numeric_quantity(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('update_cart', args=[cart_item.id]), {
            'quantity': 'abc'
        })
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid quantity!")

    def test_update_cart_missing_quantity(self):
        cart_item = Cart.objects.create(buyer=self.buyer, product=self.product, quantity=1)
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('update_cart', args=[cart_item.id]), {})
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Quantity is required!")
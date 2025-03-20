# shopping_platform/orders/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Order, OrderItem
from cart.models import Cart
from products.models import Product
from categories.models import Category
from users.models import User, Address
from django.utils import timezone
import stripe
from django.conf import settings

User = get_user_model()

class OrderModelTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123',
            is_buyer=True,
            balance=100.00
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            total_amount=50.00,
            delivery_address="123 Main St, City, Country",
            status='Pending',
            payment_status='Pending Payment'
        )

    def test_order_creation(self):
        self.assertEqual(self.order.buyer, self.buyer)
        self.assertEqual(self.order.total_amount, 50.00)
        self.assertEqual(self.order.status, 'Pending')
        self.assertEqual(self.order.payment_status, 'Pending Payment')

    def test_order_str(self):
        self.assertEqual(str(self.order), f"Order #{self.order.id} by {self.buyer.username}")

class OrderItemModelTests(TestCase):
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
        self.order = Order.objects.create(
            buyer=self.buyer,
            total_amount=10.00,
            delivery_address="123 Main St, City, Country",
            status='Pending',
            payment_status='Pending Payment'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=10.00
        )

    def test_order_item_creation(self):
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.quantity, 1)
        self.assertEqual(self.order_item.price, 10.00)

    def test_order_item_str(self):
        self.assertEqual(str(self.order_item), f"{self.product.name} in Order #{self.order.id}")

class OrderViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.buyer = User.objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='testpass123',
            is_buyer=True,
            balance=100.00
        )
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='testpass123',
            is_seller=True,
            balance=0.00
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
        self.address = Address.objects.create(
            user=self.buyer,
            address_line1="123 Main St",
            city="City",
            state="State",
            postal_code="12345",
            country="Country",
            is_default=True
        )
        self.cart_item = Cart.objects.create(
            buyer=self.buyer,
            product=self.product,
            quantity=2
        )

    def test_checkout_view_get(self):
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')
        self.assertContains(response, "Test Product")

    def test_checkout_view_post_balance_payment(self):
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('checkout'), {
            'selected_items': [self.cart_item.id],
            'address_mode': 'single',
            'delivery_address': self.address.id,
            'payment_method': 'balance',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(buyer=self.buyer).exists())
        self.buyer.refresh_from_db()
        self.seller.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.buyer.balance, 80.00)
        self.assertEqual(self.seller.balance, 20.00)
        self.assertEqual(self.product.stock, 98)
        self.assertFalse(Cart.objects.filter(buyer=self.buyer).exists())

    def test_checkout_view_post_insufficient_balance(self):
        self.buyer.balance = 10.00
        self.buyer.save()
        self.client.login(username='buyer', password='testpass123')
        response = self.client.post(reverse('checkout'), {
            'selected_items': [self.cart_item.id],
            'address_mode': 'single',
            'delivery_address': self.address.id,
            'payment_method': 'balance',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Insufficient balance, please recharge!")
        self.assertFalse(Order.objects.filter(buyer=self.buyer).exists())


    def test_seller_orders_view(self):
        self.client.login(username='seller', password='testpass123')
        order = Order.objects.create(
            buyer=self.buyer,
            total_amount=20.00,
            delivery_address="123 Main St, City, Country",
            status='Pending',
            payment_status='Paid'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=10.00
        )
        response = self.client.get(reverse('seller_orders'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/seller_orders.html')
        self.assertContains(response, "Order #")

    def test_ship_order(self):
        self.client.login(username='seller', password='testpass123')
        order = Order.objects.create(
            buyer=self.buyer,
            total_amount=20.00,
            delivery_address="123 Main St, City, Country",
            status='Pending',
            payment_status='Paid'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=10.00
        )
        response = self.client.get(reverse('ship_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Shipped')
        self.assertIsNotNone(order.shipped_at)

    def test_request_return(self):
        self.client.login(username='buyer', password='testpass123')
        order = Order.objects.create(
            buyer=self.buyer,
            total_amount=20.00,
            delivery_address="123 Main St, City, Country",
            status='Shipped',
            payment_status='Paid'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=10.00
        )
        response = self.client.get(reverse('request_return', args=[order.id]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertTrue(order.return_requested)
        self.assertEqual(order.status, 'Returned')

    def test_process_return(self):
        self.client.login(username='seller', password='testpass123')
        order = Order.objects.create(
            buyer=self.buyer,
            total_amount=20.00,
            delivery_address="123 Main St, City, Country",
            status='Returned',
            payment_status='Paid',
            return_requested=True
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=10.00
        )
        response = self.client.get(reverse('process_return', args=[order.id]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.buyer.refresh_from_db()
        self.seller.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, 'Refunded')
        self.assertIsNotNone(order.refunded_at)
        self.assertEqual(self.buyer.balance, 120.00)
        self.assertEqual(self.seller.balance, -20.00)
        self.assertEqual(self.product.stock, 102)
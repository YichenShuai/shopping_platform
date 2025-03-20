# shopping_platform/analytics/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import SalesStatistic
from products.models import Product
from categories.models import Category
from users.models import User
from orders.models import Order, OrderItem
import datetime
from django.utils import timezone
from io import BytesIO
import csv
import base64
from reportlab.pdfgen import canvas

User = get_user_model()

class SalesStatisticModelTests(TestCase):
    def setUp(self):
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
        self.statistic = SalesStatistic.objects.create(
            product=self.product,
            total_sales=50,
            total_revenue=500.00
        )

    def test_sales_statistic_creation(self):
        self.assertEqual(self.statistic.product, self.product)
        self.assertEqual(self.statistic.total_sales, 50)
        self.assertEqual(self.statistic.total_revenue, 500.00)

    def test_sales_statistic_str(self):
        self.assertEqual(str(self.statistic), f"Sales stats for {self.product.name}")

class AnalyticsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_admin=True
        )
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
            total_amount=20.00,
            delivery_address="123 Main St, City, Country",
            status='Pending',
            payment_status='Paid',
            created_at=timezone.now()
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=10.00
        )

    def test_statistics_view_get_admin(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/statistics.html')
        self.assertEqual(response.context['total_sales'], 20.00)
        self.assertEqual(response.context['order_count'], 1)
        self.assertIn(self.product, response.context['top_products'])

    def test_statistics_view_get_non_admin(self):
        self.client.login(username='buyer', password='testpass123')
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Only admins can view statistics")

    def test_statistics_view_time_range_day(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('statistics'), {'time_range': 'day'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['time_range'], 'day')
        self.assertEqual(response.context['total_sales'], 20.00)

    def test_statistics_view_time_range_week(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('statistics'), {'time_range': 'week'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['time_range'], 'week')
        self.assertEqual(response.context['total_sales'], 20.00)

    def test_statistics_view_time_range_month(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('statistics'), {'time_range': 'month'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['time_range'], 'month')
        self.assertEqual(response.context['total_sales'], 20.00)

    def test_statistics_view_time_range_year(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('statistics'), {'time_range': 'year'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['time_range'], 'year')
        self.assertEqual(response.context['total_sales'], 20.00)

    def test_statistics_view_export_pdf(self):
        self.client.login(username='admin', password='testpass123')
        chart_image_data = base64.b64encode(b"fake_image_data").decode('utf-8')
        response = self.client.post(reverse('statistics'), {
            'time_range': 'all',
            'chart_type': 'line',
            'export': 'pdf',
            'chart_image': f"data:image/png;base64,{chart_image_data}"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="sales_statistics.pdf"')

    def test_statistics_view_export_csv(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('statistics'), {
            'time_range': 'all',
            'chart_type': 'line',
            'export': 'csv'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="sales_statistics.csv"')
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(content.splitlines())
        rows = list(csv_reader)
        self.assertEqual(rows[0], ['Sales Statistics Report'])
        self.assertEqual(rows[2], ['Total Sales', '$20.00'])
        self.assertEqual(rows[3], ['Total Orders', '1'])
# shopping_platform/products/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Product, ProductImage, Review
from categories.models import Category
from PIL import Image
import io

User = get_user_model()

class ProductModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller1',
            email='seller1@example.com',
            password='testpass123',
            is_seller=True
        )
        self.buyer = User.objects.create_user(
            username='buyer1',
            email='buyer1@example.com',
            password='testpass123',
            is_buyer=True
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="A test product",
            price=99.99,
            stock=10,
            seller=self.seller,
            category=self.category
        )

    def test_update_rating_with_reviews(self):
        Review.objects.create(
            product=self.product,
            buyer=self.buyer,
            comment="Great product!",
            rating=4
        )
        Review.objects.create(
            product=self.product,
            buyer=self.buyer,
            comment="Awesome!",
            rating=5
        )
        self.product.update_rating()
        self.assertEqual(self.product.rating, 4.5)

    def test_update_rating_no_reviews(self):
        self.product.update_rating()
        self.assertEqual(self.product.rating, 0.0)

class ProductImageModelTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller2',
            email='seller2@example.com',
            password='testpass123',
            is_seller=True
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="A test product",
            price=99.99,
            stock=10,
            seller=self.seller,
            category=self.category
        )

    def test_product_image_creation(self):
        image = Image.new('RGB', (100, 100), color='red')
        output = io.BytesIO()
        image.save(output, format='JPEG')
        image_file = SimpleUploadedFile(
            "test_image.jpg", output.getvalue(), content_type="image/jpeg"
        )
        product_image = ProductImage.objects.create(
            product=self.product,
            image=image_file
        )
        self.assertTrue(product_image.image)

class ProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(
            username='seller3',
            email='seller3@example.com',
            password='testpass123',
            is_seller=True
        )
        self.buyer = User.objects.create_user(
            username='buyer2',
            email='buyer2@example.com',
            password='testpass123',
            is_buyer=True
        )
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            description="A test product",
            price=99.99,
            stock=10,
            seller=self.seller,
            category=self.category,
            is_active=True
        )

    def test_product_list_view(self):
        url = reverse('product_list')
        print(f"Testing product_list URL: {url}")
        response = self.client.get(url)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content[:500]}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertTemplateUsed(response, 'products/product_list.html')

    def test_product_list_with_query(self):
        url = reverse('product_list')
        print(f"Testing product_list with query URL: {url}?q=Test")
        response = self.client.get(url, {'q': 'Test'})
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content[:500]}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")

        response = self.client.get(url, {'q': 'Nonexistent'})
        print(f"Response status code (nonexistent): {response.status_code}")
        print(f"Response content (nonexistent): {response.content[:500]}")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Product")

    def test_product_detail_view(self):
        url = reverse('product_detail', args=[self.product.id])
        print(f"Testing product_detail URL: {url}")
        response = self.client.get(url)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content[:500]}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertTemplateUsed(response, 'products/product_detail.html')

    def test_create_product_view_get(self):
        self.client.login(username='seller3', password='testpass123')
        url = reverse('create_product')
        print(f"Testing create_product GET URL: {url}")
        response = self.client.get(url)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content[:500]}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/create_product.html')

    def test_create_product_view_post(self):
        self.client.login(username='seller3', password='testpass123')
        url = reverse('create_product')
        print(f"Testing create_product POST URL: {url}")
        response = self.client.post(url, {
            'name': 'New Product',
            'description': 'A new product',
            'price': '49.99',
            'stock': '5',
            'category': self.category.id,
        })
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content[:500]}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(name="New Product").exists())
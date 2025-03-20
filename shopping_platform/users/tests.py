# shopping_platform/users/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model, authenticate
from .models import User, Address
from django.core import mail

User = get_user_model()

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            is_buyer=True
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertTrue(self.user.is_buyer)
        self.assertFalse(self.user.is_seller)
        self.assertFalse(self.user.is_admin)
        self.assertEqual(self.user.balance, 0.00)

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')

class AddressModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.address1 = Address.objects.create(
            user=self.user,
            address_line1="123 Main St",
            city="City",
            state="State",
            postal_code="12345",
            country="Country",
            is_default=True
        )

    def test_address_creation(self):
        self.assertEqual(self.address1.address_line1, "123 Main St")
        self.assertEqual(self.address1.city, "City")
        self.assertTrue(self.address1.is_default)

    def test_address_default_logic(self):
        address2 = Address.objects.create(
            user=self.user,
            address_line1="456 Oak St",
            city="City",
            state="State",
            postal_code="67890",
            country="Country",
            is_default=True
        )
        self.address1.refresh_from_db()
        self.assertFalse(self.address1.is_default)
        self.assertTrue(address2.is_default)

    def test_address_str(self):
        self.assertEqual(str(self.address1), "123 Main St, City, Country")

class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            is_buyer=True
        )

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')


    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login_view_post_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_view_post_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertContains(response, "Wrong username or password")

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_myaccount_view_get(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('myaccount'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/myaccount.html')

    def test_myaccount_add_address(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('myaccount'), {
            'add_address': True,
            'address_line1': '789 Pine St',
            'city': 'City',
            'state': 'State',
            'postal_code': '54321',
            'country': 'Country',
            'is_default': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Address.objects.filter(address_line1='789 Pine St').exists())


    def test_myaccount_change_password(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('myaccount'), {
            'change_password': True,
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)
        user = authenticate(username='testuser', password='newpass123')
        self.assertIsNotNone(user)

    def test_password_reset_request(self):
        response = self.client.post(reverse('password_reset'), {
            'email': 'testuser@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Verification Code', mail.outbox[0].subject)

    def test_password_reset_confirm(self):
        self.client.post(reverse('password_reset'), {
            'email': 'testuser@example.com',
        })
        verification_code = mail.outbox[0].body.split('Your verification code is: ')[1].strip()
        response = self.client.post(reverse('password_reset_confirm'), {
            'code': verification_code,
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)  # 重定向到 login
        user = authenticate(username='testuser', password='newpass123')
        self.assertIsNotNone(user)
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def create_user_url():
    return reverse("user:create")


def manage_user_url():
    return reverse("user:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@Example.com", "Test2@example.com"),
            ("TEST3@EXAMPLE.com", "TEST3@example.com"),
            ("test4@example.COM", "test4@example.com"),
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "testpass123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class PublicUserApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [],
            "DEFAULT_THROTTLE_RATES": {},
        }
    )
    def test_create_user_success(self):
        cache.clear()
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
        }

        res = self.client.post(create_user_url(), payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertEqual(user.first_name, payload["first_name"])
        self.assertEqual(user.last_name, payload["last_name"])
        self.assertNotIn("password", res.data)

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [],
            "DEFAULT_THROTTLE_RATES": {},
        }
    )
    def test_user_with_existing_email_not_created(self):
        cache.clear()
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
        }
        create_user(**payload)

        res = self.client.post(create_user_url(), payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [],
            "DEFAULT_THROTTLE_RATES": {},
        }
    )
    def test_password_too_short_returns_error(self):
        cache.clear()
        payload = {
            "email": "test@example.com",
            "password": "pw",
            "first_name": "John",
            "last_name": "Doe",
        }

        res = self.client.post(create_user_url(), payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().objects.filter(email=payload["email"]).exists()
        )

    def tearDown(self):
        cache.clear()


class PrivateUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(manage_user_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertEqual(res.data["first_name"], self.user.first_name)
        self.assertEqual(res.data["last_name"], self.user.last_name)

    def test_post_not_allowed_on_me(self):
        res = self.client.post(manage_user_url(), {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {
            "first_name": "Updated",
            "last_name": "User",
            "password": "newpass123",
        }

        res = self.client.patch(manage_user_url(), payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, payload["first_name"])
        self.assertEqual(self.user.last_name, payload["last_name"])
        self.assertTrue(self.user.check_password(payload["password"]))

    def test_auth_required_for_me_endpoint(self):
        self.client.force_authenticate(user=None)

        res = self.client.get(manage_user_url())

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

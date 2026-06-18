from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor, Genre, TheatreHall


GENRES_URL = reverse("theatre:genre-list")
ACTORS_URL = reverse("theatre:actor-list")
THEATRE_HALLS_URL = reverse("theatre:theatrehall-list")


class PublicPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_anonymous_can_list_genres(self):
        Genre.objects.create(name="Drama")

        res = self.client.get(GENRES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)

    def test_anonymous_can_list_actors(self):
        Actor.objects.create(first_name="Tom", last_name="Hardy")

        res = self.client.get(ACTORS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)

    def test_anonymous_can_list_theatre_halls(self):
        TheatreHall.objects.create(name="Main Hall", rows=10, seats_in_row=20)

        res = self.client.get(THEATRE_HALLS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)

    def test_anonymous_cannot_create_genre(self):
        res = self.client.post(GENRES_URL, {"name": "Comedy"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_regular_user_cannot_create_genre(self):
        res = self.client.post(GENRES_URL, {"name": "Comedy"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_actor(self):
        res = self.client.post(
            ACTORS_URL,
            {"first_name": "Emma", "last_name": "Stone"}
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_theatre_hall(self):
        res = self.client.post(
            THEATRE_HALLS_URL,
            {"name": "Small Hall", "rows": 5, "seats_in_row": 5}
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        self.client.force_authenticate(self.admin)

    def test_admin_can_create_genre(self):
        res = self.client.post(GENRES_URL, {"name": "Comedy"})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name="Comedy").exists())

    def test_admin_can_create_actor(self):
        res = self.client.post(
            ACTORS_URL,
            {"first_name": "Emma", "last_name": "Stone"}
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Actor.objects.filter(first_name="Emma").exists())

    def test_admin_can_create_theatre_hall(self):
        res = self.client.post(
            THEATRE_HALLS_URL,
            {"name": "Small Hall", "rows": 5, "seats_in_row": 5}
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TheatreHall.objects.filter(name="Small Hall").exists())

from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Performance, Play, Reservation, TheatreHall, Ticket


RESERVATIONS_URL = reverse("theatre:reservation-list")


def detail_url(reservation_id):
    return reverse("theatre:reservation-detail", args=[reservation_id])


def sample_hall(name="Main Hall", rows=10, seats_in_row=20):
    return TheatreHall.objects.create(
        name=name,
        rows=rows,
        seats_in_row=seats_in_row,
    )


def sample_play(title="Hamlet"):
    return Play.objects.create(title=title, description="Description")


def sample_performance():
    return Performance.objects.create(
        play=sample_play(),
        theatre_hall=sample_hall(),
        show_time=timezone.make_aware(datetime(2026, 6, 20, 18, 0)),
    )


class UnauthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_for_reservation_list(self):
        res = self.client.get(RESERVATIONS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_list_reservations_only_for_authenticated_user(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="testpass123",
        )

        Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=other_user)

        res = self.client.get(RESERVATIONS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)

    def test_retrieve_own_reservation(self):
        reservation = Reservation.objects.create(user=self.user)

        res = self.client.get(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], reservation.id)

    def test_cannot_retrieve_other_user_reservation(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="testpass123",
        )
        reservation = Reservation.objects.create(user=other_user)

        res = self.client.get(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reservation_with_tickets(self):
        performance = sample_performance()
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATIONS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.user, self.user)

    def test_create_reservation_fails_with_duplicate_tickets_in_payload(self):
        performance = sample_performance()
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 1, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATIONS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_fails_when_ticket_already_booked(self):
        performance = sample_performance()
        old_reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=old_reservation,
        )

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATIONS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_fails_for_invalid_row(self):
        performance = sample_performance()
        payload = {
            "tickets": [
                {"row": 100, "seat": 1, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATIONS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_fails_for_invalid_seat(self):
        performance = sample_performance()
        payload = {
            "tickets": [
                {"row": 1, "seat": 100, "performance": performance.id},
            ]
        }

        res = self.client.post(RESERVATIONS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

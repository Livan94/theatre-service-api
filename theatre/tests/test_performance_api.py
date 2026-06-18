from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Performance, Play, TheatreHall, Reservation, Ticket


PERFORMANCES_URL = reverse("theatre:performance-list")


def detail_url(performance_id):
    return reverse("theatre:performance-detail", args=[performance_id])


def sample_hall(name="Main Hall", rows=10, seats_in_row=20):
    return TheatreHall.objects.create(
        name=name,
        rows=rows,
        seats_in_row=seats_in_row,
    )


def sample_play(title="Hamlet"):
    return Play.objects.create(title=title, description="Description")


def sample_performance(play=None, theatre_hall=None, show_time=None):
    if play is None:
        play = sample_play()
    if theatre_hall is None:
        theatre_hall = sample_hall()
    if show_time is None:
        show_time = timezone.make_aware(datetime(2026, 6, 20, 18, 0))

    return Performance.objects.create(
        play=play,
        theatre_hall=theatre_hall,
        show_time=show_time,
    )


class PublicPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_performances(self):
        sample_performance()
        sample_performance(
            play=sample_play(title="Macbeth"),
            theatre_hall=sample_hall(name="Red Hall"),
            show_time=timezone.make_aware(datetime(2026, 6, 21, 19, 0)),
        )

        res = self.client.get(PERFORMANCES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_performances_by_play(self):
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Macbeth")
        perf1 = sample_performance(play=play1)
        perf2 = sample_performance(
            play=play2,
            theatre_hall=sample_hall(name="Red Hall"),
            show_time=timezone.make_aware(datetime(2026, 6, 21, 19, 0)),
        )

        res = self.client.get(PERFORMANCES_URL, {"play": play1.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(perf1.id, ids)
        self.assertNotIn(perf2.id, ids)

    def test_filter_performances_by_theatre_hall(self):
        hall1 = sample_hall(name="Blue Hall")
        hall2 = sample_hall(name="Yellow Hall")
        perf1 = sample_performance(theatre_hall=hall1)
        perf2 = sample_performance(
            theatre_hall=hall2,
            play=sample_play(title="Macbeth"),
            show_time=timezone.make_aware(datetime(2026, 6, 21, 19, 0)),
        )

        res = self.client.get(PERFORMANCES_URL, {"theatre_hall": hall1.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(perf1.id, ids)
        self.assertNotIn(perf2.id, ids)

    def test_order_performances_by_show_time_desc(self):
        perf1 = sample_performance(
            show_time=timezone.make_aware(datetime(2026, 6, 20, 18, 0))
        )
        perf2 = sample_performance(
            play=sample_play(title="Macbeth"),
            theatre_hall=sample_hall(name="Red Hall"),
            show_time=timezone.make_aware(datetime(2026, 6, 21, 18, 0)),
        )

        res = self.client.get(PERFORMANCES_URL, {"ordering": "-show_time"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in res.data["results"]]
        self.assertEqual(ids, [perf2.id, perf1.id])

    def test_retrieve_performance_detail_with_tickets_available(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        hall = sample_hall(rows=5, seats_in_row=5)
        performance = sample_performance(theatre_hall=hall)
        reservation = Reservation.objects.create(user=user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=reservation,
        )

        res = self.client.get(detail_url(performance.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["tickets_available"], 24)

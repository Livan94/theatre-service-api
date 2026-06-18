from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)


class ModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        self.hall = TheatreHall.objects.create(
            name="Blue Hall",
            rows=10,
            seats_in_row=20,
        )
        self.play = Play.objects.create(
            title="Hamlet",
            description="Classic tragedy",
        )
        self.performance = Performance.objects.create(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.make_aware(datetime(2026, 6, 20, 18, 0)),
        )
        self.reservation = Reservation.objects.create(user=self.user)

    def test_actor_str(self):
        actor = Actor.objects.create(first_name="Tom", last_name="Hardy")
        self.assertEqual(str(actor), "Tom Hardy")

    def test_genre_str(self):
        genre = Genre.objects.create(name="Drama")
        self.assertEqual(str(genre), "Drama")

    def test_play_str(self):
        self.assertEqual(str(self.play), "Hamlet")

    def test_theatre_hall_str(self):
        self.assertEqual(str(self.hall), "Blue Hall")

    def test_theatre_hall_capacity(self):
        self.assertEqual(self.hall.capacity, 200)

    def test_reservation_str_returns_created_at(self):
        reservation = Reservation.objects.create(user=self.user)
        self.assertEqual(str(reservation), str(reservation.created_at))

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            row=1,
            seat=2,
            performance=self.performance,
            reservation=self.reservation,
        )
        self.assertIn("row: 1", str(ticket))
        self.assertIn("seat: 2", str(ticket))

    def test_ticket_clean_fails_for_row_less_than_one(self):
        ticket = Ticket(
            row=0,
            seat=1,
            performance=self.performance,
            reservation=self.reservation,
        )

        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_ticket_clean_fails_for_seat_less_than_one(self):
        ticket = Ticket(
            row=1,
            seat=0,
            performance=self.performance,
            reservation=self.reservation,
        )

        with self.assertRaises(ValidationError):
            ticket.full_clean()

    def test_ticket_clean_fails_for_row_greater_than_hall_rows(self):
        ticket = Ticket(
            row=11,
            seat=1,
            performance=self.performance,
            reservation=self.reservation,
        )

        with self.assertRaises(ValidationError) as cm:
            ticket.full_clean()

        self.assertIn("row", cm.exception.message_dict)

    def test_ticket_clean_fails_for_seat_greater_than_hall_seats_in_row(self):
        ticket = Ticket(
            row=1,
            seat=21,
            performance=self.performance,
            reservation=self.reservation,
        )

        with self.assertRaises(ValidationError) as cm:
            ticket.full_clean()

        self.assertIn("seat", cm.exception.message_dict)

    def test_ticket_save_calls_full_clean_and_saves_valid_ticket(self):
        ticket = Ticket.objects.create(
            row=3,
            seat=5,
            performance=self.performance,
            reservation=self.reservation,
        )

        self.assertEqual(ticket.row, 3)
        self.assertEqual(ticket.seat, 5)

    def test_ticket_unique_constraint_for_same_performance_row_seat(self):
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=self.performance,
            reservation=self.reservation,
        )

        second_reservation = Reservation.objects.create(user=self.user)

        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat=1,
                performance=self.performance,
                reservation=second_reservation,
            )

    def test_performance_unique_constraint_for_hall_and_show_time(self):
        with self.assertRaises(IntegrityError):
            Performance.objects.create(
                play=self.play,
                theatre_hall=self.hall,
                show_time=self.performance.show_time,
            )

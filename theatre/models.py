import pathlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TheatreHall(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rows = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    seats_in_row = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def capacity(self):
        return self.rows * self.seats_in_row


def play_image_file_path(instance: "Play", filename: str) -> pathlib.Path:
    file_name = (
        f"{slugify(instance.title)}-{uuid.uuid4()}"
        f"{pathlib.Path(filename).suffix}"
    )
    return pathlib.Path("uploads/plays/") / file_name


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField(Actor, related_name="plays")
    genres = models.ManyToManyField(Genre, related_name="plays")
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=play_image_file_path
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Performance(models.Model):
    play = models.ForeignKey(
        Play,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    theatre_hall = models.ForeignKey(
        TheatreHall,
        on_delete=models.CASCADE,
        related_name="performances"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["show_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["theatre_hall", "show_time"],
                name="unique_hall_show_time"
            )
        ]


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    performance = models.ForeignKey(
        Performance,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_ticket_for_performance"
            )
        ]
        ordering = ["row", "seat"]

    def __str__(self):
        return f"{self.performance} (row: {self.row}, seat: {self.seat})"

    def clean(self):
        if self.row < 1 or self.seat < 1:
            raise ValidationError("Row and seat must be greater than 0.")

        if self.performance:
            hall = self.performance.theatre_hall
            if self.row > hall.rows:
                raise ValidationError(
                    {
                        "row": f"Row number must be in available range: 1 to "
                               f"{hall.rows}"
                    }
                )
            if self.seat > hall.seats_in_row:
                raise ValidationError(
                    {
                        "seat": (
                            f"Seat number must be in available range: "
                            f"1 to {hall.seats_in_row}"
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

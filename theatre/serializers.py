from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Ticket,
    Reservation
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class TheatreHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PlayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "title")

class PlayImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "image")


class PlayDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "genres", "actors", "image")


class PlaySerializer(serializers.ModelSerializer):
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        source="genres"
    )
    actor_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Actor.objects.all(),
        source="actors"
    )

    class Meta:
        model = Play
        fields = ("id", "title", "description", "genre_ids", "actor_ids", "image")


class PlayTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ("id", "title")



class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    theatre_hall_capacity = serializers.IntegerField(source="theatre_hall.capacity", read_only=True)

    class Meta:
        model = Performance
        fields = (
            "id",
            "play_title",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "show_time",
        )


class PerformanceDetailSerializer(serializers.ModelSerializer):
    play = PlayTitleSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(read_only=True)
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = Performance
        fields = (
            "id",
            "play",
            "theatre_hall",
            "show_time",
            "tickets_available",
        )

    def get_tickets_available(self, obj):
        return obj.theatre_hall.capacity - obj.tickets.count()


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(read_only=True)


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat", "performance")

    def validate(self, attrs):
        row = attrs["row"]
        seat = attrs["seat"]
        performance = attrs["performance"]
        theatre_hall = performance.theatre_hall

        if row < 1 or row > theatre_hall.rows:
            raise serializers.ValidationError(
                {
                    "row": (
                        f"Row number must be in available range: "
                        f"1 to {theatre_hall.rows}"
                    )
                }
            )

        if seat < 1 or seat > theatre_hall.seats_in_row:
            raise serializers.ValidationError(
                {
                    "seat": (
                        f"Seat number must be in available range: "
                        f"1 to {theatre_hall.seats_in_row}"
                    )
                }
            )

        if Ticket.objects.filter(
            performance=performance,
            row=row,
            seat=seat,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "This ticket has already been booked."
                    ]
                }
            )

        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")


class ReservationListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")


class ReservationCreateSerializer(serializers.ModelSerializer):
    tickets = TicketCreateSerializer(many=True, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "tickets")

    def validate_tickets(self, value):
        taken_places = set()

        for ticket in value:
            place = (ticket["performance"].id, ticket["row"], ticket["seat"])

            if place in taken_places:
                raise serializers.ValidationError(
                    "Tickets must be unique for the same performance, row, and seat."
                )

            taken_places.add(place)

        return value

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        reservation = Reservation.objects.create(user=self.context["request"].user)

        for ticket_data in tickets_data:
            Ticket.objects.create(reservation=reservation, **ticket_data)

        return reservation

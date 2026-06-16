from django.contrib import admin

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name")
    search_fields = ("first_name", "last_name")


@admin.register(TheatreHall)
class TheatreHallAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "rows", "seats_in_row", "capacity")
    search_fields = ("name",)


@admin.register(Play)
class PlayAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title",)
    filter_horizontal = ("genres", "actors")


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("id", "play", "theatre_hall", "show_time")
    list_filter = ("theatre_hall", "show_time")
    search_fields = ("play__title", "theatre_hall__name")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "user")
    list_filter = ("created_at",)
    search_fields = ("user__username",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "performance", "reservation", "row", "seat")
    list_filter = ("performance",)
    search_fields = ("performance__play__title",)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall
)
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlayDetailSerializer,
    PlayListSerializer,
    PlaySerializer,
    TheatreHallSerializer,
    PerformanceDetailSerializer,
    PerformanceListSerializer,
    PerformanceSerializer,
    ReservationCreateSerializer,
    ReservationListSerializer,
    ReservationSerializer,
    PlayImageSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]

class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAdminOrReadOnly]

class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = [IsAdminOrReadOnly]

class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["genres", "actors"]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        if self.action == "upload_image":
            return PlayImageSerializer

        return PlaySerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related(
        "play", "theatre_hall"
    ).prefetch_related("tickets")
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["play", "theatre_hall"]
    ordering_fields = ["show_time"]
    ordering = ["show_time"]

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer

        if self.action == "retrieve":
            return PerformanceDetailSerializer

        return PerformanceSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "tickets__performance__play",
            "tickets__performance__theatre_hall",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        if self.action == "retrieve":
            return ReservationSerializer

        return ReservationCreateSerializer

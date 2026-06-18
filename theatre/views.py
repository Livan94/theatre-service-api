from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import permissions, serializers, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
)
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PerformanceDetailSerializer,
    PerformanceListSerializer,
    PerformanceSerializer,
    PlayDetailSerializer,
    PlayImageSerializer,
    PlayListSerializer,
    PlaySerializer,
    ReservationCreateSerializer,
    ReservationListSerializer,
    ReservationSerializer,
    TheatreHallSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List genres",
        description="Retrieve a list of theatre genres.",
        tags=["Theatre"],
    ),
    retrieve=extend_schema(
        summary="Retrieve genre",
        description="Retrieve detailed information about a genre.",
        tags=["Theatre"],
    ),
    create=extend_schema(
        summary="Create genre",
        description="Create a new genre. Admin only.",
        tags=["Theatre"],
    ),
    update=extend_schema(
        summary="Update genre",
        description="Fully update a genre. Admin only.",
        tags=["Theatre"],
    ),
    partial_update=extend_schema(
        summary="Partially update genre",
        description="Partially update a genre. Admin only.",
        tags=["Theatre"],
    ),
    destroy=extend_schema(
        summary="Delete genre",
        description="Delete a genre. Admin only.",
        tags=["Theatre"],
    ),
)
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        summary="List actors",
        description="Retrieve a list of actors.",
        tags=["Theatre"],
    ),
    retrieve=extend_schema(
        summary="Retrieve actor",
        description="Retrieve detailed information about an actor.",
        tags=["Theatre"],
    ),
    create=extend_schema(
        summary="Create actor",
        description="Create a new actor. Admin only.",
        tags=["Theatre"],
    ),
    update=extend_schema(
        summary="Update actor",
        description="Fully update an actor. Admin only.",
        tags=["Theatre"],
    ),
    partial_update=extend_schema(
        summary="Partially update actor",
        description="Partially update an actor. Admin only.",
        tags=["Theatre"],
    ),
    destroy=extend_schema(
        summary="Delete actor",
        description="Delete an actor. Admin only.",
        tags=["Theatre"],
    ),
)
class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        summary="List theatre halls",
        description="Retrieve a list of theatre halls.",
        tags=["Theatre"],
    ),
    retrieve=extend_schema(
        summary="Retrieve theatre hall",
        description="Retrieve detailed information about a theatre hall.",
        tags=["Theatre"],
    ),
    create=extend_schema(
        summary="Create theatre hall",
        description="Create a new theatre hall. Admin only.",
        tags=["Theatre"],
    ),
    update=extend_schema(
        summary="Update theatre hall",
        description="Fully update a theatre hall. Admin only.",
        tags=["Theatre"],
    ),
    partial_update=extend_schema(
        summary="Partially update theatre hall",
        description="Partially update a theatre hall. Admin only.",
        tags=["Theatre"],
    ),
    destroy=extend_schema(
        summary="Delete theatre hall",
        description="Delete a theatre hall. Admin only.",
        tags=["Theatre"],
    ),
)
class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        summary="List plays",
        description="Retrieve a list of plays "
                    "with optional filtering and search.",
        tags=["Theatre"],
        parameters=[
            OpenApiParameter(
                name="genres",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter plays by genre id.",
            ),
            OpenApiParameter(
                name="actors",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter plays by actor id.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search plays by title.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve play",
        description="Retrieve detailed information about a play.",
        tags=["Theatre"],
    ),
    create=extend_schema(
        summary="Create play",
        description="Create a new play. Admin only.",
        tags=["Theatre"],
    ),
    update=extend_schema(
        summary="Update play",
        description="Fully update a play. Admin only.",
        tags=["Theatre"],
    ),
    partial_update=extend_schema(
        summary="Partially update play",
        description="Partially update a play. Admin only.",
        tags=["Theatre"],
    ),
    destroy=extend_schema(
        summary="Delete play",
        description="Delete a play. Admin only.",
        tags=["Theatre"],
    ),
)
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

    @extend_schema(
        summary="Upload play image",
        description="Upload or replace a poster/image for a play. Admin only.",
        tags=["Theatre"],
        request={
            "multipart/form-data": inline_serializer(
                name="PlayImageUpload",
                fields={
                    "image": serializers.ImageField()
                },
            )
        },
        responses={200: PlayImageSerializer},
    )
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


@extend_schema_view(
    list=extend_schema(
        summary="List performances",
        description="Retrieve a list of performances "
                    "with filtering and ordering.",
        tags=["Theatre"],
        parameters=[
            OpenApiParameter(
                name="play",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter performances by play id.",
            ),
            OpenApiParameter(
                name="theatre_hall",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter performances by theatre hall id.",
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Order by show_time. "
                            "Use `show_time` or `-show_time`.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve performance",
        description="Retrieve detailed information about a performance.",
        tags=["Theatre"],
    ),
    create=extend_schema(
        summary="Create performance",
        description="Create a new performance. Admin only.",
        tags=["Theatre"],
    ),
    update=extend_schema(
        summary="Update performance",
        description="Fully update a performance. Admin only.",
        tags=["Theatre"],
    ),
    partial_update=extend_schema(
        summary="Partially update performance",
        description="Partially update a performance. Admin only.",
        tags=["Theatre"],
    ),
    destroy=extend_schema(
        summary="Delete performance",
        description="Delete a performance. Admin only.",
        tags=["Theatre"],
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List my reservations",
        description="Retrieve reservations created "
                    "by the current authenticated user.",
        tags=["Reservations"],
    ),
    retrieve=extend_schema(
        summary="Retrieve my reservation",
        description="Retrieve detailed information about one "
                    "of the current user's reservations.",
        tags=["Reservations"],
    ),
    create=extend_schema(
        summary="Create reservation",
        description="Create a reservation for the current authenticated user.",
        tags=["Reservations"],
        examples=[
            OpenApiExample(
                "Reservation example",
                value={
                    "tickets": [
                        {
                            "row": 1,
                            "seat": 1,
                            "performance": 1,
                        },
                        {
                            "row": 1,
                            "seat": 2,
                            "performance": 1,
                        },
                    ]
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        summary="Update reservation",
        description="Update a reservation for the current authenticated user.",
        tags=["Reservations"],
    ),
    partial_update=extend_schema(
        summary="Partially update reservation",
        description="Partially update a reservation "
                    "for the current authenticated user.",
        tags=["Reservations"],
    ),
    destroy=extend_schema(
        summary="Delete reservation",
        description="Delete a reservation for the current authenticated user.",
        tags=["Reservations"],
    ),
)
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

from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from theatre.views import (
    ActorViewSet,
    GenreViewSet,
    PlayViewSet,
    TheatreHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
)


class CustomDefaultRouter(DefaultRouter):
    def get_api_root_view(self, api_urls=None):
        api_root_view = super().get_api_root_view(api_urls=api_urls)
        api_root_view.cls.permission_classes = [permissions.AllowAny]
        return api_root_view


router = CustomDefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("theatre-halls", TheatreHallViewSet)
router.register("plays", PlayViewSet)
router.register("performances", PerformanceViewSet)
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = router.urls

app_name = "theatre"

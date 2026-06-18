from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.serializers import UserSerializer


@extend_schema(
    summary="Register new user",
    description="Create a new user account. No authentication required.",
    tags=["User"],
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


@extend_schema(
    summary="Manage current user",
    description=(
        "Retrieve or update the profile of the currently authenticated user. "
        "Requires JWT Bearer token."
    ),
    tags=["User"],
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

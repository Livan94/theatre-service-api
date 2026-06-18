from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

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


@extend_schema(
    summary="Obtain JWT token pair",
    description="Get access and refresh tokens for an existing user.",
    tags=["User"],
)
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)


@extend_schema(
    summary="Refresh JWT access token",
    description="Get a new access token using a valid refresh token.",
    tags=["User"],
)
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)


@extend_schema(
    summary="Verify JWT token",
    description="Verify whether a token is valid.",
    tags=["User"],
)
class CustomTokenVerifyView(TokenVerifyView):
    permission_classes = (AllowAny,)

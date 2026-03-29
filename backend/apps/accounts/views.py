from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import (
    PatientCreateSerializer,
    RegisterSerializer,
    StaffUserCreateSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": getattr(user, "role", None),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    requested_role = request.data.get("role")
    if requested_role and requested_role != User.Role.PATIENT:
        return Response(
            {"role": ["El registro publico solo permite usuarios PATIENT."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_patient_user(request):
    if getattr(request.user, "role", None) != User.Role.CLINIC and not request.user.is_superuser:
        raise PermissionDenied("Solo CLINIC o admin puede crear pacientes.")

    serializer = PatientCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_staff_user(request):
    user = request.user
    allowed = user.is_superuser or getattr(user, "role", None) == User.Role.CLINIC
    if not allowed:
        raise PermissionDenied("Solo CLINIC o admin puede crear personal.")

    serializer = StaffUserCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    created_user = serializer.save()
    return Response(StaffUserCreateSerializer(created_user).data, status=status.HTTP_201_CREATED)

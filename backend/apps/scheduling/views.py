from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsClinic

from .models import Appointment, Service, AppointmentService
from .serializers import (
    AppointmentSerializer,
    ServiceSerializer,
    AppointmentServiceSerializer,
)


# ============================
# APPOINTMENTS
# ============================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def appointments(request):
    if request.method == "GET":
        qs = Appointment.objects.filter(
            patient=request.user
        ).order_by("-scheduled_at")
        return Response(
            AppointmentSerializer(qs, many=True).data,
            status=status.HTTP_200_OK
        )

    serializer = AppointmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    scheduled_at = serializer.validated_data.get("scheduled_at")
    if scheduled_at and scheduled_at <= timezone.now():
        return Response(
            {"detail": "scheduled_at must be in the future"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        appt = Appointment.objects.create(
            patient=request.user,
            **serializer.validated_data
        )
    except IntegrityError:
        return Response(
            {"detail": "Ya existe una cita para este usuario en esa fecha/hora."},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        AppointmentSerializer(appt).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def appointment_detail(request, pk: int):
    appt = get_object_or_404(
        Appointment.objects.select_related("patient"),
        pk=pk,
        patient=request.user
    )

    if request.method == "GET":
        return Response(
            AppointmentSerializer(appt).data,
            status=status.HTTP_200_OK
        )

    if request.method == "PATCH":
        serializer = AppointmentSerializer(
            appt,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        new_scheduled_at = serializer.validated_data.get("scheduled_at")
        if new_scheduled_at and new_scheduled_at <= timezone.now():
            return Response(
                {"detail": "scheduled_at must be in the future"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Ya existe una cita para este usuario en esa fecha/hora."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    appt.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
# SERVICES
# ============================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def services(request):
    if request.method == "GET":
        qs = Service.objects.all().order_by("-is_active", "name")
        return Response(
            ServiceSerializer(qs, many=True).data,
            status=status.HTTP_200_OK
        )

    # POST -> solo CLINIC
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response(
            {"detail": perm.message},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = ServiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = serializer.save()

    return Response(
        ServiceSerializer(service).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def service_detail(request, pk: int):
    service = get_object_or_404(Service, pk=pk)

    if request.method == "GET":
        return Response(
            ServiceSerializer(service).data,
            status=status.HTTP_200_OK
        )

    # PATCH y DELETE -> solo CLINIC
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response(
            {"detail": perm.message},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == "PATCH":
        serializer = ServiceSerializer(
            service,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    service.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
# APPOINTMENT SERVICES
# ============================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def appointment_services(request, pk: int):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        patient=request.user
    )

    if request.method == "GET":
        qs = AppointmentService.objects.filter(
            appointment=appointment
        ).select_related("service")

        return Response(
            AppointmentServiceSerializer(qs, many=True).data,
            status=status.HTTP_200_OK
        )

    service_id = request.data.get("service_id")
    quantity = request.data.get("quantity", 1)

    if not service_id:
        return Response(
            {"detail": "service_id es requerido."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return Response(
            {"detail": "quantity debe ser entero."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {"detail": "quantity debe ser >= 1."},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = get_object_or_404(Service, pk=service_id)

    try:
        appt_service = AppointmentService.objects.create(
            appointment=appointment,
            service=service,
            quantity=quantity,
            price_at_booking=service.base_price,
        )
    except IntegrityError:
        return Response(
            {"detail": "Este servicio ya está agregado a la cita."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        AppointmentServiceSerializer(appt_service).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def appointment_service_detail(request, pk: int, item_id: int):
    item = get_object_or_404(
        AppointmentService,
        pk=item_id,
        appointment_id=pk,
        appointment__patient=request.user,
    )

    if request.method == "PATCH":
        quantity = request.data.get("quantity")

        if quantity is None:
            return Response(
                {"detail": "quantity es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {"detail": "quantity debe ser entero."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 1:
            return Response(
                {"detail": "quantity debe ser >= 1."},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])

        return Response(
            AppointmentServiceSerializer(item).data,
            status=status.HTTP_200_OK
        )

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
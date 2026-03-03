from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.accounts.permissions import IsDoctor
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsClinic

from .models import Appointment, Service, AppointmentService, MedicalRecord
from .serializers import (
    AppointmentSerializer,
    ServiceSerializer,
    AppointmentServiceSerializer,
    MedicalRecordSerializer,
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


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_doctor(request, pk: int):
    appointment = get_object_or_404(Appointment, pk=pk)

    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    doctor_id = request.data.get("doctor_id")
    if not doctor_id:
        return Response({"detail": "doctor_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    doctor = get_object_or_404(User, pk=doctor_id, role=User.Role.DOCTOR)

    appointment.doctor = doctor
    appointment.status = Appointment.Status.CONFIRMED
    appointment.save(update_fields=["doctor", "status", "updated_at"])

    return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def doctor_appointments(request):
    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    qs = (
        Appointment.objects
        .filter(doctor=request.user)
        .order_by("-scheduled_at")
    )
    return Response(AppointmentSerializer(qs, many=True).data, status=status.HTTP_200_OK)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def doctor_update_appointment_status(request, pk: int):
    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)

    new_status = request.data.get("status")
    allowed = {Appointment.Status.COMPLETED, Appointment.Status.CANCELLED}

    if new_status not in allowed:
        return Response(
            {"detail": f"status inválido. Permitidos: {', '.join(sorted(allowed))}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appointment.status = new_status
    appointment.save(update_fields=["status", "updated_at"])

    return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def doctor_update_appointment(request, pk: int):
    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    appt = get_object_or_404(Appointment, pk=pk, doctor=request.user)

    allowed_fields = {"reason", "scheduled_at"}
    data = {k: v for k, v in request.data.items() if k in allowed_fields}

    if not data:
        return Response(
            {"detail": "No hay campos válidos para actualizar. Permitidos: reason, scheduled_at"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validar fecha si viene
    if "scheduled_at" in data and data["scheduled_at"]:
        # AppointmentSerializer ya valida que sea futuro, pero esto evita bypass si cambias el serializer
        try:
            serializer = AppointmentSerializer(appt, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
        except Exception:
            raise
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = AppointmentSerializer(appt, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def appointment_medical_records(request, pk: int):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        pk=pk,
    )

    user = request.user
    is_patient_owner = appointment.patient_id == user.id
    is_assigned_doctor = appointment.doctor_id == user.id
    is_clinic = getattr(user, "role", None) == "CLINIC"

    # GET: patient dueño, doctor asignado o clinic
    if request.method == "GET":
        if not (is_patient_owner or is_assigned_doctor or is_clinic):
            return Response({"detail": "No tienes permiso para ver los records de esta cita."}, status=status.HTTP_403_FORBIDDEN)

        qs = MedicalRecord.objects.filter(appointment=appointment).select_related("doctor")
        return Response(MedicalRecordSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    # POST: solo doctor asignado
    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    if not is_assigned_doctor:
        return Response({"detail": "Solo el doctor asignado puede crear records en esta cita."}, status=status.HTTP_403_FORBIDDEN)

    serializer = MedicalRecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    record = serializer.save(appointment=appointment, doctor=user)

    return Response(MedicalRecordSerializer(record).data, status=status.HTTP_201_CREATED)

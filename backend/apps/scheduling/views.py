from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsClinic, IsDoctor
from apps.accounts.permissions import IsClinic, IsDoctor, IsClinicOrDoctor




from .models import Appointment, Service, AppointmentService, MedicalRecord, DoctorSchedule, AppointmentReminder, TelemedicineSession, DigitalPrescription
from .serializers import (
    AppointmentSerializer,
    ServiceSerializer,
    AppointmentServiceSerializer,
    MedicalRecordSerializer,
    DoctorScheduleSerializer,
    AppointmentReminderSerializer,
    TelemedicineSessionSerializer,
    DigitalPrescriptionSerializer,
)


# ============================
# APPOINTMENTS
# ============================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def appointments(request):
    if request.method == "GET":
        qs = Appointment.objects.filter(patient=request.user).order_by("-scheduled_at")
        return Response(AppointmentSerializer(qs, many=True).data, status=status.HTTP_200_OK)

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

    return Response(AppointmentSerializer(appt).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def appointment_detail(request, pk: int):
    appt = get_object_or_404(
        Appointment.objects.select_related("patient"),
        pk=pk,
        patient=request.user
    )

    if request.method == "GET":
        return Response(AppointmentSerializer(appt).data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = AppointmentSerializer(appt, data=request.data, partial=True)
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
        return Response(ServiceSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    serializer = ServiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    service = serializer.save()
    return Response(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def service_detail(request, pk: int):
    service = get_object_or_404(Service, pk=pk)

    if request.method == "GET":
        return Response(ServiceSerializer(service).data, status=status.HTTP_200_OK)

    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = ServiceSerializer(service, data=request.data, partial=True)
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
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)

    if request.method == "GET":
        qs = AppointmentService.objects.filter(appointment=appointment).select_related("service")
        return Response(AppointmentServiceSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    service_id = request.data.get("service_id")
    quantity = request.data.get("quantity", 1)

    if not service_id:
        return Response({"detail": "service_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return Response({"detail": "quantity debe ser entero."}, status=status.HTTP_400_BAD_REQUEST)

    if quantity < 1:
        return Response({"detail": "quantity debe ser >= 1."}, status=status.HTTP_400_BAD_REQUEST)

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
            {"detail": "Este servicio ya esta agregado a la cita."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(AppointmentServiceSerializer(appt_service).data, status=status.HTTP_201_CREATED)


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
            return Response({"detail": "quantity es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({"detail": "quantity debe ser entero."}, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({"detail": "quantity debe ser >= 1."}, status=status.HTTP_400_BAD_REQUEST)

        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return Response(AppointmentServiceSerializer(item).data, status=status.HTTP_200_OK)

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================
# CLINIC / DOCTOR WORKFLOW
# ============================

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

    qs = Appointment.objects.filter(doctor=request.user).order_by("-scheduled_at")
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
            {"detail": f"status invalido. Permitidos: {', '.join(sorted(allowed))}"},
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
            {"detail": "No hay campos validos para actualizar. Permitidos: reason, scheduled_at"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = AppointmentSerializer(appt, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============================
# MEDICAL RECORDS
# ============================

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

    if request.method == "GET":
        if not (is_patient_owner or is_assigned_doctor or is_clinic):
            return Response(
                {"detail": "No tienes permiso para ver los records de esta cita."},
                status=status.HTTP_403_FORBIDDEN
            )

        qs = MedicalRecord.objects.filter(appointment=appointment).select_related("doctor")
        return Response(MedicalRecordSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    if not is_assigned_doctor:
        return Response(
            {"detail": "Solo el doctor asignado puede crear records en esta cita."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = MedicalRecordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    record = serializer.save(appointment=appointment, doctor=user)
    return Response(MedicalRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def appointment_medical_record_detail(request, pk: int, record_id: int):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    record = get_object_or_404(
        MedicalRecord.objects.select_related("doctor"),
        pk=record_id,
        appointment=appointment,
    )

    user = request.user
    is_patient_owner = appointment.patient_id == user.id
    is_assigned_doctor = appointment.doctor_id == user.id
    is_clinic = getattr(user, "role", None) == "CLINIC"

    if request.method == "GET":
        if not (is_patient_owner or is_assigned_doctor or is_clinic):
            return Response(
                {"detail": "No tienes permiso para ver este record."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(MedicalRecordSerializer(record).data, status=status.HTTP_200_OK)

    perm = IsDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    if not is_assigned_doctor:
        return Response(
            {"detail": "Solo el doctor asignado puede modificar este record."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "PATCH":
        allowed_fields = {"diagnosis", "notes", "treatment"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not data:
            return Response(
                {"detail": "No hay campos validos para actualizar. Permitidos: diagnosis, notes, treatment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MedicalRecordSerializer(record, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    record.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def clinic_appointments(request):
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    qs = Appointment.objects.select_related("patient", "doctor").order_by("-scheduled_at")

    status_param = request.query_params.get("status")
    doctor_id = request.query_params.get("doctor_id")
    date_from = request.query_params.get("date_from")  # YYYY-MM-DD
    date_to = request.query_params.get("date_to")      # YYYY-MM-DD

    if status_param:
        valid_status = {choice[0] for choice in Appointment.Status.choices}
        if status_param not in valid_status:
            return Response({"detail": "status inválido."}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(status=status_param)

    if doctor_id:
        qs = qs.filter(doctor_id=doctor_id)

    if date_from:
        d_from = parse_date(date_from)
        if not d_from:
            return Response({"detail": "date_from inválido. Usa YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(scheduled_at__date__gte=d_from)

    if date_to:
        d_to = parse_date(date_to)
        if not d_to:
            return Response({"detail": "date_to inválido. Usa YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(scheduled_at__date__lte=d_to)

    return Response(AppointmentSerializer(qs, many=True).data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    perm = IsClinicOrDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    qs = Appointment.objects.all()

    # Si es DOCTOR, ve solo sus citas
    if getattr(request.user, "role", None) == "DOCTOR":
        qs = qs.filter(doctor=request.user)

    today = timezone.now().date()

    total = qs.count()
    pending = qs.filter(status=Appointment.Status.PENDING).count()
    confirmed = qs.filter(status=Appointment.Status.CONFIRMED).count()
    completed = qs.filter(status=Appointment.Status.COMPLETED).count()
    cancelled = qs.filter(status=Appointment.Status.CANCELLED).count()
    today_count = qs.filter(scheduled_at__date=today).count()

    # Alto riesgo en triage (si existe triage para la cita)
    high_risk = qs.filter(triage_assessment__risk_level="HIGH").count()

    data = {
        "scope": "DOCTOR" if getattr(request.user, "role", None) == "DOCTOR" else "CLINIC",
        "date": str(today),
        "appointments": {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "today": today_count,
        },
        "triage": {
            "high_risk": high_risk
        },
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_trends(request):
    perm = IsClinicOrDoctor()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    days_param = request.query_params.get("days", "7")
    try:
        days = int(days_param)
    except ValueError:
        return Response({"detail": "days invalido."}, status=status.HTTP_400_BAD_REQUEST)

    if days not in (7, 30):
        return Response({"detail": "days debe ser 7 o 30."}, status=status.HTTP_400_BAD_REQUEST)

    qs = Appointment.objects.all()

    if getattr(request.user, "role", None) == "DOCTOR":
        qs = qs.filter(doctor=request.user)

    today = timezone.now().date()
    start_date = today - timezone.timedelta(days=days - 1)

    points = []
    for i in range(days):
        d = start_date + timezone.timedelta(days=i)
        day_qs = qs.filter(scheduled_at__date=d)

        points.append({
            "date": str(d),
            "total": day_qs.count(),
            "pending": day_qs.filter(status=Appointment.Status.PENDING).count(),
            "confirmed": day_qs.filter(status=Appointment.Status.CONFIRMED).count(),
            "completed": day_qs.filter(status=Appointment.Status.COMPLETED).count(),
            "cancelled": day_qs.filter(status=Appointment.Status.CANCELLED).count(),
        })

    data = {
        "scope": "DOCTOR" if getattr(request.user, "role", None) == "DOCTOR" else "CLINIC",
        "days": days,
        "points": points,
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def doctor_schedules(request):
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        qs = DoctorSchedule.objects.select_related("doctor").order_by("doctor_id", "day_of_week", "start_time")
        return Response(DoctorScheduleSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    serializer = DoctorScheduleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    doctor = serializer.validated_data["doctor"]
    if getattr(doctor, "role", None) != "DOCTOR":
        return Response({"detail": "El usuario seleccionado no tiene rol DOCTOR."}, status=status.HTTP_400_BAD_REQUEST)

    item = serializer.save()
    return Response(DoctorScheduleSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def doctor_schedule_detail(request, schedule_id: int):
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    item = get_object_or_404(DoctorSchedule.objects.select_related("doctor"), pk=schedule_id)

    if request.method == "GET":
        return Response(DoctorScheduleSerializer(item).data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = DoctorScheduleSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        doctor = serializer.validated_data.get("doctor")
        if doctor and getattr(doctor, "role", None) != "DOCTOR":
            return Response({"detail": "El usuario seleccionado no tiene rol DOCTOR."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def appointment_reschedule(request, pk: int):
    appt = get_object_or_404(
        Appointment.objects.select_related("patient"),
        pk=pk,
        patient=request.user,
    )

    new_scheduled_at = request.data.get("scheduled_at")
    if not new_scheduled_at:
        return Response(
            {"detail": "scheduled_at es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = AppointmentSerializer(appt, data={"scheduled_at": new_scheduled_at}, partial=True)
    serializer.is_valid(raise_exception=True)

    try:
        serializer.save()
    except IntegrityError:
        return Response(
            {"detail": "Ya existe una cita para este usuario en esa fecha/hora."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def appointment_reminders(request, pk: int):
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "GET":
        qs = AppointmentReminder.objects.filter(appointment=appointment).order_by("-scheduled_for")
        return Response(AppointmentReminderSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    serializer = AppointmentReminderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reminder = serializer.save(appointment=appointment)
    return Response(AppointmentReminderSerializer(reminder).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_appointment_reminder(request, pk: int, reminder_id: int):
    perm = IsClinic()
    if not perm.has_permission(request, None):
        return Response({"detail": perm.message}, status=status.HTTP_403_FORBIDDEN)

    appointment = get_object_or_404(Appointment, pk=pk)
    reminder = get_object_or_404(AppointmentReminder, pk=reminder_id, appointment=appointment)

    # Simulación MVP de envío (sin proveedor externo aún)
    reminder.status = AppointmentReminder.Status.SENT
    reminder.sent_at = timezone.now()
    reminder.error_message = ""
    reminder.save(update_fields=["status", "sent_at", "error_message", "updated_at"])

    return Response(AppointmentReminderSerializer(reminder).data, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAuthenticated])
def appointment_telemedicine(request, pk: int):
    appointment = get_object_or_404(Appointment.objects.select_related("patient", "doctor"), pk=pk)

    role = getattr(request.user, "role", None)
    is_clinic = role == "CLINIC"
    is_assigned_doctor = appointment.doctor_id == request.user.id
    is_patient_owner = appointment.patient_id == request.user.id

    session = TelemedicineSession.objects.filter(appointment=appointment).first()

    # GET: patient dueño, doctor asignado o clinic
    if request.method == "GET":
        if not (is_clinic or is_assigned_doctor or is_patient_owner):
            return Response({"detail": "No tienes permiso para ver la sesion."}, status=status.HTTP_403_FORBIDDEN)

        if not session:
            return Response({"detail": "No existe sesion de telemedicina para esta cita."}, status=status.HTTP_404_NOT_FOUND)

        return Response(TelemedicineSessionSerializer(session).data, status=status.HTTP_200_OK)

    # POST: clinic o doctor asignado
    if request.method == "POST":
        if not (is_clinic or is_assigned_doctor):
            return Response({"detail": "Solo CLINIC o DOCTOR asignado puede crear la sesion."}, status=status.HTTP_403_FORBIDDEN)

        if session:
            return Response({"detail": "Ya existe sesion para esta cita."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TelemedicineSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = serializer.save(appointment=appointment)
        return Response(TelemedicineSessionSerializer(created).data, status=status.HTTP_201_CREATED)

    # PATCH: clinic o doctor asignado
    if not (is_clinic or is_assigned_doctor):
        return Response({"detail": "Solo CLINIC o DOCTOR asignado puede editar la sesion."}, status=status.HTTP_403_FORBIDDEN)

    if not session:
        return Response({"detail": "No existe sesion de telemedicina para esta cita."}, status=status.HTTP_404_NOT_FOUND)

    serializer = TelemedicineSessionSerializer(session, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST", "PATCH"])
@permission_classes([IsAuthenticated])
def telemedicine_prescription(request, pk: int):
    session = get_object_or_404(
        TelemedicineSession.objects.select_related("appointment__patient", "appointment__doctor"),
        pk=pk,
    )
    appointment = session.appointment

    role = getattr(request.user, "role", None)
    is_clinic = role == "CLINIC"
    is_assigned_doctor = appointment.doctor_id == request.user.id
    is_patient_owner = appointment.patient_id == request.user.id

    prescription = DigitalPrescription.objects.filter(telemedicine_session=session).first()

    # GET: patient dueño, doctor asignado o clinic
    if request.method == "GET":
        if not (is_clinic or is_assigned_doctor or is_patient_owner):
            return Response({"detail": "No tienes permiso para ver la receta."}, status=status.HTTP_403_FORBIDDEN)

        if not prescription:
            return Response({"detail": "No existe receta para esta sesion."}, status=status.HTTP_404_NOT_FOUND)

        return Response(DigitalPrescriptionSerializer(prescription).data, status=status.HTTP_200_OK)

    # POST: clinic o doctor asignado
    if request.method == "POST":
        if not (is_clinic or is_assigned_doctor):
            return Response({"detail": "Solo CLINIC o DOCTOR asignado puede crear receta."}, status=status.HTTP_403_FORBIDDEN)

        if prescription:
            return Response({"detail": "Ya existe receta para esta sesion."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DigitalPrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = serializer.save(telemedicine_session=session, doctor=request.user)
        return Response(DigitalPrescriptionSerializer(created).data, status=status.HTTP_201_CREATED)

    # PATCH: clinic o doctor asignado
    if not (is_clinic or is_assigned_doctor):
        return Response({"detail": "Solo CLINIC o DOCTOR asignado puede editar receta."}, status=status.HTTP_403_FORBIDDEN)

    if not prescription:
        return Response({"detail": "No existe receta para esta sesion."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DigitalPrescriptionSerializer(prescription, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)

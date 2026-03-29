from django.utils import timezone
from rest_framework import serializers
from .models import (
    Appointment, 
    Service, 
    AppointmentService, 
    MedicalRecord, 
    DoctorSchedule, 
    AppointmentReminder,
    TelemedicineSession,
    DigitalPrescription,
)



class AppointmentServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    duration_minutes = serializers.IntegerField(source="service.duration_minutes", read_only=True)

    class Meta:
        model = AppointmentService
        fields = [
            "id",
            "service",
            "service_name",
            "duration_minutes",
            "quantity",
            "price_at_booking",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    # ✅ nuevo: doctor visible (id)
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)

    # ✅ ya lo tenías: resumen de servicios y totales
    services = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "scheduled_at",
            "reason",
            "status",
            "doctor",
            "services",
            "total_duration_minutes",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "doctor",
            "services",
            "total_duration_minutes",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("No se puede agendar una cita en el pasado.")
        return value

    def get_services(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj).select_related("service")
        return AppointmentServiceSerializer(qs, many=True).data

    def get_total_duration_minutes(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj).select_related("service")
        return sum((item.service.duration_minutes or 0) * (item.quantity or 1) for item in qs)

    def get_total_price(self, obj):
        qs = AppointmentService.objects.filter(appointment=obj)
        total = 0
        for item in qs:
            price = item.price_at_booking or 0
            qty = item.quantity or 1
            total += price * qty
        return total


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "duration_minutes",
            "base_price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class MedicalRecordSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(source="doctor.username", read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "appointment",
            "doctor",
            "doctor_username",
            "diagnosis",
            "notes",
            "treatment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "appointment", "doctor", "doctor_username", "created_at", "updated_at"]

class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(source="doctor.username", read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            "id",
            "doctor",
            "doctor_username",
            "day_of_week",
            "start_time",
            "end_time",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "doctor_username", "created_at", "updated_at"]

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("start_time debe ser menor que end_time.")
        return attrs

class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = [
            "id",
            "appointment",
            "channel",
            "scheduled_for",
            "sent_at",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "appointment", "sent_at", "status", "error_message", "created_at", "updated_at"]


class TelemedicineSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineSession
        fields = [
            "id",
            "appointment",
            "meeting_url",
            "access_code",
            "status",
            "started_at",
            "ended_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "appointment", "created_at", "updated_at"]


class DigitalPrescriptionSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(source="doctor.username", read_only=True)

    class Meta:
        model = DigitalPrescription
        fields = [
            "id",
            "telemedicine_session",
            "doctor",
            "doctor_username",
            "indications",
            "medications",
            "recommendations",
            "issued_at",
        ]
        read_only_fields = ["id", "telemedicine_session", "doctor", "doctor_username", "issued_at"]

